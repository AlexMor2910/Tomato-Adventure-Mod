"""Read-only fixed actor Binky census; event rewards and node ownership are partial.

Every output must be a new file. Uses only the standard library and the existing
local Thumb decoder. No game execution, state access, or ROM writes.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analyze'))
from thumb_inspect import decode, inspect

BUS = 0x08000000
MAP_TABLE = 0x62D3E4
MAP_COUNT = 494
MAP_STRIDE = 0x1C
JP_SHA = '0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12'
EN_SHA = '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde'
EVENT_DOMAIN = (0xF9000, 0x15BA3C)
EXCHANGES = {0x107F73, 0x107FAA, 0x108118, 0x10814F, 0x108186}
WINDOWS = {
	'map_actor_registration': [(0x3F8A4, 0x3F8D8)],
	'actor_coordinates': [(0x3440C, 0x34428)],
	'actor_collection_read': [(0x34498, 0x344BE)],
	'interaction': [(0x6974A, 0x697A0)],
	'pickup': [(0x69C0C, 0x69C62), (0x69C78, 0x69CC2), (0x69CDC, 0x69D02)],
	'bit_read': [(0x69F60, 0x69F84)],
	'bit_set': [(0x69F8C, 0x69FB2)],
	'actor_bank': [(0x6AFB8, 0x6B01A), (0x6B02C, 0x6B0A6)],
	'initializer_flag_branch': [(0x27778, 0x2779C), (0x277A0, 0x277AA)],
	'inventory': [(0x80424, 0x80442), (0x8045C, 0x80490)],
	'event_reward_FE55': [(0x25634, 0x25654)],
	'arrival_dispatch': [(0x88AF0, 0x88B00), (0x88C38, 0x88C40)],
	'FE7C_map': [(0x2A0A0, 0x2A0CC)],
	'FE7D_map': [(0x2A134, 0x2A160)],
	'overworld_exit': [(0x69A2A, 0x69A58)],
}


def hx(n):
	return f'0x{n:08X}'


def mid(n):
	return f'0x{n:04X}'


def sha(data):
	return hashlib.sha256(data).hexdigest()


def u16(rom, offset):
	return struct.unpack_from('<H', rom, offset)[0]


def pointer(rom, offset, size=1):
	value = struct.unpack_from('<I', rom, offset)[0] - BUS
	if not 0 <= value <= len(rom) - size:
		raise ValueError(f'Out-of-bounds pointer at {hx(offset)}')
	return value


def node_names(text):
	block = text.split('BLOCKFIXED 49F61C 10 11 0A', 1)[1].split('BLOCKFIXED', 1)[0]
	pairs = re.findall(r'^([0-9A-Fa-f]{2})-E:(.*)$', block, re.MULTILINE)
	result = {int(k, 16): v.strip() for k, v in pairs}
	if len(pairs) != 17 or set(result) != set(range(17)):
		raise ValueError('Unexpected overworld node name IDs')
	return result


def node_components(graph, seeds):
	"""Undirected exit-component candidates, never an ownership proof."""
	result = {}
	for origin in sorted(graph):
		if origin in result:
			continue
		pending, component = [origin], set()
		while pending:
			current = pending.pop()
			if current in component:
				continue
			component.add(current)
			pending.extend(graph[current] - component)
		candidates = sorted(set().union(*(seeds.get(m, set()) for m in component)))
		for m in component:
			result[m] = candidates
	return result


def canonicalize(rows):
	"""Global collection identity prevents alias registrations counting twice."""
	groups = collections.defaultdict(list)
	for row in rows:
		groups[row['binky_id']].append(row)
	result = []
	for key, group in sorted(groups.items()):
		if len({(r['quantity'], r['source_type'], r['repeatable']) for r in group}) != 1:
			raise ValueError('Conflicting rewards share one collection identity: ' + key)
		row = dict(group[0])
		row['registration_count'] = len(group)
		row['registration_addresses'] = '|'.join(sorted({r['object_record_address'] for r in group}))
		row['possible_map_ids'] = '|'.join(sorted({r['map_id'] for r in group}))
		if len({r['map_id'] for r in group}) != 1:
			row.update(map_id='', node_id='', node_name='', node_confidence='Unresolved',
				limitations='Shared collection identity registered in multiple maps; excluded from assigned room/node subtotals')
		result.append(row)
	return result


def totals(rows):
	"""Only verified, nonrepeatable fixed rows enter fixed quantity subtotals."""
	fixed = [r for r in rows if r['source_type'] == 'fixed_actor_pickup' and r['repeatable'] == 'false' and r['confidence'] == 'Confirmed static']
	conditional = [r for r in rows if r['source_type'] == 'conditional_one_time_reward' and r['repeatable'] == 'false' and r['confidence'] == 'Confirmed static']
	return dict(fixed_binky_pickups=len(fixed), fixed_binky_quantity=sum(int(r['quantity']) for r in fixed),
		conditional_binky_quantity=sum(int(r['quantity']) for r in conditional) if conditional else '',
		unresolved_binky_candidates='', complete_total_quantity='',
		confidence='Confirmed static')


def extract(rom, menus):
	if len(rom) != 0x800000 or sha(rom) not in (JP_SHA, EN_SHA):
		raise ValueError('Expected fingerprinted original Japanese or untouched English baseline')
	end = MAP_TABLE + MAP_COUNT * MAP_STRIDE
	if end != 0x6309EC or end > len(rom) or rom[end:end + 28] != b'9' * 28:
		raise ValueError('Map table boundary mismatch')
	if rom[0x63A01C:0x63A024] != bytes([1,2,4,8,16,32,64,128]):
		raise ValueError('Collection flag mask table mismatch')
	names = node_names(menus)
	graph = {m: set() for m in range(MAP_COUNT)}
	seeds = collections.defaultdict(set)
	maps, actors, exits, pickups = [], [], [], []
	for m in range(MAP_COUNT):
		record = MAP_TABLE + m * MAP_STRIDE
		actor_block = pointer(rom, record + 20, 112 + 16)
		exit_base = pointer(rom, record + 12)
		maps.append(dict(map_id=mid(m), map_record_address=hx(BUS + record), actor_block_address=hx(BUS + actor_block)))
		for k in range(64):
			a = exit_base + k * 10
			if a >= len(rom):
				raise ValueError('Exit list outside ROM')
			if rom[a] == 255:
				break
			if a + 10 > len(rom):
				raise ValueError('Truncated exit')
			destination = u16(rom, a + 4)
			exits.append(dict(map_id=mid(m), address=hx(BUS + a), raw_hex=rom[a:a + 10].hex(' '), destination=mid(destination)))
			if destination & 0x8000:
				node = (destination & 255) - 1
				if not 0 <= node < 17:
					raise ValueError('Unknown overworld exit encoding')
				seeds[m].add(node)
			elif destination < MAP_COUNT:
				graph[m].add(destination)
				graph[destination].add(m)
			else:
				raise ValueError('Unknown map exit destination')
		else:
			raise ValueError('Exit list exceeded 64-record analysis bound')
		for k in range(15):
			a = actor_block + 112 + k * 16
			if a + 16 > len(rom):
				raise ValueError('Actor list outside ROM')
			if rom[a] == 255:
				break
			ident = u16(rom, a + 14)
			if ident >= 0xC00:
				raise ValueError('Actor collection ID exceeds serialized bank')
			actors.append(dict(map_id=mid(m), address=hx(BUS + a), collection_id=ident))
			if not rom[a + 1] & 128:
				continue
			payload = pointer(rom, a + 10)
			if rom[payload] != 0x37:
				continue
			init = pointer(rom, a + 6, 29)
			# Four variants have one leading configuration command, then the
			# identical self-loop and collection-bit guard. Do not name its effect.
			lead = 5 if rom[init:init + 5] == bytes.fromhex('01 fd 71 e1 00') else 0
			prefix = rom[init + lead:init + lead + 24]
			# Exact common Binky initializer: FD5B branches on this same actor ID.
			standard = (prefix[:7] == bytes.fromhex('01 fd 71 c2 01 fd 5b') and
				u16(prefix, 7) == ident and prefix[9:13] == bytes.fromhex('9d 0d 10 08') and
				prefix[13:20] == bytes.fromhex('00 fd 71 04 00 fd 30') and
				int.from_bytes(prefix[20:24], 'little') == BUS + init + lead)
			pickups.append(dict(binky_id=f'actor-flag-{ident:04X}', map_id=mid(m), room_name='',
				node_id='', node_name='', x=rom[a + 3], y=rom[a + 4], coordinate_units='encoded actor grid coordinates',
				quantity=1, source_type='fixed_actor_pickup' if standard else 'unresolved_actor_pickup',
				collection_flag=mid(ident), collection_flag_ram=hx(0x03003107 + (ident >> 3)),
				collection_flag_mask=f'0x{1 << (ident & 7):02X}', event_script_address=hx(BUS + init),
				object_record_address=hx(BUS + a), object_record_file_offset=hx(a), payload_address=hx(BUS + payload),
				repeatable='false' if standard else '', confidence='Confirmed static' if standard else 'Candidate',
				node_confidence='Unresolved', evidence_reference='map_actor_registration;interaction;pickup;bit_read;bit_set;initializer_flag_branch',
				limitations='Fixed actor subtype only; story reachability and event rewards not exhaustively decoded',
				initializer_hex=rom[init:init + lead + 24].hex(' '), initializer_guard_offset=lead,
				object_hex=rom[a:a + 16].hex(' ')))
	if len(actors) != 2987:
		raise ValueError('Established actor census mismatch')
	arrivals = []
	for node in range(17):
		case = pointer(rom, 0x88B04 + node * 4, 4)
		if decode(rom, case).text == 'bx r14':
			arrivals.append(dict(node_id=f'0x{node:02X}', node_name=names[node], case_bus=hx(BUS + case),
				script_bus='', script_prefix='', map_id='', limitation='dispatch returns without selecting arrival'))
			continue
		instruction = decode(rom, case + 2)
		if instruction.literal_value is None or not instruction.text.startswith('ldr r0,'):
			raise ValueError('Unknown node arrival case')
		script = instruction.literal_value - BUS
		if not 0 <= script < len(rom) - 4 or rom[script:script + 2] not in (b'\xfe\x7c', b'\xfe\x7d'):
			raise ValueError('Unknown arrival script prefix')
		destination = u16(rom, script + 2)
		if destination >= MAP_COUNT:
			raise ValueError('Arrival map outside table')
		seeds[destination].add(node)
		arrivals.append(dict(node_id=f'0x{node:02X}', node_name=names[node], case_bus=hx(BUS + case),
			script_bus=hx(BUS + script), script_prefix=rom[script:script + 15].hex(' '), map_id=mid(destination)))
	candidates = node_components(graph, seeds)
	for row in maps + pickups:
		m = int(row['map_id'], 16)
		choices = candidates[m]
		row.update(node_id=f'0x{choices[0]:02X}' if len(choices) == 1 else '',
			node_name=names[choices[0]] if len(choices) == 1 else '',
			node_candidates='|'.join(f'0x{n:02X}' for n in choices),
			node_confidence='Probable' if len(choices) == 1 else 'Unresolved',
			node_evidence='direct arrival/overworld-exit seeds propagated through undirected ordinary exit component; script transitions omitted')
	locations = canonicalize(pickups)
	collection_ids = {int(r['collection_flag'], 16) for r in locations}
	flag_matches = []
	for opcode in (0x53, 0x54):
		cursor = EVENT_DOMAIN[0]
		while True:
			cursor = rom.find(bytes([0xFD, opcode]), cursor, EVENT_DOMAIN[1])
			if cursor < 0:
				break
			if u16(rom, cursor + 2) in collection_ids:
				flag_matches.append(dict(bus=hx(BUS + cursor), opcode=f'FD{opcode:02X}', collection_id=u16(rom,cursor+2)))
			cursor += 1
	sources = []
	p = EVENT_DOMAIN[0]
	while True:
		p = rom.find(b'\xfe\x55\x37', p, EVENT_DOMAIN[1])
		if p < 0:
			break
		known_exchange = p in EXCHANGES
		sources.append(dict(source_id=f'grant-site-{p:08X}', map_id='', node_id='', event_script_address=hx(BUS + p),
			file_offset=hx(p), quantity=rom[p + 3], source_type='repeatable_AWE_exchange' if known_exchange else 'unresolved_script_reward_candidate',
			repeatable='true' if known_exchange else '', collection_flag='',
			confidence='Confirmed static' if known_exchange else 'Candidate',
			evidence_reference='prior binky_exchange_rate_two.md' if known_exchange else 'bounded_FE55_pattern_census',
			raw_hex=rom[p:p + 8].hex(' '),
			limitations='Excluded from completion totals; raw byte match is not executed-command or one-time proof' if not known_exchange else 'Original baseline award; renewable, excluded from completion totals'))
		p += 1
	rooms = []
	for m in maps:
		rows = [r for r in locations if r['map_id'] == m['map_id']]
		rooms.append(dict(map_id=m['map_id'], room_name='', node_id=m['node_id'], node_name=m['node_name'],
			node_confidence=m['node_confidence'], **totals(rows), coverage='complete registered fixed-actor subtype; script/container sources unresolved'))
	nodes = []
	for node in [f'0x{n:02X}' for n in range(17)] + ['']:
		rows = [r for r in locations if r['node_id'] == node]
		nodes.append(dict(node_id=node, node_name=names[int(node, 16)] if node else 'Unassigned pool (not an overworld node)',
			map_count=sum(m['node_id'] == node for m in maps), **totals(rows),
			node_confidence='Probable' if node else 'Unresolved', coverage='known actor subtotal; node grouping and all-source totals incomplete'))
	evidence = dict(schema_version=1, rom_sha256=sha(rom), map_table=dict(file_offset=hx(MAP_TABLE), bus_address=hx(BUS + MAP_TABLE),
		count=MAP_COUNT, stride=MAP_STRIDE, end_file_exclusive=hx(end)), actor_registrations=len(actors),
		fixed_binky_registrations=len(pickups), unique_collection_ids=len(locations),
		fixed_actor_quantity=totals(locations)['fixed_binky_quantity'],
		collection_flag_literal_set_clear_matches=flag_matches,
		collection_flag_search_limitations='Bounded immediate-operand pattern census, not dynamic/native/all-game flag-writer closure',
		all_source_total=None, scope='Known map/actor/exit tables; 17 arrival roots; bounded event-domain pattern census',
		event_pattern_domain_file_exclusive=[hx(n) for n in EVENT_DOMAIN],
		address_convention='ROM bus=file+0x08000000; RAM has no ROM file offset',
		collection_encoding='ID=u16le(actor+0x0E); byte=0x03003107+(ID>>3); mask=1<<(ID&7)',
		pickup_encoding='actor[1]&0x80; item=u8(u32le(actor+0x0A)); quantity=1 at 0x08069C4A..4C',
		complete_scopes=['494 descriptors; 2987 registered actors; initial pickup payload-37 subtype'],
		incomplete_scopes=['script/container/conditional rewards','enemy drops','shop stock','event-created actors','full map-to-node ownership'],
		maps=maps, exits=exits, arrivals=arrivals, locations=locations, other_sources=sources, native_windows=[])
	for label, ranges in WINDOWS.items():
		for start, stop in ranges:
			evidence['native_windows'].append(dict(label=label, file_start=hx(start), file_end_exclusive=hx(stop),
				bus_start=hx(BUS + start), bus_end_exclusive=hx(BUS + stop), sha256=sha(rom[start:stop]),
				instructions=[dict(bus=hx(i.address), file_offset=hx(i.address - BUS), bytes=i.raw.hex(' '), text=i.text) for i in inspect(rom, start, stop)]))
	unresolved = [r for r in sources if r['confidence'] == 'Candidate']
	other = [r for r in sources if r['confidence'] != 'Candidate']
	return locations, rooms, nodes, other, maps, unresolved, evidence


def csv_text(rows):
	stream = io.StringIO(newline='')
	writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
	writer.writeheader()
	writer.writerows(rows)
	return stream.getvalue()


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	for name in ('rom','menus','output-dir','evidence-output'):
		parser.add_argument('--' + name, required=True, type=Path)
	args = parser.parse_args()
	paths = [args.output_dir / name for name in ('binky_locations.csv','binkies_per_room.csv','binkies_per_node.csv','binky_other_sources.csv','binky_map_nodes.csv','binky_unresolved.csv')] + [args.evidence_output]
	if len({p.resolve() for p in paths}) != 7 or any(p.exists() or p.resolve() in (args.rom.resolve(), args.menus.resolve()) for p in paths):
		parser.error('Output paths must be distinct new files; refusing to overwrite')
	before = {p: sha(p.read_bytes()) for p in (args.rom,args.menus)}
	*data, evidence = extract(args.rom.read_bytes(), args.menus.read_text(encoding='utf-8-sig'))
	evidence['sources'] = [dict(path=p.as_posix(),sha256=digest) for p,digest in before.items()]
	for path, content in zip(paths, [csv_text(rows) for rows in data] + [json.dumps(evidence,indent=2)+'\n']):
		path.parent.mkdir(parents=True,exist_ok=True)
		with path.open('x',encoding='utf-8',newline='') as stream:
			stream.write(content)
	if any(sha(p.read_bytes()) != digest for p,digest in before.items()):
		raise RuntimeError('Source changed during extraction')
	print(f"{evidence['fixed_actor_quantity']} fixed actor Binkies; {len(data[1])} rooms; all-source/node totals partial; inputs unchanged")


if __name__ == '__main__':
	main()

"""Bounded read-only enemy combat extraction. All outputs must be new files.

Uses the existing Thumb inspector, never an emulator or ROM writer.
See reverse_engineering/enemy_attack_defense_susceptibility.md.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analyze'))
from thumb_inspect import inspect

BASE = 0x08000000
TABLE = 0x634F50
STRIDE = 0x4C
COUNT = 182
ATTACK_TABLE = 0x638558
JP_SHA = '0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12'
EN_SHA = '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde'
EFFECTS = [
	('target_flag_0001_counter', 0, 0x48A1C, 0x489D4, 'flag 0x0001; counter +3=max(old,4*duration_nibble)'),
	('target_flag_0004_state', 2, 0x48ABC, 0x48A70, 'flag 0x0004; +4=0; +5=duration_nibble'),
	('target_event_06', 4, 0x48B50, 0x48B10, 'target event byte +0x0C=6'),
	('turn_selection_down_50_percent', 6, 0x48C0C, 0x48BC8, 'flag 0x0020; additive +0x16 += trunc(-50*s16(+0x12)/100)'),
	('defense_down_50_percent', 8, 0x48D00, 0x48CBC, 'flag 0x0040; additive +0x18 += trunc(-50*s16(+0x14)/100)'),
	('actor_recovery_from_damage', 10, 0x48DC4, 0x48DB4, 'party actor +0x1E += trunc(damage*(30+random%10)/100)'),
]
# Half-open code intervals; pools and switch tables are deliberately omitted.
WINDOWS = {
	'INIT': [(0x48230, 0x48266), (0x48272, 0x48292), (0x482C4, 0x48306)],
	'ACTION_LOAD': [(0x41FCC, 0x4200C), (0x4215C, 0x4219E), (0x42300, 0x42332)],
	'ACTION_REPLACE': [(0x41E30, 0x41E84)],
	'ATK': [(0x496FE, 0x49776)],
	'TURN_SELECTION': [(0x4D254, 0x4D2B0), (0x4D32C, 0x4D344)],
	'DEF': [(0x48764, 0x48798), (0x487EC, 0x48812)],
	'DEF_SET': [(0x418C0, 0x41904)],
	'DEF_RESET': [(0x41C9C, 0x41D04)],
	'DEF_DYNAMIC': [(0x49890, 0x49938)],
	'EFFECT_DISPATCH': [(0x4892A, 0x4894E), (0x4897C, 0x489CE)],
	'SUS0': [(0x489D4, 0x48A60)],
	'SUS1': [(0x48A70, 0x48B00)],
	'SUS2': [(0x48B10, 0x48B86)],
	'SUS3': [(0x48BC8, 0x48CA0), (0x48CB4, 0x48CBC)],
	'SUS4': [(0x48CBC, 0x48D94), (0x48DA8, 0x48DB2)],
	'SUS5': [(0x48DB4, 0x48E2A)],
	'RNG': [(0x2F73C, 0x2F77E)],
	'VM_ACTION': [(0x40F08, 0x40F14), (0x40F30, 0x40F3C), (0x40F58, 0x40F64)],
	'ACTION_APPLY': [(0x477C0, 0x477EE), (0x495D4, 0x495F0)],
}


def hx(value):
	return f'0x{value:08X}'


def sha(data):
	return hashlib.sha256(data).hexdigest()


def names_from_text(text):
	parts = text.split('ATTACKS:')
	if len(parts) != 2 or not parts[0].startswith('NAMES:'):
		raise ValueError('Invalid name sections')
	result = []
	for part, count in zip(parts, (COUNT, 256)):
		pairs = re.findall(r'^([0-9A-Fa-f]{2})-E:(.*)$', part, re.MULTILINE)
		mapping = {int(k, 16): v.strip() for k, v in pairs}
		if len(pairs) != count or set(mapping) != set(range(count)) or any(not v for v in mapping.values()):
			raise ValueError('Missing/duplicate/empty name IDs')
		result.append(mapping)
	return result


def read_csv(path):
	with path.open(encoding='utf-8-sig', newline='') as stream:
		return list(csv.DictReader(stream))


def validate_ids(rows):
	if len(rows) != COUNT or [int(row['enemy_id']) for row in rows] != list(range(COUNT)):
		raise ValueError('Expected ordered enemy IDs 0..181 exactly once')


def extract(jp, en, names, hp, old, raw):
	if len(jp) != 0x800000 or len(en) != 0x800000 or sha(jp) != JP_SHA or sha(en) != EN_SHA:
		raise ValueError('Requires the fingerprinted unmodified Japanese and English baselines')
	for rows in (hp, old, raw):
		validate_ids(rows)
	enemy_names, attack_names = names
	lookup = list(jp[0x631AD4:0x631AD8])
	if lookup != [100, 60, 20, 0] or en[0x631AD4:0x631AD8] != bytes(lookup):
		raise ValueError('Susceptibility lookup mismatch')
	if TABLE + COUNT * STRIDE != ATTACK_TABLE or ATTACK_TABLE + 256 * 16 > len(jp):
		raise ValueError('Table bounds mismatch')
	master, attacks, suscept, records = [], [], [], []
	for enemy_id in range(COUNT):
		offset = TABLE + enemy_id * STRIDE
		block = jp[offset:offset + STRIDE]
		if block[8:] != en[offset + 8:offset + STRIDE]:
			raise ValueError(f'Numeric record differs between baselines: {enemy_id}')
		if bytes.fromhex(raw[enemy_id]['record_hex']) != en[offset:offset + STRIDE]:
			raise ValueError('Existing raw CSV mismatch')
		h = hp[enemy_id]
		raw_hp, initiative, defense, packed = struct.unpack_from('<4H', block, 10)
		if h['english_name'] != enemy_names[enemy_id] or old[enemy_id]['english_name'] != enemy_names[enemy_id]:
			raise ValueError('Name mismatch')
		if int(h['raw_hp']) != raw_hp or int(h['initialized_hp']) != raw_hp & 0x7FFF or int(old[enemy_id]['base_mitigation']) != defense:
			raise ValueError('HP/Defense source mismatch')
		if int(h['record_file_offset'], 16) != offset:
			raise ValueError('HP record offset mismatch')
		# Preserve every authoritative HP column, including evidence and limitations.
		row = dict(h)
		row.update(hp_classification=h['encoding_classification'], hp_confidence=h['confidence'],
			estimated_practical_hp='', suspected_mechanic='', suspected_mechanic_confidence='',
			base_atk='', atk_status='Unresolved as a species scalar; action power established',
			base_defense=defense, base_defense_confidence='Confirmed static',
			dynamic_mitigation='T+0x14 replaceable; T+0x18 additive signed16 at use',
			raw_turn_selection_base=initiative, raw_susceptibility_word=packed,
			susceptibility_summary=';'.join(f'{effect}={lookup[(packed >> shift) & 3]}%' for effect, shift, *_ in EFFECTS),
			combat_evidence_refs='INIT;ATK;DEF;DEF_SET;DEF_DYNAMIC;SUS0..SUS5',
			combat_limitations='Action type-specific formulas and named status taxonomy incomplete; no elemental mapping established')
		if raw_hp == 20000:
			row.update(suspected_mechanic='distraction_target', suspected_mechanic_confidence='Gameplay-supported hypothesis (user); not static proof')
		elif 'scripted_high_hp_unresolved' in h['encoding_classification']:
			row.update(suspected_mechanic='possible_recurring_enemy', suspected_mechanic_confidence='Gameplay-supported hypothesis (user); not static proof')
		master.append(row)
		for category, shift, reader, routine, operation in EFFECTS:
			code = (packed >> shift) & 3
			suscept.append(dict(enemy_id=enemy_id, english_name=enemy_names[enemy_id], effect_category=category,
				field_file_offset=hx(offset + 16), field_bus_address=hx(BASE + offset + 16),
				record_relative_offset='0x10', width='u16le (first reader uses u8)', bit_shift=shift, bit_width=2,
				raw_word=packed, encoded_value=code, application_multiplier_percent=lookup[code],
				reader_bus=hx(BASE + reader), routine_bus=hx(BASE + routine), effect_operation=operation,
				confidence='Confirmed static', evidence_ref=f'SUS{shift // 2}',
				limitations='Conditional application multiplier, not duration or unconditional immunity; see report gates'))
		for slot in range(3):
			field = offset + 28 + 4 * slot
			pointer = struct.unpack_from('<I', jp, field)[0]
			if pointer == 0:
				continue
			position = pointer - BASE
			if not ATTACK_TABLE <= position < ATTACK_TABLE + 256 * 16 or (position - ATTACK_TABLE) % 16:
				raise ValueError(f'Action pointer outside named action table: {hx(pointer)}')
			if jp[position + 8:position + 16] != en[position + 8:position + 16]:
				raise ValueError('Action numeric/script data moved')
			action_id = (position - ATTACK_TABLE) // 16
			power, kind, parameter, extra = jp[position + 8:position + 12]
			script = struct.unpack_from('<I', jp, position + 12)[0]
			if script != 0 and not BASE <= script < BASE + len(jp):
				raise ValueError('Action script out of ROM bounds')
			attacks.append(dict(enemy_id=enemy_id, english_name=enemy_names[enemy_id], slot=slot,
				pointer_field_file_offset=hx(field), pointer_field_bus_address=hx(BASE + field),
				action_id=action_id, action_name=attack_names[action_id], action_file_offset=hx(position),
				action_bus_address=hx(pointer), raw_power_u8=power, ordinary_path_power=2 * power,
				raw_type_u8=kind, type_low7=kind & 127, all_target_bit7=(kind >> 7),
				raw_parameter_0A=parameter, raw_parameter_0B=extra, script_bus_address=hx(script) if script else '',
				confidence='Confirmed static direct slot; execution/reachability not exhaustive', evidence_refs='INIT;ACTION_LOAD;ATK',
				limitations='2*power applies to traced ordinary path; special types/scripts may differ; slots can be replaced'))
		records.append(dict(enemy_id=enemy_id, record_file_offset=hx(offset), record_bus_address=hx(BASE + offset),
			base_defense=defense, raw_turn_selection_base=initiative, raw_susceptibility_word=packed))
	evidence = dict(schema_version=1, scope='Bounded read-only static analysis; no runtime claims added',
		address_convention='ROM bus=file+0x08000000; RAM has no ROM offset',
		roms=dict(japanese_sha256=sha(jp), english_sha256=sha(en)),
		tables=dict(enemy_file_offset=hx(TABLE), enemy_bus=hx(BASE + TABLE), stride=STRIDE, count=COUNT,
			action_file_offset=hx(ATTACK_TABLE), action_stride=16, named_action_count=256,
			susceptibility_lookup_file_offset='0x00631AD4', susceptibility_lookup_bus='0x08631AD4', susceptibility_lookup=lookup),
		fields=[dict(record_relative_offset='0x0E', width='u16le', purpose='base Defense, copied to T+0x14', reader='0x080482E6', writer='0x080482E8', confidence='Confirmed static'),
			dict(record_relative_offset='0x0C', width='u16le', purpose='turn selection input T+0x12; not established ATK', reader='0x080482E0', writer='0x080482E2', confidence='Confirmed static'),
			dict(record_relative_offset='0x10', width='u16le packed', formula='code=(word>>shift)&3; multiplier=[100,60,20,0][code]', shifts=[0,2,4,6,8,10], confidence='Confirmed static', limitations='Bits 12..15 unresolved; named statuses incomplete')],
		records=records, instruction_windows=[])
	evidence['dispatch_tables'] = [dict(file_offset=hx(start), bus_address=hx(BASE + start),
		values=[hx(struct.unpack_from('<I', jp, start + 4 * i)[0]) for i in range(count)])
		for start, count in [(0x4096C + 0x40 * 4, 3), (0x495F8, 23), (0x48958, 9)]]
	evidence['calculations'] = {
		'ordinary_enemy_action': {
			'confidence': 'Confirmed static', 'action_power_field': 'u8(action+0x08)',
			'formula': 'V=clamp(s16((P.u16[0x18]+P.u16[0x1C])&65535),1,999); D=max(s16(2*power-V),1); if P.flags(+0x10)&0x4000: D=0',
			'reader_bus': '0x08049722', 'reader_file_offset': '0x00049722',
			'hp_writer_bus': '0x08049750', 'hp_writer_file_offset': '0x00049750',
			'ordinary_dispatch_types': list(range(8)) + list(range(12,21)),
			'limitations': 'Conditional path only; alternate types, prior flag-4 branch, action script reachability not reconstructed'},
		'enemy_mitigation': {
			'confidence': 'Confirmed static',
			'formula': 'clamp(s16((T.u16[0x14]+T.u16[0x18])&65535),1,999)',
			'base_writer_bus': '0x080482E8', 'base_writer_file_offset': '0x000482E8',
			'readers_bus': ['0x0804876C','0x0804876E'],
			'readers_file_offset': ['0x0004876C','0x0004876E'],
			'limitations': 'Not universal to every Gimmick/action; live base can be replaced'},
		'susceptibility': {
			'confidence': 'Confirmed static',
			'formula': 'q=u8(trunc(base_threshold*lookup[(R.u16[0x10]>>shift)&3]/100)); apply if u8(PRNG()%100)<q',
			'unresolved_bits': [12,13,14,15],
			'categories': [dict(category=category, shift=shift, mask=hx(3 << shift),
				reader_bus=hx(BASE + reader), reader_file_offset=hx(reader),
				handler_bus=hx(BASE + handler), handler_file_offset=hx(handler),
				base_threshold=f'{4 if shift == 4 else 8}*low_nibble', operation=operation,
				guards=[] if shift == 10 else ['signed current HP != 0', 'not(raw initial u16 HP > 3000 and signed current HP <= 3000)', 'target flags & 0x4000 == 0'] + (['target flags & 4 == 0'] if shift == 2 else []))
				for category, shift, reader, handler, operation in EFFECTS],
			'limitations': 'Stored application multiplier only; no universal immunity, duration scaling, elemental categories or uniform-roll claim'},
	}
	evidence['representative_actions'] = [dict(row, script_prefix_hex=jp[int(row['script_bus_address'], 16) - BASE:int(row['script_bus_address'], 16) - BASE + 32].hex(' ') if row['script_bus_address'] else '')
		for row in attacks if row['enemy_id'] in (2, 12, 0xA5, 0xB5)]
	for label, windows in WINDOWS.items():
		for start, end in windows:
			evidence['instruction_windows'].append(dict(label=label, file_start=hx(start), file_end_exclusive=hx(end),
				bus_start=hx(BASE + start), bus_end_exclusive=hx(BASE + end),
				japanese_sha256=sha(jp[start:end]), english_sha256=sha(en[start:end]), identical=jp[start:end] == en[start:end],
				instructions=[dict(file_offset=hx(i.address - BASE), bus=hx(i.address), bytes=i.raw.hex(' '), text=i.text) for i in inspect(jp, start, end)]))
	return master, attacks, suscept, evidence


def check_consistency(master, attacks, suscept, evidence):
	validate_ids(master)
	if len(suscept) != COUNT * len(EFFECTS) or len({(r['enemy_id'], r['effect_category']) for r in suscept}) != len(suscept):
		raise ValueError('Susceptibility coverage/uniqueness mismatch')
	if len({(r['enemy_id'], r['slot']) for r in attacks}) != len(attacks):
		raise ValueError('Duplicate action relationship')
	for m, e in zip(master, evidence['records']):
		if int(m['enemy_id']) != e['enemy_id'] or int(m['base_defense']) != e['base_defense'] or int(m['raw_susceptibility_word']) != e['raw_susceptibility_word']:
			raise ValueError('CSV/JSON mismatch')
	for s in suscept:
		m = master[int(s['enemy_id'])]
		code = (int(m['raw_susceptibility_word']) >> int(s['bit_shift'])) & 3
		if int(s['encoded_value']) != code or int(s['application_multiplier_percent']) != [100,60,20,0][code]:
			raise ValueError('Susceptibility consistency mismatch')
	for a in attacks:
		if int(a['ordinary_path_power']) != 2 * int(a['raw_power_u8']):
			raise ValueError('Action consistency mismatch')


def csv_text(rows):
	stream = io.StringIO(newline='')
	writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
	writer.writeheader()
	writer.writerows(rows)
	return stream.getvalue()


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	for name in ('japanese-rom', 'english-rom', 'names', 'hp-csv', 'enemies-csv', 'raw-csv', 'output-dir', 'evidence-output'):
		parser.add_argument('--' + name, type=Path, required=True)
	args = parser.parse_args()
	inputs = [args.japanese_rom, args.english_rom, args.names, args.hp_csv, args.enemies_csv, args.raw_csv]
	outputs = [args.output_dir / name for name in ('enemies_complete.csv', 'enemy_attacks.csv', 'enemy_susceptibilities.csv')] + [args.evidence_output]
	if len({p.resolve() for p in outputs}) != len(outputs) or any(p.exists() or p.resolve() in {q.resolve() for q in inputs} for p in outputs):
		parser.error('Outputs must be distinct new files and must not alias inputs')
	before = {p: sha(p.read_bytes()) for p in inputs}
	master, attacks, suscept, evidence = extract(args.japanese_rom.read_bytes(), args.english_rom.read_bytes(),
		names_from_text(args.names.read_text(encoding='utf-8-sig')), read_csv(args.hp_csv), read_csv(args.enemies_csv), read_csv(args.raw_csv))
	evidence['sources'] = [dict(path=p.as_posix(), sha256=digest) for p, digest in before.items()]
	check_consistency(master, attacks, suscept, evidence)
	for path, content in zip(outputs, [csv_text(master), csv_text(attacks), csv_text(suscept), json.dumps(evidence, indent=2) + '\n']):
		path.parent.mkdir(parents=True, exist_ok=True)
		with path.open('x', encoding='utf-8', newline='') as stream:
			stream.write(content)
	check_consistency(*(read_csv(p) for p in outputs[:3]), json.loads(outputs[3].read_text(encoding='utf-8')))
	if any(sha(p.read_bytes()) != digest for p, digest in before.items()):
		raise RuntimeError('Input changed during extraction')
	print(f'Validated {len(master)} enemies, {len(attacks)} direct action slots, {len(suscept)} susceptibility rows; input hashes unchanged.')


if __name__ == '__main__':
	main()

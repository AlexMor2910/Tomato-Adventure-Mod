"""One supported v3 music extension; canonical baseline and v2 increment agree.

python -B tools/patch/cumulative_v3.py --output-dir NEW_DIRECTORY
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/patch'), str(ROOT / 'tools/analyze')]
import cumulative_v2 as previous
from verify_cumulative_v2 import verify as verify_v2

V2_DIR = ROOT / 'tools/patch/output/cumulative-v2-20261028/build'
DECISION = ROOT / 'reverse_engineering/cumulative_v3_music_resolution.json'
DECISION_HASH = '22d57633dfcda1e64a3788a7a18977881053524dc7e9651072e7b32262e69b61'
OPERATION = dict(feature='music', area='Oyster Sewers', map_id=0x16D,
	offset=0x62FBD5, bus=0x0862FBD5, old='0e', new='10')


def build(baseline, v1, v2):
	rule = previous.v1
	rule.require(len(v2) == 8388608 and rule.sha(v2) ==
		'300e38f33881307682e1faf0bae4d4194306c2bfec9978f63d30b244719bd482', 'Unexpected v2 input')
	verify_v2(baseline, v1, v2, V2_DIR)
	decision_bytes = DECISION.read_bytes()
	rule.require(rule.sha(decision_bytes) == DECISION_HASH, 'Decision ledger changed')
	decision = json.loads(decision_bytes)
	rule.require(len(decision['approved_operations']) == 1, 'Operation count')
	op = decision['approved_operations'][0]
	rule.require(all(op[k] == v for k, v in OPERATION.items()) and op['confidence'] == 'Confirmed static', 'Unapproved operation')
	rebuilt_v2, old_ops, _ = previous.build(baseline, v1)
	rule.require(rebuilt_v2 == v2, 'V2 reproduction')
	canonical_ops = old_ops + [op]
	canonical = rule.apply(baseline, canonical_ops)
	incremental = rule.apply(v2, [op])
	rule.require(canonical == incremental, 'Canonical/incremental mismatch')
	return canonical, canonical_ops


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--output-dir', required=True, type=Path)
	args = parser.parse_args()
	rule = previous.v1
	baseline = rule.hawker.BASELINE.read_bytes()
	v1 = (previous.V1_DIR / 'tomato_cumulative_v1_INCOMPLETE.gba').read_bytes()
	v2 = (V2_DIR / 'tomato_cumulative_v2_INCOMPLETE.gba').read_bytes()
	output, operations = build(baseline, v1, v2)
	args.output_dir.mkdir(parents=True, exist_ok=False)
	rom = args.output_dir / 'tomato_cumulative_v3_INCOMPLETE.gba'
	with rom.open('xb') as f:
		f.write(output)
	rule.require(rom.read_bytes() == output, 'Readback mismatch')
	ledger = []
	for i, (a, b) in enumerate(zip(baseline, output)):
		if a != b:
			op = next(o for o in operations if o['offset'] <= i < o['offset'] + len(bytes.fromhex(o['old'])))
			ledger.append(dict(file=i, bus=i + 0x08000000, old=a, new=b, feature=op['feature'], area=op.get('area')))
	rule.write_json(args.output_dir / 'operations.json', operations)
	rule.write_json(args.output_dir / 'changed_bytes.json', ledger)
	rule.write_json(args.output_dir / 'v2_to_v3_bytes.json', [dict(file=0x62FBD5, bus=0x0862FBD5, old=14, new=16, map_id=365)])
	for feature in sorted({o['feature'] for o in operations}):
		rule.write_json(args.output_dir / (feature + '_bytes.json'), [r for r in ledger if r['feature'] == feature])
	for name, source in [('tomato_cumulative_v3.bps', baseline), ('v2_to_v3.bps', v2)]:
		with (args.output_dir / name).open('xb') as f:
			f.write(rule.bps(source, output))
	manifest = dict(status='Tomato Adventure — Cumulative v3 Incomplete Experimental Build',
		output_name=rom.name, output_sha256=rule.sha(output), size=len(output),
		baseline_sha256=rule.sha(baseline), v1_sha256=rule.sha(v1), v2_sha256=rule.sha(v2),
		changed_bytes_from_baseline=len(ledger), changed_bytes_from_v2=1, canonical_incremental_equal=True,
		music_room_counts={'Dropper Village': 8, 'Mayonen Caverns': 15, 'Captain Grocko Ship': 29, 'Oyster Sewers': 15, 'The Vault': 21},
		unresolved_maps=['0x012C', '0x0158'], exhaustive_event_coverage=False, alessa_wrapper_excluded=True, added_hawkers=False,
		decision_sha256=DECISION_HASH, builder_sha256=rule.sha(Path(__file__).read_bytes()),
		bps_sha256=rule.sha((args.output_dir / 'tomato_cumulative_v3.bps').read_bytes()),
		incremental_bps_sha256=rule.sha((args.output_dir / 'v2_to_v3.bps').read_bytes()), runtime='Untested; user-operated validation only')
	rule.write_json(args.output_dir / 'manifest.json', manifest)
	print(json.dumps(manifest))


if __name__ == '__main__':
	main()

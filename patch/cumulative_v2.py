"""Guarded cumulative v2 builder; canonical baseline and incremental v1 agree.

python -B tools/patch/cumulative_v2.py --output-dir NEW_DIRECTORY
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/patch'), str(ROOT / 'tools/analyze')]
import cumulative_v1 as v1
from verify_cumulative_v1 import verify as verify_v1

PLAN = ROOT / 'reverse_engineering/cumulative_v2_music_plan.json'
PLAN_HASH = '2da9f2375c1bdb1f14b3fc0177ad958439cf09f22b21f9814dc4ee4b1697169a'
V1_DIR = ROOT / 'tools/patch/output/cumulative-v1-20261028/build'
V1_HASH = '1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f'


def load_plan():
	data = PLAN.read_bytes()
	v1.require(v1.sha(data) == PLAN_HASH, 'Music plan changed')
	plan = json.loads(data)
	for kind in ('rooms', 'tracks'):
		p = ROOT / f'reverse_engineering/cumulative_v2_music_{kind}.csv'
		v1.require(v1.sha(p.read_bytes()) == plan[kind + '_csv_sha256'], 'Music evidence CSV changed')
	v1.require(len(plan['operations']) == 88, 'Music operation count')
	for op in plan['operations']:
		v1.require(op['confidence'] == 'Confirmed' and op['bus'] == op['offset'] + 0x08000000, 'Unconfirmed operation/address')
	return plan


def build(baseline, prior):
	v1.require(len(baseline) == len(prior) == 0x800000, 'Wrong ROM size')
	v1.require(v1.sha(baseline) == v1.BASE_HASH and v1.sha(prior) == V1_HASH, 'Wrong ROM identity')
	verify_v1(baseline, prior, V1_DIR)
	plan = load_plan()
	old_ops = v1.operations(baseline)
	v1.require(v1.apply(baseline, old_ops) == prior, 'Prior canonical reproduction mismatch')
	# Reuse all four feature groups verbatim. Replace only the old one-room music operation.
	canonical_ops = [op for op in old_ops if op['feature'] != 'music'] + plan['operations']
	canonical = v1.apply(baseline, canonical_ops)
	incremental_ops = [dict(op, old=op['old_v1']) for op in plan['operations']]
	incremental = v1.apply(prior, incremental_ops)
	v1.require(canonical == incremental, 'Canonical and incremental builds differ')
	return canonical, canonical_ops, incremental_ops


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--output-dir', required=True, type=Path)
	args = parser.parse_args()
	baseline = v1.hawker.BASELINE.read_bytes()
	prior = (V1_DIR / 'tomato_cumulative_v1_INCOMPLETE.gba').read_bytes()
	target, operations, incremental = build(baseline, prior)
	args.output_dir.mkdir(parents=True, exist_ok=False)
	rom = args.output_dir / 'tomato_cumulative_v2_INCOMPLETE.gba'
	with rom.open('xb') as f:
		f.write(target)
	v1.require(rom.read_bytes() == target, 'Output readback')
	ledger = []
	for i, (old, new) in enumerate(zip(baseline, target)):
		if old != new:
			op = next(o for o in operations if o['offset'] <= i < o['offset'] + len(bytes.fromhex(o['old'])))
			ledger.append(dict(file=i, bus=i + 0x08000000, old=old, new=new, feature=op['feature'], area=op.get('area')))
	v1.write_json(args.output_dir / 'operations.json', operations)
	v1.write_json(args.output_dir / 'incremental_operations.json', incremental)
	v1.write_json(args.output_dir / 'changed_bytes.json', ledger)
	for feature in sorted({o['feature'] for o in operations}):
		v1.write_json(args.output_dir / (feature + '_bytes.json'), [x for x in ledger if x['feature'] == feature])
	for name, source in [('tomato_cumulative_v2.bps', baseline), ('v1_to_v2.bps', prior)]:
		with (args.output_dir / name).open('xb') as f:
			f.write(v1.bps(source, target))
	v1.write_json(args.output_dir / 'manifest.json', dict(status='Cumulative v2 — Incomplete Experimental Build',
		all_five_areas_exhaustively_proven=False, output_name=rom.name, size=len(target),
		baseline_sha256=v1.sha(baseline), v1_sha256=v1.sha(prior), output_sha256=v1.sha(target),
		changed_bytes_from_baseline=len(ledger), changed_bytes_from_v1=sum(a != b for a, b in zip(prior, target)),
		canonical_incremental_equal=True, alessa_wrapper_excluded=True, extra_hawkers=False,
		plan_sha256=PLAN_HASH, builder_sha256=v1.sha(Path(__file__).read_bytes()),
		bps_sha256=v1.sha((args.output_dir / 'tomato_cumulative_v2.bps').read_bytes()),
		incremental_bps_sha256=v1.sha((args.output_dir / 'v1_to_v2.bps').read_bytes()),
		room_counts={k: len(v) for k, v in load_plan()['confirmed_rooms'].items()},
		runtime='Untested final ROM; user-operated testing only'))
	print(json.dumps(dict(rom=str(rom), sha256=v1.sha(target), bytes=len(target), changed_bytes=len(ledger))))


if __name__ == '__main__':
	main()

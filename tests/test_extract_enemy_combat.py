"""Read-only integration and invalid-input tests for the bounded combat export."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('enemy_combat', ROOT / 'tools/extract/extract_enemy_combat.py')
combat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(combat)


class CombatExtractionTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.hp = combat.read_csv(ROOT / 'tools/extract/extracted_data/enemy_hp_verified.csv')
		cls.old = combat.read_csv(ROOT / 'tools/extract/extracted_data/enemies.csv')
		cls.raw = combat.read_csv(ROOT / 'tools/extract/extracted_data/enemies_raw.csv')
		cls.names = combat.names_from_text((ROOT / 'tomatotrans-1.1.1/ta_enemies_eng.txt').read_text(encoding='utf-8-sig'))
		cls.jp = (ROOT / 'Tomato Adventure (Japan).gba').read_bytes()
		cls.en = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
		cls.result = combat.extract(cls.jp, cls.en, cls.names, cls.hp, cls.old, cls.raw)

	def test_all_hp_columns_preserved(self):
		for original, complete in zip(self.hp, self.result[0]):
			self.assertEqual(original, {k: complete[k] for k in original})

	def test_representative_ordinary_and_boss(self):
		master, attacks, suscept, evidence = self.result
		self.assertEqual((master[2]['initialized_hp'], master[2]['base_defense']), ('24', 10))
		self.assertEqual((master[12]['initialized_hp'], master[12]['effective_hp']), ('3030', '30'))
		self.assertEqual([r['ordinary_path_power'] for r in attacks if r['enemy_id'] == 2], [8, 8, 8])
		self.assertEqual([r['ordinary_path_power'] for r in attacks if r['enemy_id'] == 12], [14, 8, 8])
		self.assertEqual([r['application_multiplier_percent'] for r in suscept if r['enemy_id'] == 12], [0,0,0,0,0,20])
		self.assertTrue(all(w['identical'] for w in evidence['instruction_windows']))

	def test_exceptional_and_null_script(self):
		master, attacks, _, _ = self.result
		self.assertEqual(master[0xA5]['base_defense'], 38)
		self.assertEqual([r['action_id'] for r in attacks if r['enemy_id'] == 0xA5], [212,147,197])
		self.assertEqual(next(r for r in attacks if r['enemy_id'] == 6 and r['slot'] == 2)['script_bus_address'], '')
		for row in master:
			if row['initialized_hp'] == '20000':
				self.assertEqual(row['suspected_mechanic'], 'distraction_target')
				self.assertEqual(row['estimated_practical_hp'], '')

	def test_roundtrip_and_published_consistency(self):
		master, attacks, suscept, evidence = self.result
		decoded = [list(csv.DictReader(io.StringIO(combat.csv_text(rows)))) for rows in (master, attacks, suscept)]
		combat.check_consistency(*decoded, json.loads(json.dumps(evidence)))
		for rows, name in zip(decoded, ('enemies_complete.csv','enemy_attacks.csv','enemy_susceptibilities.csv')):
			self.assertEqual(rows, combat.read_csv(ROOT / 'tools/extract/extracted_data' / name))
		published = json.loads((ROOT / 'reverse_engineering/enemy_attack_defense_susceptibility_evidence.json').read_text(encoding='utf-8'))
		combat.check_consistency(*decoded, published)
		self.assertEqual(evidence, {k: v for k, v in published.items() if k != 'sources'})

	def test_cli_reproduction_and_no_overwrite(self):
		with tempfile.TemporaryDirectory() as directory:
			output = Path(directory)
			command = [sys.executable, str(ROOT / 'tools/extract/extract_enemy_combat.py'),
				'--japanese-rom', str(ROOT / 'Tomato Adventure (Japan).gba'),
				'--english-rom', str(ROOT / 'Tomato Adventure (Japan) (patched).gba'),
				'--names', str(ROOT / 'tomatotrans-1.1.1/ta_enemies_eng.txt'),
				'--hp-csv', str(ROOT / 'tools/extract/extracted_data/enemy_hp_verified.csv'),
				'--enemies-csv', str(ROOT / 'tools/extract/extracted_data/enemies.csv'),
				'--raw-csv', str(ROOT / 'tools/extract/extracted_data/enemies_raw.csv'),
				'--output-dir', str(output), '--evidence-output', str(output / 'evidence.json')]
			first = subprocess.run(command, capture_output=True, text=True)
			self.assertEqual(first.returncode, 0, first.stderr)
			paths = list(output.iterdir())
			before = {p: p.read_bytes() for p in paths}
			second = subprocess.run(command, capture_output=True, text=True)
			self.assertNotEqual(second.returncode, 0)
			self.assertIn('Outputs must be distinct new files', second.stderr)
			self.assertEqual(before, {p: p.read_bytes() for p in paths})

	def test_bad_ids_and_names_rejected(self):
		with self.assertRaises(ValueError):
			combat.validate_ids(self.hp[:-1])
		with self.assertRaises(ValueError):
			combat.names_from_text('NAMES:\n00-E:Name\nATTACKS:\n00-E:Action\n')

	def test_short_or_modified_rom_rejected(self):
		with self.assertRaises(ValueError):
			combat.extract(self.jp[:100], self.en, self.names, self.hp, self.old, self.raw)
		changed = bytes([self.jp[0] ^ 1]) + self.jp[1:]
		with self.assertRaises(ValueError):
			combat.extract(changed, self.en, self.names, self.hp, self.old, self.raw)

	def test_inconsistent_susceptibility_rejected(self):
		master, attacks, suscept, evidence = self.result
		bad = [dict(r) for r in suscept]
		bad[0]['application_multiplier_percent'] = 123
		with self.assertRaises(ValueError):
			combat.check_consistency(master, attacks, bad, evidence)


if __name__ == '__main__':
	unittest.main()

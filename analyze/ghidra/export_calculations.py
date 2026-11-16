"""Attach bounded Ghidra calculation evidence to the authored research report."""
import argparse
import hashlib
import re
from pathlib import Path

MARKER = "<!-- generated-ghidra-calculation-evidence -->"


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("trace", type=Path)
	args = parser.parse_args()
	text = args.trace.read_text(encoding="utf-8")
	if not text.endswith("TRACE_COMPLETE\n") or "Calculation instruction count: 136" not in text or "Language: ARM:LE:32:v4t" not in text:
		raise SystemExit("Incomplete or unexpected calculation trace; documentation not changed.")
	calc = text.split("COMPLETE CALCULATION FUNCTION\n", 1)[1].split("CALLER SCANS", 1)[0].strip()
	blocks = re.findall(r"(BLOCK ([0-9a-f]{8})[^\n]*\n.*?)(?=\nBLOCK |\nSWITCH DATA|\Z)", text.split("CALLER AND CALLEE CONTEXTS\n", 1)[1], re.S)
	selected = [block.strip() for block, start in blocks if start in {"08079ae4", "08081188", "080742b8", "08079b78"}]
	if len(selected) != 4:
		raise SystemExit("Missing expected supporting contexts.")
	report = Path(__file__).resolve().parents[3] / "reverse_engineering/gimmick_calculations.md"
	prose = report.read_text(encoding="utf-8").split(MARKER, 1)[0].rstrip()
	digest = hashlib.sha256(args.trace.read_bytes()).hexdigest()
	appendix = f"\n\n{MARKER}\n\nTrace SHA-256: `{digest}`.\n\n### Complete calculation function\n\n```text\n{calc}\n```\n\n### Selected writer and renderer contexts\n\n```text\n" + "\n\n".join(selected) + "\n```\n"
	report.write_text(prose + appendix, encoding="utf-8")
	print(f"Updated calculation evidence: {report}")


if __name__ == "__main__":
	main()

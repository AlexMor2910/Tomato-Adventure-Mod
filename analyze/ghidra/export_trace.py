"""Attach successful Ghidra instruction evidence to the authored loader report."""
import argparse
import hashlib
from pathlib import Path

MARKER = "<!-- generated-ghidra-instruction-evidence -->"


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("trace", type=Path, help="successful ignored run's loader.txt")
	parser.add_argument("--output", type=Path, default=Path("reverse_engineering/ghidra_loader_trace.md"))
	args = parser.parse_args()
	text = args.trace.read_text(encoding="utf-8")
	if not text.endswith("TRACE_COMPLETE\n"):
		raise SystemExit("Incomplete Ghidra trace; documentation not changed.")
	for expected in ("Language: ARM:LE:32:v4t", "ram 08000000..087fffff initialized=true", "Loader instruction count: 203"):
		if expected not in text:
			raise SystemExit(f"Unexpected trace configuration: {expected}")
	loader = text.split("LOADER (", 1)[1].split("RAW THUMB BL CANDIDATES", 1)[0]
	loader = "LOADER (" + loader.strip()
	contexts = "TARGETED CONTEXTS " + text.split("TARGETED CONTEXTS", 1)[1].split("POINTER TAIL TARGETS", 1)[0].strip()
	prose = args.output.read_text(encoding="utf-8").split(MARKER, 1)[0].rstrip()
	digest = hashlib.sha256(args.trace.read_bytes()).hexdigest()
	evidence = f"\n\n{MARKER}\n\nTrace: `{args.trace.as_posix()}`; SHA-256 `{digest}`.\n\n### Complete loader and literals\n\n```text\n{loader}\n```\n\n### Caller and consumer contexts\n\n```text\n{contexts}\n```\n"
	args.output.write_text(prose + evidence, encoding="utf-8")
	print(f"Updated instruction appendix: {args.output}")


if __name__ == "__main__":
	main()

"""Probe debugger capabilities from a fresh ROM boot, not a gameplay test."""
import argparse
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from prepare_session import verify
from rsp import RSP


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("session", type=Path)
	parser.add_argument("--frontend", choices=("sdl", "qt"), default="sdl")
	args = parser.parse_args()
	session = args.session.resolve()
	manifest = verify(session)
	for name in ("probe-command.json", "probe-process.log", "probe-rsp.jsonl", "probe-results.json"):
		if (session / "logs" / name).exists():
			raise RuntimeError("Existing probe evidence would be overwritten; prepare a fresh session")
	with socket.socket() as test:
		test.bind(("127.0.0.1", 2345))  # Refuse to reuse an unrelated listener.
	env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", QT_QPA_PLATFORM="offscreen")
	command = [str(session / "bin" / ("mgba-sdl.exe" if args.frontend == "sdl" else "mGBA.exe")), "-g"]
	for key, value in manifest["config"].items():
		command += ["-C", f"{key}={value}"]
	command += [manifest["rom"]]
	(session / "logs/probe-command.json").write_text(json.dumps(command, indent=2) + "\n")
	process = None
	client = None
	result = dict(scope="fresh-boot debugger capability probe; no Gimmick/menu/battle verification")
	try:
		with (session / "logs/probe-process.log").open("w") as output, (session / "logs/probe-rsp.jsonl").open("w") as wire:
			process = subprocess.Popen(command, cwd=session, env=env, stdout=output, stderr=subprocess.STDOUT,
				creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
			deadline = time.monotonic() + 10
			while time.monotonic() < deadline:
				if process.poll() is not None:
					raise RuntimeError("mGBA exited before debugger connection; inspect probe-process.log")
				try:
					client = RSP(log=wire)
					break
				except (ConnectionRefusedError, TimeoutError):
					time.sleep(0.05)
			if not client:
				raise RuntimeError("mGBA debugger did not become available")
			result["stop"] = client.command("?")
			result["supported"] = client.command("qSupported:hwbreak+;swbreak+")
			result["initial_registers"] = client.registers()
			result["rom_header_hex"] = client.memory(0x080000A0, 16).hex()
			result["calculation_opcode_hex"] = client.memory(0x08075970, 8).hex()
			for kind in (2, 3, 4):
				client.point(kind, 0x03003F56)
				client.point(kind, 0x03003F56, enabled=False)
			result["watchpoint_registration"] = "Z2/Z3/Z4 accepted and removed; firing not tested"
			# Derive startup target from the ROM header's ARM B instruction.
			word = int.from_bytes(client.memory(0x08000000, 4), "little")
			if word & 0xFF000000 != 0xEA000000:
				raise RuntimeError("Unexpected ROM startup branch")
			delta = word & 0xFFFFFF
			if delta & 0x800000:
				delta -= 0x1000000
			target = 0x08000008 + delta * 4
			client.point(1, target, 4)
			result["startup_break_address"] = target
			result["break_stop"] = client.command("c")
			result["break_registers"] = client.registers()
			if result["break_registers"]["pc"] != target:
				raise RuntimeError("Execution breakpoint did not stop at expected PC")
			client.point(1, target, 4, enabled=False)
			result["step_stop"] = client.command("s")
			result["after_step_registers"] = client.registers()
			result["status"] = "capability probe passed"
			client.close()
			client = None
	except Exception as error:
		result["status"] = "probe failed"
		result["error"] = repr(error)
		raise
	finally:
		try:
			if client:
				client.log = None  # Exception paths may already have closed the log.
				client.close()
		finally:
			if process and process.poll() is None:
				process.terminate()
				process.wait(timeout=5)
			verify(session)
			(session / "logs/probe-results.json").write_text(json.dumps(result, indent=2) + "\n")
	print(json.dumps(result, indent=2))


if __name__ == "__main__":
	main()

"""Launch the isolated Qt frontend for manual gameplay; verify protected files on exit."""
import argparse
import json
import os
import subprocess
import uuid
from pathlib import Path
from prepare_session import verify


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("session", type=Path)
	args = parser.parse_args()
	session = args.session.resolve()
	manifest = verify(session)
	launch_id = uuid.uuid4().hex
	launch_log = session / "logs" / f"manual-launch-{launch_id}.json"
	process_log = session / "logs" / f"manual-process-{launch_id}.log"
	command = [str(session / "bin/mGBA.exe")]
	for key, value in manifest["config"].items():
		command += ["-C", f"{key}={value}"]
	command += [manifest["rom"]]
	# Default launch deliberately requires no remote debugger or imported state.
	# This is an interactive tool the user needs to see/control for the manual run.
	with launch_log.open("x") as output:
		json.dump(command, output, indent=2)
		output.write("\n")
	env = dict(os.environ)
	for key in ("QT_QPA_PLATFORM", "SDL_VIDEODRIVER", "SDL_AUDIODRIVER"):
		env.pop(key, None)
	try:
		with process_log.open("x") as output:
			process = subprocess.Popen(command, cwd=session, env=env, stdout=output, stderr=subprocess.STDOUT,
				creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
			result = process.wait()
			if result:
				raise RuntimeError(f"mGBA exited with {result}; inspect {process_log}")
	finally:
		verify(session)
	print("Protected ROMs and executable/ROM copies verified unchanged.")


if __name__ == "__main__":
	main()

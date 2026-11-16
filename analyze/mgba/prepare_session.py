"""Prepare a fresh isolated mGBA session. Never import existing saves or states."""
import hashlib
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
	"Tomato Adventure (Japan).gba": "0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12",
	"Tomato Adventure (Japan) (patched).gba": "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde",
}


def digest(path):
	return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(session):
	manifest = json.loads((session / "session.json").read_text())
	for entry in manifest["protected"]:
		path = Path(entry["path"])
		stat = path.stat()
		if digest(path) != entry["sha256"] or stat.st_size != entry["size"] or stat.st_mtime_ns != entry["mtime_ns"]:
			raise RuntimeError(f"Protected file changed: {path}")
	if digest(session / "rom/english.gba") != EXPECTED["Tomato Adventure (Japan) (patched).gba"]:
		raise RuntimeError("Isolated ROM copy fingerprint mismatch")
	for name, expected in manifest["executable_hashes"].items():
		if digest(session / "bin" / name) != expected:
			raise RuntimeError(f"Isolated executable fingerprint mismatch: {name}")
	return manifest


def prepare():
	protected = []
	for name, expected in EXPECTED.items():
		path = ROOT / name
		stat = path.stat()
		actual = digest(path)
		if actual != expected:
			raise RuntimeError(f"Unexpected ROM revision: {name}")
		protected.append(dict(path=str(path), sha256=actual, size=stat.st_size, mtime_ns=stat.st_mtime_ns))
	session = ROOT / "reverse_engineering/mgba" / ("run-" + uuid.uuid4().hex[:12])
	for name in ("bin", "rom", "saves", "states", "screenshots", "logs", "patches", "cheats"):
		(session / name).mkdir(parents=True, exist_ok=False)
	hashes = {}
	for name in ("mGBA.exe", "mgba-sdl.exe"):
		path = ROOT / "mGBA" / name
		hashes[name] = digest(path)
		shutil.copyfile(path, session / "bin" / name)
	(session / "bin/portable.ini").touch(exist_ok=False)
	shutil.copyfile(ROOT / "Tomato Adventure (Japan) (patched).gba", session / "rom/english.gba")
	config = {
		"savegamePath": str(session / "saves"), "savestatePath": str(session / "states"),
		"screenshotPath": str(session / "screenshots"), "patchPath": str(session / "patches"),
		"cheatsPath": str(session / "cheats"), "useBios": "0", "skipBios": "1",
		"frameskip": "0", "rewindEnable": "0", "logToFile": "1",
		"logFile": str(session / "logs/emulator.log"),
	}
	(session / "bin/config.ini").write_text("[mgba]\n" + "\n".join(f"{key}={value}" for key, value in config.items()) + "\n", encoding="utf-8")
	manifest = dict(protected=protected, executable_hashes=hashes, config=config,
		rom=str(session / "rom/english.gba"), imported_save=None, imported_state=None)
	(session / "session.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
	verify(session)
	print(session)
	return session


if __name__ == "__main__":
	prepare()

"""Build an isolated, one-byte Gear-Yo experiment; never launch the emulator."""
import hashlib
import json
import shutil
import uuid
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OFFSET = 0x62C272
EXPECTED = {
    "Tomato Adventure (Japan).gba": "0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12",
    "Tomato Adventure (Japan) (patched).gba": "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    protected = {}
    for path in list(ROOT.glob("*.gba")) + list((ROOT / "reverse_engineering/mgba").rglob("*.ss*")) + list((ROOT / "reverse_engineering/mgba").rglob("*.sav")):
        protected[path] = (sha(path.read_bytes()), path.stat().st_mtime_ns)
    for name, expected in EXPECTED.items():
        if protected[ROOT / name][0] != expected:
            raise ValueError(f"Unexpected input ROM: {name}")
    original = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
    if len(original) != 0x800000 or original[OFFSET] != 0x15:
        raise ValueError("Unexpected ROM size or base Attack byte")
    modified = bytearray(original)
    modified[OFFSET] = 0x16
    differences = [i for i, (a, b) in enumerate(zip(original, modified)) if a != b]
    if differences != [OFFSET]:
        raise ValueError("Expected exactly the requested byte difference")
    run = ROOT / "reverse_engineering/experiments/testing" / ("gearyo-" + uuid.uuid4().hex)
    run.mkdir(parents=True, exist_ok=False)
    outputs = {}
    for label, data in (("A", original), ("B", modified)):
        session = run / label
        for folder in ("bin", "rom", "saves", "states", "screenshots", "logs", "patches", "cheats"):
            (session / folder).mkdir(parents=True, exist_ok=False)
        rom = session / "rom" / ("english.gba" if label == "A" else "gearyo_attack_22.gba")
        with rom.open("xb") as output:
            output.write(data)
        if rom.read_bytes() != data:
            raise RuntimeError("Output readback mismatch")
        shutil.copyfile(ROOT / "mGBA/mGBA.exe", session / "bin/mGBA.exe")
        (session / "bin/portable.ini").touch(exist_ok=False)
        config = {"savegamePath": str(session / "saves"), "savestatePath": str(session / "states"),
                  "screenshotPath": str(session / "screenshots"), "patchPath": str(session / "patches"),
                  "cheatsPath": str(session / "cheats"), "loadStateExtdata": "9", "useBios": "0",
                  "skipBios": "1", "frameskip": "0", "rewindEnable": "0", "logToFile": "0"}
        (session / "bin/config.ini").write_text("[mgba]\n" + "\n".join(f"{k}={v}" for k, v in config.items()) + "\n", encoding="utf-8")
        # Each launcher invocation uses new logs and verifies the ROM on exit.
        launcher = '''import hashlib, json, subprocess, uuid
from pathlib import Path
s = Path(__file__).resolve().parent
m = json.loads((s / "session.json").read_text())
r = Path(m["rom"])
def verify():
    if hashlib.sha256(r.read_bytes()).hexdigest() != m["sha256"]:
        raise RuntimeError("Session ROM changed")
verify()
cmd = [str(s / "bin/mGBA.exe")]
for k,v in m["config"].items(): cmd += ["-C", f"{k}={v}"]
cmd += [str(r)]
tag = uuid.uuid4().hex
with (s / "logs" / (tag + ".json")).open("x") as f: json.dump(cmd,f,indent=2)
try:
    with (s / "logs" / (tag + ".log")).open("x") as f:
        subprocess.run(cmd,cwd=s,stdout=f,stderr=subprocess.STDOUT,check=True)
finally: verify()
'''
        (session / "launch.py").write_text(launcher, encoding="utf-8")
        entry = {"rom": str(rom), "sha256": sha(data), "crc32": f"{zlib.crc32(data):08x}", "config": config}
        (session / "session.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        for name, expected in {
            "gimmick_menu.ss0": "570e17c82b6d3592a0b003d991a33b6bf320c04ff7322a339e735f6c65280230",
            "gimmick_battle.ss0": "cd21cb39ce11ac7ab032982576e1bed13ab2864fa431e855a6bb209c125667c7",
        }.items():
            source = ROOT / "reverse_engineering/mgba/run-6d783e19ca1b" / name
            if source.exists():
                state = source.read_bytes()
                if sha(state) != expected:
                    raise ValueError(f"Unexpected baseline checkpoint: {name}")
                with (session / "states" / name).open("xb") as output:
                    output.write(state)
        outputs[label] = entry
    for path, before in protected.items():
        if before != (sha(path.read_bytes()), path.stat().st_mtime_ns):
            raise RuntimeError(f"Protected input changed: {path}")
    report = {"bus_address": "0x0862C272", "record_index": 0, "record_bus": "0x0862C250",
              "field_offset": "0x22", "file_offset": hex(OFFSET), "original_byte": "15", "modified_byte": "16",
              "difference_count": len(differences), "outputs": outputs, "protected_input_checks": "passed",
              "runtime_status": "untested"}
    (run / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(run)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()

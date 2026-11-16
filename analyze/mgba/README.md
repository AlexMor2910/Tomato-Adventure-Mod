# Isolated mGBA runtime investigation

Prepare a fresh session from the fingerprinted ROMs:

```powershell
python tools/analyze/mgba/prepare_session.py
```

Use the exact directory printed, then launch visible manual gameplay:

```powershell
python tools/analyze/mgba/start_session.py reverse_engineering/mgba/run-<ID>
```

The launcher waits until mGBA closes and verifies both source ROMs plus the
isolated ROM/executable copies. It refuses to overwrite launch logs. The session
contains copies of the installed executables, an English ROM copy, portable
configuration and isolated saves/states/screenshots/logs. It imports no existing
save/state and applies no patch or cheat. The entire session tree is Git-ignored.

`probe_debugger.py <session> [--frontend sdl|qt]` is an **experimental diagnostic**,
not a verified capture workflow. Both hidden probes in this session failed to
establish a GDB endpoint. It launches only its own emulator, times out, stops that
process and checks fingerprints. `rsp.py` implements read-only remote operations
for the probe; its register/breakpoint/stepping operations were not reached in
these attempts. No generic write or patch command is exposed.

Use [the setup procedure](../../../reverse_engineering/mgba_setup.md) and
[the manual test plan](../../../reverse_engineering/gimmick_runtime_tests.md).
`check_capture.py` checks numbers **you actually recorded**; it cannot establish
runtime evidence from invented inputs. Its output can be redirected to a new,
uniquely named file under the session's `logs/` directory.

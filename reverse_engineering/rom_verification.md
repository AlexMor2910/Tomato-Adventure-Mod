# ROM Verification: Gimmick Table and Loader

Read-only binary reconnaissance. Confidence: **Confirmed (binary)** means exact observed bytes or arithmetic; **Confirmed (source comparison)** means the documented limited checks pass; gameplay meanings remain Candidate/Unconfirmed until consumer and runtime evidence establishes them.

## Inputs and reproducibility

ROMs were located recursively rather than assumed from prior paths. Filename hints select default roles; matching title/game code and patch checks support these roles, but this report does not authenticate a canonical clean dump against an external hash database. All file offsets are zero-based; ROM bus address = file offset + 0x08000000. RAM literals have no ROM file offsets.

| Role | Located path | Bytes | SHA-256 | Header title / game code |
| --- | --- | --- | --- | --- |
| Japanese | `Tomato Adventure (Japan).gba` | 8,388,608 (`0x00800000`) | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` | `TOMATO_ADV` / `AGLJ` |
| English-patched | `Tomato Adventure (Japan) (patched).gba` | 8,388,608 (`0x00800000`) | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` | `TOMATO_ADV` / `AGLJ` |

Discovered .gba candidates: `Tomato Adventure (Japan) (patched).gba`; `Tomato Adventure (Japan).gba`

Toolkit source/asset aggregate SHA-256 before/after analysis: `86b596dd580c0cc86b41392d45ac622bb2a256aa6bfca51cbb93618ce2529787` (relative filenames + each file's SHA-256; .gba excluded).

Re-run from the repository root:

```powershell
python tools/analyze/verify_gimmick_roms.py --japanese 'Tomato Adventure (Japan).gba' --english 'Tomato Adventure (Japan) (patched).gba'
```

Without explicit input flags, the script recursively discovers .gba files and refuses ambiguous filename-based selection. Pass discovered paths explicitly if files are renamed or additional candidates appear. The script uses read-only input reads, bounds checks, and post-analysis hash/size/timestamp checks; it writes only this report and the CSV. It never executes the translation build. Script paths: `tools/analyze/verify_gimmick_roms.py` and `tools/analyze/thumb_inspect.py`.

## Table extraction and byte-for-byte comparison

Inspected 50 records of 0x58 bytes at file `0x0062C250` / bus `0x0862C250`. Half-open table extent: file `0x0062C250`–`0x0062D380`, bus `0x0862C250`–`0x0862D380`. This verifies those 50 supported records are present; it does not prove a physical table terminator or exclude unused entries.

**49/50 complete records are byte-identical; 1 record(s) differ; 3 differing bytes total.** Text bytes +0x00–+0x21 differ at 0 positions; non-text bytes +0x22–+0x57 differ at 3 positions.

| Record index / English source name | Field offset | File offset | ROM bus | Japanese byte | English byte |
| --- | --- | --- | --- | --- | --- |
| `0x1D` / Choo-Choo | `0x44` | `0x0062CC8C` | `0x0862CC8C` | `0x1C` | `0xB0` |
| `0x1D` / Choo-Choo | `0x45` | `0x0062CC8D` | `0x0862CC8D` | `0x7A` | `0xAF` |
| `0x1D` / Choo-Choo | `0x46` | `0x0062CC8E` | `0x0862CC8E` | `0x57` | `0x68` |

CSV: [data/gimmick_raw_fields.csv](data/gimmick_raw_fields.csv), 100 rows (50 per ROM). Each row contains all 54 non-text bytes as unsigned decimal columns `byte_22_u8`…`byte_57_u8`, a lossless hex string, record hash/address, difference metadata, and little-endian word views at +0x3C/+0x40/+0x44/+0x48/+0x4C/+0x50/+0x54. Word views are raw numeric interpretations, not assertions that these fields are pointers. English names are manifest annotations; expected loader IDs are source-derived, not emulator observations.

### Choo-Choo graphics pointer

Record index 0x1D (manifest Choo-Choo), expected loader ID 0x1E, starts at file `0x0062CC48` / bus `0x0862CC48`. Field +0x44 occupies file `0x0062CC8C`–`0x0062CC90` (half-open).

- Japanese bytes: `1c 7a 57 08` → little-endian `0x08577A1C`.
- English bytes: `b0 af 68 08` → little-endian `0x0868AFB0`.
- Japanese pointed-to file offset `0x00577A1C`, first four bytes `30 00 30 00`; format byte `0x30`, 24-bit LE size `0x00003000`.
- English-patched pointed-to file offset `0x0068AFB0`, first four bytes `30 00 30 00`; format byte `0x30`, 24-bit LE size `0x00003000`.

RLE packet metadata walk (no graphics decompression/export):

| ROM | Encoded bytes consumed through final packet | Header decoded size | Nominal packet output | Overshoot | Final packet evidence |
| --- | --- | --- | --- | --- | --- |
| Japanese | 5049 | 12288 | 12288 | 0 | File `0x00578DD3` / bus `0x08578DD3`; flag `0x98`, payload preview `00` (1 byte(s)); 12261 bytes before packet, nominal count 27 |
| English-patched | 6955 | 12288 | 12357 | 69 | File `0x0068CAD9` / bus `0x0868CAD9`; flag `0xFF`, payload preview `00` (1 byte(s)); 12227 bytes before packet, nominal count 130 |

**Observed RLE length inconsistency:** the English stream consumes 6955 encoded bytes through its final packet, exceeding the source's 5,049-byte original budget. Its packets nominally produce 12357 bytes against a header size of 12288 (69 extra). This supports relocation while identifying a data-format anomaly. `inserter/rle.cpp:17-35` initializes a repeat length to 0x82 and can retain it when fewer identical bytes remain; that source defect is consistent with an oversized final repeat, but build provenance and actual decompressor behavior are not established. No graphics were decompressed/exported and no runtime fault is claimed.

`inserter/images.cpp:754-786` loads original tileset file 0x00577A1C and conditionally rewrites slot 0x0062CC8C through `SaveCompressedTileset`/`WriteRelocs` (lines 167-180/92-96). Header method 0x30 is the RLE format implemented in `inserter/rle.cpp`; the source's shared allocation pool spans file 0x0064B4EC-0x007F0000 for comparison with the observed location. A changed pointer is consistent with known translation image relocation. It does not prove the entire patch was produced by the currently checked source/executable, nor decode the graphic or its runtime consumer. No gameplay-field meanings are inferred from numeric values.

## Loader literals

The four slots are compared across ROMs and with `asm/gimmick_text.asm:77-92` comments. Literal slot addresses are ROM; values beginning 0x03 are IWRAM.

| Slot file / bus | Japanese raw bytes / value | English raw bytes / value | Expected value / role | Comparison |
| --- | --- | --- | --- | --- |
| `0x000655D4` / `0x080655D4` | `bc 18 00 03` / `0x030018BC` | `bc 18 00 03` / `0x030018BC` | `0x030018BC`; utility parameters (IWRAM) | MATCH |
| `0x000655D8` / `0x080655D8` | `d2 1a 00 03` / `0x03001AD2` | `d2 1a 00 03` / `0x03001AD2` | `0x03001AD2`; ID argument (IWRAM) | MATCH |
| `0x000655DC` / `0x080655DC` | `f8 c1 62 08` / `0x0862C1F8` | `f8 c1 62 08` / `0x0862C1F8` | `0x0862C1F8`; original record base minus 0x58 (ROM bus) | MATCH |
| `0x000655E0` / `0x080655E0` | `34 3f 00 03` / `0x03003F34` | `34 3f 00 03` / `0x03003F34` | `0x03003F34`; work-record base (IWRAM) | MATCH |

## Loader regions and exact bytes

Ranges are half-open. The continuation includes its original four-word literal pool; it is not all executable instructions. Inspection ends at 0x000656C2, the source epilogue patch boundary, not a claim about the full native function size.

| Region | File range / bus range | Bytes | Differing bytes | Japanese SHA-256 | English SHA-256 |
| --- | --- | --- | --- | --- | --- |
| loader prefix | `0x00065518`–`0x0006556C` / `0x08065518`–`0x0806556C` | 84 | 79 | `64df0a92cac379ef5e4319871c621977031f36ab0afde7d2ae3cda9d65b42c52` | `2720356cf682fb2f58890e6f6f19f739744d26f2d803965b56f65ddd18a6ea03` |
| retained continuation, including four literal slots | `0x0006556C`–`0x000656B8` / `0x0806556C`–`0x080656B8` | 332 | 0 | `2f5bd28aac0da08d04a439acfc24e65529bee9f6f5c92c6226516cd4598184f3` | `2f5bd28aac0da08d04a439acfc24e65529bee9f6f5c92c6226516cd4598184f3` |
| epilogue patch region | `0x000656B8`–`0x000656C2` / `0x080656B8`–`0x080656C2` | 10 | 5 | `a9d2b3876577ccd2bdf166081cfe0cc83c24bccaaf5eb50cf6d7049e7746a779` | `5841a4fd9d4d4b2eebf704deaa0459cb48f639f4da4a67d3b0e0ce5af9e05e10` |

### Japanese: loader hex dump

Format: file offset / ROM bus address, followed by exact bytes. Includes literal pools as data.

```text
00065518 / 08065518  f0 b5 47 46 80 b4 2d 4f 2d 4c 20 78 58 22 50 43
00065528 / 08065528  2c 49 40 18 f8 60 2c 4e be 60 7a 60 04 f0 6a fd
00065538 / 08065538  fe 60 00 20 80 46 08 20 78 70 04 f0 c9 fd 79 78
00065548 / 08065548  30 1c 68 30 01 70 43 38 02 78 7f 21 8c 46 60 46
00065558 / 08065558  10 40 31 1c 70 31 08 70 52 00 30 1c 6f 30 02 70
00065568 / 08065568  48 38 01 78 0f 25 2a 1c 0a 40 45 30 02 70 00 20
00065578 / 08065578  33 1c 6d 33 18 70 09 06 09 0f 03 20 01 40 30 1c
00065588 / 08065588  6e 30 01 70 60 78 01 38 40 00 78 70 38 71 40 46
00065598 / 08065598  78 71 30 1c 28 30 b9 88 43 18 fb 60 19 78 58 1c
000655A8 / 080655A8  f8 60 30 1c 69 30 01 70 7a 70 01 2a 01 d0 02 2a
000655B8 / 080655B8  14 d1 59 78 28 1c 08 40 78 70 31 1c 72 31 08 70
000655C8 / 080655C8  58 78 01 09 00 01 09 18 29 40 0e e0 bc 18 00 03
000655D8 / 080655D8  d2 1a 00 03 f8 c1 62 08 34 3f 00 03 59 78 60 46
000655E8 / 080655E8  08 40 31 1c 72 31 08 70 00 21 79 70 30 1c 71 30
000655F8 / 080655F8  01 70 32 49 32 4a d0 6b c8 60 03 78 4b 70 01 30
00065608 / 08065608  c8 60 10 1c 6b 30 03 70 08 30 88 60 08 20 08 71
00065618 / 08065618  0b 1c 2c 4d a8 46 17 1c 2b 4d 2c 4e 2c 4c d8 68
00065628 / 08065628  01 78 59 70 01 30 d8 60 08 06 00 28 09 d0 98 68
00065638 / 08065638  01 70 01 30 98 60 18 79 01 38 18 71 00 06 00 28
00065648 / 08065648  ed d1 9a 68 2a 60 f9 6b 45 46 68 78 01 38 58 70
00065658 / 08065658  58 78 98 80 98 88 09 18 d9 60 09 20 58 60 9a 60
00065668 / 08065668  08 20 58 70 09 20 58 60 d8 68 09 30 d8 60 22 68
00065678 / 08065678  90 00 80 19 19 68 01 60 01 32 22 60 d8 68 01 78
00065688 / 08065688  59 70 98 68 01 70 01 30 98 60 41 46 88 78 58 70
00065698 / 08065698  39 1c 6a 31 08 70 20 68 01 38 20 60 80 00 80 19
000656A8 / 080656A8  00 68 18 60 58 78 01 38 58 70 00 06 00 28 d9 d1
000656B8 / 080656B8  08 bc 98 46 f0 bc 01 bc 00 47
```

### English-patched: loader hex dump

Format: file offset / ROM bus address, followed by exact bytes. Includes literal pools as data.

```text
00065518 / 08065518  43 46 f8 b5 2d 4f 30 4e 2d 4c 20 78 85 01 58 22
00065528 / 08065528  50 43 2c 49 09 18 30 1c 94 f0 0c f8 00 20 80 46
00065538 / 08065538  0b 48 40 19 30 60 f8 60 10 20 78 70 04 f0 c8 fd
00065548 / 08065548  79 78 33 1c 68 33 19 70 35 1c 25 35 2a 78 7f 20
00065558 / 08065558  84 46 10 40 18 72 52 00 da 71 a8 1c 01 68 01 e0
00065568 / 08065568  de ff 7e 08 0f 25 2a 1c 0a 40 45 30 02 70 00 20
00065578 / 08065578  33 1c 6d 33 18 70 09 06 09 0f 03 20 01 40 30 1c
00065588 / 08065588  6e 30 01 70 60 78 01 38 40 00 78 70 38 71 40 46
00065598 / 08065598  78 71 30 1c 28 30 b9 88 43 18 fb 60 19 78 58 1c
000655A8 / 080655A8  f8 60 30 1c 69 30 01 70 7a 70 01 2a 01 d0 02 2a
000655B8 / 080655B8  14 d1 59 78 28 1c 08 40 78 70 31 1c 72 31 08 70
000655C8 / 080655C8  58 78 01 09 00 01 09 18 29 40 0e e0 bc 18 00 03
000655D8 / 080655D8  d2 1a 00 03 f8 c1 62 08 34 3f 00 03 59 78 60 46
000655E8 / 080655E8  08 40 31 1c 72 31 08 70 00 21 79 70 30 1c 71 30
000655F8 / 080655F8  01 70 32 49 32 4a d0 6b c8 60 03 78 4b 70 01 30
00065608 / 08065608  c8 60 10 1c 6b 30 03 70 08 30 88 60 08 20 08 71
00065618 / 08065618  0b 1c 2c 4d a8 46 17 1c 2b 4d 2c 4e 2c 4c d8 68
00065628 / 08065628  01 78 59 70 01 30 d8 60 08 06 00 28 09 d0 98 68
00065638 / 08065638  01 70 01 30 98 60 18 79 01 38 18 71 00 06 00 28
00065648 / 08065648  ed d1 9a 68 2a 60 f9 6b 45 46 68 78 01 38 58 70
00065658 / 08065658  58 78 98 80 98 88 09 18 d9 60 09 20 58 60 9a 60
00065668 / 08065668  08 20 58 70 09 20 58 60 d8 68 09 30 d8 60 22 68
00065678 / 08065678  90 00 80 19 19 68 01 60 01 32 22 60 d8 68 01 78
00065688 / 08065688  59 70 98 68 01 70 01 30 98 60 41 46 88 78 58 70
00065698 / 08065698  39 1c 6a 31 08 70 20 68 01 38 20 60 80 00 80 19
000656A8 / 080656A8  00 68 18 60 58 78 01 38 58 70 00 06 00 28 d9 d1
000656B8 / 080656B8  f8 bc 98 46 01 bc 00 47 00 00
```

## ASM comparison

Checks below derive expected bytes from the currently read `asm/gimmick_text.asm`. They cover its direct db/dw writes, the loader prefix, name consumer patch, description pointer-store patches and epilogue instructions. The small source encoder implements only the relevant Thumb subset. The symbolic `bl CopyString8x8Clear8` remains NOT VERIFIED because its placement is not declared here; its actual decoded call target is still recorded. The prefix's pseudo-ldr is checked by resolved literal value rather than an assumed allocation address. Region padding and the entire translation project are not reassembled.

Results: **77 matching checks, 0 mismatches, 1 unverified check(s).** Source file SHA-256: `562e3dffa998a1709329af6d05bc34cefde895f3c0277a7e70100f4ccbe2fdc3`.

| Source line | Bus / file | ASM | Expected | English observed | Status |
| --- | --- | --- | --- | --- | --- |
| `asm/gimmick_text.asm:36` | `0x0804AB7C` / `0x0004AB7C` | `dw org(GimmickText)` | `1e 00 7f 08` | `1e 00 7f 08` | MATCH |
| `asm/gimmick_text.asm:38` | `0x0804AAC4` / `0x0004AAC4` | `db @Stride` | `40` | `40` | MATCH |
| `asm/gimmick_text.asm:40` | `0x0804AAD0` / `0x0004AAD0` | `db @NameLen` | `10` | `10` | MATCH |
| `asm/gimmick_text.asm:43` | `0x0804AADC` / `0x0004AADC` | `bl CopyString8x8Clear8` | `bl CopyString8x8Clear8` | `26 f0 8d fe; bl 0x080717FA` | NOT VERIFIED |
| `asm/gimmick_text.asm:56` | `0x0802B868` / `0x0002B868` | `ldr r1,[r0,0]` | `01 68` | `01 68` | MATCH |
| `asm/gimmick_text.asm:57` | `0x0802B86A` / `0x0002B86A` | `str r1,[r5,12]` | `e9 60` | `e9 60` | MATCH |
| `asm/gimmick_text.asm:59` | `0x0802B86C` / `0x0002B86C` | `add r0,0x68` | `68 30` | `68 30` | MATCH |
| `asm/gimmick_text.asm:60` | `0x0802B86E` / `0x0002B86E` | `ldrb r0,[r0,0]` | `00 78` | `00 78` | MATCH |
| `asm/gimmick_text.asm:61` | `0x0802B870` / `0x0002B870` | `strb r0,[r5,5]` | `68 71` | `68 71` | MATCH |
| `asm/gimmick_text.asm:62` | `0x0802B872` / `0x0002B872` | `str r2,[r5,8]` | `aa 60` | `aa 60` | MATCH |
| `asm/gimmick_text.asm:65` | `0x0802B874` / `0x0002B874` | `bl 0x0802BEF0` | `00 f0 3c fb` | `00 f0 3c fb` | MATCH |
| `asm/gimmick_text.asm:66` | `0x0802B878` / `0x0002B878` | `b 0x0802B882` | `03 e0` | `03 e0` | MATCH |
| `asm/gimmick_text.asm:73` | `0x08065518` / `0x00065518` | `mov r3,r8` | `43 46` | `43 46` | MATCH |
| `asm/gimmick_text.asm:74` | `0x0806551A` / `0x0006551A` | `push r3-r7,r14` | `f8 b5` | `f8 b5` | MATCH |
| `asm/gimmick_text.asm:77` | `0x0806551C` / `0x0006551C` | `ldr r7,[0x080655D4]` | `2d 4f` | `2d 4f` | MATCH |
| `asm/gimmick_text.asm:79` | `0x0806551E` / `0x0006551E` | `ldr r6,[0x080655E0]` | `30 4e` | `30 4e` | MATCH |
| `asm/gimmick_text.asm:81` | `0x08065520` / `0x00065520` | `ldr r4,[0x080655D8]` | `2d 4c` | `2d 4c` | MATCH |
| `asm/gimmick_text.asm:84` | `0x08065522` / `0x00065522` | `ldrb r0,[r4]` | `20 78` | `20 78` | MATCH |
| `asm/gimmick_text.asm:87` | `0x08065524` / `0x00065524` | `lsl r5,r0,6` | `85 01` | `85 01` | MATCH |
| `asm/gimmick_text.asm:89` | `0x08065526` / `0x00065526` | `mov r2,0x58` | `58 22` | `58 22` | MATCH |
| `asm/gimmick_text.asm:90` | `0x08065528` / `0x00065528` | `mul r0,r2` | `50 43` | `50 43` | MATCH |
| `asm/gimmick_text.asm:92` | `0x0806552A` / `0x0006552A` | `ldr r1,[0x080655DC]` | `2c 49` | `2c 49` | MATCH |
| `asm/gimmick_text.asm:93` | `0x0806552C` / `0x0006552C` | `add r1,r1,r0` | `09 18` | `09 18` | MATCH |
| `asm/gimmick_text.asm:95` | `0x0806552E` / `0x0006552E` | `mov r0,r6` | `30 1c` | `30 1c` | MATCH |
| `asm/gimmick_text.asm:96` | `0x08065530` / `0x00065530` | `bl 0x080F954C` | `94 f0 0c f8` | `94 f0 0c f8` | MATCH |
| `asm/gimmick_text.asm:99` | `0x08065534` / `0x00065534` | `mov r0,0` | `00 20` | `00 20` | MATCH |
| `asm/gimmick_text.asm:100` | `0x08065536` / `0x00065536` | `mov r8,r0` | `80 46` | `80 46` | MATCH |
| `asm/gimmick_text.asm:103` | `0x08065538` / `0x00065538` | `ldr r0,=GimmickText - @Stride` | `PC-relative ldr r0 resolving to 0x087EFFDE` | `0b 48; ldr r0, [pc, #44] ; slot 0x08065568 = 0x087EFFDE` | MATCH (literal-resolved) |
| `asm/gimmick_text.asm:104` | `0x0806553A` / `0x0006553A` | `add r0,r0,r5` | `40 19` | `40 19` | MATCH |
| `asm/gimmick_text.asm:105` | `0x0806553C` / `0x0006553C` | `str r0,[r6]` | `30 60` | `30 60` | MATCH |
| `asm/gimmick_text.asm:108` | `0x0806553E` / `0x0006553E` | `str r0,[r7,12]` | `f8 60` | `f8 60` | MATCH |
| `asm/gimmick_text.asm:109` | `0x08065540` / `0x00065540` | `mov r0,@NameLen` | `10 20` | `10 20` | MATCH |
| `asm/gimmick_text.asm:110` | `0x08065542` / `0x00065542` | `strb r0,[r7,1]` | `78 70` | `78 70` | MATCH |
| `asm/gimmick_text.asm:111` | `0x08065544` / `0x00065544` | `bl 0x0806A0D8` | `04 f0 c8 fd` | `04 f0 c8 fd` | MATCH |
| `asm/gimmick_text.asm:112` | `0x08065548` / `0x00065548` | `ldrb r1,[r7,1]` | `79 78` | `79 78` | MATCH |
| `asm/gimmick_text.asm:113` | `0x0806554A` / `0x0006554A` | `mov r3,r6` | `33 1c` | `33 1c` | MATCH |
| `asm/gimmick_text.asm:114` | `0x0806554C` / `0x0006554C` | `add r3,0x68` | `68 33` | `68 33` | MATCH |
| `asm/gimmick_text.asm:115` | `0x0806554E` / `0x0006554E` | `strb r1,[r3,0]` | `19 70` | `19 70` | MATCH |
| `asm/gimmick_text.asm:118` | `0x08065550` / `0x00065550` | `mov r5,r6` | `35 1c` | `35 1c` | MATCH |
| `asm/gimmick_text.asm:119` | `0x08065552` / `0x00065552` | `add r5,0x25` | `25 35` | `25 35` | MATCH |
| `asm/gimmick_text.asm:120` | `0x08065554` / `0x00065554` | `ldrb r2,[r5]` | `2a 78` | `2a 78` | MATCH |
| `asm/gimmick_text.asm:121` | `0x08065556` / `0x00065556` | `mov r0,0x7F` | `7f 20` | `7f 20` | MATCH |
| `asm/gimmick_text.asm:122` | `0x08065558` / `0x00065558` | `mov r12,r0` | `84 46` | `84 46` | MATCH |
| `asm/gimmick_text.asm:123` | `0x0806555A` / `0x0006555A` | `and r0,r2` | `10 40` | `10 40` | MATCH |
| `asm/gimmick_text.asm:125` | `0x0806555C` / `0x0006555C` | `strb r0,[r3,8]` | `18 72` | `18 72` | MATCH |
| `asm/gimmick_text.asm:127` | `0x0806555E` / `0x0006555E` | `lsl r2,r2,1` | `52 00` | `52 00` | MATCH |
| `asm/gimmick_text.asm:128` | `0x08065560` / `0x00065560` | `strb r2,[r3,7]` | `da 71` | `da 71` | MATCH |
| `asm/gimmick_text.asm:131` | `0x08065562` / `0x00065562` | `add r0,r5,2` | `a8 1c` | `a8 1c` | MATCH |
| `asm/gimmick_text.asm:132` | `0x08065564` / `0x00065564` | `ldr r1,[r0]` | `01 68` | `01 68` | MATCH |
| `asm/gimmick_text.asm:133` | `0x08065566` / `0x00065566` | `b 0x0806556C` | `01 e0` | `01 e0` | MATCH |
| `asm/gimmick_text.asm:140` | `0x080656B8` / `0x000656B8` | `pop r3-r7` | `f8 bc` | `f8 bc` | MATCH |
| `asm/gimmick_text.asm:141` | `0x080656BA` / `0x000656BA` | `mov r8,r3` | `98 46` | `98 46` | MATCH |
| `asm/gimmick_text.asm:142` | `0x080656BC` / `0x000656BC` | `pop r0` | `01 bc` | `01 bc` | MATCH |
| `asm/gimmick_text.asm:143` | `0x080656BE` / `0x000656BE` | `bx r0` | `00 47` | `00 47` | MATCH |
| `asm/gimmick_text.asm:152` | `0x0804DE4C` / `0x0004DE4C` | `dw org(GimmickText) + @NameLen` | `2e 00 7f 08` | `2e 00 7f 08` | MATCH |
| `asm/gimmick_text.asm:154` | `0x0804DE2A` / `0x0004DE2A` | `db @Stride` | `40` | `40` | MATCH |
| `asm/gimmick_text.asm:156` | `0x0804DE24` / `0x0004DE24` | `db @DescLen` | `30` | `30` | MATCH |
| `asm/gimmick_text.asm:161` | `0x0804DE32` / `0x0004DE32` | `add r0,r0,2` | `80 1c` | `80 1c` | MATCH |
| `asm/gimmick_text.asm:162` | `0x0804DE34` / `0x0004DE34` | `str r1,[r0,0]` | `01 60` | `01 60` | MATCH |
| `asm/gimmick_text.asm:163` | `0x0804DE36` / `0x0004DE36` | `nop` | `c0 46` | `c0 46` | MATCH |
| `asm/gimmick_text.asm:167` | `0x0804DF80` / `0x0004DF80` | `dw org(GimmickText) + @NameLen` | `2e 00 7f 08` | `2e 00 7f 08` | MATCH |
| `asm/gimmick_text.asm:169` | `0x0804DF3E` / `0x0004DF3E` | `db @Stride` | `40` | `40` | MATCH |
| `asm/gimmick_text.asm:171` | `0x0804DF38` / `0x0004DF38` | `db @DescLen` | `30` | `30` | MATCH |
| `asm/gimmick_text.asm:176` | `0x0804DF46` / `0x0004DF46` | `add r0,r0,2` | `80 1c` | `80 1c` | MATCH |
| `asm/gimmick_text.asm:177` | `0x0804DF48` / `0x0004DF48` | `str r1,[r0,0]` | `01 60` | `01 60` | MATCH |
| `asm/gimmick_text.asm:178` | `0x0804DF4A` / `0x0004DF4A` | `nop` | `c0 46` | `c0 46` | MATCH |
| `asm/gimmick_text.asm:182` | `0x0804E04C` / `0x0004E04C` | `dw org(GimmickText) + @NameLen` | `2e 00 7f 08` | `2e 00 7f 08` | MATCH |
| `asm/gimmick_text.asm:184` | `0x0804DFC2` / `0x0004DFC2` | `db @Stride` | `40` | `40` | MATCH |
| `asm/gimmick_text.asm:186` | `0x0804DFBC` / `0x0004DFBC` | `db @DescLen` | `30` | `30` | MATCH |
| `asm/gimmick_text.asm:191` | `0x0804DFCA` / `0x0004DFCA` | `add r0,r0,2` | `80 1c` | `80 1c` | MATCH |
| `asm/gimmick_text.asm:192` | `0x0804DFCC` / `0x0004DFCC` | `str r1,[r0,0]` | `01 60` | `01 60` | MATCH |
| `asm/gimmick_text.asm:193` | `0x0804DFCE` / `0x0004DFCE` | `nop` | `c0 46` | `c0 46` | MATCH |
| `asm/gimmick_text.asm:198` | `0x0804E7F8` / `0x0004E7F8` | `dw org(GimmickText) + @NameLen` | `2e 00 7f 08` | `2e 00 7f 08` | MATCH |
| `asm/gimmick_text.asm:200` | `0x0804E7C8` / `0x0004E7C8` | `db @Stride` | `40` | `40` | MATCH |
| `asm/gimmick_text.asm:202` | `0x0804E7C2` / `0x0004E7C2` | `db @DescLen` | `30` | `30` | MATCH |
| `asm/gimmick_text.asm:207` | `0x0804E7D0` / `0x0004E7D0` | `add r0,r0,2` | `80 1c` | `80 1c` | MATCH |
| `asm/gimmick_text.asm:208` | `0x0804E7D2` / `0x0004E7D2` | `str r1,[r0,0]` | `01 60` | `01 60` | MATCH |
| `asm/gimmick_text.asm:209` | `0x0804E7D4` / `0x0004E7D4` | `nop` | `c0 46` | `c0 46` | MATCH |

## Linear Thumb instruction inspection

Generated by the local `thumb_inspect.py` helper. This is limited instruction-format inspection, not an independently validated full disassembler, control-flow graph or runtime trace. Register moves may appear as add-immediate-zero encodings; this report uses instruction encoding rather than guessing higher-level semantics. The four literal slots at file [0x655D4,0x655E4) are excluded from both listings; the patched prefix's literal at [0x65568,0x6556C) is also excluded. Padding at [0x656C0,0x656C2) is excluded.

### Japanese: instruction listing

```text
00065518 / 08065518  f0 b5       push {r4, r5, r6, r7, lr}
0006551A / 0806551A  47 46       mov r7, r8
0006551C / 0806551C  80 b4       push {r7}
0006551E / 0806551E  2d 4f       ldr r7, [pc, #180] ; slot 0x080655D4 = 0x030018BC
00065520 / 08065520  2d 4c       ldr r4, [pc, #180] ; slot 0x080655D8 = 0x03001AD2
00065522 / 08065522  20 78       ldrb r0, [r4, #0]
00065524 / 08065524  58 22       mov r2, #88
00065526 / 08065526  50 43       mul r0, r2
00065528 / 08065528  2c 49       ldr r1, [pc, #176] ; slot 0x080655DC = 0x0862C1F8
0006552A / 0806552A  40 18       add r0, r0, r1
0006552C / 0806552C  f8 60       str r0, [r7, #12]
0006552E / 0806552E  2c 4e       ldr r6, [pc, #176] ; slot 0x080655E0 = 0x03003F34
00065530 / 08065530  be 60       str r6, [r7, #8]
00065532 / 08065532  7a 60       str r2, [r7, #4]
00065534 / 08065534  04 f0 6a fd bl 0x0806A00C
00065538 / 08065538  fe 60       str r6, [r7, #12]
0006553A / 0806553A  00 20       mov r0, #0
0006553C / 0806553C  80 46       mov r8, r0
0006553E / 0806553E  08 20       mov r0, #8
00065540 / 08065540  78 70       strb r0, [r7, #1]
00065542 / 08065542  04 f0 c9 fd bl 0x0806A0D8
00065546 / 08065546  79 78       ldrb r1, [r7, #1]
00065548 / 08065548  30 1c       add r0, r6, #0
0006554A / 0806554A  68 30       add r0, #104
0006554C / 0806554C  01 70       strb r1, [r0, #0]
0006554E / 0806554E  43 38       sub r0, #67
00065550 / 08065550  02 78       ldrb r2, [r0, #0]
00065552 / 08065552  7f 21       mov r1, #127
00065554 / 08065554  8c 46       mov r12, r1
00065556 / 08065556  60 46       mov r0, r12
00065558 / 08065558  10 40       and r0, r2
0006555A / 0806555A  31 1c       add r1, r6, #0
0006555C / 0806555C  70 31       add r1, #112
0006555E / 0806555E  08 70       strb r0, [r1, #0]
00065560 / 08065560  52 00       lsl r2, r2, #1
00065562 / 08065562  30 1c       add r0, r6, #0
00065564 / 08065564  6f 30       add r0, #111
00065566 / 08065566  02 70       strb r2, [r0, #0]
00065568 / 08065568  48 38       sub r0, #72
0006556A / 0806556A  01 78       ldrb r1, [r0, #0]
0006556C / 0806556C  0f 25       mov r5, #15
0006556E / 0806556E  2a 1c       add r2, r5, #0
00065570 / 08065570  0a 40       and r2, r1
00065572 / 08065572  45 30       add r0, #69
00065574 / 08065574  02 70       strb r2, [r0, #0]
00065576 / 08065576  00 20       mov r0, #0
00065578 / 08065578  33 1c       add r3, r6, #0
0006557A / 0806557A  6d 33       add r3, #109
0006557C / 0806557C  18 70       strb r0, [r3, #0]
0006557E / 0806557E  09 06       lsl r1, r1, #24
00065580 / 08065580  09 0f       lsr r1, r1, #28
00065582 / 08065582  03 20       mov r0, #3
00065584 / 08065584  01 40       and r1, r0
00065586 / 08065586  30 1c       add r0, r6, #0
00065588 / 08065588  6e 30       add r0, #110
0006558A / 0806558A  01 70       strb r1, [r0, #0]
0006558C / 0806558C  60 78       ldrb r0, [r4, #1]
0006558E / 0806558E  01 38       sub r0, #1
00065590 / 08065590  40 00       lsl r0, r0, #1
00065592 / 08065592  78 70       strb r0, [r7, #1]
00065594 / 08065594  38 71       strb r0, [r7, #4]
00065596 / 08065596  40 46       mov r0, r8
00065598 / 08065598  78 71       strb r0, [r7, #5]
0006559A / 0806559A  30 1c       add r0, r6, #0
0006559C / 0806559C  28 30       add r0, #40
0006559E / 0806559E  b9 88       ldrh r1, [r7, #4]
000655A0 / 080655A0  43 18       add r3, r0, r1
000655A2 / 080655A2  fb 60       str r3, [r7, #12]
000655A4 / 080655A4  19 78       ldrb r1, [r3, #0]
000655A6 / 080655A6  58 1c       add r0, r3, #1
000655A8 / 080655A8  f8 60       str r0, [r7, #12]
000655AA / 080655AA  30 1c       add r0, r6, #0
000655AC / 080655AC  69 30       add r0, #105
000655AE / 080655AE  01 70       strb r1, [r0, #0]
000655B0 / 080655B0  7a 70       strb r2, [r7, #1]
000655B2 / 080655B2  01 2a       cmp r2, #1
000655B4 / 080655B4  01 d0       beq 0x080655BA
000655B6 / 080655B6  02 2a       cmp r2, #2
000655B8 / 080655B8  14 d1       bne 0x080655E4
000655BA / 080655BA  59 78       ldrb r1, [r3, #1]
000655BC / 080655BC  28 1c       add r0, r5, #0
000655BE / 080655BE  08 40       and r0, r1
000655C0 / 080655C0  78 70       strb r0, [r7, #1]
000655C2 / 080655C2  31 1c       add r1, r6, #0
000655C4 / 080655C4  72 31       add r1, #114
000655C6 / 080655C6  08 70       strb r0, [r1, #0]
000655C8 / 080655C8  58 78       ldrb r0, [r3, #1]
000655CA / 080655CA  01 09       lsr r1, r0, #4
000655CC / 080655CC  00 01       lsl r0, r0, #4
000655CE / 080655CE  09 18       add r1, r1, r0
000655D0 / 080655D0  29 40       and r1, r5
000655D2 / 080655D2  0e e0       b 0x080655F2
000655E4 / 080655E4  59 78       ldrb r1, [r3, #1]
000655E6 / 080655E6  60 46       mov r0, r12
000655E8 / 080655E8  08 40       and r0, r1
000655EA / 080655EA  31 1c       add r1, r6, #0
000655EC / 080655EC  72 31       add r1, #114
000655EE / 080655EE  08 70       strb r0, [r1, #0]
000655F0 / 080655F0  00 21       mov r1, #0
000655F2 / 080655F2  79 70       strb r1, [r7, #1]
000655F4 / 080655F4  30 1c       add r0, r6, #0
000655F6 / 080655F6  71 30       add r0, #113
000655F8 / 080655F8  01 70       strb r1, [r0, #0]
000655FA / 080655FA  32 49       ldr r1, [pc, #200] ; slot 0x080656C4 = 0x030018BC
000655FC / 080655FC  32 4a       ldr r2, [pc, #200] ; slot 0x080656C8 = 0x03003F34
000655FE / 080655FE  d0 6b       ldr r0, [r2, #60]
00065600 / 08065600  c8 60       str r0, [r1, #12]
00065602 / 08065602  03 78       ldrb r3, [r0, #0]
00065604 / 08065604  4b 70       strb r3, [r1, #1]
00065606 / 08065606  01 30       add r0, #1
00065608 / 08065608  c8 60       str r0, [r1, #12]
0006560A / 0806560A  10 1c       add r0, r2, #0
0006560C / 0806560C  6b 30       add r0, #107
0006560E / 0806560E  03 70       strb r3, [r0, #0]
00065610 / 08065610  08 30       add r0, #8
00065612 / 08065612  88 60       str r0, [r1, #8]
00065614 / 08065614  08 20       mov r0, #8
00065616 / 08065616  08 71       strb r0, [r1, #4]
00065618 / 08065618  0b 1c       add r3, r1, #0
0006561A / 0806561A  2c 4d       ldr r5, [pc, #176] ; slot 0x080656CC = 0x03001AD2
0006561C / 0806561C  a8 46       mov r8, r5
0006561E / 0806561E  17 1c       add r7, r2, #0
00065620 / 08065620  2b 4d       ldr r5, [pc, #172] ; slot 0x080656D0 = 0x03001ADC
00065622 / 08065622  2c 4e       ldr r6, [pc, #176] ; slot 0x080656D4 = 0x03000608
00065624 / 08065624  2c 4c       ldr r4, [pc, #176] ; slot 0x080656D8 = 0x03000604
00065626 / 08065626  d8 68       ldr r0, [r3, #12]
00065628 / 08065628  01 78       ldrb r1, [r0, #0]
0006562A / 0806562A  59 70       strb r1, [r3, #1]
0006562C / 0806562C  01 30       add r0, #1
0006562E / 0806562E  d8 60       str r0, [r3, #12]
00065630 / 08065630  08 06       lsl r0, r1, #24
00065632 / 08065632  00 28       cmp r0, #0
00065634 / 08065634  09 d0       beq 0x0806564A
00065636 / 08065636  98 68       ldr r0, [r3, #8]
00065638 / 08065638  01 70       strb r1, [r0, #0]
0006563A / 0806563A  01 30       add r0, #1
0006563C / 0806563C  98 60       str r0, [r3, #8]
0006563E / 0806563E  18 79       ldrb r0, [r3, #4]
00065640 / 08065640  01 38       sub r0, #1
00065642 / 08065642  18 71       strb r0, [r3, #4]
00065644 / 08065644  00 06       lsl r0, r0, #24
00065646 / 08065646  00 28       cmp r0, #0
00065648 / 08065648  ed d1       bne 0x08065626
0006564A / 0806564A  9a 68       ldr r2, [r3, #8]
0006564C / 0806564C  2a 60       str r2, [r5, #0]
0006564E / 0806564E  f9 6b       ldr r1, [r7, #60]
00065650 / 08065650  45 46       mov r5, r8
00065652 / 08065652  68 78       ldrb r0, [r5, #1]
00065654 / 08065654  01 38       sub r0, #1
00065656 / 08065656  58 70       strb r0, [r3, #1]
00065658 / 08065658  58 78       ldrb r0, [r3, #1]
0006565A / 0806565A  98 80       strh r0, [r3, #4]
0006565C / 0806565C  98 88       ldrh r0, [r3, #4]
0006565E / 0806565E  09 18       add r1, r1, r0
00065660 / 08065660  d9 60       str r1, [r3, #12]
00065662 / 08065662  09 20       mov r0, #9
00065664 / 08065664  58 60       str r0, [r3, #4]
00065666 / 08065666  9a 60       str r2, [r3, #8]
00065668 / 08065668  08 20       mov r0, #8
0006566A / 0806566A  58 70       strb r0, [r3, #1]
0006566C / 0806566C  09 20       mov r0, #9
0006566E / 0806566E  58 60       str r0, [r3, #4]
00065670 / 08065670  d8 68       ldr r0, [r3, #12]
00065672 / 08065672  09 30       add r0, #9
00065674 / 08065674  d8 60       str r0, [r3, #12]
00065676 / 08065676  22 68       ldr r2, [r4, #0]
00065678 / 08065678  90 00       lsl r0, r2, #2
0006567A / 0806567A  80 19       add r0, r0, r6
0006567C / 0806567C  19 68       ldr r1, [r3, #0]
0006567E / 0806567E  01 60       str r1, [r0, #0]
00065680 / 08065680  01 32       add r2, #1
00065682 / 08065682  22 60       str r2, [r4, #0]
00065684 / 08065684  d8 68       ldr r0, [r3, #12]
00065686 / 08065686  01 78       ldrb r1, [r0, #0]
00065688 / 08065688  59 70       strb r1, [r3, #1]
0006568A / 0806568A  98 68       ldr r0, [r3, #8]
0006568C / 0806568C  01 70       strb r1, [r0, #0]
0006568E / 0806568E  01 30       add r0, #1
00065690 / 08065690  98 60       str r0, [r3, #8]
00065692 / 08065692  41 46       mov r1, r8
00065694 / 08065694  88 78       ldrb r0, [r1, #2]
00065696 / 08065696  58 70       strb r0, [r3, #1]
00065698 / 08065698  39 1c       add r1, r7, #0
0006569A / 0806569A  6a 31       add r1, #106
0006569C / 0806569C  08 70       strb r0, [r1, #0]
0006569E / 0806569E  20 68       ldr r0, [r4, #0]
000656A0 / 080656A0  01 38       sub r0, #1
000656A2 / 080656A2  20 60       str r0, [r4, #0]
000656A4 / 080656A4  80 00       lsl r0, r0, #2
000656A6 / 080656A6  80 19       add r0, r0, r6
000656A8 / 080656A8  00 68       ldr r0, [r0, #0]
000656AA / 080656AA  18 60       str r0, [r3, #0]
000656AC / 080656AC  58 78       ldrb r0, [r3, #1]
000656AE / 080656AE  01 38       sub r0, #1
000656B0 / 080656B0  58 70       strb r0, [r3, #1]
000656B2 / 080656B2  00 06       lsl r0, r0, #24
000656B4 / 080656B4  00 28       cmp r0, #0
000656B6 / 080656B6  d9 d1       bne 0x0806566C
000656B8 / 080656B8  08 bc       pop {r3}
000656BA / 080656BA  98 46       mov r8, r3
000656BC / 080656BC  f0 bc       pop {r4, r5, r6, r7}
000656BE / 080656BE  01 bc       pop {r0}
```

### English-patched: instruction listing

```text
00065518 / 08065518  43 46       mov r3, r8
0006551A / 0806551A  f8 b5       push {r3, r4, r5, r6, r7, lr}
0006551C / 0806551C  2d 4f       ldr r7, [pc, #180] ; slot 0x080655D4 = 0x030018BC
0006551E / 0806551E  30 4e       ldr r6, [pc, #192] ; slot 0x080655E0 = 0x03003F34
00065520 / 08065520  2d 4c       ldr r4, [pc, #180] ; slot 0x080655D8 = 0x03001AD2
00065522 / 08065522  20 78       ldrb r0, [r4, #0]
00065524 / 08065524  85 01       lsl r5, r0, #6
00065526 / 08065526  58 22       mov r2, #88
00065528 / 08065528  50 43       mul r0, r2
0006552A / 0806552A  2c 49       ldr r1, [pc, #176] ; slot 0x080655DC = 0x0862C1F8
0006552C / 0806552C  09 18       add r1, r1, r0
0006552E / 0806552E  30 1c       add r0, r6, #0
00065530 / 08065530  94 f0 0c f8 bl 0x080F954C
00065534 / 08065534  00 20       mov r0, #0
00065536 / 08065536  80 46       mov r8, r0
00065538 / 08065538  0b 48       ldr r0, [pc, #44] ; slot 0x08065568 = 0x087EFFDE
0006553A / 0806553A  40 19       add r0, r0, r5
0006553C / 0806553C  30 60       str r0, [r6, #0]
0006553E / 0806553E  f8 60       str r0, [r7, #12]
00065540 / 08065540  10 20       mov r0, #16
00065542 / 08065542  78 70       strb r0, [r7, #1]
00065544 / 08065544  04 f0 c8 fd bl 0x0806A0D8
00065548 / 08065548  79 78       ldrb r1, [r7, #1]
0006554A / 0806554A  33 1c       add r3, r6, #0
0006554C / 0806554C  68 33       add r3, #104
0006554E / 0806554E  19 70       strb r1, [r3, #0]
00065550 / 08065550  35 1c       add r5, r6, #0
00065552 / 08065552  25 35       add r5, #37
00065554 / 08065554  2a 78       ldrb r2, [r5, #0]
00065556 / 08065556  7f 20       mov r0, #127
00065558 / 08065558  84 46       mov r12, r0
0006555A / 0806555A  10 40       and r0, r2
0006555C / 0806555C  18 72       strb r0, [r3, #8]
0006555E / 0806555E  52 00       lsl r2, r2, #1
00065560 / 08065560  da 71       strb r2, [r3, #7]
00065562 / 08065562  a8 1c       add r0, r5, #2
00065564 / 08065564  01 68       ldr r1, [r0, #0]
00065566 / 08065566  01 e0       b 0x0806556C
0006556C / 0806556C  0f 25       mov r5, #15
0006556E / 0806556E  2a 1c       add r2, r5, #0
00065570 / 08065570  0a 40       and r2, r1
00065572 / 08065572  45 30       add r0, #69
00065574 / 08065574  02 70       strb r2, [r0, #0]
00065576 / 08065576  00 20       mov r0, #0
00065578 / 08065578  33 1c       add r3, r6, #0
0006557A / 0806557A  6d 33       add r3, #109
0006557C / 0806557C  18 70       strb r0, [r3, #0]
0006557E / 0806557E  09 06       lsl r1, r1, #24
00065580 / 08065580  09 0f       lsr r1, r1, #28
00065582 / 08065582  03 20       mov r0, #3
00065584 / 08065584  01 40       and r1, r0
00065586 / 08065586  30 1c       add r0, r6, #0
00065588 / 08065588  6e 30       add r0, #110
0006558A / 0806558A  01 70       strb r1, [r0, #0]
0006558C / 0806558C  60 78       ldrb r0, [r4, #1]
0006558E / 0806558E  01 38       sub r0, #1
00065590 / 08065590  40 00       lsl r0, r0, #1
00065592 / 08065592  78 70       strb r0, [r7, #1]
00065594 / 08065594  38 71       strb r0, [r7, #4]
00065596 / 08065596  40 46       mov r0, r8
00065598 / 08065598  78 71       strb r0, [r7, #5]
0006559A / 0806559A  30 1c       add r0, r6, #0
0006559C / 0806559C  28 30       add r0, #40
0006559E / 0806559E  b9 88       ldrh r1, [r7, #4]
000655A0 / 080655A0  43 18       add r3, r0, r1
000655A2 / 080655A2  fb 60       str r3, [r7, #12]
000655A4 / 080655A4  19 78       ldrb r1, [r3, #0]
000655A6 / 080655A6  58 1c       add r0, r3, #1
000655A8 / 080655A8  f8 60       str r0, [r7, #12]
000655AA / 080655AA  30 1c       add r0, r6, #0
000655AC / 080655AC  69 30       add r0, #105
000655AE / 080655AE  01 70       strb r1, [r0, #0]
000655B0 / 080655B0  7a 70       strb r2, [r7, #1]
000655B2 / 080655B2  01 2a       cmp r2, #1
000655B4 / 080655B4  01 d0       beq 0x080655BA
000655B6 / 080655B6  02 2a       cmp r2, #2
000655B8 / 080655B8  14 d1       bne 0x080655E4
000655BA / 080655BA  59 78       ldrb r1, [r3, #1]
000655BC / 080655BC  28 1c       add r0, r5, #0
000655BE / 080655BE  08 40       and r0, r1
000655C0 / 080655C0  78 70       strb r0, [r7, #1]
000655C2 / 080655C2  31 1c       add r1, r6, #0
000655C4 / 080655C4  72 31       add r1, #114
000655C6 / 080655C6  08 70       strb r0, [r1, #0]
000655C8 / 080655C8  58 78       ldrb r0, [r3, #1]
000655CA / 080655CA  01 09       lsr r1, r0, #4
000655CC / 080655CC  00 01       lsl r0, r0, #4
000655CE / 080655CE  09 18       add r1, r1, r0
000655D0 / 080655D0  29 40       and r1, r5
000655D2 / 080655D2  0e e0       b 0x080655F2
000655E4 / 080655E4  59 78       ldrb r1, [r3, #1]
000655E6 / 080655E6  60 46       mov r0, r12
000655E8 / 080655E8  08 40       and r0, r1
000655EA / 080655EA  31 1c       add r1, r6, #0
000655EC / 080655EC  72 31       add r1, #114
000655EE / 080655EE  08 70       strb r0, [r1, #0]
000655F0 / 080655F0  00 21       mov r1, #0
000655F2 / 080655F2  79 70       strb r1, [r7, #1]
000655F4 / 080655F4  30 1c       add r0, r6, #0
000655F6 / 080655F6  71 30       add r0, #113
000655F8 / 080655F8  01 70       strb r1, [r0, #0]
000655FA / 080655FA  32 49       ldr r1, [pc, #200] ; slot 0x080656C4 = 0x030018BC
000655FC / 080655FC  32 4a       ldr r2, [pc, #200] ; slot 0x080656C8 = 0x03003F34
000655FE / 080655FE  d0 6b       ldr r0, [r2, #60]
00065600 / 08065600  c8 60       str r0, [r1, #12]
00065602 / 08065602  03 78       ldrb r3, [r0, #0]
00065604 / 08065604  4b 70       strb r3, [r1, #1]
00065606 / 08065606  01 30       add r0, #1
00065608 / 08065608  c8 60       str r0, [r1, #12]
0006560A / 0806560A  10 1c       add r0, r2, #0
0006560C / 0806560C  6b 30       add r0, #107
0006560E / 0806560E  03 70       strb r3, [r0, #0]
00065610 / 08065610  08 30       add r0, #8
00065612 / 08065612  88 60       str r0, [r1, #8]
00065614 / 08065614  08 20       mov r0, #8
00065616 / 08065616  08 71       strb r0, [r1, #4]
00065618 / 08065618  0b 1c       add r3, r1, #0
0006561A / 0806561A  2c 4d       ldr r5, [pc, #176] ; slot 0x080656CC = 0x03001AD2
0006561C / 0806561C  a8 46       mov r8, r5
0006561E / 0806561E  17 1c       add r7, r2, #0
00065620 / 08065620  2b 4d       ldr r5, [pc, #172] ; slot 0x080656D0 = 0x03001ADC
00065622 / 08065622  2c 4e       ldr r6, [pc, #176] ; slot 0x080656D4 = 0x03000608
00065624 / 08065624  2c 4c       ldr r4, [pc, #176] ; slot 0x080656D8 = 0x03000604
00065626 / 08065626  d8 68       ldr r0, [r3, #12]
00065628 / 08065628  01 78       ldrb r1, [r0, #0]
0006562A / 0806562A  59 70       strb r1, [r3, #1]
0006562C / 0806562C  01 30       add r0, #1
0006562E / 0806562E  d8 60       str r0, [r3, #12]
00065630 / 08065630  08 06       lsl r0, r1, #24
00065632 / 08065632  00 28       cmp r0, #0
00065634 / 08065634  09 d0       beq 0x0806564A
00065636 / 08065636  98 68       ldr r0, [r3, #8]
00065638 / 08065638  01 70       strb r1, [r0, #0]
0006563A / 0806563A  01 30       add r0, #1
0006563C / 0806563C  98 60       str r0, [r3, #8]
0006563E / 0806563E  18 79       ldrb r0, [r3, #4]
00065640 / 08065640  01 38       sub r0, #1
00065642 / 08065642  18 71       strb r0, [r3, #4]
00065644 / 08065644  00 06       lsl r0, r0, #24
00065646 / 08065646  00 28       cmp r0, #0
00065648 / 08065648  ed d1       bne 0x08065626
0006564A / 0806564A  9a 68       ldr r2, [r3, #8]
0006564C / 0806564C  2a 60       str r2, [r5, #0]
0006564E / 0806564E  f9 6b       ldr r1, [r7, #60]
00065650 / 08065650  45 46       mov r5, r8
00065652 / 08065652  68 78       ldrb r0, [r5, #1]
00065654 / 08065654  01 38       sub r0, #1
00065656 / 08065656  58 70       strb r0, [r3, #1]
00065658 / 08065658  58 78       ldrb r0, [r3, #1]
0006565A / 0806565A  98 80       strh r0, [r3, #4]
0006565C / 0806565C  98 88       ldrh r0, [r3, #4]
0006565E / 0806565E  09 18       add r1, r1, r0
00065660 / 08065660  d9 60       str r1, [r3, #12]
00065662 / 08065662  09 20       mov r0, #9
00065664 / 08065664  58 60       str r0, [r3, #4]
00065666 / 08065666  9a 60       str r2, [r3, #8]
00065668 / 08065668  08 20       mov r0, #8
0006566A / 0806566A  58 70       strb r0, [r3, #1]
0006566C / 0806566C  09 20       mov r0, #9
0006566E / 0806566E  58 60       str r0, [r3, #4]
00065670 / 08065670  d8 68       ldr r0, [r3, #12]
00065672 / 08065672  09 30       add r0, #9
00065674 / 08065674  d8 60       str r0, [r3, #12]
00065676 / 08065676  22 68       ldr r2, [r4, #0]
00065678 / 08065678  90 00       lsl r0, r2, #2
0006567A / 0806567A  80 19       add r0, r0, r6
0006567C / 0806567C  19 68       ldr r1, [r3, #0]
0006567E / 0806567E  01 60       str r1, [r0, #0]
00065680 / 08065680  01 32       add r2, #1
00065682 / 08065682  22 60       str r2, [r4, #0]
00065684 / 08065684  d8 68       ldr r0, [r3, #12]
00065686 / 08065686  01 78       ldrb r1, [r0, #0]
00065688 / 08065688  59 70       strb r1, [r3, #1]
0006568A / 0806568A  98 68       ldr r0, [r3, #8]
0006568C / 0806568C  01 70       strb r1, [r0, #0]
0006568E / 0806568E  01 30       add r0, #1
00065690 / 08065690  98 60       str r0, [r3, #8]
00065692 / 08065692  41 46       mov r1, r8
00065694 / 08065694  88 78       ldrb r0, [r1, #2]
00065696 / 08065696  58 70       strb r0, [r3, #1]
00065698 / 08065698  39 1c       add r1, r7, #0
0006569A / 0806569A  6a 31       add r1, #106
0006569C / 0806569C  08 70       strb r0, [r1, #0]
0006569E / 0806569E  20 68       ldr r0, [r4, #0]
000656A0 / 080656A0  01 38       sub r0, #1
000656A2 / 080656A2  20 60       str r0, [r4, #0]
000656A4 / 080656A4  80 00       lsl r0, r0, #2
000656A6 / 080656A6  80 19       add r0, r0, r6
000656A8 / 080656A8  00 68       ldr r0, [r0, #0]
000656AA / 080656AA  18 60       str r0, [r3, #0]
000656AC / 080656AC  58 78       ldrb r0, [r3, #1]
000656AE / 080656AE  01 38       sub r0, #1
000656B0 / 080656B0  58 70       strb r0, [r3, #1]
000656B2 / 080656B2  00 06       lsl r0, r0, #24
000656B4 / 080656B4  00 28       cmp r0, #0
000656B6 / 080656B6  d9 d1       bne 0x0806566C
000656B8 / 080656B8  f8 bc       pop {r3, r4, r5, r6, r7}
000656BA / 080656BA  98 46       mov r8, r3
000656BC / 080656BC  01 bc       pop {r0}
000656BE / 080656BE  00 47       bx r0
```

### Focused continuation observations

These data-flow observations use actual instruction bytes and the small local Thumb decoder; the listed signatures were checked in both inputs; confirm them independently before assigning gameplay meanings:

- Japanese file `0x0006556A` / bus `0x0806556A` has `01 78` (`ldrb r1,[r0]`) after forming work-record +0x27. English file `0x00065564` / bus `0x08065564` has `01 68` (`ldr r1,[r0]`), matching source line 132. This byte-load versus unaligned word-load difference is real, source-consistent, and needs architecture/runtime validation; it is not a discrepancy between the English bytes and ASM.
- At file `0x0006556C`–`0x0006558C`, both ROMs mask low four bits of incoming r1 and store at work +0x6C; shifts and mask 3 extract low-byte bits 4–5 into work +0x6E. Meaning of these groups remains unidentified.
- At file `0x0006558C`–`0x000655AE`, ID-argument byte +1 supplies a one-based selector: subtract one, multiply by two, and add to copied record +0x28. A byte is read into work +0x69; the next byte is consumed in a branch selected by the preceding low-bit group. This supports an indexed two-byte lookup, not a confirmed nine-level difficulty model or power formula.
- At file `0x000655FE` / bus `0x080655FE`, bytes `d0 6b` load a word from work-record +0x3C; at file `0x00065602` / bus `0x08065602`, `03 78` dereferences that value as a byte. PC-relative literals at file `0x000656C4` / bus `0x080656C4` and file `0x000656C8` / bus `0x080656C8` resolve to `0x030018BC` and `0x03003F34`. This strengthens the pointer-access interpretation at +0x3C but does not identify its data meaning.

## Tool availability and limits

- `arm-none-eabi-objdump` on PATH: not found.
- `arm-linux-gnueabi-objdump` on PATH: not found.
- `llvm-objdump` on PATH: not found.
- `objdump` on PATH: `C:\msys64\mingw64\bin\objdump.EXE`
- `r2` on PATH: not found.
- `radare2` on PATH: not found.
- `ghidra` on PATH: not found.
- `mgba` on PATH: not found.
- Python `capstone`: not installed.
- Python `lief`: not installed.
- Python `keystone`: not installed.
- Existing GNU objdump architecture listing exit 0; ARM advertised: False. BFD header file version (GNU Binutils) 2.43.1
- Search scope: workspace filenames and command PATH (plus Python import paths); this is not an exhaustive inventory of all installed applications.

No tool was installed. The existing objdump is usable for GBA only if its architecture listing advertises ARM; generic binary input support alone is insufficient. If no ARM-capable tool is found, obtain an ARMv4T/Thumb-capable disassembler (ARM GNU objdump, LLVM with ARM support, or Ghidra) and a GBA debugger such as mGBA for the next investigation. The local Python helper is sufficient for these bounded format/byte checks, not a replacement for full disassembly or emulation.

## Conclusions and next investigation

- The measured 50-record window and literal comparisons provide evidence for assessing the source layout. Numerical gameplay field meanings remain unverified.
- The exact table difference list above distinguishes actual changes from hypothetical source relocation. Text and raw field bytes are preserved except the explicitly listed differences.
- Source checks establish only the bounded agreement reported above; unverified symbolic calls, padding, runtime behavior and whole-ROM build provenance are outside that claim.
- Next: independently disassemble the retained loader continuation and trace accesses to +0x27 and its indexed +0x28 region, then locate callers and damage/difficulty consumers. Use debugger read watchpoints on the verified IWRAM work base and record per-Gimmick calculation paths. Investigate any RLE packet overshoot separately before trusting a future build; do not assign power/RNG/Kaizo semantics solely from byte values.

Both ROMs were re-read after analysis; SHA-256, byte size and modification timestamp matched the initial snapshots. Toolkit fingerprint also matched. Outputs contain analysis only; no translation build, source edit or ROM write occurred.

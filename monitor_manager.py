#!/usr/bin/env python3
"""Monitor Manager — parse displays, apply position via displayplacer.

Positions: R L T B TL TR BL BR  (corner = edge + configurable offset)

Offset:
  - How far the external display is pushed away from the flush corner
    alignment (left corners -> left, right corners -> right).
  - Default for corners: 2/3 of the main display's width.
  - Default for plain edges (L/R/T/B): 0.
  - Accepts pixels ("600") or a fraction of the main width ("2/3", "0.5").
  - Negative value shifts in the opposite direction.

Fixes vs. old version:
- Robust per-display parsing (no cross-contamination from the
  "Resolutions for rotation" mode blocks, which also contain "Scaling:")
- Main display detected by "main display" / built-in screen, not by list order
- Enabled displays only; error reporting from displayplacer
- No shell=True
- Corner positions no longer glue both displays to the same edge
"""

import subprocess
import re
import json
import os
import sys
import argparse

CONFIG_FILE = os.path.expanduser("~/.display_config.json")

DP_PATHS = [
    "/opt/homebrew/bin/displayplacer",
    "/usr/local/bin/displayplacer",
    "displayplacer",
]

POSITIONS = ["R", "L", "T", "B", "TL", "TR", "BL", "BR"]
DEFAULT_CORNER_OFFSET = 2 / 3  # fraction of the main display's width


def displayplacer_exec():
    for path in DP_PATHS:
        if path == "displayplacer":
            found = subprocess.run(["which", "displayplacer"], capture_output=True)
            if found.returncode == 0:
                return found.stdout.decode().strip()
        elif os.path.exists(path):
            return path
    return None


def get_display_info(ext_id=None):
    """Return (main, ext) dicts: {id, res, scaling, origin}. None if <2 displays."""
    dp = displayplacer_exec()
    if not dp:
        return None

    try:
        result = subprocess.run([dp, "list"], capture_output=True, text=True)
        output = result.stdout
    except Exception:
        return None

    # Split into display blocks: each starts with "Persistent screen id:".
    # This isolates header fields from the "Resolutions for rotation" lists.
    blocks = re.split(r"(?=Persistent screen id:)", output)
    displays = []
    for block in blocks:
        if not block.strip():
            continue
        m = re.search(r"Persistent screen id:\s*([A-Za-z0-9-]+)", block)
        if not m:
            continue
        res = re.search(r"^Resolution:\s*(\d+)x(\d+)", block, re.M)
        scaling = re.search(r"^Scaling:\s*(on|off)", block, re.M)
        enabled = re.search(r"^Enabled:\s*(true|false)", block, re.M)
        origin = re.search(r"^Origin:\s*\((-?\d+),(-?\d+)\)", block, re.M)
        is_main = "main display" in block or "MacBook built in screen" in block
        displays.append({
            "id": m.group(1),
            "res": (int(res.group(1)), int(res.group(2))) if res else (0, 0),
            "scaling": scaling.group(1) if scaling else "on",
            "enabled": enabled.group(1) == "true" if enabled else True,
            "origin": (int(origin.group(1)), int(origin.group(2))) if origin else (0, 0),
            "is_main": is_main,
        })

    if len(displays) < 2:
        return None

    main = next((d for d in displays if d["is_main"]), displays[0])
    exts = [d for d in displays if d is not main and d["enabled"]]
    if not exts:
        return None

    if ext_id:
        match = next((d for d in exts if d["id"] == ext_id), None)
        if match is None:
            return None
        return main, match

    return main, exts[0]


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def entry_value(entry):
    """Config entries are either a bare position string (old) or a dict."""
    if isinstance(entry, str):
        return entry, None
    if isinstance(entry, dict):
        return entry.get("pos"), entry.get("offset")
    return None, None


def parse_offset(value, main_res):
    """'600' -> 600 px, '2/3' -> 2/3 * main width, None -> corner default."""
    Mw = main_res[0]
    if value is None:
        return int(round(Mw * DEFAULT_CORNER_OFFSET))
    s = str(value).strip()
    if "/" in s:
        num, den = s.split("/", 1)
        return int(round(Mw * (float(num) / float(den))))
    return int(round(float(s)))


def compute_origin(pos, main_res, ext_res, offset=None):
    """displayplacer origin = top-left corner of the external display,
    y grows DOWNWARD. Main display is anchored at (0,0)."""
    Mw, Mh = main_res
    Ew, Eh = ext_res

    off = 0 if offset is None else offset

    if pos == "R":
        return Mw + off, (Mh - Eh) // 2
    if pos == "L":
        return -Ew - off, (Mh - Eh) // 2
    if pos == "T":
        return (Mw - Ew) // 2 - off, -Eh
    if pos == "B":
        return (Mw - Ew) // 2 - off, Mh
    if pos == "TL":
        return 0 - off, -Eh
    if pos == "TR":
        return Mw - Ew + off, -Eh
    if pos == "BL":
        return 0 - off, Mh
    if pos == "BR":
        return Mw - Ew + off, Mh
    return None


def apply_position(pos, offset, main, ext):
    dp = displayplacer_exec()
    if not dp:
        return False, "displayplacer not found"

    origin = compute_origin(pos, main["res"], ext["res"], offset)
    if origin is None:
        return False, f"unknown position: {pos}"

    x, y = origin
    cmd = [
        dp,
        f"id:{main['id']} res:{main['res'][0]}x{main['res'][1]} scaling:{main['scaling']} origin:(0,0)",
        f"id:{ext['id']} res:{ext['res'][0]}x{ext['res'][1]} scaling:{ext['scaling']} origin:({x},{y})",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip()
    return True, ""


def main():
    parser = argparse.ArgumentParser(description="Arrange the external monitor.")
    parser.add_argument("mode", choices=["check", "set", "preview"])
    parser.add_argument("--pos", help="R L T B TL TR BL BR")
    parser.add_argument(
        "--offset",
        help="Shift in px or a fraction of the main width (e.g. 2/3). "
             "Default for corners: 2/3 of the main display width.",
    )
    parser.add_argument("--id", help="Persistent screen id of the external display")
    args = parser.parse_args()

    info = get_display_info(args.id)
    if not info:
        print(json.dumps({"status": "error", "msg": "No external monitor"}))
        sys.exit(0)

    main_d, ext = info
    config = load_config()

    if args.mode == "check":
        pos, saved_offset = entry_value(config.get(ext["id"]))
        print(json.dumps({
            "status": "known" if pos else "new",
            "pos": pos,
            "offset": saved_offset,
            "ext_id": ext["id"],
            "main_res": main_d["res"],
            "ext_res": ext["res"],
            "current_origin": ext["origin"],
        }))
        return

    if args.mode == "preview":
        pos = args.pos or entry_value(config.get(ext["id"]))[0] or "TL"
        off = parse_offset(args.offset, main_d["res"]) if args.offset else None
        rows = {}
        for p in POSITIONS:
            default_off = parse_offset(None, main_d["res"]) if p in ("TL", "TR", "BL", "BR") else 0
            rows[p] = {
                "flush": compute_origin(p, main_d["res"], ext["res"], 0),
                "default": compute_origin(p, main_d["res"], ext["res"], default_off),
            }
        print(json.dumps({
            "status": "preview",
            "main_res": main_d["res"],
            "ext_res": ext["res"],
            "corner_default_offset": parse_offset(None, main_d["res"]),
            "requested": {"pos": pos, "offset": off,
                          "origin": compute_origin(pos, main_d["res"], ext["res"], off)},
            "all": rows,
        }, indent=2))
        return

    # mode == set
    if not args.pos:
        print(json.dumps({"status": "error", "msg": "missing --pos"}))
        sys.exit(1)

    if args.offset is None:
        _, saved_offset = entry_value(config.get(ext["id"]))
        offset = parse_offset(saved_offset, main_d["res"]) if args.pos in ("TL", "TR", "BL", "BR") else 0
    else:
        offset = parse_offset(args.offset, main_d["res"])

    ok, err = apply_position(args.pos, offset, main_d, ext)
    if ok:
        origin = compute_origin(args.pos, main_d["res"], ext["res"], offset)
        config[ext["id"]] = {"pos": args.pos, "offset": offset}
        save_config(config)
        print(json.dumps({"status": "success", "pos": args.pos,
                          "offset": offset, "origin": origin}))
    else:
        print(json.dumps({"status": "error", "msg": err}))
        sys.exit(1)


if __name__ == "__main__":
    main()

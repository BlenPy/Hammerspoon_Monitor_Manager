import subprocess
import re
import json
import os
import sys
import argparse

CONFIG_FILE = os.path.expanduser("~/.display_config.json")

def get_display_info():
    # Path search for displayplacer
    possible_paths = [
        '/opt/homebrew/bin/displayplacer',
        '/usr/local/bin/displayplacer',
        'displayplacer'
    ]
    
    cmd = None
    for path in possible_paths:
        if os.path.exists(path) or path == 'displayplacer':
            if subprocess.run(['which', path], capture_output=True).returncode == 0 or os.path.exists(path):
                cmd = [path, 'list']
                break
    
    if not cmd:
        return None, None, None, None, None, None

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
    except:
        return None, None, None, None, None, None

    # 1. Find IDs
    ids = re.findall(r"Persistent screen id:\s*([A-F0-9-]+)", output)
    if len(ids) < 2:
        return None, None, None, None, None, None
        
    main_id = ids[0]
    ext_id = ids[1]
    
    # 2. Find resolutions
    res_matches = re.findall(r"Resolution:\s*(\d+)x(\d+)", output)
    if not res_matches: return None, None, None, None, None, None

    main_res = (int(res_matches[0][0]), int(res_matches[0][1]))
    ext_res = (int(res_matches[1][0]), int(res_matches[1][1]))

    # 3. Find scaling
    scaling_matches = re.findall(r"Scaling:\s*(on|off)", output)
    main_sc = scaling_matches[0] if len(scaling_matches) > 0 else "on"
    ext_sc = scaling_matches[1] if len(scaling_matches) > 1 else "on"
    
    return main_id, ext_id, main_res, ext_res, main_sc, ext_sc

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def apply_position(pos, main_id, ext_id, main_res, ext_res, main_sc, ext_sc):
    Mw, Mh = main_res
    Ew, Eh = ext_res
    
    x, y = 0, 0
    
    # CALCULATION OF POSITIONS
    if pos == "R":   x, y = Mw, (Mh - Eh) // 2 
    elif pos == "L": x, y = -Ew, (Mh - Eh) // 2
    elif pos == "T": x, y = (Mw - Ew) // 2, -Eh
    elif pos == "B": x, y = (Mw - Ew) // 2, Mh
    elif pos == "TL": x, y = 0, -Eh
    elif pos == "TR": x, y = Mw - Ew, -Eh
    elif pos == "BL": x, y = 0, Mh
    elif pos == "BR": x, y = Mw - Ew, Mh

    # Find executable
    dp_exec = "displayplacer"
    if os.path.exists("/opt/homebrew/bin/displayplacer"): dp_exec = "/opt/homebrew/bin/displayplacer"
    elif os.path.exists("/usr/local/bin/displayplacer"): dp_exec = "/usr/local/bin/displayplacer"

    # BUILD COMMAND
    cmd_str = (
        f'{dp_exec} '
        f'"id:{main_id} res:{Mw}x{Mh} scaling:{main_sc} origin:(0,0)" '
        f'"id:{ext_id} res:{Ew}x{Eh} scaling:{ext_sc} origin:({x},{y})"'
    )
    
    subprocess.run(cmd_str, shell=True, capture_output=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["check", "set"])
    parser.add_argument("--pos")
    args = parser.parse_args()

    info = get_display_info()
    if not info or not info[0]:
        # No external monitor: Silent end or Error-JSON
        print(json.dumps({"status": "error", "msg": "No monitor"}))
        sys.exit(0)

    main_id, ext_id, main_res, ext_res, main_sc, ext_sc = info
    config = load_config()

    if args.mode == "check":
        known_pos = config.get(ext_id)
        print(json.dumps({
            "status": "known" if known_pos else "new", 
            "pos": known_pos
        }))

    elif args.mode == "set":
        if args.pos:
            config[ext_id] = args.pos
            save_config(config)
            apply_position(args.pos, main_id, ext_id, main_res, ext_res, main_sc, ext_sc)
            # Optional: Success feedback for Hammerspoon (usually ignored)
            print(json.dumps({"status": "success"}))

if __name__ == "__main__":
    main()
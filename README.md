# Monitor Manager for Hammerspoon

A Dynamic-Island-style HUD for macOS that arranges your external display relative to your MacBook in a few keystrokes. Built for people who switch between desk setups often, or who are tired of macOS forgetting how their monitors are positioned.

Press **⌘ ⌥ ⌃ D** and a small pill appears at the top of the laptop screen, showing whether an external monitor is connected and where it sits. Click it or press a key to expand it into a 3×3 grid and place the monitor.

## Features

- Compact HUD that expands into a 3×3 position grid
- Fully keyboard-driven, with modifiers for corner placement
- Remembers each external display by its persistent ID, including corner offsets
- Opens automatically when an external monitor is connected
- Adjustable corner offset, in pixels or as a fraction of the main display width
- One-key shortcut to macOS Display Settings
- Works with both Apple Silicon and Intel Homebrew paths

## Requirements

- macOS
- [Hammerspoon](https://www.hammerspoon.org/)
- Python 3 (the script runs with `/usr/bin/python3` by default)
- [displayplacer](https://github.com/jakehilborn/displayplacer)

Install displayplacer with Homebrew:

```bash
brew install displayplacer
```

## Installation

1. **Clone or download this repository:**

   ```bash
   git clone https://github.com/YOUR_USER/monitor-manager.git
   cd monitor-manager
   ```

2. **Copy the files into place:**

   ```bash
   mkdir -p ~/.hammerspoon/modules
   cp display_manager.html ~/.hammerspoon/modules/
   cp display_manager.lua ~/.hammerspoon/modules/
   mkdir -p ~/Scripts
   cp monitor_manager.py ~/Scripts/
   ```

3. **Set the paths** at the top of `display_manager.lua`:

   ```lua
   local scriptPath = "/Users/YOUR_USER/Scripts/monitor_manager.py"
   local pythonPath = "/usr/bin/python3"
   local htmlPath   = "/Users/YOUR_USER/.hammerspoon/modules/display_manager.html"
   ```

4. **Load the module** from your `~/.hammerspoon/init.lua`:

   ```lua
   require("modules.display_manager")
   ```

   Alternatively, paste the contents of `display_manager.lua` directly into `init.lua`.

5. **Reload Hammerspoon** (menu bar icon → Reload Config).

## Usage

Press **⌘ ⌥ ⌃ D** to show the HUD. Click the pill or wait for auto-expand to open the grid, then use these keys:

| Key | Action |
| --- | --- |
| ↑ ↓ ← → | Place the monitor above, below, left of, or right of the laptop |
| ⇧ ← / ⇧ → | Top-left / top-right corner |
| ⌥ ← / ⌥ → | Bottom-left / bottom-right corner |
| S | Open macOS Display Settings |
| Esc / Return | Close the HUD without changes |

You can also click any cell in the grid instead of using the keyboard.

The HUD opens automatically about two seconds after an external monitor is connected.

## Corner Offset

Edge positions (L, R, T, B) place the monitor flush against the laptop with no offset. Corner positions align the monitor to the outer corner and push it outward by an offset. By default, that offset is **2/3 of the main display's width**.

Saved offsets are used by the HUD. To change them, run the script from the terminal:

```bash
# 600 pixels outward
python3 ~/Scripts/monitor_manager.py set --pos TL --offset 600

# Half the main display's width
python3 ~/Scripts/monitor_manager.py set --pos BR --offset 1/2
```

Fractions must be written as `a/b` (for example `2/3` or `1/2`). A negative value shifts the monitor in the opposite direction.

## Command-Line Interface

`monitor_manager.py` can also be used on its own:

| Command | Description |
| --- | --- |
| `check` | Prints JSON with the saved position, offset, and current origin of the external display |
| `preview` | Prints the computed origin for every position, both flush and with the default offset |
| `set --pos POS [--offset X] [--id ID]` | Applies a position and saves it |

Positions are `R L T B TL TR BL BR`.

```bash
python3 ~/Scripts/monitor_manager.py preview
```

## Configuration

Preferences are stored in `~/.display_config.json`, keyed by each external display's persistent screen ID. To reset all saved positions, delete this file.

## Troubleshooting

- **"display_manager.html fehlt" alert:** The `htmlPath` in `display_manager.lua` does not point to an existing file. Check the path.
- **"No external monitor" error:** The external display must be connected and enabled in macOS. Run `displayplacer list` in Terminal to confirm that it appears.
- **Position is wrong after reconnecting:** Run the HUD again (⌘ ⌥ ⌃ D) and select the position. The saved offset is reapplied automatically.
- **Nothing happens when applying a position:** Open the Hammerspoon console for error messages. If Python lives somewhere other than `/usr/bin/python3`, update `pythonPath`.

## How It Works

1. `monitor_manager.py` parses the output of `displayplacer list`, identifies the main display and the first enabled external display, computes the external display's origin from the chosen position and offset, and calls `displayplacer` to apply it.
2. Hammerspoon shows `display_manager.html` in a borderless, transparent webview. Clicks and key presses are sent back to Lua, which runs the Python script.
3. A screen watcher detects when a new screen is connected and opens the HUD.

## Limitations

- Only one external display is handled. Without `--id`, the first enabled external display is used.
- The HUD labels are currently in German.

## Credits

- [displayplacer](https://github.com/jakehilborn/displayplacer) by Jake Hilborn

## License

MIT (or your license of choice)

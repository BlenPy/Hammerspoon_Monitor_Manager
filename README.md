# Monitor Manager for Hammerspoon

This tool provides a visual interface (HUD) to quickly arrange external monitors relative to your MacBook. It is designed for users who frequently switch desk setups or encounter issues with macOS remembering window positions.

## Features

- Visual HUD to select monitor position.
- Keyboard-driven control (Arrow keys and modifiers).
- Persists monitor preferences for specific display IDs.
- Quick access to macOS System Settings.

## Prerequisites

Before installing, ensure you have the following requirements met:

1. **Hammerspoon**: You must have Hammerspoon installed.
2. **displayplacer**: This script relies on `displayplacer` to handle the screen arrangement. Install it via Homebrew:
   
   ```bash
   brew install displayplacer

## Installation

1. **Download Files**: Clone this repository or download the source files.

2. **Configure Lua Script**: Open display_manager.lua and copy its contents into your Hammerspoon init.lua file. Alternatively, you can place the file in your configuration directory and require it in your init.lua.

3. **Verify File Path**: Ensure the file path in the Lua script points correctly to the Python script.

`local scriptPath = "/Users/YOUR_USER/Path/To/monitor_manager.py"`

4. **Reload Configuration**: Reload the Hammerspoon configuration to apply the changes.

## Usage
Default Hotkey: Cmd + Alt + Ctrl + D

When the menu opens, use the following keys to arrange the external monitor:

- **Arrow Keys** (Up, Down, Left, Right): Place the monitor directly above, below, or to the sides of the main display.

- **Shift + Arrow Keys**: Place the monitor in the corners (e.g., Top-Left, Bottom-Right).

- **S**: Open macOS System Settings for displays.

- **Esc**: Close the menu without making changes.

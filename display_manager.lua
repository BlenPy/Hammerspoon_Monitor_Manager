local scriptPath = "/Users/USERNAME/Documents/monitor_manager.py"
local pythonPath = "/usr/bin/python3"

local lastScreenCount = #hs.screen.allScreens()
local webview = nil 

-- WINDOW SIZE (Variables must be defined up here!)
local winWidth = 500  
local winHeight = 350 

-- ==========================================
-- 1. KEYBOARD MODE (MODAL)
-- ==========================================
local gridModal = hs.hotkey.modal.new()

function closeMenu()
    if webview then 
        webview:delete() 
        webview = nil 
    end
    gridModal:exit()
end

function setPosition(pos)
    closeMenu() 

    if pos == "CLOSE" or pos == "KEEP" then return end

    if pos == "SYSTEM" then
        hs.execute("open 'x-apple.systempreferences:com.apple.preference.displays'")
        return
    end

    local task = hs.task.new(pythonPath, nil, {scriptPath, "set", "--pos", pos})
    task:start()
    hs.alert.show("Position: " .. pos)
end

-- KEY ASSIGNMENTS
-- Arrow keys (Center)
gridModal:bind({}, 'up',    function() setPosition("T") end)
gridModal:bind({}, 'down',  function() setPosition("B") end)
gridModal:bind({}, 'left',  function() setPosition("L") end)
gridModal:bind({}, 'right', function() setPosition("R") end)

-- Corners (Shift/ Alt + Arrow keys)
gridModal:bind({"shift"}, 'left',    function() setPosition("TL") end)
gridModal:bind({"shift"}, 'right', function() setPosition("TR") end)
gridModal:bind({"alt"}, 'right',  function() setPosition("BR") end)
gridModal:bind({"alt"}, 'left',  function() setPosition("BL") end)

-- Letters
gridModal:bind({}, 's', function() setPosition("SYSTEM") end)

gridModal:bind({}, 'escape', function() closeMenu() end)
gridModal:bind({}, 'return', function() closeMenu() end)


-- ==========================================
-- 2. HTML INTERFACE
-- ==========================================
local htmlContentTemplate = [[
<!DOCTYPE html>
<html>
<head>
<style>
    body { background-color: #1e1e1e; color: white; font-family: -apple-system, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; user-select: none; cursor: default; }
    h2 { margin: 0 0 10px 0; font-size: 15px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .grid-container { display: grid; grid-template-columns: 1fr 1fr 1fr; grid-template-rows: 1fr 1fr 1fr; gap: 8px; width: 90%; height: 75%; }
    
    .btn { 
        background: #333; border: 2px solid #444; border-radius: 6px; 
        display: flex; flex-direction: column; align-items: center; justify-content: center; 
        cursor: pointer; font-size: 24px; transition: 0.1s; color: #ddd; position: relative; 
    }
    .btn:hover { background: #007aff; border-color: #007aff; color: white; }
    .btn:active { transform: scale(0.96); }

    /* NEU: Der Style für die aktive Position */
    .active-pos { 
        border-color: #4cd964 !important; 
        background-color: #1e3a23;
        box-shadow: 0 0 10px rgba(76, 217, 100, 0.4);
        color: white;
    }

    .key-hint { position: absolute; top: 4px; left: 6px; font-size: 10px; opacity: 0.4; font-weight: bold; font-family: monospace; }
    .center { background: #222; border: 2px dashed #555; cursor: default; font-size: 12px; color: #777; }
    .system { grid-column: 1 / span 3; margin-top: 10px; font-size: 13px; height: 35px; background: #2a2a2a; }
</style>
</head>
<body>
    <h2 id="title">Monitor Position</h2>
    <div class="grid-container">
        <div id="TL" class="btn" onclick="send('TL')"><span class="key-hint">⇧ + ◀</span>↖️</div>
        <div id="T"  class="btn" onclick="send('T')"><span class="key-hint">▲</span>⬆️</div>
        <div id="TR" class="btn" onclick="send('TR')"><span class="key-hint">⇧ + ▶</span>↗️</div>
        
        <div id="L"  class="btn" onclick="send('L')"><span class="key-hint">◀</span>⬅️</div>
        <div class="btn center">💻<br>Laptop</div>
        <div id="R"  class="btn" onclick="send('R')"><span class="key-hint">▶</span>➡️</div>
        
        <div id="BL" class="btn" onclick="send('BL')"><span class="key-hint">⌥ + ◀</span>↙️</div>
        <div id="B"  class="btn" onclick="send('B')"><span class="key-hint">▼</span>⬇️</div>
        <div id="BR" class="btn" onclick="send('BR')"><span class="key-hint">⌥ + ▶</span>↘️</div>
    </div>
    <div class="btn system" onclick="send('SYSTEM')">🛠 System Settings (S)</div>

    <script>
        // Hier wird {{CURRENT_POS}} von Lua durch den echten Wert ersetzt (z.B. "R")
        const currentPos = "{{CURRENT_POS}}";

        // Wenn eine Position bekannt ist, markiere den Button
        if (currentPos && currentPos !== "null") {
            const btn = document.getElementById(currentPos);
            if (btn) {
                btn.classList.add("active-pos");
            }
        }

        function send(val) { try { window.webkit.messageHandlers.hammerspoon.postMessage(val); } catch(e) {} }
    </script>
</body>
</html>
]]

function msgCallback(message)
    if message and message.body then setPosition(message.body) end
end

-- Function: Show window
function showWebview(knownPos)
    if webview then webview:delete() webview = nil end

    local screen = hs.screen.find("Built-in Retina Display")
    if not screen then screen = hs.screen.find("Built-in") end
    if not screen then screen = hs.screen.primaryScreen() end
    
    local frame = screen:frame()
    local rect = {
        x = frame.x + (frame.w - winWidth) / 2,
        y = frame.y + (frame.h - winHeight) / 2,
        w = winWidth,
        h = winHeight
    }

    local uce = hs.webview.usercontent.new("hammerspoon")
    uce:setCallback(msgCallback)

    -- Current Position for HTML
    local finalHtml = htmlContentTemplate:gsub("{{CURRENT_POS}}", knownPos or "")

    webview = hs.webview.new(rect, {}, uce)
    webview:windowStyle({"titled", "closable", "utility", "HUD"}) 
    webview:level(hs.drawing.windowLevels.floating) 
    webview:html(finalHtml)
    webview:show()
    webview:bringToFront()
    
    gridModal:enter()
end

function checkMonitorStatus()
    local callback = function(exitCode, stdOut, stdErr)
        if exitCode == 0 then
            local data = hs.json.decode(stdOut)
            showWebview(data.pos)
        end
    end
    local task = hs.task.new(pythonPath, callback, {scriptPath, "check"})
    task:start()
end

monitorWatcher = hs.screen.watcher.new(function()
    local currentCount = #hs.screen.allScreens()
    if currentCount > lastScreenCount then
        hs.timer.doAfter(2.0, checkMonitorStatus)
    end
    lastScreenCount = currentCount
end)
monitorWatcher:start()

hs.hotkey.bind({"cmd", "alt", "ctrl"}, "D", checkMonitorStatus)

hs.alert.show("Monitor Manager")

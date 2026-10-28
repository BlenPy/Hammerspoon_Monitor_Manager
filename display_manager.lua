-- Monitor Manager — Dynamic-Island-Style HUD
-- Pill oben mittig auf dem Laptop-Display, expandiert zu einem Grid.

local scriptPath = "/Users/USER/Documents/monitor_manager.py"
local pythonPath = "/usr/bin/python3"
local htmlPath   = "/Users/USER/.hammerspoon/modules/display_manager.html"

local COLLAPSED = { w = 300, h = 46 }
local EXPANDED  = { w = 520, h = 220 }

local webview = nil
local expanded = false
local lastScreenCount = #hs.screen.allScreens()

local gridModal = hs.hotkey.modal.new()

local ARROW_MAP = { up = "T", down = "B", left = "L", right = "R" }

function readHtml()
    local f = io.open(htmlPath, "r")
    if not f then
        hs.alert.show("display_manager.html fehlt")
        return nil
    end
    local html = f:read("*a")
    f:close()
    return html
end

function islandRect(size)
    local screen = hs.screen.find("Built-in Retina Display")
        or hs.screen.find("Built-in")
        or hs.screen.primaryScreen()
    local frame = screen:frame()
    return {
        x = frame.x + (frame.w - size.w) / 2,
        y = frame.y + 12,
        w = size.w,
        h = size.h
    }
end

-- Die Island skaliert per CSS-Transition innerhalb des Fensters,
-- deshalb wird das Fenster einmal in Endgröße erstellt.

function closeIsland()
    if webview then
        webview:delete()
        webview = nil
    end
    expanded = false
    gridModal:exit()
end

function expandIsland()
    if expanded or not webview then return end
    expanded = true
    -- Die Island skaliert selbst per CSS (GPU) — kein Fenster-Resize nötig
    webview:evaluateJavaScript("document.body.classList.add('expanded')")
    gridModal:enter()
end

function applyPosition(pos)
    closeIsland()

    if pos == "SYSTEM" then
        hs.execute("open 'x-apple.systempreferences:com.apple.preference.displays'")
        return
    end

    local task = hs.task.new(pythonPath, function(exitCode, stdOut, stdErr)
        if exitCode ~= 0 then
            hs.alert.show("Fehler: " .. (stdErr or stdOut or "displayplacer fehlgeschlagen"))
        end
    end, {scriptPath, "set", "--pos", pos})
    task:start()
end

function msgCallback(message)
    local body = message.body
    if type(body) ~= "table" then return end

    if body.action == "expand" then
        expandIsland()
    elseif body.action == "set" and body.pos then
        applyPosition(body.pos)
    elseif body.action == "system" then
        applyPosition("SYSTEM")
    elseif body.action == "close" then
        closeIsland()
    end
end

function showIsland(knownPos, autoExpand)
    if webview then
        webview:delete()
        webview = nil
    end
    expanded = false

    local html = readHtml()
    if not html then return end

    html = html:gsub("{{STATUS}}", knownPos and "Monitor verbunden" or "Neuer Monitor")
    html = html:gsub("{{POS_LABEL}}", knownPos or "—")
    html = html:gsub("{{CURRENT_POS}}", knownPos or "")
    html = html:gsub("{{DOT_CLASS}}", knownPos and "" or "new")

    local uce = hs.webview.usercontent.new("hammerspoon")
    uce:setCallback(msgCallback)

    webview = hs.webview.new(islandRect(EXPANDED), { transparent = true }, uce)
    webview:transparent(true)
    webview:windowStyle({ "borderless", "utility" })
    webview:level(hs.drawing.windowLevels.floating)
    webview:html(html)
    webview:show()
    webview:bringToFront()

    if autoExpand then
        hs.timer.doAfter(0.4, expandIsland)
    end
end

-- ==========================================
-- Tastatur (nur wenn expandiert)
-- ==========================================
for key, pos in pairs(ARROW_MAP) do
    gridModal:bind({}, key, function()
        if expanded then applyPosition(pos) end
    end)
end

gridModal:bind({ "shift" }, "left",  function() if expanded then applyPosition("TL") end end)
gridModal:bind({ "shift" }, "right", function() if expanded then applyPosition("TR") end end)
gridModal:bind({ "alt" },   "left",  function() if expanded then applyPosition("BL") end end)
gridModal:bind({ "alt" },   "right", function() if expanded then applyPosition("BR") end end)

gridModal:bind({}, "s", function() if expanded then applyPosition("SYSTEM") end end)
gridModal:bind({}, "escape", closeIsland)
gridModal:bind({}, "return", closeIsland)

-- ==========================================
-- Auslöser
-- ==========================================
function checkMonitorStatus()
    local callback = function(exitCode, stdOut, stdErr)
        if exitCode == 0 then
            local ok, data = pcall(hs.json.decode, stdOut)
            -- Island nur zeigen, wenn tatsächlich ein externer Monitor verbunden ist
            if ok and data and data.status ~= "error" then
                showIsland(data.pos, true)
            end
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

hs.hotkey.bind({ "cmd", "alt", "ctrl" }, "D", checkMonitorStatus)

hs.alert.show("Monitor Manager (Island)")

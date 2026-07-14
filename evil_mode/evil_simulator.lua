--!lua5.1
-- evil_mode simulator/emulator
-- Runs XHider evil_mode scripts outside Roblox by providing stub environments
--
-- Usage:
--   lua5.1 evil_simulator.lua <script.lua>           -- auto-detect variant
--   lua5.1 evil_simulator.lua --variant-a <script.lua>  -- force Variant A (LCG)
--   lua5.1 evil_simulator.lua --variant-b <script.lua>  -- force Variant B (hex pool XOR)
--
-- Supports:
--   - Variant A: LCG stream cipher (one.lua, Blox Fruits)
--   - Variant B: hex pool XOR (two.lua, three.lua, fibo.lua, print_hi.lua, look.lua)
--   - Anti-tamper bypass for two.lua
--   - Roblox API stubs for one.lua

local target = arg[1]
local variant = nil

-- Parse args
if target == "--variant-a" then
    variant = "A"
    target = arg[2]
elseif target == "--variant-b" then
    variant = "B"
    target = arg[2]
end

if not target then
    io.stderr:write("Usage: lua5.1 evil_simulator.lua [--variant-a|--variant-b] <script.lua>\n")
    os.exit(1)
end

------------------------------------------------------------------------
-- Lua 5.1 compat
------------------------------------------------------------------------
unpack = unpack or table.unpack
loadstring = loadstring or load
getfenv = getfenv or function(n) if n==1 or n==nil then return _ENV or _G end; return _ENV or _G end
setfenv = setfenv or function() end
if not math.modf then math.modf = function(x) local i=math.floor(x);return i,x-i end end

------------------------------------------------------------------------
-- Detect variant
------------------------------------------------------------------------
local fh = io.open(target, "rb")
if not fh then
    io.stderr:write("ERROR: cannot open " .. target .. "\n")
    os.exit(1)
end
local src = fh:read("*a"); fh:close()

if not variant then
    if src:find('D%("') or src:find("D%('") or src:find("LCG") or src:find("34013992534017") then
        variant = "A"
    else
        variant = "B"
    end
end
io.stderr:write(string.format("[simulator] Variant: %s, File: %s (%d bytes)\n", variant, target, #src))

------------------------------------------------------------------------
-- Capture print output
------------------------------------------------------------------------
local _orig_print = print
local captured = {}
print = function(...)
    local p = {}
    for i = 1, select("#", ...) do
        p[i] = tostring(select(i, ...))
    end
    local line = table.concat(p, "\t")
    table.insert(captured, line)
    _orig_print(line)
end

------------------------------------------------------------------------
-- Anti-tamper bypass
------------------------------------------------------------------------
-- Disable debug hook checks
if debug and debug.sethook then debug.sethook = function() end end

-- Set metatables for false/nil to prevent NaN-based traps
pcall(debug.setmetatable, false, {
    __index = function(self, key) return 0/0 end,
    __call = function(self, ...) return 0/0 end,
    __len = function(self) return 0/0 end,
    __unm = function(self) return 0/0 end,
})
pcall(debug.setmetatable, nil, {
    __index = function(self, key) return 0/0 end,
    __call = function(self, ...) return 0/0 end,
    __len = function(self) return 0/0 end,
})

------------------------------------------------------------------------
-- Roblox API stubs (for Variant A / one.lua)
------------------------------------------------------------------------
local function make_instance(className)
    local obj = {ClassName = className, Name = className, Parent = nil, Value = 0}
    return setmetatable(obj, {
        __index = function(t, k)
            if k == "Value" then return 0 end
            if k == "Name" then return t.ClassName end
            return function(...) end
        end,
        __newindex = function(t, k, v) rawset(t, k, v) end,
    })
end

-- Core Roblox
game = game or setmetatable({
    PlaceId = 2753915549,
    JobId = "stub-job-id",
    GameId = 2753915549,
    PlaceVersion = 1,
}, {
    __index = function(t, k)
        if k == "GetService" then
            return function(self, name)
                return setmetatable({ClassName = name, Name = name}, {
                    __index = function(t2, k2) return function(...) end end
                })
            end
        end
        if k == "FindFirstChild" then return function() return nil end end
        if k == "GetChildren" then return function() return {} end end
        if k == "IsLoaded" then return function() return true end end
        if k == "Players" then
            return setmetatable({}, {
                __index = function(t2, k2)
                    if k2 == "LocalPlayer" then
                        return setmetatable({}, {
                            __index = function(t3, k3)
                                if k3 == "Character" then
                                    return setmetatable({}, {
                                        __index = function(t4, k4)
                                            if k4 == "HumanoidRootPart" then
                                                return setmetatable({}, {
                                                    __index = function(t5, k5)
                                                        if k5 == "Position" then return Vector3.new(0, 0, 0) end
                                                        if k5 == "CFrame" then return CFrame.new(0, 0, 0) end
                                                        return function(...) end
                                                    end
                                                })
                                            end
                                            return setmetatable({Value = 100}, {
                                                __index = function() return function() end end
                                            })
                                        end
                                    })
                                end
                                if k3 == "Backpack" then
                                    return setmetatable({}, {
                                        __index = function() return function() return nil end end
                                    })
                                end
                                if k3 == "Team" then return "Marines" end
                                return function(...) end
                            end
                        })
                    end
                    return function(...) end
                end
            })
        end
        return function(...) end
    end
})

workspace = workspace or game.Workspace or setmetatable({}, {
    __index = function(t, k)
        if k == "FindFirstChild" then return function() return nil end end
        if k == "GetChildren" then return function() return {} end end
        return function(...) end
    end
})

-- Math stubs
Vector3 = Vector3 or setmetatable({}, {
    __call = function(t, x, y, z) return {X=x or 0, Y=y or 0, Z=z or 0, __class = "Vector3"} end,
    __index = function(t, k)
        if k == "new" then return t end
        if k == "zero" then return Vector3.new(0, 0, 0) end
        return function(...) end
    end
})
Vector3.new = Vector3

CFrame = CFrame or setmetatable({}, {
    __call = function(t, ...) return {__class = "CFrame"} end,
    __index = function(t, k)
        if k == "new" then return t end
        if k == "lookAt" then return function() return CFrame.new() end end
        if k == "Angles" then return function() return CFrame.new() end end
        return function() return CFrame.new() end
    end
})
CFrame.new = CFrame

Instance = Instance or setmetatable({}, {
    __index = function(t, k)
        if k == "new" then
            return function(className) return make_instance(className) end
        end
        return function(...) end
    end
})

Enum = Enum or setmetatable({}, {
    __index = function(t, k)
        return setmetatable({}, {
            __index = function(t2, k2) return k2 end
        })
    end
})

TweenInfo = TweenInfo or setmetatable({}, {
    __call = function(t, ...) return {} end,
    __index = function(t, k) if k == "new" then return t end; return function() end end
})
TweenInfo.new = TweenInfo

-- Services
VirtualInputManager = VirtualInputManager or setmetatable({}, {
    __index = function() return function() end end
})

TeleportService = TeleportService or setmetatable({}, {
    __index = function() return function() end end
})

TweenService = TweenService or setmetatable({}, {
    __index = function(t, k)
        if k == "Create" then
            return function(self, obj, info, goals)
                return setmetatable({}, {
                    __index = function(t2, k2)
                        if k2 == "Play" then return function() end end
                        if k2 == "Cancel" then return function() end end
                        return function() end
                    end
                })
            end
        end
        return function() end
    end
})

Lighting = Lighting or setmetatable({ClockTime = 14}, {
    __index = function() return function() end end
})

-- Executor APIs
hookfunction = hookfunction or function(f, g) return g end
getrawmetatable = getrawmetatable or function() return {} end
setreadonly = setreadonly or function() end
newcclosure = newcclosure or function(f) return f end
getnamecallmethod = getnamecallmethod or function() return "" end
getgenv = getgenv or function() return _G end
getgc = getgc or function() return {} end
getupvalues = getupvalues or function() return {} end
typeof = typeof or function(v) return type(v) end
checkcaller = checkcaller or function() return false end
islclosure = islclosure or function() return true end
iscclosure = iscclosure or function() return false end
debug_info = debug.info or function() return "" end
-- Rename to avoid conflict with debug library
local _debug_info = debug.info

-- Coroutine/task stubs
spawn = spawn or function(f) if coroutine.wrap then coroutine.wrap(f)() end end
task = task or setmetatable({}, {
    __index = function(t, k)
        if k == "spawn" then return spawn end
        if k == "wait" then return function() end end
        if k == "defer" then return function(f) return f() end end
        return function() end
    end
})
wait = wait or function() end
delay = delay or function() end
tick = tick or os.clock
warn = warn or print

-- RandomStrings stub (used by two.lua anti-tamper)
RandomStrings = RandomStrings or setmetatable({}, {
    __index = function(t, k)
        if k == "randomString" then
            return function()
                local chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                local s = {}
                for i = 1, 16 do
                    local idx = math.random(1, #chars)
                    s[i] = chars:sub(idx, idx)
                end
                return table.concat(s)
            end
        end
        return function() return "" end
    end
})

-- originalError stub (used by two.lua)
originalError = originalError or function(msg)
    io.stderr:write("[simulator] originalError: " .. tostring(msg) .. "\n")
end

------------------------------------------------------------------------
-- Run script
------------------------------------------------------------------------
local fn, err = loadstring(src, "@" .. target)
if not fn then
    io.stderr:write("COMPILE ERROR: " .. tostring(err) .. "\n")
    os.exit(1)
end

-- Set environment for the script
local env = setmetatable({}, {__index = _G})
setfenv(fn, env)

local ok, result = xpcall(fn, function(e)
    return debug.traceback(tostring(e), 2)
end)

if not ok then
    io.stderr:write("RUNTIME: " .. tostring(result):sub(1, 500) .. "\n")
end

------------------------------------------------------------------------
-- Output
------------------------------------------------------------------------
if #captured > 0 then
    for _, line in ipairs(captured) do
        _orig_print(line)
    end
else
    io.stderr:write("[simulator] No output captured\n")
end

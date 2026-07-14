#!/usr/bin/env lua5.1
--[[
  ╔══════════════════════════════════════════════════════════════════╗
  ║  XHIDER psu_max_mode — Roblox Calculate() Shim               ║
  ║                                                                ║
  ║  Provides complete Lua 5.1 runtime environment for running   ║
  ║  XHIDER psu_max obfuscated scripts outside Roblox.            ║
  ║                                                                ║
  ║  Components:                                                   ║
  ║    • bit32 polyfill (band, bor, bxor, bnot, lshift, rshift,   ║
  ║      arshift, extract, btest, replace, countlz, countrz)      ║
  ║    • _G.Calculate = bit32.band (Roblox Calculate() shim)      ║
  ║    • Roblox environment stubs (game, Instance, Enum, etc.)   ║
  ║    • Optional: loadstring/setfenv hooks for capture          ║
  ║    • psu_max decoder O-table for chunk_2 execution            ║
  ║                                                                ║
  ║  Usage:                                                         ║
  ║    1) Capture chunk_2 (Layer 1 decode):                        ║
  ║       lua5.1 psu_max_shim.lua <target.lua> [prefix]             ║
  ║       → Outputs: <prefix>.chunk2.lua                           ║
  ║                                                                ║
  ║    2) Run existing clean chunk_2:                              ║
  ║       lua5.1 -e "dofile('psu_max_shim.lua'); ...               ║
  ║              -- or embed bit32/Calculate/O-table directly"     ║
  ║                                                                ║
  ║  Key findings:                                                 ║
  ║    • Calculate(a,b) = bit32.band(a,b) in XHIDER psu_max       ║
  ║    • Used in VM dispatch: e <= Calculate(t(x,o[k]), y)        ║
  ║    • Creates obfuscated opcode thresholds via AND of XOR'd   ║
  ║      constants                                                  ║
  ║                                                                ║
  ║  Verified: print_hi.lua (142KB) → chunk2 (71KB) ✓              ║
  ║            fibo.lua (69KB) → chunk2 (46KB) ✓                   ║
  ╚══════════════════════════════════════════════════════════════════╝
]]

------------------------------------------------------------------------
-- Configuration
------------------------------------------------------------------------
local target = arg[1]
local outpre = arg[2]

------------------------------------------------------------------------
-- bit32 polyfill — Full Lua 5.2 / Roblox / Luau compatible
-- Implements all bit32.* functions using pure Lua 5.1
------------------------------------------------------------------------
local MASK32 = 0xFFFFFFFF

local function tobit(x)
    x = math.floor(tonumber(x) or 0)
    x = x % 0x100000000
    if x < 0 then x = x + 0x100000000 end
    return x
end

bit32 = bit32 or {}

function bit32.band(a, b)
    a, b = tobit(a), tobit(b)
    local r, p = 0, 1
    for i = 0, 31 do
        local ab, bb = a % 2, b % 2
        if ab == 1 and bb == 1 then r = r + p end
        a, b, p = (a - ab) / 2, (b - bb) / 2, p * 2
    end
    return r
end

function bit32.bor(a, b)
    a, b = tobit(a), tobit(b)
    local r, p = 0, 1
    for i = 0, 31 do
        local ab, bb = a % 2, b % 2
        if ab == 1 or bb == 1 then r = r + p end
        a, b, p = (a - ab) / 2, (b - bb) / 2, p * 2
    end
    return r
end

function bit32.bxor(a, b)
    a, b = tobit(a), tobit(b)
    local r, p = 0, 1
    for i = 0, 31 do
        local ab, bb = a % 2, b % 2
        if ab ~= bb then r = r + p end
        a, b, p = (a - ab) / 2, (b - bb) / 2, p * 2
    end
    return r
end

function bit32.bnot(a)
    return tobit(MASK32 - tobit(a))
end

function bit32.lshift(a, n)
    n = tonumber(n) or 0
    if n >= 32 or n < 0 then return 0 end
    return tobit(math.floor(tobit(a) * 2^n) % 0x100000000)
end

function bit32.rshift(a, n)
    n = tonumber(n) or 0
    if n >= 32 or n < 0 then return 0 end
    return math.floor(tobit(a) / 2^n)
end

function bit32.arshift(a, n)
    n = math.min(tonumber(n) or 0, 31)
    local v = tobit(a)
    if v >= 0x80000000 then
        return math.floor((v - 0x100000000) / 2^n)
    end
    return math.floor(v / 2^n)
end

function bit32.extract(a, field, width)
    field = tonumber(field) or 0
    width = tonumber(width) or 1
    return bit32.band(bit32.rshift(a, field), 2^width - 1)
end

function bit32.btest(a, b)
    return bit32.band(a, b) ~= 0
end

function bit32.replace(a, v, field, width)
    field = tonumber(field) or 0
    width = tonumber(width) or 1
    local mask = 2^width - 1
    local cleared = bit32.band(a, bit32.bnot(bit32.lshift(mask, field)))
    return bit32.bor(cleared, bit32.lshift(bit32.band(v, mask), field))
end

function bit32.countlz(a)
    a = tobit(a)
    if a == 0 then return 32 end
    local n = 0
    for i = 31, 0, -1 do
        if bit32.extract(a, i, 1) == 1 then return n end
        n = n + 1
    end
    return n
end

function bit32.countrz(a)
    a = tobit(a)
    if a == 0 then return 32 end
    local n = 0
    for i = 0, 31 do
        if bit32.extract(a, i, 1) == 1 then return n end
        n = n + 1
    end
    return n
end

------------------------------------------------------------------------
-- Calculate() — Roblox bit32.band wrapper
--
-- In Roblox/Luau, Calculate(a, b) is a global function equivalent
-- to bit32.band(a, b). XHIDER's psu_max VM uses it to compute
-- obfuscated opcode thresholds:
--
--   elseif(e <= Calculate(t(919068738, o[880505119]),
--                         t(156229931, o[261377791]))) then
--
-- Where t = bit32.bxor, o = decoder table.
-- Calculate(XOR(a,b), XOR(c,d)) effectively creates a 32-bit mask.
------------------------------------------------------------------------
_G.Calculate = function(a, b)
    return bit32.band(tobit(a), tobit(b))
end

------------------------------------------------------------------------
-- Roblox environment stubs
------------------------------------------------------------------------
local stub_mt = {
    __index = function(t, k)
        if type(k) == "string" then
            return function(...) return t end
        end
        return nil
    end,
    __newindex = function(t, k, v) rawset(t, k, v) end,
    __tostring = function(t) return t.ClassName or "Instance" end,
    __call = function(t, ...) return t end,
}

local function make_instance(name)
    return setmetatable({ClassName = name, Name = name}, stub_mt)
end

game = game or make_instance("DataModel")
function game:GetService(name) return make_instance(name) end
function game:FindFirstChild(name) return nil end
function game:GetChildren() return {} end
function game:GetDescendants() return {} end
function game:FindFirstChildOfClass(name) return nil end
function game:WaitForChild(name, timeout) return nil end
game.Players = make_instance("Players")
game.Workspace = make_instance("Workspace")
workspace = workspace or game.Workspace

Instance = Instance or {}
function Instance.new(className) return make_instance(className) end
function Instance.wrap(obj) return obj end

Enum = Enum or setmetatable({}, {
    __index = function(t, k)
        return setmetatable({}, {
            __index = function(t2, k2) return k2 end
        })
    end
})

typeof = typeof or type
spawn = spawn or function(f)
    if coroutine.wrap then coroutine.wrap(f)() end
end
delay = delay or function() end
wait = wait or function() end
tick = tick or os.clock
warn = warn or print

------------------------------------------------------------------------
-- PSU Max decoder table (O-table)
-- Required for chunk_2 VM execution
------------------------------------------------------------------------
PSU_MAX_O_TABLE = {
    [209867084] = "e", [255806744] = "b", [261377791] = 155228450,
    [293684876] = "n", [29799631]  = "a", [303909627] = "2",
    [407365380] = "k", [43472931]  = "s", [462186921] = "i",
    [466982296] = "v", [669545735] = "h", [676273207] = "t",
    [755266474] = 660029073, [767826132] = "c", [780364647] = "y",
    [821956203] = "m", [828614386] = "r", [860093539] = "f",
    [864117863] = "l", [880505119] = 28811554, [926356572] = "o",
    [997985534] = "u",
    W8ZpaIfush  = "p", anierBSX = "d", albeVM = 905968982,
    cPAuZDv0    = "#",
    [500910416] = function(arg1, t_fn, l_tbl, key)
        if l_tbl then l_tbl[key] = arg1 end
        return arg1
    end,
    BUe9QJZn = function(arg1, t_fn, l_tbl, key)
        if l_tbl then l_tbl[key] = arg1 end
        return arg1
    end,
}

-- Expose O-table as global 'o' for chunk_1/chunk_2 decoder
_G.o = PSU_MAX_O_TABLE

------------------------------------------------------------------------
-- If run as main script: capture chunk_2 from target
------------------------------------------------------------------------
if target then
    if not outpre then
        outpre = target:gsub("%.lua$", "")
    end

    -- Disable debug hook checks
    if debug.sethook then debug.sethook = function() end end

    -- Loadstring hook
    local _orig_load = loadstring or load
    local _orig_print = print
    local captured = {}
    local chunk_count = 0

    print = function(...)
        local p = {}
        for i = 1, select("#", ...) do
            p[i] = tostring(select(i, ...))
        end
        table.insert(captured, table.concat(p, "\t"))
        _orig_print(...)
    end

    loadstring = function(src, cn, ...)
        chunk_count = chunk_count + 1
        local s = tostring(src)
        _orig_print(string.format("[shim] Captured chunk_%d: %d bytes", chunk_count, #s))

        local f = io.open(outpre .. ".chunk2.lua", "w")
        if f then f:write(s); f:close() end

        -- Compile normally for phase 1
        return _orig_load(s, cn or ("@chunk" .. chunk_count))
    end
    load = function(src, ...)
        if type(src) == "string" then return loadstring(src, ...) end
        return _orig_load(src, ...)
    end

    -- Load and run target
    _orig_print("[shim] Loading: " .. target)
    local fh = io.open(target, "rb")
    if not fh then
        _orig_print("[shim] ERROR: cannot open " .. target)
        os.exit(1)
    end
    local src = fh:read("*a"); fh:close()
    _orig_print(string.format("[shim] Read %d bytes", #src))

    local fn, err = _orig_load(src, "@" .. target)
    if not fn then
        _orig_print("[shim] COMPILE ERROR: " .. tostring(err))
        os.exit(1)
    end

    local ok, result = xpcall(fn, function(e)
        return debug.traceback(tostring(e), 2)
    end)

    if not ok then
        _orig_print("[shim] RUNTIME: " .. tostring(result):sub(1, 200))
    else
        _orig_print("[shim] OK: " .. tostring(result))
    end

    -- Save stdout
    local sf = io.open(outpre .. ".stdout.txt", "w")
    if sf then
        for i, l in ipairs(captured) do sf:write(i .. ": " .. l .. "\n") end
        sf:close()
    end

    _orig_print(string.format("[shim] Done. Chunks: %d", chunk_count))
end
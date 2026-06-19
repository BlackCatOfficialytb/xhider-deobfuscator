#!/usr/bin/env lua5.1
--[[
  psu_max_run_chunk2_v2.lua — Execute chunk_2 and capture VM output via setfenv hook.

  The psu_max VM builds the final script as a string, wraps it in a function
  via loadstring/setfenv, and calls it. We hook setfenv to capture both
  the function AND its string source.

  Usage:
    lua5.1 psu_max_run_chunk2_v2.lua <chunk2.lua> [output_prefix]
]]

------------------------------------------------------------------------
-- Config
------------------------------------------------------------------------
local target = arg[1] or error("usage: lua5.1 psu_max_run_chunk2_v2.lua <chunk2.lua> [prefix]")
local outpre = arg[2] or target:gsub("%.lua$", "")

------------------------------------------------------------------------
-- bit32 polyfill
------------------------------------------------------------------------
local MASK32 = 0xFFFFFFFF
local function tobit(x)
    x = math.floor(tonumber(x) or 0)
    return (x % 0x100000000 + 0x100000000) % 0x100000000
end

bit32 = {}
function bit32.band(a, b)
    a, b = tobit(a), tobit(b)
    local r, p = 0, 1
    for i = 0, 31 do
        if a % 2 == 1 and b % 2 == 1 then r = r + p end
        a, b, p = (a-a%2)/2, (b-b%2)/2, p*2
    end
    return r
end
function bit32.bor(a, b)
    a, b = tobit(a), tobit(b)
    local r, p = 0, 1
    for i = 0, 31 do
        if a%2==1 or b%2==1 then r=r+p end
        a, b, p = (a-a%2)/2, (b-b%2)/2, p*2
    end
    return r
end
function bit32.bxor(a, b)
    a, b = tobit(a), tobit(b)
    local r, p = 0, 1
    for i = 0, 31 do
        if a%2 ~= b%2 then r=r+p end
        a, b, p = (a-a%2)/2, (b-b%2)/2, p*2
    end
    return r
end
function bit32.bnot(a) return tobit(MASK32 - tobit(a)) end
function bit32.lshift(a, n)
    n = tonumber(n) or 0
    if n >= 32 or n < 0 then return 0 end
    return tobit(math.floor(tobit(a) * 2^n))
end
function bit32.rshift(a, n)
    n = tonumber(n) or 0
    if n >= 32 or n < 0 then return 0 end
    return math.floor(tobit(a) / 2^n)
end
function bit32.arshift(a, n)
    n = math.min(tonumber(n) or 0, 31)
    local v = tobit(a)
    if v >= 0x80000000 then return math.floor((v-0x100000000)/2^n) end
    return math.floor(v/2^n)
end
function bit32.extract(a, p, w)
    p, w = tonumber(p) or 0, tonumber(w) or 1
    return bit32.band(bit32.rshift(a, p), 2^w - 1)
end
function bit32.btest(a, b) return bit32.band(a, b) ~= 0 end

------------------------------------------------------------------------
-- Calculate = bit32.band
------------------------------------------------------------------------
_G.Calculate = function(a, b) return bit32.band(tobit(a), tobit(b)) end

------------------------------------------------------------------------
-- Roblox stubs
------------------------------------------------------------------------
local stub_mt = {
    __index = function(t, k)
        if type(k) == "string" then return function(...) return t end end
        return nil
    end,
    __newindex = rawset,
    __tostring = function(t) return t.ClassName or "Instance" end,
    __call = function(t, ...) return t end,
}
local function mkinst(n) return setmetatable({ClassName=n, Name=n}, stub_mt) end

game = game or mkinst("DataModel")
function game:GetService(n) return mkinst(n) end
function game:FindFirstChild(n) return nil end
function game:GetChildren() return {} end
function game:GetDescendants() return {} end
workspace = workspace or mkinst("Workspace")
Instance = Instance or {}
function Instance.new(cn) return mkinst(cn) end
Enum = Enum or setmetatable({}, {
    __index = function(t, k) return setmetatable({}, {__index = function(_,k) return k end}) end
})
typeof = typeof or type
spawn = spawn or function(f) if coroutine.wrap then coroutine.wrap(f)() end end
delay = delay or function() end
wait = wait or function() end
tick = tick or os.clock
warn = warn or print

------------------------------------------------------------------------
-- Capture system
------------------------------------------------------------------------
local captured_prints = {}
local final_source = nil
local vm_string_table = nil  -- The string constant table built by E()

-- Hook print
local _orig_print = print
print = function(...)
    local p = {}
    for i = 1, select("#", ...) do p[i] = tostring(select(i, ...)) end
    table.insert(captured_prints, table.concat(p, "\t"))
    _orig_print(...)
end

------------------------------------------------------------------------
-- Loadstring/setfenv hooks
------------------------------------------------------------------------
local _orig_loadstring = loadstring or load
local _orig_setfenv = setfenv
local _orig_getfenv = getfenv
local loadstring_calls = 0
local setfenv_calls = 0

-- Track the most recently created function via loadstring
local last_loaded_fn = nil
local last_loaded_src = nil

loadstring = function(src, chunkname, ...)
    loadstring_calls = loadstring_calls + 1
    local s = tostring(src)
    last_loaded_src = s
    _orig_print(string.format("[hook] loadstring #%d: %d bytes", loadstring_calls, #s))

    -- Save it
    final_source = s
    local f = io.open(outpre .. ".final.lua", "w")
    if f then f:write(s); f:close() end

    -- Compile normally
    local fn, err = _orig_loadstring(s, chunkname)
    if fn then last_loaded_fn = fn end
    return fn, err
end

load = function(src, ...)
    if type(src) == "string" then return loadstring(src, ...) end
    return _orig_load(src, ...)
end

setfenv = function(fn, env)
    setfenv_calls = setfenv_calls + 1
    _orig_print(string.format("[hook] setfenv #%d: fn=%s env=%s",
        setfenv_calls, type(fn), type(env)))

    -- If this is the function created by loadstring, capture it
    if fn == last_loaded_fn then
        _orig_print("[hook]   -> This is the VM output function!")
    end

    return _orig_setfenv(fn, env)
end

-- Disable debug hook checks
if debug.sethook then debug.sethook = function() end end

------------------------------------------------------------------------
-- O table for chunk_2
------------------------------------------------------------------------
local o_table = {
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

------------------------------------------------------------------------
-- Load and run chunk_2
------------------------------------------------------------------------
print("[chunk2_v2] Loading: " .. target)
local fh = io.open(target, "rb")
if not fh then print("[chunk2_v2] ERROR: cannot open"); os.exit(1) end
local src = fh:read("*a"); fh:close()
print(string.format("[chunk2_v2] Read %d bytes", #src))

local fn, err = _orig_loadstring(src, "@" .. target)
if not fn then
    print("[chunk2_v2] COMPILE ERROR: " .. tostring(err))
    os.exit(1)
end

-- chunk_2 returns: (function(o,...)...end)(...)
-- We call it with o_table
local ok, result = xpcall(function()
    local inner = fn()
    if type(inner) ~= "function" then
        print("[chunk2_v2] fn() returned: " .. type(inner))
        return inner
    end
    return inner(o_table)
end, function(e)
    return debug.traceback(tostring(e), 2)
end)

if not ok then
    print("[chunk2_v2] RUNTIME ERROR: " .. tostring(result))
else
    print("[chunk2_v2] OK: " .. tostring(result))
end

------------------------------------------------------------------------
-- Summary
------------------------------------------------------------------------
print(string.format("[chunk2_v2] === Summary ==="))
print(string.format("[chunk2_v2] loadstring calls: %d", loadstring_calls))
print(string.format("[chunk2_v2] setfenv calls: %d", setfenv_calls))
if final_source then
    print(string.format("[chunk2_v2] Final source: %d bytes -> %s.final.lua", #final_source, outpre))
end
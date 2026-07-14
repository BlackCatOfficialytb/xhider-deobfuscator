--!lua5.1
-- PSU Max end-to-end runner: runs both layers
-- Usage: lua5.1 run_psu_max.lua <target.lua>

local target = arg[1]
if not target then
    io.stderr:write("Usage: lua5.1 run_psu_max.lua <target.lua>\n")
    os.exit(1)
end

------------------------------------------------------------------------
-- bit32 polyfill
------------------------------------------------------------------------
local MASK32 = 0xFFFFFFFF
local function tobit(x)
    x = math.floor(tonumber(x) or 0)
    x = x % 0x100000000
    if x < 0 then x = x + 0x100000000 end
    return x
end
bit32 = bit32 or {}
function bit32.band(a,b) a,b=tobit(a),tobit(b);local r,p=0,1;for i=0,31 do local ab=a%2;local bb=b%2;if ab==1 and bb==1 then r=r+p end;a=(a-ab)/2;b=(b-bb)/2;p=p*2 end;return r end
function bit32.bor(a,b) a,b=tobit(a),tobit(b);local r,p=0,1;for i=0,31 do local ab=a%2;local bb=b%2;if ab==1 or bb==1 then r=r+p end;a=(a-ab)/2;b=(b-bb)/2;p=p*2 end;return r end
function bit32.bxor(a,b) a,b=tobit(a),tobit(b);local r,p=0,1;for i=0,31 do local ab=a%2;local bb=b%2;if ab~=bb then r=r+p end;a=(a-ab)/2;b=(b-bb)/2;p=p*2 end;return r end
function bit32.bnot(a) return tobit(0xFFFFFFFF-tobit(a)) end
function bit32.lshift(a,n) return tobit(math.floor(tobit(a)*2^n)%0x100000000) end
function bit32.rshift(a,n) return math.floor(tobit(a)/2^n) end
function bit32.arshift(a,n) a=tobit(a);if a>=0x80000000 then a=a-0x100000000 end;return tobit(math.floor(a/2^n)) end
function bit32.extract(a,f,w) w=w or 1;return bit32.band(bit32.rshift(a,f),2^w-1) end
function bit32.replace(a,v,f,w) w=w or 1;local mask=bit32.lshift(2^w-1,f);return bit32.bor(bit32.band(a,bit32.bnot(mask)),bit32.lshift(v,f)) end

------------------------------------------------------------------------
-- Lua 5.1 compat
------------------------------------------------------------------------
ldexp = ldexp or function(x,e) return x*(2^e) end
unpack = unpack or table.unpack
loadstring = loadstring or load
getfenv = getfenv or function(n) if n==1 or n==nil then return _ENV or _G end; return _ENV or _G end
setfenv = setfenv or function() end
frexp = frexp or function(x) if x==0 then return 0,0 end;local e=math.floor(math.log(math.abs(x),2));return x/(2^e),e end
if not math.modf then math.modf = function(x) local i=math.floor(x);return i,x-i end end

------------------------------------------------------------------------
-- Calculate = bit32.band
------------------------------------------------------------------------
_G.Calculate = bit32.band

------------------------------------------------------------------------
-- Disable anti-tamper
------------------------------------------------------------------------
if debug and debug.sethook then debug.sethook = function() end end
pcall(debug.setmetatable, false, {
    __index=function(self,key) return 0/0 end,
    __call=function(self,...) return 0/0 end,
    __len=function(self) return 0/0 end,
    __unm=function(self) return 0/0 end,
})
pcall(debug.setmetatable, nil, {
    __index=function(self,key) return 0/0 end,
    __call=function(self,...) return 0/0 end,
    __len=function(self) return 0/0 end,
})

------------------------------------------------------------------------
-- Roblox stubs
------------------------------------------------------------------------
_G.game = _G.game or setmetatable({}, {__index=function(t,k) return function(...) end end})
_G.workspace = _G.workspace or _G.game
_G.Instance = _G.Instance or setmetatable({}, {__index=function(t,k) return function(...) return {} end end})
function Instance.new(className) return setmetatable({ClassName=className}, {__index=function(t,k) return function(...) end end}) end
_G.Enum = _G.Enum or setmetatable({}, {__index=function(t,k) return setmetatable({}, {__index=function(t2,k2) return k2 end}) end})
_G.spawn = _G.spawn or function(f) if coroutine.wrap then coroutine.wrap(f)() end end
_G.delay = _G.delay or function() end
_G.wait = _G.wait or function() end
_G.tick = _G.tick or os.clock
_G.warn = _G.warn or print
_G.typeof = _G.typeof or type

------------------------------------------------------------------------
-- O-table for chunk_2 decoder
------------------------------------------------------------------------
_G.o = {
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
end

------------------------------------------------------------------------
-- Two-phase loadstring hook:
-- Phase 1: run original → capture chunk_1
-- Phase 2: run chunk_1 → capture final Lua
------------------------------------------------------------------------
local phase = 1
local chunk1_src = nil
local _orig_load = loadstring or load

loadstring = function(src, cn, ...)
    local s = tostring(src)
    if phase == 1 then
        chunk1_src = s
        return _orig_load(s, cn or "@chunk1")
    else
        return _orig_load(s, cn or "@final")
    end
end
load = function(src, ...)
    if type(src) == "string" then return loadstring(src, ...) end
    return _orig_load(src, ...)
end

------------------------------------------------------------------------
-- Phase 1: run original target
------------------------------------------------------------------------
local fh = io.open(target, "rb")
if not fh then
    io.stderr:write("ERROR: cannot open " .. target .. "\n")
    os.exit(1)
end
local src = fh:read("*a"); fh:close()

local fn, err = _orig_load(src, "@" .. target)
if not fn then
    io.stderr:write("COMPILE ERROR: " .. tostring(err) .. "\n")
    os.exit(1)
end

local ok, result = xpcall(fn, function(e)
    return debug.traceback(tostring(e), 2)
end)

------------------------------------------------------------------------
-- Phase 2: run chunk_1 if captured
------------------------------------------------------------------------
if chunk1_src and #chunk1_src > 0 then
    phase = 2
    local fn2, err2 = _orig_load(chunk1_src, "@chunk1")
    if fn2 then
        local ok2, res2 = xpcall(fn2, function(e)
            return debug.traceback(tostring(e), 2)
        end)
        if not ok2 then
            io.stderr:write("CHUNK1 ERROR: " .. tostring(res2):sub(1, 500) .. "\n")
        end
    else
        io.stderr:write("CHUNK1 COMPILE ERROR: " .. tostring(err2) .. "\n")
    end
end

------------------------------------------------------------------------
-- Output
------------------------------------------------------------------------
for _, line in ipairs(captured) do
    _orig_print(line)
end

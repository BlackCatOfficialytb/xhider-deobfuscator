#!/usr/bin/env lua5.1
--[[
  psu_max_full.lua — End-to-end psu_max deobfuscation.
  
  1. Loads target .lua → captures chunk_2 via loadstring hook
  2. Runs chunk_2 with bit32/Calculate/Roblox shims
  3. Captures final decoded source via loadstring hook (phase 2)
  
  Usage:
    lua5.1 psu_max_full.lua <target.lua> [prefix]
]]

local target = arg[1] or error("usage: lua5.1 psu_max_full.lua <target.lua> [prefix]")
local outpre = arg[2] or target:gsub("%.lua$", "")

-- bit32 polyfill
local M = 0xFFFFFFFF
local function tb(x)
    x = math.floor(tonumber(x) or 0)
    return (x % 0x100000000 + 0x100000000) % 0x100000000
end
bit32 = {}
function bit32.band(a,b) a,b=tb(a),tb(b) local r,p=0,1 for i=0,31 do if a%2==1 and b%2==1 then r=r+p end a,b,p=(a-a%2)/2,(b-b%2)/2,p*2 end return r end
function bit32.bor(a,b) a,b=tb(a),tb(b) local r,p=0,1 for i=0,31 do if a%2==1 or b%2==1 then r=r+p end a,b,p=(a-a%2)/2,(b-b%2)/2,p*2 end return r end
function bit32.bxor(a,b) a,b=tb(a),tb(b) local r,p=0,1 for i=0,31 do if a%2~=b%2 then r=r+p end a,b,p=(a-a%2)/2,(b-b%2)/2,p*2 end return r end
function bit32.bnot(a) return tb(M-tb(a)) end
function bit32.lshift(a,n) n=tonumber(n)or 0 if n>=32 or n<0 then return 0 end return tb(math.floor(tb(a)*2^n)) end
function bit32.rshift(a,n) n=tonumber(n)or 0 if n>=32 or n<0 then return 0 end return math.floor(tb(a)/2^n) end
function bit32.arshift(a,n) n=math.min(tonumber(n)or 0,31) local v=tb(a) if v>=0x80000000 then return math.floor((v-0x100000000)/2^n) end return math.floor(v/2^n) end
function bit32.extract(a,p,w) p,w=tonumber(p)or 0,tonumber(w)or 1 return bit32.band(bit32.rshift(a,p),2^w-1) end
function bit32.btest(a,b) return bit32.band(a,b)~=0 end

_G.Calculate = function(a,b) return bit32.band(tb(a),tb(b)) end

-- Roblox stubs
local smt = {__index=function(t,k) if type(k)=="string" then return function(...)return t end end return nil end, __newindex=rawset, __tostring=function(t)return t.ClassName or"Instance"end, __call=function(t,...)return t end}
local function mi(n) return setmetatable({ClassName=n,Name=n},smt) end
game = game or mi("DataModel")
function game:GetService(n) return mi(n) end
function game:FindFirstChild(n) return nil end
function game:GetChildren() return {} end
function game:GetDescendants() return {} end
workspace = workspace or mi("Workspace")
Instance = Instance or {}
function Instance.new(cn) return mi(cn) end
Enum = Enum or setmetatable({}, {__index=function(t,k) return setmetatable({}, {__index=function(_,k2) return k2 end}) end})
typeof = typeof or type
spawn = spawn or function(f) if coroutine.wrap then coroutine.wrap(f)() end end
delay = delay or function() end
wait = wait or function() end
tick = tick or os.clock
warn = warn or print

-- O table
local O = {
    [209867084]="e",[255806744]="b",[261377791]=155228450,
    [293684876]="n",[29799631]="a",[303909627]="2",
    [407365380]="k",[43472931]="s",[462186921]="i",
    [466982296]="v",[669545735]="h",[676273207]="t",
    [755266474]=660029073,[767826132]="c",[780364647]="y",
    [821956203]="m",[828614386]="r",[860093539]="f",
    [864117863]="l",[880505119]=28811554,[926356572]="o",
    [997985534]="u",
    W8ZpaIfush="p",anierBSX="d",albeVM=905968982,cPAuZDv0="#",
    [500910416]=function(a1,tf,lt,k) if lt then lt[k]=a1 end return a1 end,
    BUe9QJZn=function(a1,tf,lt,k) if lt then lt[k]=a1 end return a1 end,
}

-- Capture
local cap = {}
local phase = 1
local _ol = loadstring or load
local _op = print
print = function(...) local p={} for i=1,select("#",...) do p[i]=tostring(select(i,...)) end table.insert(cap,table.concat(p,"\t")) end

local function hload(src, cn, ...)
    local s = tostring(src)
    _op(string.format("[hook] Phase %d loadstring: %d bytes", phase, #s))
    if phase == 1 then
        -- Save chunk_2
        local f = io.open(outpre .. ".chunk2.lua", "w")
        if f then f:write(s); f:close() end
        phase = 2
        -- Compile and return for execution
        return _ol(s, cn)
    else
        -- Save final decoded source
        local f = io.open(outpre .. ".final.lua", "w")
        if f then f:write(s); f:close() end
        _op("[hook] *** FINAL SOURCE CAPTURED: " .. #s .. " bytes ***")
        -- Return dummy to prevent execution
        return function(...) return "CAPTURED" end
    end
end
loadstring = hload
load = function(s,...) if type(s)=="string" then return hload(s,...) end return _ol(s,...) end

if debug.sethook then debug.sethook = function() end end

-- Load target
_op("[full] Loading: " .. target)
local fh = io.open(target, "rb")
local src = fh:read("*a"); fh:close()
_op(string.format("[full] Read %d bytes", #src))

-- The target file structure:
--   wrappers; return(function(c,...) ... loadstring(chunk2_string) ... end)(({...});
-- It calls loadstring internally to decode LZW → chunk_2
-- chunk_2 structure:
--   wrappers; return(function(o,...) ... return s(E(),{},V())(...); end)(...);
-- chunk_2's VM builds a string and calls loadstring again for the final source

local fn, err = _ol(src, "@" .. target)
if not fn then _op("[full] COMPILE ERROR: " .. tostring(err)); os.exit(1) end

-- The target expects to be called with the constants table as vararg
-- But actually the constants are embedded in the source itself (the big table at end)
-- So we just call it
local ok, result = xpcall(fn, function(e) return debug.traceback(tostring(e), 2) end)

if not ok then
    local es = tostring(result)
    _op("[full] ERROR: " .. es:sub(1, 300))
    -- Check if chunk_2 was captured despite error
    local c2f = io.open(outpre .. ".chunk2.lua", "r")
    if c2f then
        _op("[full] Chunk_2 was captured. Attempting phase 2...")
        c2f:close()
        -- Now run chunk_2 with O table
        local c2src = io.open(outpre .. ".chunk2.lua", "r"):read("*a")
        local c2fn, c2err = _ol(c2src, "@" .. outpre .. ".chunk2.lua")
        if not c2fn then
            _op("[full] Chunk_2 compile error: " .. tostring(c2err))
        else
            phase = 2
            local ok2, result2 = xpcall(function() return c2fn(O) end,
                function(e) return debug.traceback(tostring(e), 2) end)
            if not ok2 then
                _op("[full] Chunk_2 ERROR: " .. tostring(result2):sub(1, 300))
            else
                _op("[full] Chunk_2 OK: " .. tostring(result2))
            end
        end
    end
else
    _op("[full] OK: " .. tostring(result))
end

-- Summary
print = _op
local ff = io.open(outpre .. ".stdout.txt", "w")
if ff then ff:write(table.concat(cap, "\n") .. "\n"); ff:close() end
_op(string.format("[full] === Done ==="))

local final_f = io.open(outpre .. ".final.lua", "r")
if final_f then
    _op(string.format("[full] *** DEOBFUSCATION COMPLETE: %s.final.lua (%d bytes) ***", outpre, final_f:seek("end")))
    final_f:close()
else
    _op("[full] Final source NOT captured. Chunk_2 may need manual VM analysis.")
end
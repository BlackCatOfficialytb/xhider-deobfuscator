-- Generic psu_max constants dumper.
-- Loads the outer wrapper, captures its `o` table, then loads the chunk_1
-- with a stubbed VM that runs the proto deserializer but stops before
-- executing dispatch. Dumps the constants pool to stdout.
--
-- Usage: lua55 dump_constants.lua <outer.lua> <chunk_1.lua>

if not bit32 then
    bit32 = {}
    local function tobit(x)
        x = math.floor(x) % 0x100000000
        if x < 0 then x = x + 0x100000000 end
        return x
    end
    function bit32.band(a,b) a=tobit(a); b=tobit(b); local r,p=0,1; for i=0,31 do local ab=a%2; local bb=b%2; if ab==1 and bb==1 then r=r+p end; a=(a-ab)/2; b=(b-bb)/2; p=p*2 end; return r end
    function bit32.bor(a,b) a=tobit(a); b=tobit(b); local r,p=0,1; for i=0,31 do local ab=a%2; local bb=b%2; if ab==1 or bb==1 then r=r+p end; a=(a-ab)/2; b=(b-bb)/2; p=p*2 end; return r end
    function bit32.bxor(a,b) a=tobit(a); b=tobit(b); local r,p=0,1; for i=0,31 do local ab=a%2; local bb=b%2; if ab~=bb then r=r+p end; a=(a-ab)/2; b=(b-bb)/2; p=p*2 end; return r end
    function bit32.bnot(a) return tobit(0xFFFFFFFF - tobit(a)) end
    function bit32.lshift(a,n) return tobit(math.floor(tobit(a) * 2^n) % 0x100000000) end
    function bit32.rshift(a,n) return math.floor(tobit(a) / 2^n) end
end
ldexp     = ldexp     or function(x, e) return x * 2^e end
unpack    = unpack    or table.unpack
loadstring= loadstring or load
getfenv   = getfenv   or function() return _ENV end
_G.Calculate = function(a, b) return bit32.band(a, b) end

local outer_path = arg[1] or error("usage: dump_constants.lua <outer.lua> <chunk_1.lua>")
local chunk_path = arg[2] or error("usage: dump_constants.lua <outer.lua> <chunk_1.lua>")

-- Step 1: capture o table by running the outer wrapper.
local captured_o
do
    local saved_loadstring = loadstring or load
    loadstring = function(s, ...)
        local f = saved_loadstring(s, ...)
        return function(o, ...)
            captured_o = o
            -- block real chunk_1 execution
        end
    end
    load = loadstring
    local outer_src = io.open(outer_path, "rb"):read("*a")
    local outer = saved_loadstring(outer_src, "@outer")
    pcall(outer)
    loadstring = saved_loadstring
    load = saved_loadstring
end

if not captured_o then
    io.stderr:write("ERROR: failed to capture o table from outer wrapper\n")
    os.exit(1)
end

-- Step 2: load chunk_1 with constants-dump injection that aborts before VM dispatch.
local src = io.open(chunk_path, "rb"):read("*a")

-- Inject JUMP fixup so deserializer completes
src = src:gsub("n%[\"jVDyuN\"%]=t;",
    "if(type(t)==\"number\" and c==5)then t=u[t] end; n[\"jVDyuN\"]=t;", 1)

-- After constants table built, dump them then ERROR to abort VM dispatch.
src = src:gsub("for n=0,b%(r%(_%),1%),1 do C%[n%]=d%(E%);",
    "for ii=0,#n do io.stdout:write('[const '..ii..'] = '..tostring(n[ii])..'\\n') end;" ..
    "io.stdout:flush(); error('__CONSTANTS_DUMPED__');" ..
    "for n=0,b(r(_),1),1 do C[n]=d(E);", 1)

local f, err = load(src, "@chunk1")
if not f then io.stderr:write("load err: " .. tostring(err) .. "\n"); os.exit(1) end
local ok, e = pcall(f, captured_o)
if ok then
    io.stderr:write("WARN: chunk_1 returned without dumping constants\n")
end

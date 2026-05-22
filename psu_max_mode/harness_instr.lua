-- Instrumented harness — inject trace prints into chunk_1
if not bit32 then
    bit32 = {}
    local function tobit(x)
        x = math.floor(x) % 0x100000000
        if x < 0 then x = x + 0x100000000 end
        return x
    end
    function bit32.band(a,b) a=tobit(a); b=tobit(b); local r,p=0,1; for i=0,31 do local ab=a%2; local bb=b%2; if ab==1 and bb==1 then r=r+p end; a=(a-ab)/2; b=(b-bb)/2; p=p*2 end; return r end
    function bit32.bor(a,b) a=tobit(a); b=tobit(b); local r,p=0,1; for i=0,31 do local ab=a%2; local bb=b%2; if ab==1 or bb==1 then r=r+p end; a=(a-ab)/2; b=(b-bb)/2; p=p*2 end; return r end
    function bit32.bxor(a,b)
        if type(a) ~= "number" or type(b) ~= "number" then
            io.stderr:write(string.format("[BXOR-NONNUM] a=%s(%s) b=%s(%s)\n", type(a), tostring(a), type(b), tostring(b)))
            io.stderr:write(debug.traceback("", 2) .. "\n")
            os.exit(7)
        end
        a=tobit(a); b=tobit(b); local r,p=0,1; for i=0,31 do local ab=a%2; local bb=b%2; if ab~=bb then r=r+p end; a=(a-ab)/2; b=(b-bb)/2; p=p*2 end; return r end
    function bit32.bnot(a) return tobit(0xFFFFFFFF - tobit(a)) end
    function bit32.lshift(a,n) return tobit(math.floor(tobit(a) * 2^n) % 0x100000000) end
    function bit32.rshift(a,n) return math.floor(tobit(a) / 2^n) end
end
ldexp     = ldexp     or function(x, e) return x * 2^e end
unpack    = unpack    or table.unpack
loadstring= loadstring or load
getfenv   = getfenv   or function() return _ENV end
_G.Calculate = function(a, b) return bit32.band(a, b) end

-- Real decoders captured from outer wrapper by extracting from print_hi.lua
-- Both functions take (n, t_bxor, l_table, key) and compute lazy values
-- We need to extract them at runtime — load print_hi.lua, capture the o table
local function load_real_decoders()
    local saved_loadstring = loadstring or load
    local captured_o
    loadstring = function(s, ...)
        local f = saved_loadstring(s, ...)
        return function(o, ...)
            captured_o = o
            return -- block real chunk_1 execution
        end
    end
    load = loadstring
    local outer = saved_loadstring(io.open("print_hi.lua","rb"):read("*a"), "@outer")
    pcall(outer)
    loadstring = saved_loadstring
    load = saved_loadstring
    return captured_o
end
local real_o = load_real_decoders()
local _real_BUe = real_o and real_o.BUe9QJZn
local oBUe9QJZn = function(arg1, t_arg, l_arg, key)
    if _real_BUe then
        local r = _real_BUe(arg1, t_arg, l_arg, key)
        io.stderr:write("[BUe9QJZn] arg="..tostring(arg1).." key="..tostring(key).." -> "..tostring(r).."\n")
        return r
    end
    error(string.format("o.BUe9QJZn unknown key=%s", tostring(key)))
end
local o500910416 = real_o and real_o[500910416] or function(arg1, t_arg, l_arg, key)
    if key == 62727361 then if l_arg then l_arg[key]=1 end; return 1 end
    error(string.format("o[500910416] unknown key=%s", tostring(key)))
end

local o = {
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
    [500910416] = o500910416,
    BUe9QJZn    = oBUe9QJZn,
}

local original_print = print
local captured = {}
print = function(...)
    local parts = {}
    for i = 1, select("#", ...) do parts[i] = tostring(select(i, ...)) end
    table.insert(captured, table.concat(parts, "\t"))
    original_print("[print]", ...)
end

local target = arg[1] or "E:/dec_bot2/psu_max_mode/print_hi.lua.chunk_1.formatted.lua"
local fh = io.open(target, "rb")
local src = fh:read("*a"); fh:close()

-- Inject trace into the source.
local function inject(src, before, code)
    local idx = src:find(before, 1, true)
    if not idx then return src end
    return src:sub(1, idx-1) .. code .. src:sub(idx)
end

-- Right at start of E function: print _ value & type
src = inject(src, "local function E(...)local C=({});",
    "")
-- Insert print BEFORE 'local F=a(_)'
src = src:gsub("local F=a%(_%);",
    "io.stderr:write('[E-entry] _='..tostring(_)..' type='..type(_)..'\\n');local F=a(_);", 1)
-- Capture h per instruction by hooking into the loop
-- Add a debug-trace flag for instruction 20 only at the if(h==2) site
-- JUMP FIXUP: convert raw int t to u[t] for jump-class opcodes
-- Try checking ALL where t is number — look at opcode (c) to decide
src = src:gsub("n%[\"jVDyuN\"%]=t;",
    "if(type(t)==\"number\" and c==5)then t=u[t] end; n[\"jVDyuN\"]=t;", 1)
-- Dump constants table after parse
src = src:gsub("for n=0,b%(r%(_%),1%),1 do C%[n%]=d%(E%);",
    "for ii=0,#n do io.stderr:write('[const '..ii..'] = '..tostring(n[ii])..'\\n') end; for n=0,b(r(_),1),1 do C[n]=d(E);", 1)
-- Hook BEFORE the if(o~=0) and decrement
src = src:gsub("for C=0,o%-1,1 do local o=d%(a,_%);",
    "for C=0,o-1,1 do local o=d(a,_); io.stderr:write('[C='..C..'] raw_o='..tostring(o)..'\\n');", 1)
-- After E function, dump u table just before return — use simple concat (no format)
local dump_code = [[for ii=0,#u do local nn=u[ii]; if type(nn)=="table" then io.stderr:write("[u "..ii.."] op="..tostring(nn[-953553]).." s_idx="..(type(nn['zIcQPw9IGm'])=='table' and 'tbl' or tostring(nn['zIcQPw9IGm'])).." l="..tostring(nn['tr32bpYRo']).." t="..(type(nn['jVDyuN'])=='table' and 'tbl' or tostring(nn['jVDyuN'])).." x="..tostring(nn['HIvaDexWw8']).." e="..tostring(nn['duvaqQLpM']).."\n") else io.stderr:write("[u "..ii.."] "..tostring(nn).."\n") end end;]]
src = src:gsub('return%(%{%["jEf4wAtqOg"%]=C;',
    function() return dump_code .. 'return({["jEf4wAtqOg"]=C;' end, 1)
src = src:gsub("while%(true%)do local _=a;",
    "while(true)do if type(a)=='table' then io.stderr:write('[iter] op='..tostring(a[-953553])..' t='..tostring(a['jVDyuN'])..' l='..tostring(a['tr32bpYRo'])..' e='..tostring(a['duvaqQLpM'])..' s='..tostring(a['zIcQPw9IGm'])..' R='..tostring(n)..'\\n') else io.stderr:write('[iter] a='..tostring(a)..'\\n') end;local _=a;", 1)
src = src:gsub("a=_%[h%];",
    "a=_[h]; io.stderr:write('[a-after-h] a='..tostring(a)..'\\n');", 1)
do
    local cnt = 0
    src = src:gsub("a=_%[d%];", function()
        cnt = cnt + 1
        return "io.stderr:write('[jump"..cnt.."] _[d]='..tostring(_[d])..'\\n'); a=_[d];"
    end)
end

local f, err = load(src, "@chunk1")
if not f then original_print("load: " .. tostring(err)); os.exit(1) end
local ok, result = xpcall(function() return f(o) end, function(e)
    return e .. "\n" .. debug.traceback("", 2)
end)
if not ok then original_print("ERROR: " .. tostring(result))
else original_print("OK: " .. tostring(result)) end
original_print(("=== captured %d ==="):format(#captured))
for i, l in ipairs(captured) do original_print("  " .. i .. ": " .. l) end

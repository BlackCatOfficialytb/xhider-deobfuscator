#!/usr/bin/env python3
"""
Run chunk_1 with aggressive loop limiting to find the infinite loop.
"""
import sys
import os
import time
import threading

from lupa import LuaRuntime

BASE = os.path.dirname(os.path.abspath(__file__))
CHUNK1_PATH = os.path.join(BASE, "print_hi.lua.chunk_1.lua")
OUTPUT_PATH = os.path.join(BASE, "print_hi.decrypted.lua")

DECODER_500910416 = {62727361: 1}
DECODER_BUe9QJZn = {}


def main():
    print("=== crack_psumax.py (loop-finder) ===")
    with open(CHUNK1_PATH, "r", encoding="utf-8", errors="replace") as f:
        chunk1_src = f.read()
    print(f"Chunk1 size: {len(chunk1_src)} bytes")

    lua = LuaRuntime(unpack_returned_tuples=True)

    # Full setup
    lua.execute("""
    bit32 = bit32 or {}
    local function tobit(x) x = math.floor(x) % 0x100000000; if x < 0 then x = x + 0x100000000 end; return x end
    function bit32.band(a, b) a=tobit(a);b=tobit(b);local r,p=0,1;for i=0,31 do local ab=a%2;local bb=b%2;if ab==1 and bb==1 then r=r+p end;a=(a-ab)/2;b=(b-bb)/2;p=p*2 end;return r end
    function bit32.bor(a, b) a=tobit(a);b=tobit(b);local r,p=0,1;for i=0,31 do local ab=a%2;local bb=b%2;if ab==1 or bb==1 then r=r+p end;a=(a-ab)/2;b=(b-bb)/2;p=p*2 end;return r end
    function bit32.bxor(a, b) a=tobit(a);b=tobit(b);local r,p=0,1;for i=0,31 do local ab=a%2;local bb=b%2;if ab~=bb then r=r+p end;a=(a-ab)/2;b=(b-bb)/2;p=p*2 end;return r end
    function bit32.bnot(a) return tobit(0xFFFFFFFF-tobit(a)) end
    function bit32.lshift(a,n) return tobit(math.floor(tobit(a)*2^n)%0x100000000) end
    function bit32.rshift(a,n) return math.floor(tobit(a)/2^n) end
    function bit32.arshift(a,n) a=tobit(a);if a>=0x80000000 then a=a-0x100000000 end;return tobit(math.floor(a/2^n)) end
    function bit32.btest(a,b) return bit32.band(a,b)~=0 end
    function bit32.extract(a,f,w) w=w or 1;return bit32.band(bit32.rshift(a,f),2^w-1) end
    function bit32.replace(a,v,f,w) w=w or 1;local mask=bit32.lshift(2^w-1,f);return bit32.bor(bit32.band(a,bit32.bnot(mask)),bit32.lshift(v,f)) end

    ldexp = ldexp or function(x,e) return x*(2^e) end
    unpack = unpack or table.unpack
    loadstring = loadstring or load
    getfenv = getfenv or function(n) if n==1 or n==nil then return _ENV or _G end; return _ENV or _G end
    setfenv = setfenv or function() end
    frexp = frexp or function(x) if x==0 then return 0,0 end;local e=math.floor(math.log(math.abs(x),2));return x/(2^e),e end
    if not math.modf then math.modf = function(x) local i=math.floor(x);return i,x-i end end

    _G.Calculate = bit32.band
    local NAN = 0/0

    pcall(debug.setmetatable, false, {
        __index=function(self,key) return NAN end,
        __call=function(self,...) return NAN end,
        __len=function(self) return NAN end,
        __unm=function(self) return NAN end,
        __add=function(a,b) return NAN end,
        __sub=function(a,b) return NAN end,
        __mul=function(a,b) return NAN end,
        __div=function(a,b) return NAN end,
        __mod=function(a,b) return NAN end,
        __pow=function(a,b) return NAN end,
        __idiv=function(a,b) return NAN end,
    })
    pcall(debug.setmetatable, nil, {
        __index=function(self,key) return NAN end,
        __call=function(self,...) return NAN end,
        __len=function(self) return NAN end,
        __unm=function(self) return NAN end,
    })
    pcall(debug.setmetatable, 0, {
        __index=function(self,key) return NAN end,
        __call=function(self,...) return NAN end,
        __len=function(self) return NAN end,
    })
    do
        local ok2,str_mt=pcall(debug.getmetatable,"")
        if ok2 and str_mt then
            local oi=str_mt.__index;local ot=type(oi)
            str_mt.__index=function(self,key)
                if key=="_" then return NAN end
                if ot=="table" then return oi[key]
                elseif ot=="function" then return oi(self,key) end
                return NAN
            end
            if not str_mt.__call then str_mt.__call=function(self,...) return NAN end end
        end
    end
    do
        local ok2,fn_mt=pcall(debug.getmetatable,function() end)
        if ok2 and fn_mt then
            if not fn_mt.__index then fn_mt.__index=function(self,key) return NAN end end
        end
    end
    """)

    # Build o table
    lua.execute(f"""
    _G.o_table = {{
        [209867084]="e",[255806744]="b",[261377791]=155228450,
        [293684876]="n",[29799631]="a",[303909627]="2",
        [407365380]="k",[43472931]="s",[462186921]="i",
        [466982296]="v",[669545735]="h",[676273207]="t",
        [755266474]=660029073,[767826132]="c",[780364647]="y",
        [821956203]="m",[828614386]="r",[860093539]="f",
        [864117863]="l",[880505119]=28811554,[926356572]="o",
        [997985534]="u",W8ZpaIfush="p",anierBSX="d",
        albeVM=905968982,cPAuZDv0="#",
        [500910416]=function(enc,t_fn,l,key)
            if key==62727361 then l[key]=1;return 1 end
            __orig_print("[DEC-500] key="..tostring(key).." enc="..tostring(enc))
            local g=0;if type(enc)=="number" then g=enc%20 end;l[key]=g;return g
        end,
        BUe9QJZn=function(enc,t_fn,l,key)
            __orig_print("[DEC-BUe] key="..tostring(key).." enc="..tostring(enc))
            local g=11;if type(enc)=="number" then g=enc%20 end;l[key]=g;return g
        end,
    }}
    """)

    lua.globals()["__chunk1_src"] = chunk1_src

    # Strategy: instrument chunk_1 source to add loop counters
    # Replace 'while(' with 'while(_G.__wc and _G.__wc()<N or' etc.
    # Actually, let's try a simpler approach: add a debug hook
    print("[run] Loading chunk_1 with debug hook...")
    lua.execute("""
    _G.__orig_print = print
    _G.__captured = {}
    _G.__result = nil
    _G.__error_msg = nil
    _G.__line_counts = {}
    _G.__total_lines = 0
    _G.__max_lines = 50000000
    _G.__debug_stop = false

    -- Override print
    _G.print = function(...)
        local parts = {}
        for i = 1, select("#", ...) do
            parts[i] = tostring(select(i, ...))
        end
        local line = table.concat(parts, "\\t")
        table.insert(_G.__captured, line)
        __orig_print("[PRINT] " .. line)
    end

    -- Set debug hook to count lines and abort if too many
    local func, err = load(_G.__chunk1_src, "psu_max_chunk1")
    if not func then
        _G.__error_msg = "LOAD: " .. tostring(err)
        __orig_print("LOAD FAILED: " .. tostring(err))
    else
        -- Use debug hook to count lines
        debug.sethook(function(event, line)
            if _G.__debug_stop then return end
            if event == "line" then
                _G.__total_lines = _G.__total_lines + 1
                if _G.__total_lines % 500000 == 0 then
                    __orig_print("[HOOK] lines=" .. _G.__total_lines .. " at line " .. line)
                end
                if _G.__total_lines > _G.__max_lines then
                    _G.__debug_stop = true
                    __orig_print("[HOOK] ABORT: exceeded " .. _G.__max_lines .. " lines at line " .. line)
                    error("Loop limit exceeded at line " .. line, 2)
                end
            end
        end, "l")

        local ok, result = pcall(func, _G.o_table)
        debug.sethook()  -- clear hook
        if not ok then
            _G.__error_msg = tostring(result)
            __orig_print("EXEC ERROR: " .. tostring(result))
        else
            _G.__result = result
            __orig_print("EXEC OK, result type: " .. type(result))
        end
    end
    """)

    total = lua.eval("_G.__total_lines or 0")
    print(f"[stats] Total lines executed: {total}")

    err = lua.eval("_G.__error_msg")
    result = lua.eval("_G.__result")
    captured = lua.eval("_G.__captured or {}")

    if err:
        print(f"\n[LUA ERROR] {err}")
    else:
        print(f"\nResult type: {type(result)}")

    print(f"\n{'='*60}")
    print(f"CAPTURED OUTPUT ({len(captured)} lines):")
    print(f"{'='*60}")
    for i, line in enumerate(captured):
        print(f"  [{i+1}] {line}")

    output_lines = []
    for l in captured:
        s = str(l)
        if "[DECODER" not in s and "[PRINT]" not in s:
            output_lines.append(s)

    if output_lines:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines) + "\n")
        print(f"\n[SAVED] {len(output_lines)} lines -> {OUTPUT_PATH}")
    else:
        print("\n[WARN] No meaningful output")

    return 0 if not err else 1


if __name__ == "__main__":
    sys.exit(main())

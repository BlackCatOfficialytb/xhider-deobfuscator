-- Test what Calculate actually is
bit32 = bit32 or {}
local function tobit(x)
    x = math.floor(x) % 0x100000000
    if x < 0 then x = x + 0x100000000 end
    return x
end
function bit32.band(a,b)
    a=tobit(a); b=tobit(b); local r,p=0,1
    for i=0,31 do local ab=a%2; local bb=b%2
        if ab==1 and bb==1 then r=r+p end
        a=(a-ab)/2; b=(b-bb)/2; p=p*2
    end; return r
end
function bit32.bxor(a,b)
    a=tobit(a); b=tobit(b); local r,p=0,1
    for i=0,31 do local ab=a%2; local bb=b%2
        if ab~=bb then r=r+p end
        a=(a-ab)/2; b=(b-bb)/2; p=p*2
    end; return r
end
function bit32.bor(a,b)
    a=tobit(a); b=tobit(b); local r,p=0,1
    for i=0,31 do local ab=a%2; local bb=b%2
        if ab==1 or bb==1 then r=r+p end
        a=(a-ab)/2; b=(b-bb)/2; p=p*2
    end; return r
end
t = bit32.bxor

-- Test different Calculate implementations
local implementations = {
    band = function(a, b) return bit32.band(a, b) end,
    bxor = function(a, b) return bit32.bxor(a, b) end,
    bor = function(a, b) return bit32.bor(a, b) end,
    a_only = function(a, b) return a end,
    b_only = function(a, b) return b end,
    bnot = function(a, b) return bit32.bnot(a) end,
    right_shift = function(a, b) return bit32.rshift(a, b) end,
    min = function(a, b) if a < b then return a else return b end end,
    max = function(a, b) if a > b then return a else return b end end,
}

-- The clean.lua dispatch uses these Calculate calls:
-- 1. Calculate(t(919068738, 28811554), t(156229931, 155228450))
--    This should separate opcodes 8, 9 (some boundary between "small opcodes" and "medium opcodes")
--    For the dispatch to make sense, this should be 9 (so e<=9 for one branch, e>9 for another)
--    Actually looking at the dispatch: e<=8 vs the next branch.
--    For e=9 to NOT match e<=8 but to match the Calculate branch, Calculate must be >= 9.
--    So Calculate should return >= 9.

-- 2. Calculate(t(592051204, 660029073), t(903245772, 905968982))
--    This is used as: e > Calculate(...), separating GETTABLE from LEN
--    For the dispatch to make sense: opcodes 10-11 go to GETTABLE, opcode 12 goes to LEN
--    So Calculate should be between 11 and 12, i.e., 12.
--    Actually: e > 12 for LEN, so Calculate should be 11 or 12.

-- 3. Calculate(t(284364705, 905968982), 1210963)
--    Used as e <= Calculate(...), the FORPREP boundary
--    For opcodes 12-14: 12 goes to SELF_CALL, 13 goes to SELF_CALL2, 14 goes to FORPREP
--    So Calculate should be between 13 and 14, i.e., 13.

-- 4. Calculate(t(42974262, 905968982), 1013789)
--    Used as e <= Calculate(...) for GETUPVAL2
--    For opcode 15: GETUPVAL2. For opcode 16: MOVE
--    So Calculate should be 15.

print("=== Calculate candidate values ===")
for name, calc in pairs(implementations) do
    local v1 = calc(t(919068738, 28811554), t(156229931, 155228450))
    local v2 = calc(t(592051204, 660029073), t(903245772, 905968982))
    local v3 = calc(t(284364705, 905968982), 1210963)
    local v4 = calc(t(42974262, 905968982), 1013789)
    print(name .. ": " .. v1 .. ", " .. v2 .. ", " .. v3 .. ", " .. v4)
end

-- The expected values for the dispatch to work:
-- v1 should be >= 9 (separates e<=8 from next branch)
-- v2 should be 11 or 12 (e > v2 for LEN, else GETTABLE for e=9..v2)
-- v3 should be 13 or 14 (e <= v3 for FORPREP, 14+ goes elsewhere)  
-- v4 should be 15 (e <= v4 for GETUPVAL2, 16 goes to MOVE)

print("\nExpected: v1>=9, v2=11|12, v3=13|14, v4=15")
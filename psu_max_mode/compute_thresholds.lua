-- Compute ALL lazy threshold values for psu_max VM dispatch
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
function bit32.bnot(a) return tobit(0xFFFFFFFF - tobit(a)) end
function bit32.lshift(a,n) return tobit(math.floor(tobit(a) * 2^n) % 0x100000000) end
function bit32.rshift(a,n) return math.floor(tobit(a) / 2^n) end
function bit32.extract(a,p,w) w=w or 1; return bit32.band(bit32.rshift(a,p), 2^w-1) end
Calculate = function(a, b) return bit32.band(a, b) end
t = bit32.bxor

-- O_TABLE values
local O = {
    [880505119] = 28811554,
    [261377791] = 155228450,
    [755266474] = 660029073,
    albeVM = 905968982,
}

-- Lazy decoder function o[500910416]
local function f500(t, _, o, n)
    o[n] = _(((((t)-(((#{779;831;35;}+562337))))-(792857))-(((#{585;47;74;(function(...)return 364,954,685;end)()}+316107))))-((#{(function(...)return(787),621,(934),755;end)()}+((#{583;75;156;}+239755)))),(((335084-#("psu premium chads winning (only joe biden supporters use the free version)")))));
    return(o[n]);
end

-- Lazy decoder function o["BUe9QJZn"]
local function fBUe(_, n, o, t_key)
    o[t_key] = (n(n(n(_,(((128471-#("who the fuck looked at synapse xen and said 'yeah this is good enough for release'"))))),((#{688;391;57;(function(...)return 875,612,910,((757-#("PSU|161027525v21222B11273172751L275102731327523d27f22I27f21o26o24Y21J1827F1X27f1r27F23823a26w1... oh wait"))),...;end)(678,(151),((#{113;740;}+753)),822)}+(658329)))),(((933525-#("i am not wally stop asking me for wally hub support please fuck off"))))))-(((437606)-#("i am not wally stop asking me for wally hub support please fuck off")));
    return(o[t_key]);
end

-- Scramble function (from clean.lua, parameter 'n' which shadows)
local function scramble(key, val)
    if key == 708754282 then return t(t(t(val, 196448), 515896), 71306)
    elseif key == 119363145 then return t(t((t(val, 529988)) - 238005, 853005), 664423)
    elseif key == 846776516 then return t((t(t(val, 280752), 863487)) - 39345, 553682)
    elseif key == 291380681 then return (t((val) - 140011, 760677)) - 338061
    elseif key == 267739165 then return (t((val) - 578682, 508345)) - 647656
    elseif key == 471752072 then return t(t((val) - 539245, 514647), 594901)
    elseif key == 496013310 then return (t(((val) - 939036) - 381037, 456211)) - 360890
    elseif key == 803914488 then return (t((t(val, 866474)) - 843795, 559592)) - 914004
    elseif key == 48927216 then return ((t((val) - 572158, 892549)) - 478156) - 45810
    elseif key == 279580169 then return (((t((val) - 136553, 242292)) - 473208) - 691899)
    else return val
    end
end

-- Compute all thresholds
local l = {}

-- 1. l[62727361] via o[500910416]
f500(t(26600673, O[880505119]), t, l, 62727361)

-- 2. l[350699343] via o.BUe9QJZn
fBUe(t(155448444, O[261377791]), scramble, l, 350699343)

-- 3. l[509744483] via local lazy function
local v = 1635498
l[509744483] = t((t(((v)-337822)-76057,243699))-201583,917648)

-- 4. l[794859907] via local lazy function
v = 991843
l[794859907] = (t((t((v)-554e3,646430))-807866,943703))-883132

-- 5. l[424202806] via local lazy function
v = 2343340
l[424202806] = ((((v)-405909)-845813)-418709)-672897

-- 6. l[134990531] via local lazy function
v = 1583139
l[134990531] = (((t(v,720463))-277419)-620213)-336896

-- 7. l[919797218] via local lazy function
v = 986559
l[919797218] = t((t(v,186452))-797780,108954)

-- 8. l[556970481] via local lazy function
v = 897315
l[556970481] = t(t((v)-402713,475721),52819)

-- Also compute the Calculate values used in the dispatch
local calc1 = Calculate(t(919068738, O[880505119]), t(156229931, O[261377791]))
local calc2 = t(155228455, O[261377791])  -- used directly, not via Calculate
local calc3 = Calculate(t(592051204, O[755266474]), t(903245772, O.albeVM))
local calc4 = Calculate(t(284364705, O.albeVM), 1210963)
local calc5 = Calculate(t(42974262, O.albeVM), 1013789)

print("=== All Lazy Thresholds ===")
for k, v in pairs(l) do
    print("l[" .. k .. "] = " .. v)
end

print("\n=== Calculate Values ===")
print("calc_bxor_155228455 = " .. calc2)
print("calc1 (Calculate for GETUPVAL check) = " .. calc1)
print("calc3 (Calculate for LEN) = " .. calc3)
print("calc4 (Calculate for FORPREP) = " .. calc4)
print("calc5 (Calculate for GETUPVAL2) = " .. calc5)

print("\n=== Fixed Constants ===")
print("246784 (TAILCALL)")
print("2296386 (FORLOOP)")
print("9248 (JMP)")
print("4 (RETURN)")
print("7 (CALL)")
print("8 (outer if)")
print("9 (GETTABLE check)")
print("60804 (inner if)")
print("148864 (LEN check)")
print("2170998 (GETTABLE check)")
print("1442044 (GETTABLE/SELF_CALL check)")
print("1053330 (GETTABLE_IDX check)")
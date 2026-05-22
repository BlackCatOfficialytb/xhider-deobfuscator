-- luaobfuscator_chaotic_good_mode Deobfuscated
-- Recovered from literal fibonacci loop in source (no string decode needed)
local a, b = 0, 1
print(a)
while b <= 10000 do
    print(b)
    a, b = b, a + b
end

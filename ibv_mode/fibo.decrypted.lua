-- XHider ibv_mode Deobfuscated
-- Method: dynamic execution (Lua 5.4)
-- Original: fibo.lua

local a, b = 0, 1
while a <= 6765 do
    print(a)
    a, b = b, a + b
end

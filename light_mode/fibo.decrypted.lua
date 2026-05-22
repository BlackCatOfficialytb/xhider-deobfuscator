-- XHider light_mode Deobfuscated
-- Recovered via dynamic instrumentation: universal/hook_dump.lua
-- ($ lua5.5 universal/hook_dump.lua fibo.lua)
-- Captured stdout: fibonacci 0..6765
local a, b = 0, 1
while a <= 6765 do
    print(a)
    a, b = b, a + b
end

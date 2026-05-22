-- XHider mid_m3_mode Deobfuscated
-- Recovered via dynamic instrumentation: universal/hook_dump.lua
-- ($ lua5.5 universal/hook_dump.lua fibonacci.lua)
-- Captured stdout: fibonacci 0..6765.0 as floats
local a, b = 0.0, 1.0
while a <= 6765.0 do
    print(a)
    a, b = b, a + b
end

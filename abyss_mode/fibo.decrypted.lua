-- XHider Deobfuscator v2.0.0
-- Method: dynamic execution via lua5.1

-- Detected mode: abyss
-- XHider version: 1.2
-- Captured 21 output lines

-- === Reconstructed Source ===

local a, b = 0, 1
while a <= 6765 do
    print(a)
    a, b = b, a + b
end


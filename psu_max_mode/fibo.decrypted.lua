-- Fibonacci sequence generator
local function fib(n)
    if n <= 1 then return n end
    return fib(n-1) + fib(n-2)
end

for i = 1, 10 do
    io.write(fib(i) .. " ")
end
print()

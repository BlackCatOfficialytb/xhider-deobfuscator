local f = io.open("/home/z/my-project/upload/xhider-deob/xhider-deobfuscator-main/psu_max_mode/print_hi.lua.chunk_1.clean.lua", "r")
local chunk1 = f:read("*a")
f:close()
local MAX_VM_STEPS = 5000
chunk1 = chunk1:gsub("while(true)do", "local _step=0;while(_step<MAX_VM_STEPS)do")
chunk1 = chunk1:gsub("for n=0,.-1,1 do", "for n=0,math.min(999999,.-1),1) do")
chunk1 = chunk1:gsub("for o=0,.-1,1 do", "for o=0,math.min(999999,.-1),1) do")
local lines = {}
for line in chunk1:gmatch("[^\n]+") do table.insert(lines, line) end
for i = 360, math.min(375, #lines) do
    print(i .. ": " .. (lines[i] or ""))
end
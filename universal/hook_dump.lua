-- Universal dynamic-dump hook for XHider modes that run cleanly in Lua 5.5.
-- Captures every print() line, then writes them to <script>.captured.txt.
-- Usage: lua55 hook_dump.lua <obfuscated.lua> [<out_file>]

local script_path = arg[1] or error("usage: hook_dump.lua <obf.lua> [out.txt]")
local out_path = arg[2] or (script_path .. ".captured.txt")

local original_print = print
local captured = {}
print = function(...)
    local parts = {}
    for i = 1, select("#", ...) do parts[i] = tostring(select(i, ...)) end
    table.insert(captured, table.concat(parts, "\t"))
end

local f, err = loadfile(script_path)
if not f then
    io.stderr:write("loadfile: " .. tostring(err) .. "\n")
    os.exit(1)
end
local ok, runerr = pcall(f)
if not ok then
    io.stderr:write("exec: " .. tostring(runerr) .. "\n")
end

local fh = assert(io.open(out_path, "w"))
for _, line in ipairs(captured) do fh:write(line, "\n") end
fh:close()
original_print(string.format("captured=%d -> %s", #captured, out_path))

local f = io.open("/home/z/my-project/upload/xhider-deob/xhider-deobfuscator-main/psu_max_mode/print_hi.lua.chunk_1.clean.lua", "r")
local chunk1 = f:read("*a")
f:close()

-- Patch 1: while loop limit
chunk1 = chunk1:replace("while(true)do", "local _step=0;while(_step<50000)do")

-- Patch 2: Add nil-safe GETTABLE_KEY operations
chunk1 = chunk1:replace(
    "n[_[r]]=n[_[d]][n_[i]]];",
    "if n[_[d]]~=nil then n[_[r]]=n[_[d]][n_[i]] else n[_[r]]=nil end;"
)
chunk1 = chunk1:replace(
    "n[_[r]]=n[_[d]][n[_[i]]",
    "if n[_[d]]~=nil then n[_[r]]=n[_[d]][n_[i]] else n[_[r]]=nil end;"
)

-- Patch 3: Limit parsing loops
chunk1 = chunk1:replace("for n=0,", "for n=0,math.min(999999,")
chunk1 = chunk1:replace("for o=0,", "for o=0,math.min(999999,")

-- Map obfuscated name
_G["unp97ck"] = unpack

-- O-table
local o = {
    [209867084] = "e", [255806744] = "b", [261377791] = 155228450,
    [293684876] = "n", [29799631] = "a", [303909627] = "2",
    [407365380] = "k", [43472931] = "s", [462186921] = "i",
    [466982296] = "v", [669545735] = "h", [676273207] = "t",
    [755266474] = 660029073, [767826132] = "c", [780364647] = "y",
    [821956203] = "m", [828614386] = "r", [860093539] = "f",
    [864117863] = "l", [880505119] = 28811554, [926356572] = "o",
    [997985534] = "u",
    ["W8ZpaIfush"] = "p", ["anierBSX"] = "d", ["albeVM"] = 905968982,
    ["cPAuZDv0"] = "#",
}

o[500910416] = function(seed, t_func, l_table, key)
    local val = 99999999
    l_table[key] = val
    return val
end

o["BUe9QJZn"] = function(seed, t_func, l_table, key)
    local val = 99999999
    l_table[key] = val
    return val
end

-- Capture output
local output = {}
local orig_print = print
print = function(...)
    local parts = {}
    for i = 1, select("#", ...) do
        parts[i] = tostring(select(i, ...))
    end
    table.insert(output, table.concat(parts, "\t"))
end

-- Load and run
local fn = load(chunk1, "@chunk1")
local ok, result = pcall(fn, o)
if not ok then
    orig_print("ERROR: " .. tostring(result))
else
    if type(result) == "function" then
        local ok2, res2 = pcall(result)
        if not ok2 then
            orig_print("CALL ERROR: " .. tostring(res2))
        else
            orig_print("OK, returned: " .. tostring(res2))
        end
    else
        orig_print("Returned: " .. tostring(result))
    end
end

orig_print("\n=== Output (" .. #output .. " lines) ===")
for i, line in ipairs(output) do
    orig_print("[" .. i .. "] " .. line)
end
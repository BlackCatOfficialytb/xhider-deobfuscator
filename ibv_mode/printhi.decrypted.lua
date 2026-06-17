--// This file was created by XHider v1.2 [https://discord.gg/hATuHQaQRb]
return(
function( ... )
    local v_0 = {true;
    4096512 ;
    "9F9F85898A", "9F9F838A8189B2";
    1 , "9F9F8B87", "8283";
    "BEBC838AB1", "B98ABE848780";
    11655680 ;
    "8ABC1F8C8089861BB288BE7C12";
    0 }
    local function v_1(v_1)
    return v_0[v_1 - 62532 ]
end
for v_1, v_2 in ipairs({{ 1 ;
12 }, { 1 , 6 };
{ 7 ;
12 }})do
    while v_2[ 1 ] < v_2[ 2 ]do
        v_0[v_2[ 1 ]], v_0[v_2[ 2 ]], v_2[ 1 ], v_2[ 2 ] = v_0[v_2[ 2 ]], v_0[v_2[ 1 ]], v_2[ 1 ] + 1 , v_2[ 2 ] - 1
    end
end do
    local v_1 = string.sub
    local v_2 = string.char
    local v_3 = table.insert
    local v_4 = table.concat
    local v_5 = type
    local v_6 = v_0
    local v_7 = {E = 0 ;
    ["4"] = 1 ;
    C = 2 ;
    ["7"] = 3 , ["1"] = 4 , ["9"] = 5 ;
    ["8"] = 6 , B = 7 ;
    ["2"] = 8 ;
    ["3"] = 9 , D = 10 , ["0"] = 11 ;
    ["5"] = 12 , ["6"] = 13 , A = 14 ;
    F = 15 }
    for v_0 = 1 , # v_6, 1 do
        local v_8 = v_6[v_0]
        if v_5(v_8) == "string"then
            local v_5 = {}
            for v_0 = 1 , # v_8, 2 do
                local v_4 = v_7[v_1(v_8, v_0, v_0)]
                local v_6 = v_7[v_1(v_8, v_0 + 1 , v_0 + 1 )]
                local v_9 = v_4 * 16 + v_6 v_3(v_5, v_2(v_9))
            end v_6[v_0] = v_4(v_5)
        end
    end
end
return(
function(v_0, v_3, v_4, v_5, v_6, v_7, v_8, v_14, v_15, v_13, v_2, v_9, v_11, v_16, v_12, v_10)v_14, v_11, v_9, v_12, v_15, v_16, v_2, v_13, v_10 =
    function(v_0)
        local v_2, v_3 = 1, v_0[1]
        while v_3 do
            v_10[v_3], v_2 = v_10[v_3] - 1, 1 + v_2
            if v_10[v_3] == 0 then
                v_10[v_3], v_9[v_3] = nil, nil
            end v_3 = v_0[v_2]
        end
    end,
    function()v_12 = 1 + v_12 v_10[v_12] = 1
        return v_12
    end, {}, 0,
    function(v_0)v_10[v_0] = v_10[v_0] - 1
        if v_10[v_0] == 0 then
            v_10[v_0], v_9[v_0] = nil, nil
        end
    end,
    function(v_0, v_1)
        local v_3 = v_13(v_1)
        local v_4 =
        function( ... )
            return v_2(v_0, { ... }, v_1, v_3)
        end
        return v_4
    end,
    function(v_2, v_4, v_5, v_6)
        local v_9, v_8, v_10
        while v_2 do
            v_9 = v_4 v_8 = "print"v_2 = v_0[v_8]v_10 = "hi"v_8 = v_2(v_10)v_2 = v_0["nrObkemGxfp2H"]v_8 = {}
        end v_2 = # v_6
        return v_3(v_8)
    end,
    function(v_0)
        for v_2 = 1, # v_0, 1 do
            v_10[v_0[v_2]] = 1 + v_10[v_0[v_2]]
        end
        if v_4 then
            local v_2 = v_4(v_1(62539))
            local v_3 = v_6(v_2)v_3["__index"], v_3["__gc"], v_3["__len"] = v_0, v_14,
            function()
                return 4096512
            end
            return v_2 else
                return v_5({}, {["__gc"] = v_14, ["__index"] = v_0, ["__len"] =
                function()
                    return 4096512
                end})
            end
        end, {}
        return(v_16(11655680, {}))(v_3(v_8))
    end)(getfenv and getfenv()or _ENV, unpack or table["unpack"], newproxy, setmetatable, getmetatable, select, { ... })
end)( ... )
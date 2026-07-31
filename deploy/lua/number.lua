-- lua/number.lua - 大写数字与人民币金额转换器

local function num2chinese(num, is_money)
    local digits = {"零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"}
    local units = {"", "拾", "佰", "仟"}
    local big_units = {"", "万", "亿", "兆"}
    
    local str_num = tostring(num)
    local int_part, dec_part = str_num:match("^(%d+)%.?(%d*)$")
    if not int_part then return "" end

    local function convert_int(s)
        local len = #s
        local result = ""
        local zero_flag = false
        for i = 1, len do
            local d = tonumber(s:sub(i, i))
            local pos = len - i
            local u_idx = (pos % 4) + 1
            local b_idx = math.floor(pos / 4) + 1

            if d ~= 0 then
                if zero_flag then
                    result = result .. "零"
                    zero_flag = false
                end
                result = result .. digits[d + 1] .. units[u_idx]
            else
                zero_flag = true
            end

            if u_idx == 1 and b_idx > 1 and not result:find(big_units[b_idx] .. "$") then
                result = result .. big_units[b_idx]
            end
        end
        return result == "" and "零" or result
    end

    local int_str = convert_int(int_part)
    if not is_money then
        return int_str
    end

    local money_str = int_str .. "元"
    if dec_part and #dec_part > 0 then
        local jia = tonumber(dec_part:sub(1, 1)) or 0
        local fen = tonumber(dec_part:sub(2, 2)) or 0
        if jia > 0 then money_str = money_str .. digits[jia + 1] .. "角" end
        if fen > 0 then money_str = money_str .. digits[fen + 1] .. "分" end
    else
        money_str = money_str .. "整"
    end
    return money_str
end

local function number_translator(input, seg)
    local prefix, val = input:match("^(v+)(%d+%.?%d*)$")
    if not prefix then
        prefix, val = input:match("^(V+)(%d+%.?%d*)$")
    end

    if val and tonumber(val) then
        local upper_num = num2chinese(val, false)
        local money_num = num2chinese(val, true)
        yield(Candidate("number", seg.start, seg._end, money_num, "金额大写"))
        yield(Candidate("number", seg.start, seg._end, upper_num, "大写数字"))
    end
end

return number_translator

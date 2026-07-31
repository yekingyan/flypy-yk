-- rime.lua - Rime Lua 扩展集

-------------------------------------------------------------------------------
-- 1. 动态日期时间 (date_translator)
-------------------------------------------------------------------------------
function date_translator(input, seg)
   if (input == "date") then
      yield(Candidate("date", seg.start, seg._end, os.date("%Y-%m-%d"), "日期"))
      yield(Candidate("date", seg.start, seg._end, os.date("%Y年%m月%d日"), "日期"))
      yield(Candidate("date", seg.start, seg._end, os.date("%m-%d-%Y"), "日期"))
      yield(Candidate("date", seg.start, seg._end, os.date("%Y/%m/%d"), "日期"))
   end
   if (input == "time") then
      yield(Candidate("time", seg.start, seg._end, os.date("%H:%M:%S"), "时间"))
      yield(Candidate("time", seg.start, seg._end, os.date("%H:%M"), "时间"))
      yield(Candidate("time", seg.start, seg._end, os.date("%Y%m%d%H%M%S"), "时间"))
   end
end


-------------------------------------------------------------------------------
-- 2. 数字大写与人民币金额转换 (number_translator)
-- 使用方式: 输入 v123 或 V123 或 vv123
-------------------------------------------------------------------------------
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

function number_translator(input, seg)
    -- 支持 v/V/vv 开头的数字 (例如 V123 或 vv123)
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


-------------------------------------------------------------------------------
-- 3. 行快简易计算器 (calculator_translator)
-- 使用方式: 输入 =1+1 或 =100*1.13
-------------------------------------------------------------------------------
function calculator_translator(input, seg)
    -- 支持 C100*1.13 或 cc100*1.13 或 =100*1.13 前缀 (C 取自 Calculator)
    local expr = nil
    if input:sub(1, 1) == "C" then
        expr = input:sub(2)
    elseif input:sub(1, 2) == "cc" or input:sub(1, 2) == "CC" then
        expr = input:sub(3)
    elseif input:sub(1, 1) == "=" then
        expr = input:sub(2)
    end

    if expr and #expr > 0 then
        -- 安全字符过滤：仅允许数字与基础计算符号
        if expr:find("^[0-9%.%+%-%*%/%(%)%s]+$") then
            local func, err = load("return " .. expr)
            if func then
                local ok, res = pcall(func)
                if ok and res ~= nil then
                    yield(Candidate("calculator", seg.start, seg._end, tostring(res), "计算结果"))
                    yield(Candidate("calculator", seg.start, seg._end, expr .. "=" .. tostring(res), "算式"))
                end
            end
        end
    end
end


-------------------------------------------------------------------------------
-- 4. 快捷帮助指令 (help_translator)
-- 使用方式: 输入 help 或 rmhelp
-------------------------------------------------------------------------------
function help_translator(input, seg)
    if input == "help" or input == "rmhelp" then
        yield(Candidate("help", seg.start, seg._end, "V123", "金额大写 (如 V12345.6)"))
        yield(Candidate("help", seg.start, seg._end, "C1+1", "简易算式计算器 (如 C100*1.13 或 cc1+1)"))
        yield(Candidate("help", seg.start, seg._end, "zhk", "z 键反查五笔拆码 (如 zhk)"))
        yield(Candidate("help", seg.start, seg._end, "date", "当前系统日期 (如 2026-07-31)"))
        yield(Candidate("help", seg.start, seg._end, "time", "当前系统时间 (如 17:29)"))
        yield(Candidate("help", seg.start, seg._end, "-=/,. ", "选词与翻页 (减/加/逗/句)"))
    end
end

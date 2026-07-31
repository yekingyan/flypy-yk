-- lua/calculator.lua - 增强型简易计算器 (支持基础运算、乘方^与取模%)

local function format_num(val)
    if type(val) ~= "number" then return tostring(val) end
    if val == math.floor(val) then
        return string.format("%d", val)
    else
        -- 消除浮点数长尾精度误差 (例如 1/3 显示 0.33333333333333 -> 保留常用精细有效数字)
        local str = string.format("%.6g", val)
        return str
    end
end

local function calculator_translator(input, seg)
    local expr = nil
    if input:sub(1, 1) == "C" then
        expr = input:sub(2)
    elseif input:sub(1, 2) == "cc" or input:sub(1, 2) == "CC" then
        expr = input:sub(3)
    elseif input:sub(1, 1) == "=" then
        expr = input:sub(2)
    end

    if expr and #expr > 0 then
        -- 安全字符过滤：仅允许数字与基础运算符、括号、乘方^、取模%
        if expr:find("^[0-9%.%+%-%*%/%(%)%s%^%%]+$") then
            local func, err = load("return " .. expr)
            if func then
                local ok, res = pcall(func)
                if ok and res ~= nil and type(res) == "number" and res == res and res ~= math.huge and res ~= -math.huge then
                    local res_str = format_num(res)
                    yield(Candidate("calculator", seg.start, seg._end, res_str, "计算结果"))
                    yield(Candidate("calculator", seg.start, seg._end, expr .. "=" .. res_str, "算式"))
                end
            end
        end
    end
end

return calculator_translator

-- lua/calculator.lua - 简易表达式计算器 (仅大写 C)

local function calculator_translator(input, seg)
    -- 仅支持大写 C 开头 (如 C100*1.13)
    local expr = nil
    if input:sub(1, 1) == "C" then
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

return calculator_translator

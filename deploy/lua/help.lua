-- lua/help.lua - 快捷帮助提示卡片

local function help_translator(input, seg)
    if input == "help" or input == "rmhelp" then
        yield(Candidate("help", seg.start, seg._end, "V123", "金额大写 (如 V12345.6)"))
        yield(Candidate("help", seg.start, seg._end, "C100*1.13", "简易算式计算器 (如 C100*1.13)"))
        yield(Candidate("help", seg.start, seg._end, "date / time", "动态日期/时间 (如 2026-07-31)"))
        yield(Candidate("help", seg.start, seg._end, "dt / iso", "快捷组合时间与 ISO 8601 标准时间戳"))
        yield(Candidate("help", seg.start, seg._end, "; /", "快捷选字 (分号第2候选 / 斜杠第3候选)"))
        yield(Candidate("help", seg.start, seg._end, "-=/,. ", "选词与翻页 (减/加/逗/句)"))
    end
end

return help_translator

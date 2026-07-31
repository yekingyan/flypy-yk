-- lua/help.lua - 快捷帮助提示卡片

local function help_translator(input, seg)
    if input == "help" or input == "rmhelp" then
        yield(Candidate("help", seg.start, seg._end, "V123", "金额大写 (如 V12345.6)"))
        yield(Candidate("help", seg.start, seg._end, "C1+1", "简易算式计算器 (如 C100*1.13 或 =1+1)"))
        yield(Candidate("help", seg.start, seg._end, "hktz", "z 键任意位置模糊通配 (如 hktz / hkzz)"))
        yield(Candidate("help", seg.start, seg._end, "date", "当前系统日期 (如 2026-07-31)"))
        yield(Candidate("help", seg.start, seg._end, "time", "当前系统时间 (如 17:29)"))
        yield(Candidate("help", seg.start, seg._end, "; /", "快捷选字 (分号第2候选 / 斜杠第3候选)"))
        yield(Candidate("help", seg.start, seg._end, "-=/,. ", "选词与翻页 (减/加/逗/句)"))
    end
end

return help_translator

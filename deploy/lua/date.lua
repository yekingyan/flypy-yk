-- lua/date.lua - 动态日期时间翻译器

local function date_translator(input, seg)
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

return date_translator

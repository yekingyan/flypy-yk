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
   if (input == "dt") then
      yield(Candidate("dt", seg.start, seg._end, os.date("%Y-%m-%d %H:%M:%S"), "日期时间"))
      yield(Candidate("dt", seg.start, seg._end, os.date("%Y-%m-%d"), "日期"))
      yield(Candidate("dt", seg.start, seg._end, os.date("%H:%M:%S"), "时间"))
      yield(Candidate("dt", seg.start, seg._end, os.date("%Y%m%d%H%M%S"), "时间戳"))
   end
   if (input == "iso") then
      yield(Candidate("iso", seg.start, seg._end, os.date("%Y-%m-%dT%H:%M:%S+08:00"), "ISO 8601 (Local)"))
      yield(Candidate("iso", seg.start, seg._end, os.date("!%Y-%m-%dT%H:%M:%SZ"), "ISO 8601 (UTC)"))
      yield(Candidate("iso", seg.start, seg._end, os.date("%Y-%m-%dT%H:%M:%S"), "ISO 8601 (Basic)"))
   end
end

return date_translator

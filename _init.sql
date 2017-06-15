
-- 文件总表
CREATE TABLE [FILES] (
  [FID] CHAR(32), 
  [FNAME] TEXT, 
  [FSIZE] INT, 
  [FPATH] TEXT, 
  [FDATE] INT, 
  [FLAG] INT, 
  CONSTRAINT [sqlite_autoindex_FILES_1] PRIMARY KEY ([FID]));

-- 文件的模板
CREATE TABLE [TEMPLATE] (
  [PID] CHAR(40), 
  [FSTART] INT, 
  [FEND] INT, 
  [HEADSIZE] INT, 
  [PTIME] INT);











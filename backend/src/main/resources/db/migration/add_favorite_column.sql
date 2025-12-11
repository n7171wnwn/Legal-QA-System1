-- 为已存在的数据库添加收藏字段
-- 如果数据库已经存在，执行此SQL来添加is_favorite字段

ALTER TABLE question_answers 
ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE COMMENT '是否收藏';

-- 为收藏字段添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_user_favorite ON question_answers(user_id, is_favorite);
















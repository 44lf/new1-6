from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `prompts` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `is_active` BOOL NOT NULL DEFAULT 0,
    `is_deleted` INT NOT NULL COMMENT '逻辑删除状态，0=正常, 1=已删除' DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `resumes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `is_deleted` INT NOT NULL COMMENT '逻辑删除状态，0=正常, 1=已删除' DEFAULT 0,
    `file_url` VARCHAR(255) NOT NULL COMMENT '简历文件URL',
    `avatar_url` VARCHAR(255) COMMENT '头像URL',
    `status` INT NOT NULL COMMENT '处理状态' DEFAULT 0,
    `name` VARCHAR(50) COMMENT '姓名',
    `phone` VARCHAR(50) COMMENT '联系电话',
    `email` VARCHAR(100) COMMENT '邮箱',
    `university` VARCHAR(100) COMMENT '毕业院校',
    `schooltier` VARCHAR(50) COMMENT '学校层次',
    `degree` VARCHAR(50) COMMENT '学历',
    `major` VARCHAR(100) COMMENT '专业',
    `graduation_time` VARCHAR(50) COMMENT '毕业时间/年份',
    `education_history` JSON COMMENT '完整教育经历列表',
    `skills` JSON COMMENT '技能标签列表，如 [\'Python\', \'Vue\']',
    `parse_result` JSON COMMENT 'AI解析结果',
    `is_qualified` BOOL NOT NULL COMMENT '是否合格' DEFAULT 0,
    `reason` LONGTEXT COMMENT 'AI判断合格/不合格的理由',
    `score` INT COMMENT 'AI判断岗位契合度分数',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `prompt_id` INT COMMENT '关联的岗位提示词',
    CONSTRAINT `fk_resumes_prompts_90fcba2e` FOREIGN KEY (`prompt_id`) REFERENCES `prompts` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `candidates` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `is_deleted` INT NOT NULL COMMENT '逻辑删除状态，0=正常, 1=已删除' DEFAULT 0,
    `score` INT COMMENT 'AI判断岗位契合度分数',
    `name` VARCHAR(50),
    `phone` VARCHAR(20),
    `email` VARCHAR(100),
    `file_url` VARCHAR(255) NOT NULL COMMENT '简历文件URL',
    `avatar_url` VARCHAR(255) COMMENT '头像URL',
    `university` VARCHAR(100) COMMENT '毕业院校',
    `schooltier` VARCHAR(50) COMMENT '学校层次',
    `degree` VARCHAR(50) COMMENT '学历',
    `major` VARCHAR(100) COMMENT '专业',
    `graduation_time` VARCHAR(50) COMMENT '毕业时间/年份',
    `education_history` JSON COMMENT '完整教育经历列表',
    `skills` JSON COMMENT '技能标签列表，如 [\'Python\', \'Vue\']',
    `work_experience` JSON COMMENT '工作经历列表',
    `project_experience` JSON COMMENT '项目经验列表',
    `parse_result` JSON COMMENT 'AI解析结果',
    `selection_time` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `prompt_id` INT COMMENT '关联的岗位提示词',
    `resume_id` INT NOT NULL,
    CONSTRAINT `fk_candidat_prompts_e296e466` FOREIGN KEY (`prompt_id`) REFERENCES `prompts` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_candidat_resumes_ba741cee` FOREIGN KEY (`resume_id`) REFERENCES `resumes` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)

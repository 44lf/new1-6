from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `prompt_id` INT COMMENT '关联的岗位提示词',
    `resume_id` INT NOT NULL,
    CONSTRAINT `fk_candidat_prompts_e296e466` FOREIGN KEY (`prompt_id`) REFERENCES `prompts` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_candidat_resumes_ba741cee` FOREIGN KEY (`resume_id`) REFERENCES `resumes` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)

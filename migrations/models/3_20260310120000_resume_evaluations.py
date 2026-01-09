from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `candidate_skills`;
        DROP TABLE IF EXISTS `candidates`;
        ALTER TABLE `resumes` DROP FOREIGN KEY `fk_resumes_prompts_90fcba2e`;
        ALTER TABLE `resumes` DROP COLUMN `prompt_id`;
        ALTER TABLE `resumes` DROP COLUMN `is_qualified`;
        ALTER TABLE `resumes` DROP COLUMN `reason`;
        ALTER TABLE `resumes` DROP COLUMN `score`;
        CREATE TABLE IF NOT EXISTS `resume_evaluations` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `score` INT COMMENT 'AI判断岗位契合度分数',
    `is_qualified` BOOL NOT NULL COMMENT '是否合格' DEFAULT 0,
    `reason` LONGTEXT COMMENT 'AI判断合格/不合格的理由',
    `evaluated_at` DATETIME(6) NOT NULL COMMENT '评估时间' DEFAULT CURRENT_TIMESTAMP(6),
    `resume_id` INT NOT NULL,
    `prompt_id` INT NOT NULL,
    UNIQUE KEY `uid_resume_evaluations_resume_id_prompt_id` (`resume_id`, `prompt_id`),
    CONSTRAINT `fk_resume_evaluations_resumes` FOREIGN KEY (`resume_id`) REFERENCES `resumes` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_resume_evaluations_prompts` FOREIGN KEY (`prompt_id`) REFERENCES `prompts` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `resume_evaluations`;
        ALTER TABLE `resumes` ADD COLUMN `score` INT COMMENT 'AI判断岗位契合度分数';
        ALTER TABLE `resumes` ADD COLUMN `reason` LONGTEXT COMMENT 'AI判断合格/不合格的理由';
        ALTER TABLE `resumes` ADD COLUMN `is_qualified` BOOL NOT NULL COMMENT '是否合格' DEFAULT 0;
        ALTER TABLE `resumes` ADD COLUMN `prompt_id` INT COMMENT '关联的岗位提示词';
        ALTER TABLE `resumes` ADD CONSTRAINT `fk_resumes_prompts_90fcba2e` FOREIGN KEY (`prompt_id`) REFERENCES `prompts` (`id`) ON DELETE CASCADE;
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
    `skills` JSON COMMENT '技能标签列表，如 ['Python', 'Vue']',
    `work_experience` JSON COMMENT '工作经历列表',
    `project_experience` JSON COMMENT '项目经验列表',
    `parse_result` JSON COMMENT 'AI解析结果',
    `selection_time` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `prompt_id` INT COMMENT '关联的岗位提示词',
    `resume_id` INT NOT NULL,
    CONSTRAINT `fk_candidat_prompts_e296e466` FOREIGN KEY (`prompt_id`) REFERENCES `prompts` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_candidat_resumes_ba741cee` FOREIGN KEY (`resume_id`) REFERENCES `resumes` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `candidate_skills` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `candidate_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    UNIQUE KEY `uid_candidate_skills_candidate_id_skill_id` (`candidate_id`, `skill_id`),
    CONSTRAINT `fk_candidate_skills_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_candidate_skills_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


MODELS_STATE = ""

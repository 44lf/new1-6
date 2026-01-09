from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `skills` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL UNIQUE COMMENT '技能名称',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `candidate_skills` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `candidate_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    UNIQUE KEY `uid_candidate_skills_candidate_id_skill_id` (`candidate_id`, `skill_id`),
    CONSTRAINT `fk_candidate_skills_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `candidates` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_candidate_skills_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `resume_skills` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `resume_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    UNIQUE KEY `uid_resume_skills_resume_id_skill_id` (`resume_id`, `skill_id`),
    CONSTRAINT `fk_resume_skills_resume` FOREIGN KEY (`resume_id`) REFERENCES `resumes` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_resume_skills_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `resume_skills`;
        DROP TABLE IF EXISTS `candidate_skills`;
        DROP TABLE IF EXISTS `skills`;"""


MODELS_STATE = ""

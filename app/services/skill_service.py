from app.db.skill_table import Skill
from app.utils.skill_utils import normalize_skills_lower


class SkillService:
    @staticmethod
    async def get_or_create_skills(skills: list[str]) -> list[Skill]:
        normalized = normalize_skills_lower(skills)
        if not normalized:
            return []

        existing_skills = await Skill.filter(name__in=normalized)
        existing_by_name = {skill.name: skill for skill in existing_skills}
        missing = [name for name in normalized if name not in existing_by_name]

        if missing:
            await Skill.bulk_create(
                [Skill(name=name) for name in missing],
                ignore_conflicts=True,
            )
            existing_skills = await Skill.filter(name__in=normalized)

        return existing_skills

    @staticmethod
    async def backfill_skill_tags() -> None:
        from app.db.resume_table import Resume

        resumes = await Resume.all()
        for resume in resumes:
            resume_skills = await SkillService.get_or_create_skills(resume.skills or [])
            await resume.skill_tags.clear()
            if resume_skills:
                await resume.skill_tags.add(*resume_skills)

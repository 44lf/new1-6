from app.db.skill_table import Skill
from app.utils.helpers import normalize_skills


class SkillService:
    @staticmethod
    async def get_or_create_skills(skills: list[str]) -> list[Skill]:
        normalized = normalize_skills(skills)
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

from app.db.candidate_table import Candidate

class CandidateService:
    @staticmethod
    async def get_all_candidates():
        return await Candidate.all().order_by("-created_at")

    @staticmethod
    async def update_candidate_info(candidate_id: int, update_data: dict):
        candidate = await Candidate.get_or_none(id=candidate_id)
        if candidate:
            await candidate.update_from_dict(update_data)
            await candidate.save()
            return candidate
        return None
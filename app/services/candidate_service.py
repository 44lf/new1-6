from app.db.candidate_table import Candidate

class CandidateService:
    @staticmethod
    async def get_all_candidates(prompt_id: int = None):
        """
        获取候选人列表
        :param prompt_id: 如果提供了 prompt_id，则只返回该岗位下的候选人
        """
        # 关联查询 resume，以便访问 resume.prompt_id
        query = Candidate.all().prefetch_related("resume")

        if prompt_id:
            # 筛选：候选人 -> 简历 -> 提示词ID
            query = query.filter(resume__prompt_id=prompt_id)

        return await query.order_by("-created_at")

    @staticmethod
    async def update_candidate_info(candidate_id: int, update_data: dict):
        candidate = await Candidate.get_or_none(id=candidate_id)
        if candidate:
            await candidate.update_from_dict(update_data)
            await candidate.save()
            return candidate
        return None
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BasePromptProvider(ABC):
    """提示词提供者的抽象基类"""

    @abstractmethod
    def build_messages(self, criteria_content: str, resume_content: str) -> List[dict]:
        """构建发送给 LLM 的消息列表"""
        pass

    @abstractmethod
    def get_json_structure(self) -> Dict[str, Any]:
        """获取期望的 JSON 输出结构"""
        pass
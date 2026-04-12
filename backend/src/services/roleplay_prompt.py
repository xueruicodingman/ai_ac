import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RolePlayPromptBuilder:
    def __init__(self):
        pass
    
    def build(
        self,
        role_info: Dict[str, Any],
        context_chunks: List[Dict],
        conversation_history: List[Dict],
        latest_message: str
    ) -> str:
        """构建4部分动态Prompt"""
        
        prompt_parts = []
        
        part1 = self._build_role_section(role_info)
        prompt_parts.append(part1)
        
        part2 = self._build_context_section(context_chunks)
        prompt_parts.append(part2)
        
        part3 = self._build_history_section(conversation_history)
        prompt_parts.append(part3)
        
        part4 = self._build_latest_section(latest_message)
        prompt_parts.append(part4)
        
        return "\n\n".join(prompt_parts)
    
    def _build_role_section(self, role_info: Dict) -> str:
        """构建角色定义部分"""
        return f"""[角色定义]
你扮演{role_info.get('subordinate_name', '下级角色')}，
角色背景：{role_info.get('background', '')}
性格特点：{role_info.get('personality', '')}
立场：{role_info.get('position', '')}"""
    
    def _build_context_section(self, chunks: List[Dict]) -> str:
        """构建话题上下文部分"""
        if not chunks:
            return "[话题上下文]\n当前无相关上下文"
        
        contexts = []
        for i, chunk in enumerate(chunks, 1):
            ctx = chunk.get('chunk', {})
            contexts.append(f"相关背景{i}：{ctx.get('content', '')[:200]}")
        
        topics = set()
        for c in chunks:
            topics.add(c.get('chunk', {}).get('chunk_type', ''))
        
        return f"""[话题上下文]
当前话题：{', '.join(topics)}
{chr(10).join(contexts)}"""
    
    def _build_history_section(self, history: List[Dict]) -> str:
        """构建对话历史部分（最近5轮=10条消息）"""
        if not history:
            return "[对话历史]\n暂无对话历史"
        
        recent = history[-10:]
        lines = ["[对话历史]"]
        
        for msg in recent:
            role = "你" if msg.get('role') == 'ai' else "用户"
            content = msg.get('content', '')
            lines.append(f"{role}：{content[:200]}")
        
        return "\n".join(lines)
    
    def _build_latest_section(self, message: str) -> str:
        """构建用户最新答复部分"""
        return f"""[用户最新答复]
用户：{message}"""
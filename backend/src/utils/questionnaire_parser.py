import json
from typing import Dict, Any, Optional

def parse_questionnaire_content(content: str) -> Dict[str, Any]:
    """解析题本内容，支持JSON和旧格式"""
    if not content:
        return {}
    
    # 如果已经是字典，直接返回
    if isinstance(content, dict):
        return content
    
    # 尝试解析为统一JSON格式
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "meta" in parsed and "content" in parsed:
            # 新格式：返回content部分
            return parsed.get("content", parsed)
        elif isinstance(parsed, dict):
            # 可能是旧格式或其他格式
            return parsed
    except json.JSONDecodeError:
        pass
    
    # 如果不是JSON，可能是旧文本格式
    # 包装为兼容格式
    return {"raw_content": content}


def get_tool_id_from_content(content: str) -> str:
    """从题本内容推断工具类型"""
    parsed = parse_questionnaire_content(content)
    
    # 如果是新格式，从meta获取
    if "meta" in parsed:
        return parsed.get("meta", {}).get("tool_id", "unknown")
    
    # 旧格式推断逻辑
    if "competencies" in parsed:
        return "beh"
    if "role_play_content" in parsed or "role_info" in parsed:
        return "roleplay"
    if "discussion_topic" in parsed:
        return "lgd"
    if "materials" in parsed:
        return "case"
    if "vision_prompt" in parsed:
        return "vision"
    
    return "unknown"
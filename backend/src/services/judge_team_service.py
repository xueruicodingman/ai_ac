import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.models.judge_team import JudgeTeam
from src.config import settings

EVALUATION_STYLES = [
    "宽松型打分",
    "严格型打分"
]

EXPERTISE_AREAS = [
    "研发设计",
    "产品规划",
    "市场营销",
    "销售服务",
    "供应链采购",
    "智能制造",
    "质量管理",
    "人力资源",
    "财务管理",
    "战略运营"
]

class JudgeTeamService:
    def __init__(self, db: AsyncSession, user_id: int, api_key: str = None, api_url: str = None, model: str = None):
        self.db = db
        self.user_id = user_id
        self.api_key = api_key or settings.API_KEY
        self.api_url = api_url or settings.DEFAULT_API_URL
        self.model = model or settings.DEFAULT_MODEL
    
    async def get_judge_teams(self) -> Dict[str, Any]:
        result = await self.db.execute(
            select(JudgeTeam).where(JudgeTeam.user_id == self.user_id)
        )
        teams = result.scalars().all()
        return {team.tool: json.loads(team.judges) for team in teams}
    
    async def get_judge_team(self, tool: str) -> Optional[List[Dict]]:
        result = await self.db.execute(
            select(JudgeTeam).where(
                and_(JudgeTeam.user_id == self.user_id, JudgeTeam.tool == tool)
            )
        )
        team = result.scalar_one_or_none()
        if team:
            return json.loads(team.judges)
        return None
    
    async def get_judges(self) -> Optional[List[Dict]]:
        result = await self.db.execute(
            select(JudgeTeam).where(JudgeTeam.user_id == self.user_id, JudgeTeam.tool == "default")
        )
        team = result.scalar_one_or_none()
        if team:
            return json.loads(team.judges)
        return None
    
    async def save_judge_team(self, tool: str, judges: List[Dict]) -> Dict:
        result = await self.db.execute(
            select(JudgeTeam).where(
                and_(JudgeTeam.user_id == self.user_id, JudgeTeam.tool == tool)
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.judges = json.dumps(judges)
        else:
            new_team = JudgeTeam(
                user_id=self.user_id,
                tool=tool,
                judges=json.dumps(judges)
            )
            self.db.add(new_team)
        
        await self.db.commit()
        return {"tool": tool, "judges": judges}
    
    async def save_judges(self, judges: List[Dict]) -> Dict:
        result = await self.db.execute(
            select(JudgeTeam).where(JudgeTeam.user_id == self.user_id, JudgeTeam.tool == "default")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.judges = json.dumps(judges)
        else:
            new_team = JudgeTeam(
                user_id=self.user_id,
                tool="default",
                judges=json.dumps(judges)
            )
            self.db.add(new_team)
        
        await self.db.commit()
        return {"judges": judges}
    
    async def generate_judges(self, count: int = 3) -> List[Dict]:
        import random
        available_styles = random.sample(EVALUATION_STYLES, min(count, len(EVALUATION_STYLES)))
        available_expertise = random.sample(EXPERTISE_AREAS, min(count, len(EXPERTISE_AREAS)))
        
        prompt = f"""你是一个AC测评的评委组设计专家。请设计{count}个评委的角色，这些评委将参与对新能源汽车部门候选人的综合评估。

请设计{count}个评委，每个评委需要包含：
1. 角色名称（如：研发总监、产品专家、营销精英等）
2. 个性描述（该评委的性格特点，如：严谨务实、善于提问、关注细节等）
3. 用人偏好（该评委看重候选人的哪些特质）
4. 评价风格（从以下选择确保不重复：{', '.join(available_styles)}）
5. 专长领域（从以下选择确保不重复：{', '.join(available_expertise)}）
6. 具体任务描述（该评委在测评中的职责，如：负责考察候选人的项目管理能力、沟通协调能力等）

输出JSON格式的数组：
[{{"role": "评委1", "personality": "性格描述", "hiring_preference": "用人偏好", "evaluation_style": "宽松型打分", "expertise_area": "研发设计", "task": "任务描述"}}, ...]"""

        import requests
        api_url = self.api_url.rstrip('/')
        if not api_url.endswith('/chat/completions'):
            api_url = f"{api_url}/chat/completions"
        
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
            timeout=120
        )
        
        if response.status_code != 200:
            raise ValueError(f"LLM调用失败: {response.status_code}")
        
        content = response.json()["choices"][0]["message"]["content"]
        
        try:
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                judges = json.loads(match.group())
            else:
                judges = json.loads(content)
            
            for i, judge in enumerate(judges):
                judge["evaluation_style"] = available_styles[i] if i < len(available_styles) else available_styles[0]
                judge["expertise_area"] = available_expertise[i] if i < len(available_expertise) else available_expertise[0]
            
            return judges
        except Exception as e:
            raise ValueError(f"LLM返回内容解析失败: {str(e)}")
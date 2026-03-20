from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

class AIService(ABC):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=0.7
        )
    
    @abstractmethod
    async def generate(self, **kwargs) -> Dict[str, Any]:
        pass
    
    def create_prompt(self, system: str, human: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system),
            HumanMessage(content=human)
        ])
    
    async def call_llm(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        chain = prompt | self.llm
        response = await chain.ainvoke(kwargs)
        return response.content

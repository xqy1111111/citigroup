from typing import List, Dict, Any
import requests
from ..models.chat import Message

class AIService:
    def __init__(self):
        self.url = "https://api.siliconflow.cn/v1/chat/completions"
        self.headers = {
            "Authorization": "Bearer sk-bimctbwxwihkdzuiqrdughgjokmqwlnsunaauushiqyuprav",
            "Content-Type": "application/json"
        }
        self.default_model = "Qwen/Qwen2.5-72B-Instruct-128K"

    async def get_ai_response(self, messages: List[Message]) -> str:
        """
        获取AI的回复
        
        Args:
            messages: 消息历史列表
            
        Returns:
            str: AI的回复文本
        """
        formatted_messages = [
            {
                "role": "user" if msg.sayer == "user" else "assistant",
                "content": msg.text
            }
            for msg in messages
        ]

        payload = {
            "model": self.default_model,
            "messages": formatted_messages
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()  # 检查响应状态
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"调用AI API时发生错误: {str(e)}")

    async def chat(self, user_message: str) -> str:
        """
        单次对话接口
        
        Args:
            user_message: 用户的消息
            
        Returns:
            str: AI的回复
        """
        messages = [Message(sayer="user", text=user_message)]
        return await self.get_ai_response(messages) 
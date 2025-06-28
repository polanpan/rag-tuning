# backend/app/services/llm_service.py
import logging
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model_type = getattr(settings, 'LLM_MODEL_TYPE', 'deepseek')
        self.model_name = getattr(settings, 'LLM_MODEL_NAME', 'deepseek-chat')
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        self.base_url = getattr(settings, 'LLM_BASE_URL', 'https://api.deepseek.com')
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        
    async def generate_answer(self, question: str, context: str, temperature: float = 0.7) -> str:
        try:
            if self.model_type == 'deepseek':
                return await self._call_deepseek(question, context, temperature)
            elif self.model_type == 'ollama':
                return await self._call_ollama(question, context, temperature)
            else:
                return self._generate_fallback_answer(question, context)
        except Exception as e:
            logger.error(f"生成答案失败: {str(e)}")
            return self._generate_fallback_answer(question, context)
    
    async def _call_deepseek(self, question: str, context: str, temperature: float) -> str:
        if not self.api_key:
            logger.warning("DeepSeek API密钥未配置，使用fallback答案")
            return self._generate_fallback_answer(question, context)
        
        prompt = self._build_prompt(question, context)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model_name,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'max_tokens': 1000,
            'stream': False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result['choices'][0]['message']['content']
                        logger.info("DeepSeek API调用成功")
                        return answer.strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API调用失败: {response.status}, {error_text}")
                        return self._generate_fallback_answer(question, context)
        except Exception as e:
            logger.error(f"DeepSeek API调用异常: {str(e)}")
            return self._generate_fallback_answer(question, context)
    
    async def _call_ollama(self, question: str, context: str, temperature: float) -> str:
        prompt = self._build_prompt(question, context)
        
        payload = {
            'model': self.model_name,
            'prompt': prompt,
            'temperature': temperature,
            'stream': False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        answer = result.get('response', '')
                        logger.info("Ollama模型调用成功")
                        return answer.strip()
                    else:
                        return self._generate_fallback_answer(question, context)
        except Exception as e:
            logger.error(f"Ollama调用异常: {str(e)}")
            return self._generate_fallback_answer(question, context)
    
    def _build_prompt(self, question: str, context: str) -> str:
        return f"""请基于以下上下文信息回答用户的问题。如果上下文中没有相关信息，请诚实地说明无法从提供的信息中找到答案。

上下文信息：
{context}

用户问题：{question}

请提供准确、有用的回答："""
    
    def _generate_fallback_answer(self, question: str, context: str) -> str:
        if not context.strip():
            return "很抱歉，我在知识库中没有找到与您问题相关的信息。"
        
        sentences = context.split('。')
        question_words = set(question.replace('？', '').replace('?', '').split())
        
        for sentence in sentences[:3]:
            sentence = sentence.strip()
            if sentence and any(word in sentence for word in question_words if len(word) > 1):
                return f"根据知识库内容，{sentence}。"
        
        return f"根据知识库内容：{context[:200]}{'...' if len(context) > 200 else ''}"
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            if self.model_type == 'deepseek':
                if not self.api_key:
                    return {"status": "error", "message": "DeepSeek API密钥未配置"}
                return {"status": "ok", "model_type": "deepseek", "model_name": self.model_name}
            elif self.model_type == 'ollama':
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.ollama_url}/api/tags",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            return {"status": "ok", "model_type": "ollama", "url": self.ollama_url}
                        else:
                            return {"status": "error", "message": f"Ollama服务不可用: {response.status}"}
            return {"status": "ok", "model_type": self.model_type}
        except Exception as e:
            return {"status": "error", "message": str(e)}

from typing import List, Optional, Dict, Any
import aisuite as ai
from .base import LLMClientProtocol
from src.config import settings

def create_openai_client(api_key: str) -> LLMClientProtocol:
    """
    建立 OpenAI 客戶端。

    Args:
        api_key: OpenAI API 金鑰

    Returns:
        符合 LLMClientProtocol 的客戶端
    """
    client = ai.Client()
    class OpenAIClientImpl:
        def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model: str = f"openai:{settings.OPENAI_MODEL}",
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs: Any
        ) -> Dict[str, Any]:
            """
            使用 OpenAI 的 Chat API 執行對話完成。
            """
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                return {
                    "content": response.choices[0].message.content,
                    "role": response.choices[0].message.role,
                    "finish_reason": response.choices[0].finish_reason,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            except Exception as e:
                  raise Exception(f"OpenAI 請求失敗: {str(e)}")
        
        def embeddings(self, input: List[str], model: str = "text-embedding-ada-002") -> List[float]:
            """
            使用 OpenAI 的 Embeddings API 生成文本嵌入。
            """
            response = client.embeddings.create(input=input, model=model)
            return response.data[0].embedding

    return OpenAIClientImpl()

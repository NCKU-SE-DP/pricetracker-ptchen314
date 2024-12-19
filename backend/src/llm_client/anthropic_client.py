from typing import List, Optional, Dict, Any
import aisuite as ai
from .base import LLMClientProtocol
from src.config import settings


def create_anthropic_client(api_key: str) -> LLMClientProtocol:
    """
    建立 anthropic 客戶端。

    Args:
        api_key: anthropic API 金鑰

    Returns:
        符合 LLMClientProtocol 的客戶端
    """
    client = ai.Client()
    class AnthropicClientImpl:
        def chat_completion(
            self,
            messages: List[Dict[str, str]],
            model: str = f"anthropic:{settings.ANTHROPIC_MODEL}",
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs: Any
        ) -> Dict[str, Any]:
            """
            使用 anthropic 的 Chat API 執行對話完成。
            """
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    **kwargs
                )
                return {
                    "content": response.choices[0].message.content,
                }
            except Exception as e:
                raise Exception(f"Anthropic 請求失敗: {str(e)}")

    return AnthropicClientImpl()


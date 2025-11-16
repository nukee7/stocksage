# backend/langchain_core/utils/groq_llm.py
from typing import Optional, List, Mapping, Any
import os
import groq
from pydantic import PrivateAttr
from langchain.llms.base import LLM

class GroqLLM(LLM):
    """
    LangChain LLM wrapper for Groq chat completion API.

    Default model: llama-3.1-8b-instant (small, production).
    Alternative recommended replacement: llama-3.3-70b-versatile (larger).
    """
    model: str = "llama-3.1-8b-instant"   # <-- default small supported model
    temperature: float = 0.6

    client: Any = PrivateAttr()

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, temperature: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)

        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set and no api_key provided.")

        # create Groq client
        self.client = groq.Groq(api_key=api_key)

        if model:
            self.model = model
        if temperature is not None:
            self.temperature = temperature

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
        except groq.BadRequestError as e:
            # detect deprecated model error and raise a friendly message
            # the SDK's error body contains a JSON with 'code' or 'message'
            err_text = getattr(e, "response", None) or str(e)
            if "decommissioned" in str(err_text) or "model_decommissioned" in str(err_text):
                raise RuntimeError(
                    f"Model '{self.model}' is decommissioned. "
                    "Switch to a supported model such as 'llama-3.1-8b-instant' or 'llama-3.3-70b-versatile'."
                ) from e
            raise

        # normal extraction (sdk often provides resp.choices[0].message["content"])
        try:
            return resp.choices[0].message["content"]
        except Exception:
            try:
                return resp["choices"][0]["message"]["content"]
            except Exception:
                return str(resp)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model": self.model, "temperature": self.temperature}

    @property
    def _llm_type(self) -> str:
        return "groq"
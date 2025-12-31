"""
LLM configuration and utilities
"""
import os
from langchain_openai import ChatOpenAI
from src.config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE


def load_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    """Initialize OpenAI LLM"""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )


def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call LLM with prompt and return response"""
    llm = load_llm(model=model)
    response = llm.invoke(prompt)
    return response.content.strip()
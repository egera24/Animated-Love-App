from pydantic import BaseModel, Field


class BubbleLLMResponse(BaseModel):
    bubble_text: str = Field(min_length=1, max_length=2000)
    mood: str = Field(default="idle")
    language: str = Field(default="hu")

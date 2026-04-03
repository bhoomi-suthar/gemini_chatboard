from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's message")


class ChatResponse(BaseModel):
    response: str

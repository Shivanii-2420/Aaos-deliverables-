from pydantic import BaseModel


class LLMResponse(BaseModel):

    provider: str

    model: str

    content: str

    success: bool
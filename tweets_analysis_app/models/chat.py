from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    messages: List[Message]
    context: Optional[dict] = {}

class Choice(BaseModel):
    delta: Optional[dict] = None
    message: Optional[Message] = None
    context: Optional[dict] = None
    index: int = 0
    finish_reason: Optional[str] = None

class ChatResponse(BaseModel):
    object: str = "chat.completion"
    choices: List[Choice]
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class TimelineEvent(BaseModel):
    id: int
    type: str # 'note', 'admission', 'medication', 'procedure', 'document', 'task'
    title: str
    description: Optional[str] = None
    timestamp: datetime
    author: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Any] = None

    class Config:
        from_attributes = True

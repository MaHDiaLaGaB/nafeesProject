from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class ScanResultOut(BaseModel):
    id: UUID
    image_url: str
    prediction: str
    created_at: datetime

    class ConfigDict:
        from_attributes = True
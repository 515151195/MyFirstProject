from pydantic import BaseModel, ConfigDict

class NotificationOut(BaseModel):
    id: int
    user_id: str
    title: str
    content: str
    is_read: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)
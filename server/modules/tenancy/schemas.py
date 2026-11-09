from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Workspace(BaseModel):
    id: UUID
    name: str
    slug: str
    updated_at: datetime
    created_at: datetime

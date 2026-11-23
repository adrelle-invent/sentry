import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from modules.tenancy.models import UserRole

# ==========================================
# WORKSPACE SCHEMAS
# ==========================================


class WorkspaceBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=36)


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    slug: str | None = Field(None, max_length=36)


class WorkspaceResponse(WorkspaceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==========================================
# USER ACCOUNT SCHEMAS
# ==========================================


class UserAccountBase(BaseModel):
    provider: str = Field(..., max_length=50)
    provider_account_id: str = Field(..., max_length=255)
    access_token: str = Field(..., max_length=2048)
    refresh_token: str = Field(..., max_length=2048)
    expires_at: datetime


class UserAccountCreate(UserAccountBase):
    user_id: uuid.UUID


class UserAccountResponse(UserAccountBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==========================================
# USER SCHEMAS
# ==========================================


class UserBase(BaseModel):
    workspace_id: uuid.UUID
    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    avatar_url: str = Field(..., max_length=512)
    role: UserRole = UserRole.member
    is_active: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)


class UserUpdate(BaseModel):
    workspace_id: uuid.UUID | None = None
    email: EmailStr | None = None
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=512)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=8, max_length=255)


class UserResponse(UserBase):
    id: uuid.UUID
    email_verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

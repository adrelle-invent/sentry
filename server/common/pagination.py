from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(0, ge=0)
    size: int = Field(100, ge=1, le=100)


class PaginatedResponse[T](PaginationParams):
    items: list[T]
    total: int = Field(
        ..., description="Total number of records matching criteria"
    )
    has_more: bool

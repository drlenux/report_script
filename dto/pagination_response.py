from pydantic import BaseModel


class PaginationResponse(BaseModel):
    total: int
    total_page: int
    current_page: int
    prev_page: int
    next_page: int
    items: list
    search: dict[str, str] = {}

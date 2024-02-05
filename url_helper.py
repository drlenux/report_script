from dto.pagination_response import PaginationResponse
from urllib.parse import urlencode


def generate_url(res: PaginationResponse, base_url: str, attr: dict[str, str]) -> str:
    params = {**attr, **res.search}
    query_string = urlencode(params)

    if not base_url.endswith('?') and not base_url.endswith('&'):
        base_url += '?'

    return base_url + query_string

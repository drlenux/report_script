from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Query
from starlette.responses import StreamingResponse, HTMLResponse

from load_yaml import load_yaml
from db_connect import connect_to_mysql, pagination, PaginationResponse
from json_to_csv import json_to_csv
from fastapi.templating import Jinja2Templates
from url_helper import generate_url

app = FastAPI()
templates = Jinja2Templates(directory="templates")
conf = load_yaml('./conf/main.yaml')


@app.get("/")
async def root(request: Request):
    data = []
    for key, val in conf['reporting'].items():
        tmp: dict[str, any] = {}
        tmp['description'] = val['description']
        tmp['name'] = key

        tmp['params'] = val.get('params', [])

        data.append(tmp)

    return templates.TemplateResponse("list.html", {
        "request": request,
        "data": data,
    })


@app.get("/api/report/{name}")
async def api_report(
        request: Request,
        name: str,
        page: Annotated[int, Query(alias='page')] = 1,
        limit: Annotated[int, Query(alias='limit')] = 100
) -> PaginationResponse:
    if name not in conf['reporting']:
        raise HTTPException(status_code=404, detail="Report not found")

    report_conf = conf['reporting'][name]
    with open(f"./conf/{report_conf['sql']}", 'r', encoding='utf-8') as sql_file:
        sql = sql_file.read()

    expected_params = report_conf.get('params', [])
    actual_params = {}

    for param in expected_params:
        if param in request.query_params:
            actual_params[param] = request.query_params[param]

    db = connect_to_mysql(**conf["connect"])
    try:
        results = pagination(connection=db, query=sql, params=actual_params, page=page, limit=limit)
        results.search = actual_params
    finally:
        db.close()

    return results


@app.get("/csv/report/{name}", response_class=StreamingResponse)
async def csv_report(request: Request, name: str):
    results = await api_report(request, name, page=1, limit=0)
    return json_to_csv(results.items)


@app.get("/web/report/{name}", response_class=HTMLResponse)
async def web_report(
        request: Request,
        name: str,
        page: Annotated[int, Query(alias='page')] = 1,
        limit: Annotated[int, Query(alias='limit')] = 100
):
    data = await api_report(request=request, name=name, page=page, limit=limit)
    if data == 404:
        return "Report not found", 404

    report_conf = conf['reporting'][name]
    columns = data.items[0].keys() if data else []
    return templates.TemplateResponse("report.html", {
        "request": request,
        "data": data,
        "columns": columns,
        "name": name,
        "description": report_conf["description"],
        "limit": limit,
        "url_prev": generate_url(res=data, base_url=f"/web/report/{{ name }}/", attr={"page": str(data.prev_page)}),
        "url_next": generate_url(res=data, base_url=f"/web/report/{{ name }}/", attr={"page": str(data.next_page)}),
        "pages": get_pages_list(res=data, name=name)
    })


def get_pages_list(res: PaginationResponse, name: str) -> dict[str, str]:
    urls = {}
    base_url = f"/web/report/{name}/"

    # Always include the first page
    urls["1"] = generate_url(res=res, base_url=base_url, attr={"page": "1"})

    # Determine the range of pages to include based on current_page and total_page
    if res.total_page <= 3:
        # If total pages are 3 or less, include all
        page_range = range(1, res.total_page + 1)
    elif res.current_page == 1:
        # If on the first page, include the first three pages
        page_range = range(1, 4)
    elif res.current_page == res.total_page:
        # If on the last page, include the last three pages
        page_range = range(res.total_page - 2, res.total_page + 1)
    else:
        # If in the middle, include the previous, current, and next page
        page_range = range(max(1, res.current_page - 1), min(res.current_page + 2, res.total_page + 1))

    # Generate URLs for the determined range of pages
    for page in page_range:
        urls[str(page)] = generate_url(res=res, base_url=base_url, attr={"page": str(page)})

    # Always include the last page if there are more than 3 pages
    if res.total_page > 3:
        urls[str(res.total_page)] = generate_url(res=res, base_url=base_url, attr={"page": str(res.total_page)})

    return urls


uvicorn.run(app, host="0.0.0.0", port=8000)

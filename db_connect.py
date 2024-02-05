import math

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from dto.pagination_response import PaginationResponse


def connect_to_mysql(host: str, db_name: str, port: int, user: str, password: str) -> MySQLConnectionAbstract:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        port=port
    )
    return connection


def execute_query(connection, query: str, params: dict = None, page: int = 1, limit: int = 0) -> list:
    cursor = connection.cursor(dictionary=True)

    prepared_query = query
    prepared_params = []
    if limit:
        offset = limit * (page - 1)
        prepared_query = prepared_query.replace("{{limit}}", f"LIMIT {limit} OFFSET {offset}")
    else:
        prepared_query = prepared_query.replace("{{limit}}", "")

    if params:
        for key, value in params.items():
            prepared_query = prepared_query.replace(f":{key}", "%s")
            prepared_params.append(value)

    cursor.execute(prepared_query, prepared_params)
    results = cursor.fetchall()
    cursor.close()

    return results


def count(connection, query: str, params: dict = None) -> int:
    cursor = connection.cursor(dictionary=True)

    prepared_query = query
    prepared_params = []
    prepared_query = prepared_query.replace("{{limit}}", "")
    if params:
        for key, value in params.items():
            prepared_query = prepared_query.replace(f":{key}", "%s")
            prepared_params.append(value)

    cursor.execute(f"select count(*) as cnt from ({prepared_query}) as t", prepared_params)
    result = cursor.fetchone()
    cursor.close()
    return result["cnt"]


def pagination(connection, query: str, params: dict = None, page: int = 1, limit: int = 0) -> PaginationResponse:
    items = execute_query(connection=connection, query=query, params=params, page=page, limit=limit)

    if limit:
        total_items = count(connection=connection, query=query, params=params)
        total_page = math.ceil(total_items / limit)
    else:
        total_items = len(items)
        total_page = 1

    if page > 1:
        prev_page = page - 1
    else:
        prev_page = 1

    if page < total_page:
        next_page = page + 1
    else:
        next_page = total_page

    return PaginationResponse(
        total=total_items,
        total_page=total_page,
        current_page=page,
        prev_page=prev_page,
        next_page=next_page,
        items=items
    )

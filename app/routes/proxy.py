import os
from fastapi import APIRouter, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
import requests

router = APIRouter()

TARGET = os.getenv("MODULAR_PROXY_TARGET", "http://127.0.0.1:8004")


async def _forward(method: str, path: str, request: Request) -> Response:
    url = f"{TARGET}{path}"
    headers = {}
    # Forward selected headers
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    content_type = request.headers.get("content-type")
    if content_type:
        headers["Content-Type"] = content_type

    params = dict(request.query_params)
    data = await request.body()

    def _do_request():
        return requests.request(
            method=method,
            url=url,
            params=params if method.upper() == "GET" else None,
            data=data if method.upper() != "GET" else None,
            headers=headers,
            timeout=15,
        )

    try:
        resp = await run_in_threadpool(_do_request)
        media_type = resp.headers.get("content-type", "application/json")
        return Response(content=resp.content, status_code=resp.status_code, media_type=media_type)
    except requests.exceptions.RequestException:
        return Response(content=b'{"error":"upstream unavailable"}', status_code=502, media_type="application/json")


@router.post("/api/login")
async def proxy_login(request: Request):
    return await _forward("POST", "/api/login", request)


@router.get("/api/leads")
async def proxy_get_leads(request: Request):
    return await _forward("GET", "/api/leads", request)


@router.post("/api/leads")
async def proxy_post_lead(request: Request):
    return await _forward("POST", "/api/leads", request)


@router.get("/api/properties")
async def proxy_get_properties(request: Request):
    return await _forward("GET", "/api/properties", request)


@router.post("/api/properties")
async def proxy_post_property(request: Request):
    return await _forward("POST", "/api/properties", request)

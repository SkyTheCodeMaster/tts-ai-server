from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp.web import middleware

if TYPE_CHECKING:
  from aiohttp.web import Request
  from asyncpg import Connection

@middleware
async def pg_pool_middleware(request: Request, handler):
  async with request.app.pool.acquire() as conn:
    conn: Connection
    request.conn: Connection = conn
    request.pool = request.app.pool
    request.session = request.app.cs
    request.upc = request.app.upc
    request.LOG = request.app.LOG
    resp = await handler(request)
    return resp
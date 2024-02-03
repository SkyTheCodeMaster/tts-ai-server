from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp.web import middleware

if TYPE_CHECKING:
  from aiohttp.web import Request

@middleware
async def pg_pool_middleware(request: Request, handler):
  request.session = request.app.cs
  request.LOG = request.app.LOG
  resp = await handler(request)
  return resp
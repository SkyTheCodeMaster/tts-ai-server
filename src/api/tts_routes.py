from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response

from utils.generate_tts import models, generate, DEFAULT_MODEL

if TYPE_CHECKING:
  from utils.extra_request import Request

routes = web.RouteTableDef()

@routes.post("/ai/generate/")
async def post_ai_generate(request: Request) -> Response:
  body = await request.json()

  text = body.get("text",None)
  if not text:
    return Response(status=400,text="Must pass text!")
  voice = body.get("voice", DEFAULT_MODEL)

  if voice not in models:
    return Response(status=400,text="Passed voice not in list of models! Use GET /ai/models/ endpoint for voice list.")

  wav_bytes = await generate(text, voice)

  return Response(body=wav_bytes, status=200, content_type="audio/x-wav")

@routes.get("/ai/models/")
async def get_ai_models(request: Request) -> Response:
  return web.json_response(models)

def setup() -> web.RouteTableDef:
  return routes
from __future__ import annotations

import asyncio
from io import BytesIO
from typing import TYPE_CHECKING

from aiohttp import web
import numpy as np
from TTS.api import TTS # type: ignore
import scipy # type: ignore

if TYPE_CHECKING:
  from aiohttp.web import Request, Response

routes = web.RouteTableDef()

models: list[str] = TTS.list_models()
DEFAULT_MODEL = models[0]

cached_tts: dict[str,TTS] = {}

def _generate(text: str, model_name: str) -> tuple[bytes, int]:
  if model_name not in cached_tts:
    cached_tts[model_name] = TTS(model_name)
  tts = cached_tts[model_name]
  if text[-1] != ".": text += "."
  wav = tts.tts(text, speaker=tts.speakers[0], language=tts.languages[0]) # type: ignore
  return wav, tts.synthesizer.output_sample_rate # type: ignore

async def generate_text(text: str, model_name: str) -> tuple[bytes, int]:
  loop = asyncio.get_running_loop()
  r1,r2 = await loop.run_in_executor(None, lambda: _generate(text,model_name))
  return r1,r2

@routes.get("/voices")
async def get_voices(request: Request) -> Response:
  return web.json_response(models)

@routes.post("/tts")
async def post_tts(request: Request) -> Response:
  body = await request.json()
  voice = body.get("voice",DEFAULT_MODEL)
  text = body["text"]
  wav, rate = await generate_text(text,voice)
  nparr = np.array(wav)
  audio_stage1 = nparr * (32767 / max(0.01, np.max(np.abs(wav)))) # type: ignore

  fp = BytesIO()
  scipy.io.wavfile.write(
    fp,
    rate,
    audio_stage1.astype(np.int16)
  )
  rawdata = fp.getvalue()

  response = web.Response(body=rawdata,status=200,content_type="audio/x-wav")
  return response

app = web.Application()
app.add_routes(routes)

web.run_app(app,host="127.0.0.1",port=12502) # type: ignore

from __future__ import annotations

import asyncio
from io import BytesIO
from multiprocessing import Process, Queue

import numpy as np
import scipy  # type: ignore
from aiohttp import web
from TTS.api import TTS  # type: ignore

routes = web.RouteTableDef()

models: list[str] = TTS.list_models()
DEFAULT_MODEL = models[0]

cached_tts: dict[str,TTS] = {}

def _generate(text: str, model_name: str) -> tuple[bytes, int]:
  print("1. Made it inside of _generate")
  if model_name not in cached_tts:
    print("1.5. Downloading model.")
    cached_tts[model_name] = TTS(model_name)
  tts = cached_tts[model_name]
  print("2. Got model")
  if text[-1] != ".": text += "."
  print()
  try:
    speaker = getattr(tts,"speakers")[0]
  except:
    speaker = None
  try:
    language = getattr(tts,"languages")[0]
  except:
    language = None
  print("3. Got speaker/language")
  wav = tts.tts(text, speaker=speaker, language=language) # type: ignore
  print("4. Generated wav")
  return wav, tts.synthesizer.output_sample_rate # type: ignore

def _generate_audio(text: str, model_name: str) -> bytes:
  queue = Queue()

  def _inner():
    queue.put(_generate(text, model_name))

  p = Process(target=_inner)
  p.start()
  p.join()
  data, sample_rate = queue.get()

  nparr = np.array(data)
  audio_stage1 = nparr * (32767 / max(0.01, np.max(np.abs(data)))) # type: ignore

  fp = BytesIO()
  scipy.io.wavfile.write(
    fp,
    sample_rate,
    audio_stage1.astype(np.int16)
  )
  rawdata = fp.getvalue()
  return rawdata

async def generate(text: str, model_name: str = DEFAULT_MODEL) -> bytes:
  result = await asyncio.to_thread(_generate_audio, text, model_name)
  return result
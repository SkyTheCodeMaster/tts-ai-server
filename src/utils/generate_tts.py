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
  print("-2. Started _generate_audio")
  queue = Queue()
  print("-1. Created Queue()")
  def _inner():
    print("0. Reached _inner start")
    queue.put(_generate(text, model_name))
    print("0.1. Reached _inner end")

  p = Process(target=_inner)
  print("5. Made process")
  p.start()
  print("6. Started")
  p.join()
  print("7. Joined")
  data, sample_rate = queue.get()
  print("8. Got data and sample_rate")
  nparr = np.array(data)
  audio_stage1 = nparr * (32767 / max(0.01, np.max(np.abs(data)))) # type: ignore
  print("9. Audo stage 1")

  fp = BytesIO()
  scipy.io.wavfile.write(
    fp,
    sample_rate,
    audio_stage1.astype(np.int16)
  )
  rawdata = fp.getvalue()
  print("10. Got rawdata")
  return rawdata

async def generate(text: str, model_name: str = DEFAULT_MODEL) -> bytes:
  result = await asyncio.to_thread(_generate_audio, text, model_name)
  return result
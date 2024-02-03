from __future__ import annotations

import datetime
import os
import pathlib
import tomllib
import urllib.parse
from typing import TYPE_CHECKING

from aiohttp import web
from django import setup as django_setup
from django.conf import settings as django_settings
from django.template import Context, Engine

if TYPE_CHECKING:
  from typing import Any, Union

  from django.template import Template

django_settings.configure()
django_setup()

with open("config.toml") as f:
  config = tomllib.loads(f.read())

routes = web.RouteTableDef()

sub_grand_context = {}

# Load all of the templates in the static folder.
engine = Engine()
templates: dict[str,Template] = {}
sup_templates: dict[str,Template] = {}

def join(a: str, b: str) -> str:
  "Join 2 filepaths"
  return str(pathlib.Path(a).joinpath(pathlib.Path(b)))

for root, dirs, files in os.walk("frontend/templates"):
  for file in files:
    filepath = join(root,file)
    with open(filepath,"r") as f:
      tmpl = engine.from_string(f.read())
      templates[filepath.removeprefix("frontend/templates").removeprefix("/")] = tmpl

for root, dirs, files in os.walk("frontend/supporting"):
  for file in files:
    filepath = join(root,file)
    with open(filepath,"r") as f:
      tmpl = engine.from_string(f.read())
      sup_templates[filepath.removeprefix("frontend/supporting").removeprefix("/")] = tmpl

def reload_files():
  for root, dirs, files in os.walk("templates"):
    if "supporting" in root: continue
    for file in files:
      filepath = join(root,file)
      with open(filepath,"r") as f:
        tmpl = engine.from_string(f.read())
        templates[filepath.removeprefix("templates").removeprefix("/")] = tmpl

  for root, dirs, files in os.walk("supporting"):
    for file in files:
      filepath = join(root,file)
      with open(filepath,"r") as f:
        tmpl = engine.from_string(f.read())
        sup_templates[filepath.removeprefix("supporting").removeprefix("/")] = tmpl

def grand_context(request: web.Request) -> dict[str,str]:
  gc = {
    **sub_grand_context,
    "navbar": sup_templates["navbar.html"].render(Context(sub_grand_context))
  }

  return gc

@routes.get("/")
async def get_index(request: web.Request) -> web.Response:
  # Check devmode
  if config["devmode"]:
    reload_files()

  ctx_dict: dict[str,Any] = {
    
  }
  rendered = templates["index.html"].render(Context({**grand_context(request),**ctx_dict}))
  return web.Response(body=rendered,content_type="text/html")

routes._items.append(web.static("/","frontend/static"))

def setup() -> web.RouteTableDef:
  return routes
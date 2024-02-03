from __future__ import annotations

import asyncio
import logging
import math
import os
import tomllib

import aiohttp
import asyncpg
import coloredlogs
from aiohttp import web

from utils.get_routes import get_routes
from utils.logger import CustomWebLogger
from utils.pg_pool_middleware import pg_pool_middleware
from utils.upc import UPC

LOGFMT = "[%(filename)s][%(asctime)s][%(levelname)s] %(message)s"
LOGDATEFMT = "%Y/%m/%d-%H:%M:%S"

handlers = [
  logging.StreamHandler()
]

with open("config.toml") as f:
  config = tomllib.loads(f.read())

if config['log']:
  handlers.append(logging.FileHandler(config['log']))

logging.basicConfig(
  handlers = handlers,
  format=LOGFMT,
  datefmt=LOGDATEFMT,
  level=logging.INFO,
)

coloredlogs.install(
  fmt=LOGFMT,
  datefmt=LOGDATEFMT
)

LOG = logging.getLogger(__name__)

app = web.Application(
  logger = CustomWebLogger(LOG),
  middlewares=[
    pg_pool_middleware
  ]
)
api_app = web.Application(
  logger = CustomWebLogger(LOG),
  middlewares=[
    pg_pool_middleware
  ]
)

disabled_cogs: list[str] = []

for cog in [
    f.replace(".py","") 
    for f in os.listdir("api") 
    if os.path.isfile(os.path.join("api",f)) and f.endswith(".py")
  ]:
  if cog not in disabled_cogs:
    LOG.info(f"Loading {cog}...")
    try:
      routes = get_routes(f"api.{cog}")
      for route in routes:
        LOG.info(f"  ↳ {route}")
      api_app.add_routes(routes)
    except:  # noqa: E722
      LOG.exception(f"Failed to load cog {cog}!")

app.add_subapp("/api/", api_app)

LOG.info("Loading frontend...")
try:
  routes = get_routes("frontend.routes")
  for route in routes:
    LOG.info(f"  ↳ {route}")
  app.add_routes(routes)
except:  # noqa: E722
  LOG.exception("Failed to load frontend!")
  
async def startup():
  try:
    session = aiohttp.ClientSession()
    app.cs = session
    api_app.cs = session

    app.LOG = LOG
    api_app.LOG = LOG

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
      runner,
      config['host'],
      config['port'],
    )
    await site.start()
    print(f"Started server on http://{config['host']}:{config['port']}...\nPress ^C to close...")
    await asyncio.sleep(math.inf)
  except KeyboardInterrupt:
    pass
  except asyncio.exceptions.TimeoutError:
    LOG.error("PostgreSQL connection timeout. Check the connection arguments!")
  finally:
    try: await site.stop()   # noqa: E701
    except: pass  # noqa: E722, E701
    try: await session.close()   # noqa: E701
    except: pass  # noqa: E722, E701

asyncio.run(startup())
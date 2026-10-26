import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from reflect_bot.app.container import ApplicationContext
from reflect_bot.config import Settings

settings = Settings.from_env()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
context = ApplicationContext(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await context.application.start()
    yield
    await context.application.stop()


app = FastAPI(title="anyforms-reflect-bot", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return context.application.health()

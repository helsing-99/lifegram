from .logger import LOGGER
from .core import app
from config import MONGO_DB_NAME as DB_NAME
from config import MONGO_URI as MONGO_URL
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from pyrogram import Client, filters

mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client["cloned"]
db = mongo_client.lgram
WELCOME_DELAY_KICK_SEC = 120
app = app()

LOGGER("lgram").info("Main bot and clone bot management initialized.")
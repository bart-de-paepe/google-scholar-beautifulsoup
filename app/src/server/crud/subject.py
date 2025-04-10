import os

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import HTTPException

from app.src.server.models.search_result_collection import SearchResultCollection
from app.src.server.models.subject_collection import SubjectCollection

load_dotenv()
MOTOR = os.getenv('MOTOR')
DATABASE = os.getenv('DATABASE')
COLLECTION = os.getenv('COLLECTION_EMAILS')
client = motor.motor_asyncio.AsyncIOMotorClient(MOTOR)
db = client.get_database(DATABASE)
collection = db.get_collection(COLLECTION)

async def get_all_subjects():
    return SubjectCollection(subjects = await collection.find({}, {"subject": 1}).distinct('subject'))







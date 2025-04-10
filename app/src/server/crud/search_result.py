import os

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import HTTPException

from app.src.server.models.search_result_collection import SearchResultCollection

load_dotenv()
MOTOR = os.getenv('MOTOR')
DATABASE = os.getenv('DATABASE')
COLLECTION = os.getenv('COLLECTION_COLLECTION_SEARCH_RESULTS')
client = motor.motor_asyncio.AsyncIOMotorClient(MOTOR)
db = client.get_database(DATABASE)
collection = db.get_collection(COLLECTION)
"""
db.createView("collection-search-results", "search-results", [
        {
            $lookup:
                {
                    from: "emails",
                    localField: "email",
                    foreignField: "_id",
                    as: "subject"
                }
        },
        {
            $project:
                {
                    author: 1,
                    link: 1,
                    publisher: 1,
                    text: 1,
                    title: 1,
                    year: 1,
                    collection: "$subject.subject"
                }
        },
            { $unwind: "$collection"}
    ] )
"""


async def get_all_search_results():
    return SearchResultCollection(search_results = await collection.find({}, {"collection": 1, "title": 1, "author": 1, "year": 1, "publisher": 1,
                                                "link.location_replace_url": 1, "link.DOI": 1, "text": 1}).to_list())

async def get_single_search_results(objid: str):
    if(
        search_result := await collection.find_one({"_id": ObjectId(objid)}, {"collection": 1, "title": 1, "author": 1, "year": 1, "publisher": 1, "link.location_replace_url": 1, "link.DOI": 1, "text": 1})
    ) is not None:
        return search_result
    raise HTTPException(status_code=404, detail=f"Search result {objid } not found")





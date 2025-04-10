from fastapi import APIRouter

from app.src.server.crud.subject import get_all_subjects
from app.src.server.models.subject_collection import SubjectCollection

router = APIRouter()

@router.get("/subjects/",
            tags=["subjects"],
            response_description="List all Subjects",
            response_model=SubjectCollection,
            response_model_by_alias=False,)
async def subjects():
    return await get_all_subjects()

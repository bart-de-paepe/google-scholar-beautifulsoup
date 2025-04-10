from fastapi import APIRouter

from app.src.server.crud.search_result import get_all_search_results, get_single_search_results
from app.src.server.models.search_result import SearchResultModel
from app.src.server.models.search_result_collection import SearchResultCollection

router = APIRouter()

@router.get("/search-results/",
            tags=["search_results"],
            response_description="List all Search Results",
            response_model=SearchResultCollection,
            response_model_by_alias=False,)
async def search_results():
    return await get_all_search_results()

@router.get("/search-results/{objid}",
            tags=["search_results"],
            response_description="Get a single Search Result",
            response_model=SearchResultModel,
            response_model_by_alias=False,)
async def search_result(objid: str):
    return await get_single_search_results(objid)

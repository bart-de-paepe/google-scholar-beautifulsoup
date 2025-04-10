from typing import Optional

from pydantic import BaseModel, BeforeValidator, Field, HttpUrl, ConfigDict
from typing_extensions import Annotated

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class SearchResultLinkModel(BaseModel):
    location_replace_url: HttpUrl = Field(...)
    DOI: str = Field(...)

class SearchResultModel(BaseModel):
    """
    Container for a single search result record.
    """
    # The primary key for the SearchResultModel, stored as a `str` on the instance.
    # This will be aliased to `_id` when sent to MongoDB,
    # but provided as `id` in the API requests and responses.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    collection: str = Field(...)
    title: str = Field(...)
    author: str = Field(...)
    year: int|None = Field(...)
    publisher: str = Field(...)
    link: SearchResultLinkModel
    text: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "title": "Trait‐Based Prediction of Conservation Status of North American Small‐Bodied Minnows (Leuciscidae) and Darters (Percidae)",
                "collection": "traits: nieuwe resultaten",
                "author": "AM Watt, TE Pitcher",
                "year": 2025,
                "publisher": " Aquatic Conservation: Marine and Freshwater",
                "link": {
                    "location_replace_url": "https://onlinelibrary.wiley.com/doi/pdf/10.1002/aqc.70113",
                    "DOI": "10.1002/aqc.70113",
                },
                "text": """… For darters, the traits associated with an increased risk of being threatened were 
climatic zone and total length. Taken together, this study identifies key life history
and ecological traits that influence the conservation status of small‐bodied fishes …""",
            }
        },
    )

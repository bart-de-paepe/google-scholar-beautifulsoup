from typing import List

from pydantic import BaseModel

class SubjectCollection(BaseModel):
    """
    A container holding a list of `SearchResultModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability](https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    """

    subjects: List[str]
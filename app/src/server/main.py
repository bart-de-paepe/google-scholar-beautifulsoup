from fastapi import FastAPI

from .routers import search_results, subjects

app = FastAPI()
app.include_router(search_results.router)
app.include_router(subjects.router)
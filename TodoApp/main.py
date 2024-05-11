from fastapi import FastAPI
from . import models
from .database import engine
from .router import auth, todos, admin

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


@app.get("/healthy")
def health_check():
    return {"status": "healthy"}


app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)

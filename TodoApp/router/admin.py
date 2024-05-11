from fastapi import APIRouter, Depends, HTTPException, Path, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette import status
from models import Todos
from typing import Annotated
from database import SessionLocal
from auth import getCurrentUser

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependecy = Annotated[Session, Depends(get_db)]
user_dependecy = Annotated[dict, Depends(getCurrentUser)]


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependecy, db: db_dependecy):
    if user is None and user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication failed")
    return db.query(Todos).all()

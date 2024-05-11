from fastapi import APIRouter, Depends, HTTPException, Path, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette import status
from ..models import Todos
from typing import Annotated
from ..database import SessionLocal
from .auth import getCurrentUser

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependecy = Annotated[Session, Depends(get_db)]
user_dependecy = Annotated[dict, Depends(getCurrentUser)]


class TodoRequest(BaseModel):
    title: str
    description: str
    priority: int
    complete: bool


@router.get("/")
async def read_all(user: user_dependecy, db: db_dependecy):
    print(user)
    return db.query(Todos).filter(Todos.owner_id == user.get("user_id")).all()


@router.get("/todo/{id}", status_code=status.HTTP_200_OK)
async def getTodo(user: user_dependecy, db: db_dependecy, id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == id)
        .filter(Todos.owner_id == user.get("user_id"))
        .first()
    )
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Could not find todo")


@router.post("/todo")
async def createTodo(user: user_dependecy, db: db_dependecy, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    print(user)
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get("user_id"))
    db.add(todo_model)
    db.commit()
    return JSONResponse(content={"message": "Added successfully"})


@router.put("/todo/{id}")
async def updateTodo(
    user: user_dependecy,
    db: db_dependecy,
    todo_request: TodoRequest,
    id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    todoModel = (
        db.query(Todos)
        .filter(Todos.id == id)
        .filter(Todos.owner_id == user.get("user_id"))
        .first()
    )
    todoModel.title = todo_request.title
    todoModel.description = todo_request.description
    todoModel.priority = todo_request.priority
    todoModel.complete = todo_request.complete

    db.add(todoModel)
    db.commit()


@router.delete("/todo/{id}")
async def deleteTodo(user: user_dependecy, db: db_dependecy, id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    todoModel = db.query(Todos).filter(Todos.id == id).first()
    if todoModel is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(todoModel)
    db.commit()
    return Response(content={"message": "Deleted successfully"})

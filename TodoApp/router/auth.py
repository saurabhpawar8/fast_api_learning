from typing import Annotated
from ..database import SessionLocal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status
from ..models import User
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "y9833943gbg37i9321bsxx12e"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependecy = Annotated[Session, Depends(get_db)]


def authenticateUser(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def createAccessToken(username: str, userId: int, role: str, expiresDelta: timedelta):
    encode = {"sub": username, "id": userId, "role": role}
    expires = datetime.now() + expiresDelta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def getCurrentUser(token: Annotated[str, Depends(oauth_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")

        if username is None and user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return {"username": username, "user_id": user_id, "role": role}
    except JWTError:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="COuld not validate user"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def createUser(db: db_dependecy, userRequest: CreateUserRequest):
    userModel = User(
        email=userRequest.email,
        username=userRequest.username,
        first_name=userRequest.first_name,
        last_name=userRequest.last_name,
        hashed_password=bcrypt_context.hash(userRequest.password),
        role=userRequest.role,
        is_active=True,
    )
    db.add(userModel)
    db.commit()


@router.post("/token", response_model=Token)
async def login_authentication(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependecy
):
    user = authenticateUser(form_data.username, form_data.password, db)
    if not user:
        return JSONResponse({"Error": "Not Authenticated"})
    token = createAccessToken(user.username, user.id, user.role, timedelta(minutes=20))
    return JSONResponse({"access_token": token, "token_type": "bearer"})

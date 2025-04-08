import motor.motor_asyncio
from fastapi import FastAPI, Request, Depends
from fastapi_users import FastAPIUsers, models
from fastapi_users.db import MongoDBUserDatabase
from fastapi_users.authentication import CookieAuthentication, JWTAuthentication
from dotenv import dotenv_values
from fastapi.middleware.cors import CORSMiddleware
import os

config = dotenv_values(".env")
DATABASE_URI = config.get("DATABASE_URI")
if os.getenv("DATABASE_URI"): DATABASE_URI = os.getenv("DATABASE_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URI, uuidRepresentation="standard"
)
database = client["pointer"]
collection = database["users"]


class User(models.BaseUser):
    rollno: str
    username: str
    role: str

class UserCreate(models.BaseUserCreate): #email and password added automatically
    rollno: str
    username: str
    role: str

class UserUpdate(User, models.BaseUserUpdate):
    pass

class UserDB(User, models.BaseUserDB):#add password hash field
    pass

SECRET = config.get("SECRET")
if os.getenv("SECRET"): SECRET = os.getenv("SECRET")
auth_backends = []
authentication = JWTAuthentication(secret=SECRET, lifetime_seconds=3600)
auth_backends.append(authentication)

user_db = MongoDBUserDatabase(UserDB, collection)

fastapi_users = FastAPIUsers(
    user_db,
    auth_backends,
    User,
    UserCreate,
    UserUpdate,
    UserDB
)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#to add POST /auth/login
app.include_router(
    fastapi_users.get_auth_router(auth_backends[0]),
    prefix="/auth",
    tags=["auth"]
)

def on_after_register(user: UserDB, request: Request):
    print("User {user.id} has registered.")
#to add POST /auth/register
app.include_router(
    fastapi_users.get_register_router(on_after_register),
    prefix="/auth",
    tags=["auth"]
)
# get or patch  /auth/me, get /auth/users , get or delete /auth/usrs/{id}
app.include_router(
    fastapi_users.get_users_router(),
    prefix="/auth/users",
    tags=["auth"]
)
#for post  /auth/users/forgot-password, /auth/users/reset-password
app.include_router(
    fastapi_users.get_reset_password_router("SECRET"),
    prefix="/auth/users",
    tags=["auth"]
)



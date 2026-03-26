from fastapi import  HTTPException
from user.models import UserCreate, UserResponse
from passlib.hash import bcrypt
from database.service import StoreUser, getUser, supabase
from joserfc import jwt, jwk
from joserfc.jwk import OctKey
import datetime
import os


async def register(user: UserCreate):
    existing_user = await getUser(user.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    hashed_password = bcrypt.hash(user.password)

    new_user = await StoreUser(user.email, hashed_password)

    return UserResponse(
        userID = new_user["id"],
        email = user.email
    )


async def login(email: str, password: str):
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = await getUser(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not bcrypt.verify(password, user["password"]):
        raise HTTPException(status_code=401, detail ="Invalid password")
    
    token = await create_access_token(user["id"])

    return UserResponse(
        userID = user["id"],
        email = user["email"],
        token = token
    )

async def updatePreferences(userID: str, field: str = None, location: str = None, remote: bool = None, compensation: int = None):    
    updates = {}
    result = supabase.table("users").select("preferences").eq("id", userID).execute()
    existing = result.data[0]["preferences"]
    if field is not None:
        updates["field"] = field
    if location is not None:
        updates["location"] = location
    if remote is not None:
        updates["remote"] = remote
    if compensation is not None:
        updates["compensation"] = compensation
    merged = {**existing, **updates}
    supabase.table("users").update({
        "preferences": merged
    }).eq("id", userID).execute()
        
async def create_access_token(userID: str):
    now = datetime.datetime.now(datetime.UTC)
    claims = {
        "iss": "https://qmmnzbtzzvplnvnqiwbk.supabase.co",
        "iat": now,
        "exp": now + datetime.timedelta(days=7),
        "sub": userID,
    }
    header = {"alg": "HS256"}
    key = jwk.import_key(os.getenv("JWT_SECRET"), "oct")
    text = jwt.encode(header, claims, key)
    return text
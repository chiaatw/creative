from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from joserfc import jwt, jwk, JWTError
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

    credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials"
    )

    try:
        key = jwk.import_key(os.getenv("JWT_SECRET"), "oct")
        decoded = jwt.decode(token, key)
        userID = decoded.claims["sub"]
    except JWTError:
        raise credentials_exception
    return userID



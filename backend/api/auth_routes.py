from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional

logger = logging.getLogger(__name__)

from db.mongo import users_collection
from utils.jwt_handler import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: SignupRequest):
    # Normalize email
    email = user_data.email.lower().strip()
    
    # 1. Check if email exists
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 2. Hash password
    hashed_password = hash_password(user_data.password)
    
    # 3. Insert user into MongoDB
    user_doc = {
        "email": email,
        "name": user_data.name,
        "password": hashed_password,
        "job_role": None,
        "city": None,
        "years_of_experience": None,
        "role_description": None,
        "skills": [],
        "risk_score": None,
        "created_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user_doc)
    return {"message": "User registered successfully"}


@router.post("/login")
def login(login_data: LoginRequest):
    email = login_data.email.lower().strip()
    
    # Match EXACT logs requested
    logging.info(f"API Request: POST /auth/login")
    logging.info(f"Login attempt: {email}")
    
    # 1. Find user by email
    user = users_collection.find_one({"email": email})
    logging.info(f"User found: {user is not None}")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
        
    # 2. Verify password
    logging.info("Password verification starting")
    if not verify_password(login_data.password, user["password"]):
        logging.warning("Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
        
    logging.info("Login successful")
        
    # 3. Generate JWT token
    # Mongo _id is an ObjectId, needs converting to string
    access_token = create_access_token(
        data={"user_id": str(user["_id"]), "email": user["email"]}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "name": current_user.get("name"),
        "email": current_user.get("email"),
        "job_role": current_user.get("job_role"),
        "city": current_user.get("city"),
        "years_of_experience": current_user.get("years_of_experience"),
        "role_description": current_user.get("role_description"),
        "risk_score": current_user.get("risk_score")
    }

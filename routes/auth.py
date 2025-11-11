import email
from math import e

from httpx import _status_codes
from starlette.routing import Router
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from supabase import AuthApiError
from scarlet_studio_backend.datalayer.user_model import UserCreate, UserLogin, UserResponse
from scarlet_studio_backend.datalayer import get_supabase_client, supabase
from fastapi import APIRouter, HTTPException, Header, status, Depends


router = APIRouter()

@router.post("/signup",response_model=UserResponse)
async def signup(data:UserCreate):

    supabase_client = get_supabase_client()
    try:
        response=supabase.auth.sign_up(
            {
                "email":data.email,
                "password":data.password
            }
        )
        new_user = response.user
        if not new_user:
            raise HTTPException(status_code=500,detail="Sign up failed")

        profile_data = {
            "id":new_user.id,
            "role":data.role
        }

        profile = supabase_client.table('profiles').insert(profile_data).execute()

        if not profile_data:
            return HTTPException(status_code=500,detail="Failed to create an user profile")

        return {"message": "User signed up successfully. Please check your email for verification"}

    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))


@router.post("/login")
async def login(data:UserLogin):

    try:
        response = supabase.auth.sign_in_with_password({
            "email":data.email,
            "password":data.password
        })
        return response

    except AuthApiError as e:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail=e.message)


@router.get("/me", response_model=UserResponse)
async def get_me(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer: ","")

        response = supabase.auth.get_user(token)
        user = response.user

        if not user:
            raise HTTPException(status_code=401,detail="Invalid or expired token")

        profile_res = supabase.table("profiles").select("role").eq("id", user.id).execute()
        role = profile_res.data[0]["role"] if profile_res.data else "unknown"

        return UserResponse(
            id=user.id,
            email=user.email,
            role=role,
            created_at=user.created_at
        )

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")
    
        

    

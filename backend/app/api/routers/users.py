# app/api_v1/users.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies.deps import CurrentUser, DBSessionDep
from schemas.users import UserBase, UserUpdate
from services.users_service import get_user_service, UserService
from models.users import UserRole

router = APIRouter()


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserBase,
    svc: UserService = Depends(get_user_service),
):
    return await svc.create_user(payload)


@router.get("/me")
async def read_current_user(
    current_user: CurrentUser,
):
    return current_user


@router.get("/getAll")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    svc: UserService = Depends(get_user_service),
):
    return await svc.get_all_users(skip=skip, limit=limit)


@router.get("/get/{user_id}")
async def read_user(
    user_id: UUID,
    svc: UserService = Depends(get_user_service),
):
    return await svc.get_user_by_id(user_id)


@router.put("/update/{user_id}")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: CurrentUser,
    svc: UserService = Depends(get_user_service),
):
    # only the user themself or a superadmin can update
    return await svc.update_user(user_id, payload, current_user)


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: CurrentUser,
    svc: UserService = Depends(get_user_service),
):
    await svc.delete_user(user_id, current_user)

# app/services/scan_result_service.py
from functools import lru_cache
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from crud.base_crud import BaseCRUD
from dependencies import DBSessionDep
from models.scan import ScanResult as ScanResultModel
from models.users import User as UserModel


class ScanResultService:
    def __init__(self, scan_crud: BaseCRUD[ScanResultModel], user_crud: BaseCRUD[UserModel]):
        self.scan_crud = scan_crud
        self.user_crud = user_crud

    async def create_scan_result(self, data: Dict[str, Any]) -> ScanResultModel:
        # ensure user exists
        user = await self.user_crud.get_by_id(data["user_id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            return await self.scan_crud.create(data)
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Failed to create scan result")

    async def get_scan_by_id(self, scan_id: UUID) -> ScanResultModel:
        scan = await self.scan_crud.get_by_id(scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail=f"ScanResult {scan_id} not found")
        return scan

    async def get_scans_by_user(self, user_id: UUID) -> List[ScanResultModel]:
        # returns all scan_results for a given user
        return await self.scan_crud.get_all_by_field("user_id", user_id)

    async def delete_scan(self, scan_id: UUID) -> None:
        # raises if missing
        scan = await self.get_scan_by_id(scan_id)
        await self.scan_crud.delete(scan.id)


@lru_cache()
def get_scan_service(db: DBSessionDep) -> ScanResultService:
    return ScanResultService(
        BaseCRUD(ScanResultModel, db),
        BaseCRUD(UserModel, db),
    )

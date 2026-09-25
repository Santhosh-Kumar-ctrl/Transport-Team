from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import Principal, require_roles
from app.core.roles import Role
from app.modules.dashboard import service
from app.modules.dashboard.schemas import AdminDashboard, DriverDashboard, StudentDashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/admin", response_model=AdminDashboard)
async def admin(_: Principal = Depends(require_roles(Role.ADMIN, Role.SECURITY)),
                session: AsyncSession = Depends(get_session)):
    return await service.admin(session)


@router.get("/driver", response_model=DriverDashboard)
async def driver(p: Principal = Depends(require_roles(Role.DRIVER)), session: AsyncSession = Depends(get_session)):
    return await service.driver(session, p.id)


@router.get("/student", response_model=StudentDashboard)
async def student(p: Principal = Depends(require_roles(Role.STUDENT)), session: AsyncSession = Depends(get_session)):
    return await service.student(session, p.id)

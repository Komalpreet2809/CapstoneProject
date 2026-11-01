"""Data every visitor may read: the menu catalogue, RMS categories, policies, notices.

Nothing here is personal. The dev-only demo-account list exists only when ENVIRONMENT=dev.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from mini_ums_api.conventions import Menu, Policies, Rms, conventions
from mini_ums_api.deps import AppSettings, Pool
from mini_ums_api.schemas import AnnouncementOut, EventOut, NewsOut
from mini_ums_api.seed.personas import PERSONA_PASSWORD, PERSONAS

router = APIRouter(tags=["public"])


class MenuCatalogue(BaseModel):
    menu: list[Menu]
    sidebar: list[str]
    shortcuts: list[str]


class DemoAccount(BaseModel):
    reg_no: str
    name: str
    password: str
    scenario: str


@router.get("/catalogue/menu", response_model=MenuCatalogue)
async def menu_catalogue() -> MenuCatalogue:
    c = conventions()
    return MenuCatalogue(menu=c.menu, sidebar=c.sidebar, shortcuts=c.shortcuts)


@router.get("/catalogue/rms", response_model=Rms)
async def rms_catalogue() -> Rms:
    return conventions().rms


@router.get("/catalogue/policies", response_model=Policies)
async def policies() -> Policies:
    return conventions().policies


@router.get("/content/announcements", response_model=list[AnnouncementOut])
async def announcements(pool: Pool) -> list[AnnouncementOut]:
    rows = await pool.fetch(
        "SELECT id, kind, title, body, menu_id FROM announcements ORDER BY kind, sort, id"
    )
    return [AnnouncementOut(**dict(r)) for r in rows]


@router.get("/content/news", response_model=list[NewsOut])
async def news(pool: Pool, limit: Annotated[int, Query(ge=1, le=50)] = 5) -> list[NewsOut]:
    rows = await pool.fetch(
        "SELECT id, title, summary, published_on FROM news"
        " ORDER BY published_on DESC, id DESC LIMIT $1",
        limit,
    )
    return [NewsOut(**dict(r)) for r in rows]


@router.get("/content/events", response_model=list[EventOut])
async def events(pool: Pool, limit: Annotated[int, Query(ge=1, le=50)] = 5) -> list[EventOut]:
    rows = await pool.fetch(
        "SELECT id, title, venue, starts_at FROM events WHERE starts_at >= now()"
        " ORDER BY starts_at LIMIT $1",
        limit,
    )
    return [EventOut(**dict(r)) for r in rows]


@router.get("/dev/demo-accounts", response_model=list[DemoAccount], include_in_schema=False)
async def demo_accounts(settings: AppSettings) -> list[DemoAccount]:
    if not settings.show_demo_accounts:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return [
        DemoAccount(reg_no=p.reg_no, name=p.name, password=PERSONA_PASSWORD, scenario=p.scenario)
        for p in PERSONAS
    ]

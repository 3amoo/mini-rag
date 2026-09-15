# ======================================================
# Import Libs
# ======================================================

from fastapi import APIRouter, Depends # pyright: ignore[reportMissingImports]
from helpers.config import get_settings, Settings



# ======================================================
# Func.
# ======================================================
# - func to test the app
# - get settings
# ======================================================

base_router = APIRouter(
    prefix='/api/v1'
)


@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    app_settings = get_settings()

    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION

    return {
        "app_name": app_name,
        "app_version": app_version, 
    }


import os

class Settings:
    PROJECT_NAME: str = "RetinaGuard API"
    VERSION: str = "1.0.0-hackathon-proto"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]
    MODEL_VERSION: str = "RetinaGuard-Vision-v0.1-proto"
    TELEMEDICINE_HUB: str = "District Tele-Ophthalmology Hub (AP-East)"
    IS_RESEARCH_PROTOTYPE: bool = True
    DISCLAIMER: str = (
        "RetinaGuard is a research and telemedicine prototype for AI-assisted screening "
        "and is not certified as an autonomous primary diagnostic medical device."
    )

settings = Settings()


import os
import secrets

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

API_KEY = os.getenv("RESOLVEOPS_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "RESOLVEOPS_API_KEY is missing from .env"
    )


def verify_api_key(x_api_key: str | None = Header(default=None)):
    if not x_api_key or not secrets.compare_digest(
        x_api_key, API_KEY
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )


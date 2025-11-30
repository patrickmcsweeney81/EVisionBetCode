"""
FastAPI endpoint for trigger-only injury checks across 3 free sources.
Copy this to your backend-python/app/ directory and integrate into your main router.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

# Import the injury check module (adjust path after copying to backend)
# from app.injury_check import check_injury

router = APIRouter()


class InjuryCheckRequest(BaseModel):
    player: str
    league: str  # NBA, NFL, NHL


class InjuryCheckResponse(BaseModel):
    injury_status: str | None
    injury_detail: str | None
    last_updated: str | None
    confidence: str
    sources: list[Dict]
    note: str | None


@router.post("/injury-check", response_model=InjuryCheckResponse)
async def injury_check_endpoint(request: InjuryCheckRequest):
    """
    Trigger-only injury check across BALLDONTLIE, TheSportsDB, and API-SPORTS.
    
    Returns merged consensus with confidence rating.
    
    Example request:
    ```json
    {
      "player": "Neemias Queta",
      "league": "NBA"
    }
    ```
    
    Example response:
    ```json
    {
      "injury_status": "QUESTIONABLE",
      "injury_detail": "Right ankle",
      "last_updated": "2025-11-29 12:34:56",
      "confidence": "HIGH",
      "sources": [
        {"source": "BALLDONTLIE", "status": "QUESTIONABLE", ...},
        {"source": "TheSportsDB", "status": "QUESTIONABLE", ...},
        {"source": "API-SPORTS", "status": "QUESTIONABLE", ...}
      ],
      "note": null
    }
    ```
    """
    try:
        # Uncomment after copying injury_check.py to backend
        # result = check_injury(request.player, request.league)
        # return result
        
        # Placeholder for testing endpoint structure
        return {
            "injury_status": "ACTIVE",
            "injury_detail": None,
            "last_updated": "2025-11-29 00:00:00",
            "confidence": "MEDIUM",
            "sources": [
                {"source": "BALLDONTLIE", "status": "ACTIVE", "detail": None, "last_updated": "2025-11-29 00:00:00"},
                {"source": "TheSportsDB", "status": None, "detail": None, "last_updated": None},
                {"source": "API-SPORTS", "status": "ACTIVE", "detail": None, "last_updated": "2025-11-29 00:00:00"}
            ],
            "note": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Injury check failed: {str(e)}")


# Integration into main.py:
# from app.injury_check_endpoint import router as injury_router
# app.include_router(injury_router, prefix="/api", tags=["injury"])

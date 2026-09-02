from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from ..schemas import BatchRequest, BatchResponse, MarketResponse, SentimentResponse

router = APIRouter(prefix="/api/v1/sentiment", tags=["sentiment"])


def authorize(request: Request, x_api_key: Optional[str] = Header(default=None)) -> None:
    expected = request.app.state.container.settings.api_key
    if expected and x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")


@router.get("/market", response_model=MarketResponse, dependencies=[Depends(authorize)])
def market_sentiment(request: Request, window_minutes: Optional[int] = Query(default=None, ge=1, le=1440)) -> MarketResponse:
    return MarketResponse(market_sentiment=request.app.state.container.query_service.market(window_minutes))


@router.get("/{symbol}", response_model=SentimentResponse, dependencies=[Depends(authorize)])
def symbol_sentiment(request: Request, symbol: str, window_minutes: Optional[int] = Query(default=None, ge=1, le=1440)) -> SentimentResponse:
    try:
        return request.app.state.container.query_service.get(symbol, window_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="sentiment data unavailable") from exc


@router.post("/batch", response_model=BatchResponse, dependencies=[Depends(authorize)])
def batch_sentiment(request: Request, payload: BatchRequest) -> BatchResponse:
    results = []
    for symbol in payload.symbols:
        try:
            results.append(request.app.state.container.query_service.get(symbol, payload.window_minutes))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="sentiment data unavailable") from exc
    return BatchResponse(results=results, timestamp=datetime.now(timezone.utc))


from ninja import Router, Schema
from typing import List, Optional, Dict, Any
from .forecasting import load_series, forecast, backtest_rolling

router = Router()

class FiltersSchema(Schema):
    category_id: Optional[int] = None
    product_id: Optional[int] = None

class CVSchema(Schema):
    type: str = "rolling"
    splits: int = 5
    step: int = 7

class ForecastRequest(Schema):
    metric: str = "revenue"
    freq: str = "D"
    horizon: int = 14
    model: str = "sklearn" # "arima", "sklearn", "xgboost"
    filters: Optional[FiltersSchema] = None
    train_start: Optional[str] = None
    train_end: Optional[str] = None
    cv: Optional[CVSchema] = None

class ForecastPoint(Schema):
    date: str
    yhat: float
    lower: Optional[float] = None
    upper: Optional[float] = None

class ForecastResponse(Schema):
    model_info: str
    fitted_range: Dict[str, Any]
    backtest_metrics: Optional[Dict[str, float]] = None
    forecast_series: List[ForecastPoint]

@router.post("/run", response={200: ForecastResponse, 400: dict})
def run_forecast(request, payload: ForecastRequest):
    # 1. Load the Series
    filters_dict = payload.filters.dict(exclude_none=True) if payload.filters else {}
    
    series = load_series(
        metric=payload.metric,
        freq=payload.freq,
        start=payload.train_start,
        end=payload.train_end,
        filters=filters_dict
    )
    
    if series.empty or len(series) < 30:
        return 400, {"error": "Not enough historical data matching the filters (minimum 30 steps required)."}
        
    # 2. Extract Training Range
    fitted_range = {
        "start": series.index[0].strftime('%Y-%m-%d %H:%M:%S'),
        "end": series.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
        "points": len(series)
    }

    # 3. Optional Backtest validation phase
    metrics = None
    if payload.cv and payload.cv.type == "rolling":
        res_cv = backtest_rolling(
            series, 
            model_type=payload.model, 
            horizon=payload.horizon, 
            splits=payload.cv.splits, 
            step=payload.cv.step
        )
        if "error" not in res_cv:
            metrics = res_cv.get("metrics")
            
    # 4. Generate the Future Forecast
    res_f = forecast(series, model_type=payload.model, horizon=payload.horizon)
    if "error" in res_f:
        return 400, {"error": res_f["error"]}
        
    return 200, {
        "model_info": f"{payload.model.upper()} ({payload.metric} @ {payload.freq})",
        "fitted_range": fitted_range,
        "backtest_metrics": metrics,
        "forecast_series": res_f["forecast"]
    }

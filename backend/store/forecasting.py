import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncHour, TruncWeek
from store.models import Receipt, ReceiptItem
from store.analytics_api import get_date_range

# Optional Machine Learning Imports
try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

def load_series(metric='revenue', freq='D', start=None, end=None, filters=None):
    """
    Loads historical receipt data and returns a pandas Series indexed by datetime.
    freq: 'H' (hourly), 'D' (daily), 'W' (weekly)
    """
    start_date, end_date = get_date_range(start, end)
    
    if filters and ('category_id' in filters or 'product_id' in filters):
        qs = ReceiptItem.objects.filter(receipt__created_at__range=(start_date, end_date))
        if 'category_id' in filters:
            qs = qs.filter(product__category_id=filters['category_id'])
        if 'product_id' in filters:
            qs = qs.filter(product_id=filters['product_id'])
        date_field = 'receipt__created_at'
        revenue_field = 'line_total'
    else:
        qs = Receipt.objects.filter(created_at__range=(start_date, end_date))
        date_field = 'created_at'
        revenue_field = 'total_amount'

    if freq == 'H':
        trunc_func = TruncHour(date_field)
        resample_rule = 'h'
    elif freq == 'W':
        trunc_func = TruncWeek(date_field)
        resample_rule = 'W-MON'
    else:
        trunc_func = TruncDate(date_field)
        resample_rule = 'D'

    if metric == 'orders':
        if filters and ('category_id' in filters or 'product_id' in filters):
            agg_expr = Count('receipt', distinct=True)
        else:
            agg_expr = Count('id')
    else:
        agg_expr = Sum(revenue_field)

    data = (
        qs.annotate(ds=trunc_func)
          .values('ds')
          .annotate(y=agg_expr)
          .order_by('ds')
    )

    records = []
    for row in data:
        if row['ds']:
            val = float(row['y'] or 0)
            if metric == 'revenue':
                val *= 100 # Convert to integer cents
            records.append({'ds': row['ds'], 'y': val})

    if not records:
        return pd.Series(dtype=float)

    df = pd.DataFrame(records)
    df['ds'] = pd.to_datetime(df['ds'])
    df['ds'] = df['ds'].dt.tz_localize(None) # Drop timezone for pure timeseries processing

    df.set_index('ds', inplace=True)
    
    # Resample to fill gap days/hours with 0s
    s = df['y'].resample(resample_rule).sum().fillna(0)
    
    return s

def _prepare_ml_features(series):
    """
    Generates engineered features for boosting models.
    """
    df = series.to_frame(name='y')
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek
    df['month'] = df.index.month
    df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
    
    # Lag features
    for lag in [1, 7, 14, 28]:
        df[f'lag_{lag}'] = df['y'].shift(lag)
        
    # Rolling mean features
    for win in [7, 14, 30]:
        df[f'roll_mean_{win}'] = df['y'].shift(1).rolling(window=win).mean()

    df.dropna(inplace=True)
    return df

def forecast(series, model_type='sklearn', horizon=14):
    """
    Trains a model on the provided pandas Series and predicts `horizon` steps into the future.
    """
    if series.empty or len(series) < 30:
        return {"error": "Not enough historical data to generate forecast (minimum 30 steps required)."}

    # --- ARIMA / SARIMA STATSMODELS ---
    if model_type == 'arima':
        if not HAS_STATSMODELS:
            return {"error": "statsmodels package is missing. Run: pip install statsmodels"}
        
        try:
            # Note: SARIMA(1,1,1)x(0,1,1,7) is a common daily baseline pattern
            model = SARIMAX(series, order=(1,1,1), seasonal_order=(0,1,1,7), 
                            enforce_stationarity=False, enforce_invertibility=False)
            res = model.fit(disp=False)
            f_obj = res.get_forecast(steps=horizon)
            
            mean_vals = f_obj.predicted_mean
            ci_vals = f_obj.conf_int()
            
            out = []
            for dt, val in mean_vals.items():
                out.append({
                    "date": dt.strftime('%Y-%m-%d %H:%M:%S'),
                    "yhat": max(0, float(val)), # No negative sales constraints
                    "lower": max(0, float(ci_vals.loc[dt].iloc[0])),
                    "upper": max(0, float(ci_vals.loc[dt].iloc[1]))
                })
            return {"forecast": out}
        
        except Exception as e:
            return {"error": f"ARIMA fitting failed: {str(e)}"}

    # --- TREE-BASED ENSEMBLES (XGBoost / HistGradientBoosting) ---
    elif model_type in ['sklearn', 'xgboost']:
        if not HAS_SKLEARN:
            return {"error": "scikit-learn is missing. Run: pip install scikit-learn"}
            
        df = _prepare_ml_features(series)
        if df.empty:
            return {"error": "Not enough features remaining after lag feature NaN drops."}
            
        X = df.drop(columns=['y'])
        y = df['y']
        
        # Initialize selected regressor
        if model_type == 'xgboost' and HAS_XGBOOST:
            model = XGBRegressor(n_estimators=100, max_depth=4)
        else:
            model = HistGradientBoostingRegressor(max_iter=100)
            
        model.fit(X, y)
        
        # Iterative auto-regressive forecasting
        last_dt = series.index[-1]
        freq_str = pd.infer_freq(series.index) or 'D'
            
        future_dates = pd.date_range(start=last_dt, periods=horizon+1, freq=freq_str)[1:]
        history = list(series.values)
        forecasts = []
        
        for dt in future_dates:
            row = {
                'hour': dt.hour,
                'dayofweek': dt.dayofweek,
                'month': dt.month,
                'is_weekend': int(dt.dayofweek >= 5)
            }
            
            # Predict lag values based on history array which appends live forecasts
            for lag in [1, 7, 14, 28]:
                row[f'lag_{lag}'] = history[-lag] if lag <= len(history) else np.mean(history)
                
            for win in [7, 14, 30]:
                subset = history[-win:]
                row[f'roll_mean_{win}'] = np.mean(subset) if subset else 0
                
            X_pred = pd.DataFrame([row])[X.columns]
            
            pred_val = model.predict(X_pred)[0]
            pred_val = max(0, float(pred_val))
            
            forecasts.append({
                "date": dt.strftime('%Y-%m-%d %H:%M:%S'),
                "yhat": round(pred_val, 2),
                "lower": round(pred_val * 0.85, 2), # 15% pseud-confidence bounds
                "upper": round(pred_val * 1.15, 2)
            })
            
            history.append(pred_val)
            
        return {"forecast": forecasts}

    return {"error": f"Unknown model type: {model_type}"}

def backtest_rolling(series, model_type='sklearn', horizon=7, splits=3, step=7):
    """
    Backtests a model using walk-forward validation.
    Returns MAE, RMSE, and MAPE scoring matrices.
    """
    if len(series) < (horizon * splits) + 30 + 30: # needs buffer for lags + fit
        return {"error": "Not enough historical data to generate a reliable walk-forward backtest."}
        
    metrics = []
    all_predictions = []
    
    # Walk-forward loop working backwards from the end of the data series
    for i in range(splits):
        test_end_idx = len(series) - (i * step)
        test_start_idx = test_end_idx - horizon
        
        if test_start_idx < 30:
            break
            
        train_series = series.iloc[:test_start_idx]
        test_series = series.iloc[test_start_idx:test_end_idx]
        actuals = test_series.values
        
        res = forecast(train_series, model_type=model_type, horizon=horizon)
        if "error" in res:
            return res
            
        preds = [p['yhat'] for p in res['forecast']]
        
        # Calculate Error Metrics
        mae = mean_absolute_error(actuals, preds)
        rmse = np.sqrt(mean_squared_error(actuals, preds))
        
        mask = actuals != 0
        mape = np.mean(np.abs((actuals[mask] - np.array(preds)[mask]) / actuals[mask])) if mask.any() else 0
        
        metrics.append({"split": splits - i, "mae": mae, "rmse": rmse, "mape": float(mape)})
        all_predictions.append({"actual": list(actuals), "predicted": preds})
        
    avg_metrics = {
        "avg_MAE": np.mean([m['mae'] for m in metrics]) if metrics else 0,
        "avg_RMSE": np.mean([m['rmse'] for m in metrics]) if metrics else 0,
        "avg_MAPE": np.mean([m['mape'] for m in metrics]) if metrics else 0,
    }
    
    return {
        "metrics": avg_metrics,
        "splits": metrics
    }

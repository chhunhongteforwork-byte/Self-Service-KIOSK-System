from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Sum, Count, F, Value, DecimalField
from django.db.models.functions import TruncDate, TruncHour, TruncWeek, ExtractWeekDay, ExtractHour, Cast
from ninja import Router, Schema
from typing import List, Optional
from store.models import Receipt, ReceiptItem

router = Router()

def get_date_range(start: Optional[str] = None, end: Optional[str] = None):
    # Default to last 30 days if dates are not provided
    today = timezone.now()
    end_date = today
    start_date = today - timedelta(days=30)
    
    if end:
        end_date = timezone.make_aware(datetime.strptime(end, "%Y-%m-%d"))
    if start:
        start_date = timezone.make_aware(datetime.strptime(start, "%Y-%m-%d"))
        
    return start_date, end_date + timedelta(days=1)  # Include the whole end day

class KPIResponse(Schema):
    total_revenue: float
    total_orders: int
    avg_order_value: float
    avg_items_per_order: float

@router.get("/kpi", response=KPIResponse)
def get_kpi(request, start: Optional[str] = None, end: Optional[str] = None):
    start_date, end_date = get_date_range(start, end)
    
    qs = Receipt.objects.filter(created_at__range=(start_date, end_date))
    
    aggs = qs.aggregate(
        tot_rev=Sum('total_amount'),
        tot_orders=Count('id'),
        tot_items=Sum('total_items')
    )
    
    tot_rev = aggs['tot_rev'] or 0.0
    tot_orders = aggs['tot_orders'] or 0
    tot_items = aggs['tot_items'] or 0
    
    avg_order_value = float(tot_rev) / tot_orders if tot_orders > 0 else 0.0
    avg_items_per_order = float(tot_items) / tot_orders if tot_orders > 0 else 0.0
    
    return {
        "total_revenue": float(tot_rev) * 100,
        "total_orders": tot_orders,
        "avg_order_value": avg_order_value * 100,
        "avg_items_per_order": avg_items_per_order
    }

class DailySalesResponse(Schema):
    date: str
    orders: int
    revenue: float

@router.get("/daily", response=List[DailySalesResponse])
def get_daily_sales(request, start: Optional[str] = None, end: Optional[str] = None):
    start_date, end_date = get_date_range(start, end)
    
    qs = (Receipt.objects
          .filter(created_at__range=(start_date, end_date))
          .annotate(date=TruncDate('created_at'))
          .values('date')
          .annotate(
              orders=Count('id'),
              revenue=Sum('total_amount')
          )
          .order_by('date'))
          
    results = []
    for item in qs:
        results.append({
            "date": item['date'].strftime('%Y-%m-%d') if item['date'] else "",
            "orders": item['orders'],
            "revenue": float(item['revenue'] or 0) * 100
        })
    return results

class HourlySalesResponse(Schema):
    hour: int
    orders: int
    revenue: float

@router.get("/hourly", response=List[HourlySalesResponse])
def get_hourly_sales(request, start: Optional[str] = None, end: Optional[str] = None):
    start_date, end_date = get_date_range(start, end)
    
    # Filter for operating hours 7 to 17
    # Note: Extracting just the hour for aggregation across all days in range
    # TruncHour retains the exact datetime hour (e.g. 2025-01-01 07:00:00).
    # To aggregate by hour-of-day regardless of date, we do:
    qs = Receipt.objects.filter(created_at__range=(start_date, end_date))
    
    # Since we want a universal hour 7-17 aggregation independent of the specific day:
    # Django 3.2+ ExtractHour might be simpler, but let's do it directly
    from django.db.models.functions import ExtractHour
    
    qs = (qs.annotate(hour=ExtractHour('created_at'))
            .filter(hour__gte=7, hour__lte=17)
            .values('hour')
            .annotate(
                orders=Count('id'),
                revenue=Sum('total_amount')
            )
            .order_by('hour'))
            
    # Fill in blanks so array is uniformly 7 through 17
    hour_dict = {h: {"orders": 0, "revenue": 0.0} for h in range(7, 18)}
    
    for item in qs:
        h = item['hour']
        if h in hour_dict:
            hour_dict[h]['orders'] = item['orders']
            hour_dict[h]['revenue'] = float(item['revenue'] or 0) * 100
            
    results = []
    for h in range(7, 18):
        results.append({
            "hour": h,
            "orders": hour_dict[h]['orders'],
            "revenue": hour_dict[h]['revenue']
        })
        
    return results

class TopProductResponse(Schema):
    product_name: str
    qty: int
    revenue: float

@router.get("/top-products", response=List[TopProductResponse])
def get_top_products(request, start: Optional[str] = None, end: Optional[str] = None, limit: int = 10):
    start_date, end_date = get_date_range(start, end)
    
    qs = (ReceiptItem.objects
          .filter(receipt__created_at__range=(start_date, end_date))
          .values('product_name_snapshot')
          .annotate(
              total_qty=Sum('qty'),
              total_revenue=Sum('line_total')
          )
          .order_by('-total_qty')[:limit])
          
    results = []
    for item in qs:
        results.append({
            "product_name": item['product_name_snapshot'],
            "qty": item['total_qty'],
            "revenue": float(item['total_revenue'] or 0) * 100
        })
    return results

class TimeSeriesPoint(Schema):
    ds: str
    y: float

class TimeSeriesSummary(Schema):
    total: float
    avg: float
    min: float
    max: float

class TimeSeriesBreakdown(Schema):
    weekday_avg: dict
    hour_avg: dict

class TimeSeriesResponse(Schema):
    series: List[TimeSeriesPoint]
    summary: TimeSeriesSummary
    breakdown: Optional[TimeSeriesBreakdown] = None

@router.get("/timeseries", response=TimeSeriesResponse)
def get_timeseries(
    request, 
    metric: str = "revenue", 
    freq: str = "D", 
    start: Optional[str] = None, 
    end: Optional[str] = None,
    category_id: Optional[int] = None,
    product_id: Optional[int] = None
):
    start_date, end_date = get_date_range(start, end)
    
    # 1. Base QuerySet Setup
    if category_id or product_id:
        qs = ReceiptItem.objects.filter(receipt__created_at__range=(start_date, end_date))
        if category_id:
            qs = qs.filter(product__category_id=category_id)
        if product_id:
            qs = qs.filter(product_id=product_id)
            
        date_field = 'receipt__created_at'
        revenue_field = 'line_total'
    else:
        qs = Receipt.objects.filter(created_at__range=(start_date, end_date))
        date_field = 'created_at'
        revenue_field = 'total_amount'

    # 2. Aggregation Setup
    if freq == 'H':
        trunc_func = TruncHour(date_field)
    elif freq == 'W':
        trunc_func = TruncWeek(date_field)
    else:
        trunc_func = TruncDate(date_field)

    if metric == 'orders':
        if category_id or product_id:
            agg_expr = Count('receipt', distinct=True)
        else:
            agg_expr = Count('id')
    else:
        agg_expr = Sum(revenue_field)

    # 3. Time Series Data
    series_qs = (
        qs.annotate(ds=trunc_func)
          .values('ds')
          .annotate(y=agg_expr)
          .order_by('ds')
    )

    series_data = []
    y_values = []
    
    for item in series_qs:
        dt = item['ds']
        if not dt:
            continue
            
        if freq == 'H':
            dt_str = dt.strftime('%Y-%m-%d %H:00')
        else:
            dt_str = dt.strftime('%Y-%m-%d')
            
        y_val = float(item['y'] or 0)
        
        # If revenue, multiply by 100 to match frontend's cents setup
        if metric == 'revenue':
            y_val *= 100
            
        series_data.append({"ds": dt_str, "y": y_val})
        y_values.append(y_val)

    # 4. Summary Calculation
    if y_values:
        summary = {
            "total": sum(y_values),
            "avg": sum(y_values) / len(y_values),
            "min": min(y_values),
            "max": max(y_values)
        }
    else:
        summary = {"total": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

    # 5. Breakdown (Weekday & Hour of day)
    breakdown = {"weekday_avg": {}, "hour_avg": {}}
    
    unique_days = max((end_date - start_date).days, 1)
    weeks_count = max(unique_days / 7.0, 1.0)
    
    # Hour aggregation
    hour_qs = (
        qs.annotate(h=ExtractHour(date_field))
          .values('h')
          .annotate(y=agg_expr)
    )
    
    for item in hour_qs:
        h_val = item['h']
        if h_val is not None:
            val = float(item['y'] or 0)
            if metric == 'revenue':
                val *= 100
            breakdown["hour_avg"][str(h_val)] = round(val / unique_days, 2)

    # Weekday aggregation 
    wd_qs = (
        qs.annotate(wd=ExtractWeekDay(date_field))
          .values('wd')
          .annotate(y=agg_expr)
    )
    
    # ExtractWeekDay returns 1 (Sunday) to 7 (Saturday) in Django
    wd_map = {1: 'Sun', 2: 'Mon', 3: 'Tue', 4: 'Wed', 5: 'Thu', 6: 'Fri', 7: 'Sat'}
    
    for item in wd_qs:
        wd_val = item['wd']
        if wd_val is not None and wd_val in wd_map:
            val = float(item['y'] or 0)
            if metric == 'revenue':
                val *= 100
            breakdown["weekday_avg"][wd_map[wd_val]] = round(val / weeks_count, 2)

    return {
        "series": series_data,
        "summary": summary,
        "breakdown": breakdown
    }

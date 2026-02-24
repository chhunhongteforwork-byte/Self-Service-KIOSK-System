from ninja import NinjaAPI
from store.api import router as store_router
from store.analytics_api import router as analytics_router
from payments.api import router as payments_router

api = NinjaAPI(
    title="Kiosk API",
    version="1.0.0",
    description="API for Claims Self-Service Kiosk" # "Kiosk"
)

api.add_router("/store", store_router)
api.add_router("/analytics", analytics_router)
api.add_router("/payments", payments_router)

from store.forecast_api import router as forecast_router
api.add_router("/forecast", forecast_router)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import products
from app.core.config import settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Product Service API",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up API routes
app.include_router(products.router, prefix=settings.API_PREFIX)

# Register startup and shutdown events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "product-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
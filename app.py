from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PORT = int(os.getenv("PORT", 8001))

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing required environment variables SUPABASE_URL or SUPABASE_KEY")

# Remove trailing slash if present
SUPABASE_URL = SUPABASE_URL.rstrip('/')

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create httpx client with Supabase configuration
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

@app.get("/")
async def root():
    """Root endpoint to verify the API is running"""
    return {"status": "API is running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple health check query
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(f"{SUPABASE_URL}/rest/v1/categories?select=id&limit=1")
            response.raise_for_status()
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/category")
async def get_category(id: int = None):
    """Get a category by ID or a random category if no ID is provided"""
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            # Get category
            if id is None:
                response = await client.get(f"{SUPABASE_URL}/rest/v1/categories?select=*&limit=1")
            else:
                response = await client.get(f"{SUPABASE_URL}/rest/v1/categories?id=eq.{id}&select=*")
            
            response.raise_for_status()
            categories = response.json()
            
            if not categories:
                raise HTTPException(status_code=404, detail="Category not found")
                
            category = categories[0]
            
            # Get clues for the category
            clues_response = await client.get(
                f"{SUPABASE_URL}/rest/v1/clues?category_id=eq.{category['id']}&select=*"
            )
            clues_response.raise_for_status()
            category['clues'] = clues_response.json()
            
            return category
    except httpx.HTTPError as e:
        logger.error(f"Error fetching category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def get_categories():
    """Get all categories"""
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(f"{SUPABASE_URL}/rest/v1/categories?select=*")
            response.raise_for_status()
            return {"categories": response.json()}
    except httpx.HTTPError as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT) 
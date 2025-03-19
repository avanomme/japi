from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from supabase import create_client, Client
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

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client with custom options
try:
    options = {
        'headers': {
            'Authorization': f'Bearer {SUPABASE_KEY}'
        },
        'autoRefreshToken': False,
        'persistSession': False
    }
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

@app.get("/")
async def root():
    """Root endpoint to verify the API is running"""
    return {"status": "API is running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple health check query
        result = supabase.table('categories').select('id').limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/category")
async def get_category(id: int = None):
    """Get a category by ID or a random category if no ID is provided"""
    try:
        if id is None:
            # Get a random category
            result = supabase.table('categories').select('*').limit(1).execute()
        else:
            # Get specific category
            result = supabase.table('categories').select('*').eq('id', id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Category not found")
            
        category = result.data[0]
        
        # Get clues for the category
        clues = supabase.table('clues').select('*').eq('category_id', category['id']).execute()
        category['clues'] = clues.data
        
        return category
    except Exception as e:
        logger.error(f"Error fetching category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def get_categories():
    """Get all categories"""
    try:
        response = supabase.table("categories").select("*").execute()
        return {"categories": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT) 
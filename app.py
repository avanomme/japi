from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qvoktljkgsuyjilaofaa.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2b2t0bGprZ3N1eWppbGFvZmFhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDEyNTUyMTEsImV4cCI6MjA1NjgzMTIxMX0.3mSnm3DRGFkSBI5EFgjs3L9zKak9FxMOALBtb0HQdiU")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
async def root():
    """Root endpoint to verify the API is running"""
    return {"status": "API is running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        response = supabase.table("categories").select("id").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "supabase_url_configured": bool(SUPABASE_URL),
            "supabase_key_configured": bool(SUPABASE_KEY)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/category")
async def get_category(id: Optional[int] = None):
    """Get a category by ID or a random category if no ID is provided"""
    try:
        if id is not None:
            # Get the category
            category_response = supabase.table("categories").select("*").eq("id", id).execute()
            if not category_response.data:
                raise HTTPException(status_code=404, detail="Category not found")
            
            category = category_response.data[0]
            
            # Get the clues for this category
            clues_response = supabase.table("clues").select("*").eq("category_id", id).execute()
            
            # Add clues to the category response
            category["clues"] = clues_response.data
            return category
        else:
            # Get a random category
            # Note: This gets the first category. For true randomness, we'd need a different approach
            category_response = supabase.table("categories").select("*").limit(1).execute()
            if not category_response.data:
                raise HTTPException(status_code=404, detail="No categories found")
            
            category = category_response.data[0]
            
            # Get the clues for this category
            clues_response = supabase.table("clues").select("*").eq("category_id", category["id"]).execute()
            
            # Add clues to the category response
            category["clues"] = clues_response.data
            return category
    except Exception as e:
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
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port) 
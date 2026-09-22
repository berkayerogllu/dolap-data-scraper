import httpx
import asyncio
import os
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import List
from dotenv import load_dotenv
from schemas import ProductInfo

# Import our custom logger
from logger import get_logger

# Initialize the logger for this specific module
logger = get_logger(__name__)

# --- SECURITY CONFIGURATION ---
# Load environment variables from the .env file
load_dotenv()

# Define the header name where the API key should be passed
API_KEY_NAME = "X-API-Key"

# Securely fetch the secret key from the environment variables
SECRET_API_KEY = os.getenv("SECRET_API_KEY")

# Safety check to ensure the server doesn't start without a secure key
if not SECRET_API_KEY:
    logger.critical("SECRET_API_KEY is not set in the .env file!")
    raise ValueError("Missing SECRET_API_KEY environment variable.")

# Create an API key header instance
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency to check if the provided API key matches the secret key.
    Raises a 401 Unauthorized error if it doesn't match.
    """
    if api_key != SECRET_API_KEY:
        logger.warning("Failed authentication attempt with an invalid API Key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key. Access denied.",
        )
    return api_key
# ------------------------------

# Initialize the FastAPI application
app = FastAPI(
    title="Dolap Data Scraper",
    description="Data scraping and analysis tool for the shopping ecosystem",
    version="1.0.0"
)

def save_to_excel(data: List[ProductInfo], filepath: str):
    """
    Converts a list of Pydantic models to a Pandas DataFrame and saves it as an Excel file.
    """
    if not data:
        logger.warning(f"No data found to save for {filepath}.")
        return

    try:
        # Convert Pydantic models to a list of dictionaries
        dict_data = [item.model_dump() for item in data]
        df = pd.DataFrame(dict_data)
        
        # Save to Excel without the index column
        df.to_excel(filepath, index=False)
        logger.info(f"Success: {len(data)} products have been successfully saved to {filepath}.")
    except Exception as e:
        logger.error(f"Failed to save Excel file to {filepath}. Error: {e}")

async def fetch_dolap_data(keyword: str, page_limit: int) -> List[ProductInfo]:
    """
    Asynchronously fetches product data from the Dolap Search API.
    """
    base_url = "https://dolap.com/api/dolap/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    all_products = []
    logger.info(f"Starting scrape process for keyword: '{keyword}', max pages: {page_limit}")
    
    async with httpx.AsyncClient(headers=headers) as client:
        for page in range(page_limit):
            params = {
                "text": keyword,
                "order": "SUITABLE",
                "page": page
            }
            
            try:
                logger.info(f"Fetching page {page} for keyword '{keyword}'...")
                response = await client.get(base_url, params=params, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                products = data.get("products", [])
                
                if not products:
                    logger.info(f"No more products found on page {page}. Stopping pagination.")
                    break
                    
                for prod in products:
                    try:
                        validated_prod = ProductInfo(**prod)
                        all_products.append(validated_prod)
                    except Exception as e:
                        logger.warning(f"Failed to parse product ID {prod.get('id', 'UNKNOWN')}. Error: {e}")
                
                # Wait for half a second between pages to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error on page {page}: {e.response.status_code} - {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching page {page}: {e}")
                break
                
    logger.info(f"Scraping completed for '{keyword}'. Total products retrieved: {len(all_products)}")
    return all_products

@app.post("/scrape")
async def start_scraping(keyword: str, background_tasks: BackgroundTasks, pages: int = 1, api_key: str = Depends(verify_api_key)):
    """
    Endpoint to start the scraping process. Runs the Excel save task in the background.
    Protected by API Key verification.
    Saves files in a structured date format: data/YYYY-MM-DD/keyword_HH-MM-SS.xlsx
    """
    logger.info(f"Received authenticated scrape request. Keyword: '{keyword}', Pages: {pages}")
    
    # Generate timestamp components
    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    time_suffix = now.strftime("%H-%M-%S")
    
    # Create the date-based directory (e.g., data/2026-09-22)
    target_dir = os.path.join("data", date_folder)
    os.makedirs(target_dir, exist_ok=True)
    
    # Create a safe and unique filename (e.g., iphone_14-30-05.xlsx)
    safe_keyword = keyword.replace(" ", "_").lower()
    filename = f"{safe_keyword}_{time_suffix}.xlsx"
    filepath = os.path.join(target_dir, filename)
    
    # Fetch the data asynchronously
    scraped_data = await fetch_dolap_data(keyword=keyword, page_limit=pages)
    
    # Run the Excel save operation in the background
    background_tasks.add_task(save_to_excel, scraped_data, filepath)
    
    logger.info("Scraping task added to background tasks successfully.")
    return {
        "status": "success", 
        "message": f"Scraped {pages} page(s) for '{keyword}'. Found {len(scraped_data)} products. Saving to {filepath} in the background."
    }
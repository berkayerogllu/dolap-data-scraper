import httpx
import asyncio
import os
import pandas as pd
from fastapi import FastAPI, BackgroundTasks
from typing import List
from schemas import ProductInfo

# Import our custom logger
from logger import get_logger

# Initialize the logger for this specific module
logger = get_logger(__name__)

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
        dict_data = [item.model_dump() for item in data]
        df = pd.DataFrame(dict_data)
        
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
                        # Use warning for individual parsing errors so it doesn't stop the whole process
                        logger.warning(f"Failed to parse product ID {prod.get('id', 'UNKNOWN')}. Error: {e}")
                
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
async def start_scraping(keyword: str, background_tasks: BackgroundTasks, pages: int = 1):
    """
    Endpoint to start the scraping process. Runs the Excel save task in the background.
    """
    logger.info(f"Received scrape request via API. Keyword: '{keyword}', Pages: {pages}")
    
    os.makedirs("data", exist_ok=True)
    filename = keyword.replace(" ", "_").lower() + ".xlsx"
    filepath = os.path.join("data", filename)
    
    scraped_data = await fetch_dolap_data(keyword=keyword, page_limit=pages)
    
    background_tasks.add_task(save_to_excel, scraped_data, filepath)
    
    logger.info("Scraping task added to background tasks successfully.")
    return {
        "status": "success", 
        "message": f"Scraped {pages} page(s) for '{keyword}'. Found {len(scraped_data)} products. Saving to {filepath} in the background."
    }
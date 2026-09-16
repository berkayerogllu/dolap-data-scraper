import httpx
import asyncio
import os
import pandas as pd
from fastapi import FastAPI, BackgroundTasks
from typing import List
from schemas import ProductInfo

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
    # Do not proceed if the data list is empty
    if not data:
        print("No data found to save.")
        return

    # Convert Pydantic models to a list of dictionaries
    dict_data = [item.model_dump() for item in data]
    df = pd.DataFrame(dict_data)
    
    # Save to Excel without the index column
    df.to_excel(filepath, index=False)
    print(f"Success: {len(data)} products have been saved to {filepath}.")


async def fetch_dolap_data(keyword: str, page_limit: int) -> List[ProductInfo]:
    """
    Asynchronously fetches product data from the Dolap Search API.
    """
    base_url = "https://dolap.com/api/dolap/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    all_products = []
    
    # Initialize an asynchronous HTTP client
    async with httpx.AsyncClient(headers=headers) as client:
        for page in range(page_limit):
            # Query parameters are automatically URL-encoded by httpx
            params = {
                "text": keyword,
                "order": "SUITABLE",
                "page": page
            }
            
            try:
                response = await client.get(base_url, params=params, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                products = data.get("products", [])
                
                # Break the loop if there are no products on the current page
                if not products:
                    print(f"No more products found on page {page}. Stopping.")
                    break
                    
                # Validate and parse each product from the JSON response using our Pydantic model
                for prod in products:
                    try:
                        validated_prod = ProductInfo(**prod)
                        all_products.append(validated_prod)
                    except Exception as e:
                        print(f"Failed to parse a product: {e}")
                
                # Wait for half a second between pages to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break
                
    return all_products


@app.post("/scrape")
async def start_scraping(keyword: str, background_tasks: BackgroundTasks, pages: int = 1):
    """
    Endpoint to start the scraping process. Runs the Excel save task in the background.
    """
    # Ensure the 'data' directory exists in the root folder
    os.makedirs("data", exist_ok=True)
    
    # Create a safe filename and map it to the 'data' directory
    filename = keyword.replace(" ", "_").lower() + ".xlsx"
    filepath = os.path.join("data", filename)
    
    # Call the async data fetching function
    scraped_data = await fetch_dolap_data(keyword=keyword, page_limit=pages)
    
    # Add the saving process to background tasks to prevent API timeout
    background_tasks.add_task(save_to_excel, scraped_data, filepath)
    
    return {
        "status": "success", 
        "message": f"Scraped {pages} page(s) for '{keyword}'. Found {len(scraped_data)} products. Saving to {filepath} in the background."
    }
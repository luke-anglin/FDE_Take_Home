import os
import logging
import json
import re
from creative_generator import CreativeGenerator, ContentGenerationError
from dropbox_helper import DropboxHelper
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from agent import run_post_process_checks

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class ProductBrief(BaseModel):
    description: str

class CampaignBrief(BaseModel):
    campaign_name: str
    region: str
    audience: str
    message: str
    brand_colors: List[str]
    products: Dict[str, ProductBrief]

@app.post("/process-brief")
async def process_brief_endpoint(
    brief_data: str = Form(...),
    base_image_1: Optional[UploadFile] = File(None),
    base_image_desc_1: Optional[str] = Form(None),
    base_image_2: Optional[UploadFile] = File(None),
    base_image_desc_2: Optional[str] = Form(None)
):
    logging.info("New campaign request received. Starting pipeline...")
    try:
        brief = CampaignBrief(**json.loads(brief_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid brief format: {e}")

    safe_campaign_name = re.sub(r'[^\w\-_\. ]', '', brief.campaign_name).strip().replace(' ', '_')
    if not safe_campaign_name:
        raise HTTPException(status_code=400, detail="Campaign name is invalid or empty.")
    
    campaign_folder_path = f"/{safe_campaign_name}"

    try:
        dropbox_app_key = os.getenv("DROPBOX_APP_KEY")
        dropbox_app_secret = os.getenv("DROPBOX_APP_SECRET")
        dropbox_refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
        if not all([dropbox_app_key, dropbox_app_secret, dropbox_refresh_token]):
            raise HTTPException(status_code=500, detail="Dropbox environment variables are not configured.")

        dropbox_helper = DropboxHelper(app_key=dropbox_app_key, app_secret=dropbox_app_secret, refresh_token=dropbox_refresh_token)

        if dropbox_helper.folder_exists(campaign_folder_path):
            raise HTTPException(status_code=409, detail=f"A campaign named '{brief.campaign_name}' already exists. Please use a unique name.")

        base_images_data = []
        if base_image_1 and base_image_desc_1:
            base_images_data.append({
                "image_bytes": await base_image_1.read(),
                "description": base_image_desc_1
            })
        if base_image_2 and base_image_desc_2:
            base_images_data.append({
                "image_bytes": await base_image_2.read(),
                "description": base_image_desc_2
            })
        
        generator = CreativeGenerator()

        try:
            local_image_paths = generator.process_and_save_creatives(brief, base_images_data)
        except ContentGenerationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not local_image_paths:
            return {"message": "Brief processed, but no images were generated.", "image_urls": []}

        image_urls = []
        for local_path in local_image_paths:
            filename = os.path.basename(local_path)
            match = re.search(r'_(\d+x\d+)_', filename)
            aspect_ratio_folder = match.group(1).replace('x', ':') if match else ""
            dropbox_path = f"{campaign_folder_path}/{aspect_ratio_folder}/{filename}"
            
            shareable_link = dropbox_helper.upload_file(local_path, dropbox_path)
            os.remove(local_path)
            if shareable_link:
                image_urls.append(shareable_link)
                logging.info(f"SUCCESS: Creative uploaded to Dropbox path: {dropbox_path}")

        logging.info("Campaign pipeline completed successfully.")
        try:
            logging.info("Handing off to Agent for post-processing checks...")
            run_post_process_checks(brief, image_urls)
        except Exception as e:
            logging.error(f"Agent failed to run post-processing checks: {e}")
        return {"message": "Brief processed successfully.", "image_urls": image_urls}

    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logging.error(f"An unexpected pipeline failure occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@app.get("/list-campaigns")
async def list_campaigns_endpoint():
    logging.info("API request received to list all campaigns.")
    try:
        dropbox_app_key = os.getenv("DROPBOX_APP_KEY")
        dropbox_app_secret = os.getenv("DROPBOX_APP_SECRET")
        dropbox_refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
        if not all([dropbox_app_key, dropbox_app_secret, dropbox_refresh_token]):
            raise HTTPException(status_code=500, detail="Dropbox environment variables are not configured.")

        dropbox_helper = DropboxHelper(app_key=dropbox_app_key, app_secret=dropbox_app_secret, refresh_token=dropbox_refresh_token)
        campaigns_data = dropbox_helper.list_campaign_assets()
        return campaigns_data
    except Exception as e:
        logging.error(f"API Error: Failed to list campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
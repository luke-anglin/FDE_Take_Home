import dropbox
import os
import logging
import webbrowser
import requests
import secrets
import hashlib
import base64
from dotenv import load_dotenv, find_dotenv, set_key
from typing import Dict, List

# ==============================================================================
# The DropboxHelper class used by the main application
# ==============================================================================

class DropboxHelper:
    def __init__(self, app_key, app_secret, refresh_token):
        try:
            self.dbx = dropbox.Dropbox(app_key=app_key, app_secret=app_secret, oauth2_refresh_token=refresh_token)
            self.dbx.users_get_current_account()
            logging.info("Dropbox client authenticated.")
        except Exception as e:
            logging.error(f"Failed to initialize Dropbox client: {e}")
            raise

    def folder_exists(self, path: str) -> bool:
        try:
            self.dbx.files_list_folder(path, limit=1)
            return True
        except dropbox.exceptions.ApiError as err:
            if isinstance(err.error, dropbox.files.ListFolderError) and err.error.get_path().is_not_found():
                return False
            raise err

    def upload_file(self, file_path, dropbox_path):
        try:
            with open(file_path, "rb") as f:
                self.dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode('overwrite'))
            return self._get_shareable_link(dropbox_path)
        except Exception as e:
            logging.error(f"An unexpected error occurred during Dropbox upload: {e}")
            return None

    def _get_shareable_link(self, dropbox_path):
        try:
            links = self.dbx.sharing_list_shared_links(path=dropbox_path, direct_only=True).links
            if links:
                return links[0].url.replace("dl=0", "raw=1")
            else:
                settings = dropbox.sharing.SharedLinkSettings(requested_visibility=dropbox.sharing.RequestedVisibility.public)
                shared_link = self.dbx.sharing_create_shared_link_with_settings(path=dropbox_path, settings=settings)
                return shared_link.url.replace("dl=0", "raw=1")
        except Exception as e:
            logging.error(f"An unexpected error during shareable link retrieval for {dropbox_path}: {e}")
            return None

    # --- THIS IS THE NEW, SIMPLIFIED, AND CORRECTED GALLERY FUNCTION ---
    def list_campaign_assets(self) -> dict:
        logging.info("Fetching all campaign assets from Dropbox...")
        campaigns = {}
        try:
            # Recursively find all items in the root folder
            result = self.dbx.files_list_folder("", recursive=True)
            # Filter to get only the files, not folders
            files_metadata = [entry for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]

            if not files_metadata:
                logging.info("No campaign files found in Dropbox.")
                return {}

            # Process each file one by one
            for entry in files_metadata:
                path_parts = entry.path_display.strip('/').split('/')
                if not path_parts: continue
                
                campaign_name = path_parts[0].replace('_', ' ')
                if campaign_name not in campaigns:
                    campaigns[campaign_name] = []
                
                # Get the shareable link for this specific file
                image_url = self._get_shareable_link(entry.path_display)

                if image_url:
                    campaigns[campaign_name].append({
                        "url": image_url,
                        "filename": entry.name
                    })

            logging.info(f"Successfully found and organized {len(campaigns)} campaigns.")
            return campaigns
        except Exception as e:
            logging.error(f"A critical error occurred while listing campaign assets: {e}")
            return {}
if __name__ == "__main__":
    print("--- Dropbox Refresh Token Generator (PKCE Secure Flow) ---")

    load_dotenv(find_dotenv())
    APP_KEY = os.getenv("DROPBOX_APP_KEY")
    APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

    if not APP_KEY or not APP_SECRET:
        print("\n[ERROR] DROPBOX_APP_KEY and DROPBOX_APP_SECRET must be set in your .env file first.")
        exit()

    code_verifier = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('utf-8').replace('=', '')

    redirect_uri = "http://localhost:8000"
    auth_url = (
        f"https://www.dropbox.com/oauth2/authorize?"
        f"client_id={APP_KEY}&"
        "response_type=code&"
        "token_access_type=offline&"
        f"redirect_uri={redirect_uri}&"
        "state=optional_string&"
        f"code_challenge={code_challenge}&"
        "code_challenge_method=S256"
    )

    print("\nStep 1: Your browser will now open to authorize this application.")
    print("Step 2: Click 'Allow' on the Dropbox page.")
    print("Step 3: Copy the 'code' from the URL you are redirected to.")
    webbrowser.open(auth_url)
    
    auth_code = input("\n> Enter the authorization code here: ").strip()

    if not auth_code:
        print("\n[ERROR] Authorization code cannot be empty.")
        exit()

    print("\nExchanging authorization code for a refresh token...")
    token_url = "https://api.dropbox.com/oauth2/token"
    payload = {
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    try:
        response = requests.post(token_url, data=payload, auth=(APP_KEY, APP_SECRET))
        response.raise_for_status()
        
        tokens = response.json()
        refresh_token = tokens.get("refresh_token")

        if not refresh_token:
            print(f"\n[ERROR] Could not retrieve refresh token. Dropbox response: {tokens}")
            exit()
            
        dotenv_path = find_dotenv()
        if not dotenv_path:
            with open(".env", "w") as f: pass
            dotenv_path = find_dotenv()

        set_key(dotenv_path, "DROPBOX_REFRESH_TOKEN", refresh_token)
        
        print("\n✅ Success! Your PKCE-secured refresh token has been saved to your .env file.")

    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] An error occurred while communicating with Dropbox: {e}")
        print(f"Server Response: {e.response.text if e.response else 'No response'}")
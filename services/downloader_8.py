import requests
import base64
import json
import time
import os
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- CONFIG ---
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION")

# --- SETUP RETRY SESSION ---
def create_retry_session(retries=3, backoff_factor=2.0, timeout=30):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # DO NOT override session.request directly!
    return session

session = create_retry_session()

# --- AUTH ---
def get_access_token(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    data = {'grant_type': 'client_credentials'}
    response = session.post('https://api.8x8.com/oauth/v2/token', headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

# --- CHECK STATUS ---
def check_bulk_download_status(access_token, region, download_id):
    url = f"https://api.8x8.com/storage/{region}/v3/bulk/download/status/{download_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = session.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# --- START DOWNLOAD ---
def start_bulk_download(access_token, region, recording_ids):
    url = f"https://api.8x8.com/storage/{region}/v3/bulk/download/start"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = session.post(url, headers=headers, data=json.dumps(recording_ids))
    response.raise_for_status()
    return response.json()

# --- FETCH RECORDINGS ---
def get_call_recordings_and_download(access_token, region, target_user_id):
    url = f'https://api.8x8.com/storage/{region}/v3/objects'
    params = {
        'filter': 'type==callrecording;duration=gt=100',
        'sortField': 'createdTime',
        'sortDirection': 'DESC',
        'pageKey': 0,
        'limit': 100
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = session.get(url, headers=headers, params=params)
    response.raise_for_status()

    content = response.json().get("content", [])
    for element in content:
        if element['userId'] == target_user_id:
            return start_bulk_download(access_token, region, [element["id"]])
    return None

def get_calls( target_user_id, amount):
    token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    url = f'https://api.8x8.com/storage/{REGION}/v3/objects'
    params = {
        'filter': 'type==callrecording;duration=gt=100',
        'sortField': 'createdTime',
        'sortDirection': 'DESC',
        'pageKey': 0,
        'limit': 100
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    response = session.get(url, headers=headers, params=params)
    response.raise_for_status()

    content = response.json().get("content", [])
    calls =[]
    _amount = 0
    for element in content:
        if element['userId'] == target_user_id and _amount<=amount:
            calls.append(element)
            _amount+=1
    return calls

# --- DOWNLOAD ZIP ---
def download_bulk_zip(access_token, region, zip_id, target_user_id):
    output_dir = f"{target_user_id}"
    output_path = os.path.join(output_dir, "downloaded_recordings.zip")
    os.makedirs(output_dir, exist_ok=True)

    url = f"https://api.8x8.com/storage/{region}/v3/bulk/download/{zip_id}.zip"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    logging.info(f"🔽 Downloading ZIP for user {target_user_id}...")
    response = session.get(url, headers=headers, stream=True, timeout=120)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logging.info(f"✅ ZIP saved to {output_path}")
    return output_path

# --- MAIN WORKFLOW ---
def download_main(target_user_id):
    try:
        logging.info(f"🔐 Starting download for user: {target_user_id}")
        token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        logging.info(f"✅ Access token acquired")

        download_info = get_call_recordings_and_download(token, REGION, target_user_id)
        logging.info(f"📥 Download info received: {download_info}")

        if not download_info:
            logging.warning("⚠️ No matching recordings found for this user.")
            return None

        download_id = download_info.get('zipName')
        if not download_id:
            logging.error("❌ zipName not found in download_info")
            return None

        logging.info(f"🕒 Waiting for bulk download job with ID: {download_id}")
        time.sleep(5)

        status_info = check_bulk_download_status(token, REGION, download_id)
        logging.info(f"📦 Download job status: {status_info}")

        if status_info.get('status') == 'DONE':
            return download_bulk_zip(token, REGION, download_id, target_user_id)
        else:
            logging.warning(f"⌛ Download job not ready. Status: {status_info.get('status')}")
            return None

    except Exception as e:
        logging.error(f"❌ Error during download process: {e}", exc_info=True)
        return None

# Need to refactore to comebine this with the above function in the future
def download_single(target_user_id, call_id):
    try:
        logging.info(f"🔐 Starting download for user: {target_user_id} and a specific call {call_id}")
        token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        logging.info(f"✅ Access token acquired")

        download_info = start_bulk_download(token, REGION, [call_id])

        # download_info = get_call_recordings_and_download(token, REGION, target_user_id)
        # logging.info(f"📥 Download info received: {download_info}")

        if not download_info:
            logging.warning("⚠️ No matching recordings found for this user.")
            return None

        download_id = download_info.get('zipName')
        if not download_id:
            logging.error("❌ zipName not found in download_info")
            return None

        logging.info(f"🕒 Waiting for bulk download job with ID: {download_id}")
        time.sleep(5)

        status_info = check_bulk_download_status(token, REGION, download_id)
        logging.info(f"📦 Download job status: {status_info}")

        if status_info.get('status') == 'DONE':
            return download_bulk_zip(token, REGION, download_id, target_user_id)
        else:
            logging.warning(f"⌛ Download job not ready. Status: {status_info.get('status')}")
            return None

    except Exception as e:
        logging.error(f"❌ Error during download process: {e}", exc_info=True)
        return None

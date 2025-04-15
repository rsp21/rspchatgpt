import requests
import base64
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REGION = os.getenv("REGION")

# --- AUTH ---
def get_access_token(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post('https://api.8x8.com/oauth/v2/token', headers=headers, data=data)

    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    else:
        raise Exception(f"Token request failed: {response.status_code} - {response.text}")

# --- CHECK STATUS ---
def check_bulk_download_status(access_token, region, download_id):
    url = f"https://api.8x8.com/storage/{region}/v3/bulk/download/status/{download_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get status: {response.status_code} - {response.text}")

# --- START DOWNLOAD ---
def start_bulk_download(access_token, region, recording_ids):
    url = f"https://api.8x8.com/storage/{region}/v3/bulk/download/start"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(recording_ids))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Request failed: {response.status_code} - {response.text}")

# --- FETCH RECORDINGS & START DOWNLOAD ---
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
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        content = response.json().get("content", [])
        for element in content:
            if element['userId'] == target_user_id:
                return start_bulk_download(access_token, region, [element["id"]])
        return None
    else:
        raise Exception(f"Failed to fetch recordings: {response.status_code} - {response.text}")

# --- DOWNLOAD ZIP ---
def download_bulk_zip(access_token, region, zip_id, output_path="downloaded_recordings.zip"):
    url = f"https://api.8x8.com/storage/{region}/v3/bulk/download/{zip_id}.zip"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return output_path
    else:
        raise Exception(f"Download failed: {response.status_code} - {response.text}")

def download_main(target_user_id):
    try:
        token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        download_info = get_call_recordings_and_download(token, REGION, target_user_id)
        time.sleep(5)
        download_id = download_info['zipName']
        status_info = check_bulk_download_status(token, REGION, download_id)
      
        if status_info['status'] == 'DONE':
            path = download_bulk_zip(token, REGION, download_id)
            return path
        else:
            print(f"⌛ Still processing: {status_info['status']}")
        

    except Exception as e:
        print(f"❌ Error: {str(e)}")

# # --- MAIN EXECUTION EXAMPLE (can be called in a Flask endpoint) ---
# if __name__ == "__main__":
#     target_user_id = '619z7VC0TZaP1DhYNAsnWg'  # Example user ID

#     try:
#         token = get_access_token(CLIENT_ID, CLIENT_SECRET)
#         download_info = get_call_recordings_and_download(token, REGION, target_user_id)
#         time.sleep(5)
#         download_id = download_info['zipName']
#         status_info = check_bulk_download_status(token, REGION, download_id)
        

#         if status_info['status'] == 'DONE':
#             path = download_bulk_zip(token, REGION, download_id)
#             print(f"✅ File saved at: {path}")
#         else:
#             print(f"⌛ Still processing: {status_info['status']}")
        

#     except Exception as e:
#         print(f"❌ Error: {str(e)}")

import requests
import time
import json

# Your API token
vance_api_key = "8c7a5f64ceff9704af727165f2e424f3"

# Path to your image file
image_path = r"C:\Users\uabin\Downloads\IMG_5421.jpg"


# 1. Upload image
def upload_image():
    url = "https://api-service.vanceai.com/web_api/v1/upload"
    files = {"image": open(image_path, "rb")}
    data = {"api_token": vance_api_key}

    response = requests.post(url, files=files, data=data)
    response.raise_for_status()
    return response.json()

# 2. Start processing (transform)
def start_transform(uid):
    url = "https://api-service.vanceai.com/web_api/v1/transform"
    jconfig = {
        # Example config; adjust as needed per API docs
        "tool": "smart_enhance",
        "model_id": "default",
        "quality": "high"
    }
    data = {
        "api_token": vance_api_key,
        "uid": uid,
        "jconfig": json.dumps(jconfig),
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()

# 3. Poll status until finished
def poll_status(trans_id, max_attempts=30, interval=6):
    url = "https://api-service.vanceai.com/web_api/v1/result"
    params = {
        "api_token": vance_api_key,
        "trans_id": trans_id,
    }

    for attempt in range(max_attempts):
        print(f"Checking status, attempt {attempt + 1}...")
        response = requests.get(url, params=params)
        if response.status_code == 200:
            resp_json = response.json()
            status = resp_json.get("data", {}).get("status")
            print("Status:", status)
            if status == "finish" or status == "finished":
                # Assuming image URL is returned here
                image_url = resp_json["data"].get("image_url")
                if image_url:
                    return image_url
                else:
                    print("No image_url found in response.")
                    return None
            else:
                time.sleep(interval)
        else:
            print(f"Error getting status: HTTP {response.status_code}")
            print(response.text)
            break
    return None

def main():
    # Upload image
    upload_resp = upload_image()
    print("Upload response:", upload_resp)

    if upload_resp.get("code") == 200:
        uid = upload_resp["data"]["uid"]
        print("Uploaded image UID:", uid)
    else:
        print("Failed to upload image.")
        return

    # Start transformation
    transform_resp = start_transform(uid)
    print("Transform response:", transform_resp)

    if transform_resp.get("code") == 200:
        trans_id = transform_resp["data"]["trans_id"]
        print("Transaction ID:", trans_id)
    else:
        print("Failed to start transform.")
        return

    # Poll status
    final_image_url = poll_status(trans_id)
    if final_image_url:
        print("Final processed image URL:", final_image_url)
    else:
        print("Failed to get final image URL.")

if __name__ == "__main__":
    main()

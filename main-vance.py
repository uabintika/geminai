import streamlit as st
import os
import requests
import time
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
token = os.getenv("AIKEY")
vance_api_key = os.getenv("VANCEKEY")
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-nano"

client = OpenAI(base_url=endpoint, api_key=token)

st.title("Echo Bot with Disney Converter 🎭")

# Chat history for text chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
style = st.selectbox("Choose Disney style", ["disney_boy", "disney_girl"])

prompt = st.chat_input("What is up?")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    system_message = [{"role": "system", "content": "You are a helpful assistant."}]
    message_to_send_with_history = system_message + st.session_state.messages

    response = client.chat.completions.create(
        model=model,
        messages=message_to_send_with_history,
        temperature=0.7,
        top_p=1.0,
    )

    response_text = response.choices[0].message.content

    with st.chat_message("assistant"):
        st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})

if uploaded_file is not None:
    st.write("Uploading image to Vance AI...")

    # Read bytes once
    image_bytes = uploaded_file.read()

    # Upload image to VanceAI
    upload_response = requests.post(
        "https://api-service.vanceai.com/web_api/v1/upload",
        files={"file": ("image.jpg", image_bytes, "image/jpeg")},
        data={"api_token": vance_api_key}
    )

    if upload_response.status_code == 200:
        upload_result = upload_response.json()
        if upload_result.get("code") == 200:
            image_uid = upload_result["data"]["uid"]
            st.write("Image uploaded. Starting processing...")

            jconfig = {
                "name": "img2anime",
                "config": {
                    "module": "img2anime",
                    "module_params": {
                        "model_name": style,  # Use selected style dynamically
                        "prompt": "",
                        "overwrite": False,
                        "denoising_strength": 0.75
                    }
                },
                "cn_configs": [
                    {"image_uid": image_uid, "cn_name": "cartoon_tile"},
                    {"image_uid": image_uid, "cn_name": "cartoon_lineart"}
                ]
            }

            form_data = {
                "api_token": vance_api_key,
                "uid": image_uid,
                "jconfig": json.dumps(jconfig),
            }

            process_response = requests.post(
                "https://api-service.vanceai.com/web_api/v1/transform",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if process_response.status_code == 200:
                process_result = process_response.json()
                if process_result.get("code") == 200:
                    trans_id = process_result["data"]["trans_id"]
                    st.write(f"Processing started (Transaction ID: {trans_id})")

                    # Poll for status
                    for attempt in range(30):
                        time.sleep(6)
                        status_response = requests.get(
                            "https://api-service.vanceai.com/web_api/v1/progress",
                            params={"api_token": vance_api_key, "trans_id": trans_id}
                        )
                        st.write(f"Attempt {attempt + 1}: HTTP {status_response.status_code}")

                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get("code") == 200:
                                status = status_data["data"]["status"]
                                st.write(f"Status: {status}")

                                if status == "finish" or status == "finished":
                                    st.write("Processing finished. Downloading image...")

                                    # Download the processed image from the /download endpoint
                                    download_url = f"https://api-service.vanceai.com/web_api/v1/download?trans_id={trans_id}&api_token={vance_api_key}"
                                    download_response = requests.get(download_url, stream=True)

                                    if download_response.status_code == 200:
                                        output_path = "output_disney_image.jpg"
                                        with open(output_path, "wb") as f:
                                            for chunk in download_response.iter_content(chunk_size=8192):
                                                if chunk:
                                                    f.write(chunk)
                                        st.image(output_path, caption="Here is your Disney version!")
                                    else:
                                        st.error(f"Failed to download the processed image. HTTP {download_response.status_code}")

                                    break
                                elif status == "failed":
                                    st.error("Image processing failed.")
                                    break
                                else:
                                    st.write("Processing... please wait.")
                            else:
                                st.error(f"Error from API: {status_data.get('message')}")
                                break
                        else:
                            st.error("Failed to get processing status.")
                            break
                    else:
                        st.warning("Processing timed out.")
                else:
                    st.error(f"Processing error: {process_result.get('message', 'Unknown error')}")
            else:
                st.error("Image processing request failed.")
        else:
            st.error(f"Image upload error: {upload_result.get('message', 'Unknown error')}")
    else:
        st.error("Image upload failed.")

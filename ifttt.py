from os import environ

import requests
from streamlit.runtime.uploaded_file_manager import UploadedFile

IMGBB_API_KEY = environ["IMGBB_API_KEY"]

IFTTT_EVENT_NAME = environ["IFTTT_EVENT_NAME"]
IFTTT_WEBHOOK_KEY = environ["IFTTT_WEBHOOK_KEY"]
IFTTT_WEBHOOK_URL = (
    f"https://maker.ifttt.com/trigger/{IFTTT_EVENT_NAME}/with/key/{IFTTT_WEBHOOK_KEY}"
)


def upload_image(image: UploadedFile) -> str:
    image.seek(0)
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        files={"image": (image.name, image, image.type)},
        data={"key": IMGBB_API_KEY, "expiration": 86400},
        timeout=30,
    )
    response.raise_for_status()
    image_url = response.json()["data"]["url"]
    if not isinstance(image_url, str) or not image_url.strip():
        raise ValueError("ImgBB did not return a valid image URL.")
    return image_url


def queue_tweet(text: str, image_url: str | None = None) -> None:
    payload = {"value1": text}
    if image_url:
        payload["value2"] = image_url
    response = requests.post(IFTTT_WEBHOOK_URL, data=payload, timeout=30)
    response.raise_for_status()

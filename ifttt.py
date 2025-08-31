from os import environ

import requests
from streamlit.runtime.uploaded_file_manager import UploadedFile

IFTTT_EVENT_NAME = environ["IFTTT_EVENT_NAME"]
IFTTT_WEBHOOK_KEY = environ["IFTTT_WEBHOOK_KEY"]
IFTTT_WEBHOOK_URL = (
    f"https://maker.ifttt.com/trigger/{IFTTT_EVENT_NAME}/with/key/{IFTTT_WEBHOOK_KEY}"
)


def upload_image(image: UploadedFile) -> str:
    image.seek(0)
    response = requests.post(
        "https://0x0.st",
        files={"file": (image.name, image, image.type)},
        headers={"User-Agent": "ugfess/1.0"},
    )
    response.raise_for_status()
    return response.text.strip()


def queue_tweet(text: str, image_url: str | None = None) -> None:
    payload = {"value1": text}
    if image_url:
        payload["value2"] = image_url
    response = requests.post(IFTTT_WEBHOOK_URL, data=payload, timeout=30)
    response.raise_for_status()

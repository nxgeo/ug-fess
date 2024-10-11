from os import environ
from time import sleep
from unicodedata import normalize

from emoji import analyze, EmojiMatch
from pytwitter import Api
from pytwitter.models import Tweet
from requests import get
from streamlit.runtime.uploaded_file_manager import UploadedFile


MAX_WEIGHTED_TWEET_LENGTH = 280

x_api = Api(
    consumer_key=environ["X_CONSUMER_KEY"],
    consumer_secret=environ["X_CONSUMER_SECRET"],
    access_token=environ["X_ACCESS_TOKEN"],
    access_secret=environ["X_ACCESS_TOKEN_SECRET"],
)


def get_character_weight(char: str | EmojiMatch) -> int:
    if isinstance(char, EmojiMatch):
        return 2

    weight_one_ranges = [
        (0, 4351),
        (8192, 8205),
        (8208, 8223),
        (8242, 8247),
    ]
    char_code_point = ord(char)

    for range_start, range_end in weight_one_ranges:
        if range_start <= char_code_point <= range_end:
            return 1

    return 2  # Default weight


def calculate_weighted_tweet_length(text: str) -> int:
    normalized_text = normalize("NFC", text)
    weighted_length = 0

    for _, char in analyze(normalized_text, non_emoji=True):
        weighted_length += get_character_weight(char)

    return weighted_length


CONT_SUFFIX = " (cont.)"
WEIGHTED_CONT_SUFFIX_LENGTH = calculate_weighted_tweet_length(CONT_SUFFIX)

MAX_WEIGHTED_TWEET_LENGTH_WITHOUT_SUFFIX = (
    MAX_WEIGHTED_TWEET_LENGTH - WEIGHTED_CONT_SUFFIX_LENGTH
)

SPACE_WEIGHT = get_character_weight(" ")


def split_tweet(text: str) -> list[str]:
    parts = []
    part = ""
    weighted_part_length = 0

    for token in text.split():
        weighted_token_length = calculate_weighted_tweet_length(token)
        weighted_part_length += weighted_token_length

        if part:
            weighted_part_length += SPACE_WEIGHT

        if weighted_part_length <= MAX_WEIGHTED_TWEET_LENGTH_WITHOUT_SUFFIX:
            if part:
                part = f"{part} {token}"
            else:
                part = token
        else:
            parts.append(part + CONT_SUFFIX)
            part = token
            weighted_part_length = weighted_token_length

    if part:
        if weighted_part_length == WEIGHTED_CONT_SUFFIX_LENGTH:
            parts[-1] = f"{parts[-1][:-WEIGHTED_CONT_SUFFIX_LENGTH]} {part}"
        else:
            parts.append(part)

    return parts


CHUNK_SIZE_IN_BYTES = 1024 * 1024 // 2


def upload_images(images: list[UploadedFile]) -> list[str]:
    media_ids = []

    for image in images:
        media_id = x_api.upload_media_chunked_init(
            image.size, image.type, "tweet_image"
        ).media_id_string

        image.seek(0)

        segment_index = 0
        while chunk := image.read(CHUNK_SIZE_IN_BYTES):
            x_api.upload_media_chunked_append(media_id, segment_index, chunk)
            segment_index += 1

        processing_info = x_api.upload_media_chunked_finalize(media_id).processing_info

        if processing_info:
            while processing_info.state != "succeeded":
                sleep(processing_info.check_after_secs)

                processing_info = x_api.upload_media_chunked_status(
                    media_id
                ).processing_info

                if processing_info.state == "failed":
                    raise Exception("Image upload failed")

        media_ids.append(media_id)

    return media_ids


def create_thread(
    text: str | None = None, media_ids: list[str] | None = None
) -> list[Tweet]:
    texts = split_tweet(text)
    tweets = []
    in_reply_to_tweet_id = None

    for text in texts:
        tweet = x_api.create_tweet(
            text=text,
            media_media_ids=media_ids,
            reply_in_reply_to_tweet_id=in_reply_to_tweet_id,
        )
        tweets.append(tweet)
        in_reply_to_tweet_id = tweet.id

        if media_ids:
            media_ids = None

    return tweets


def create_tweet(
    text: str | None = None, media_ids: list[str] | None = None
) -> Tweet | list[Tweet]:
    weighted_tweet_length = calculate_weighted_tweet_length(text)

    if weighted_tweet_length <= MAX_WEIGHTED_TWEET_LENGTH:
        return x_api.create_tweet(text=text, media_media_ids=media_ids)
    else:
        return create_thread(text, media_ids)


OEMBED_RESOURCE_URL = "https://publish.twitter.com/oembed"

STATUS_BASE_URL = "https://x.com/ug_fess/status/"


def get_tweet_oembed_html(tweet_id: str) -> str:
    tweet_url = STATUS_BASE_URL + tweet_id

    params = {
        "url": tweet_url,
        "hide_media": "true",
        "hide_thread": "true",
        "align": "center",
        "theme": "dark",
        "dnt": "true",
    }

    headers = {"Accept": "application/json"}

    try:
        response = get(OEMBED_RESOURCE_URL, params, headers=headers)
        oembed_data = response.json()
    except Exception:
        return ""

    return oembed_data.get("html", "")

from unicodedata import normalize

from emoji import EmojiMatch, analyze
import requests

MAX_WEIGHTED_TWEET_LENGTH = 280

OEMBED_RESOURCE_URL = "https://publish.twitter.com/oembed"
AUTHOR_URL = "https://twitter.com/ug_fess"


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

    return 2


def calculate_weighted_tweet_length(text: str) -> int:
    normalized_text = normalize("NFC", text)
    weighted_length = 0

    for _, char in analyze(normalized_text, non_emoji=True):
        weighted_length += get_character_weight(char)

    return weighted_length


def is_valid_tweet_url(tweet_url: str) -> bool:
    response = requests.get(
        OEMBED_RESOURCE_URL,
        {"url": tweet_url},
        headers={"Accept": "application/json"},
    )

    if response.status_code == 404:
        return False

    response.raise_for_status()

    oembed_data = response.json()

    return oembed_data["author_url"] == AUTHOR_URL

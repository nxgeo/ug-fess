import os

import filetype
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.uploaded_file_manager import UploadedFile
from urlextract import URLExtract

from auth import authenticate
from ifttt import queue_tweet, upload_image
from tweet_utils import (
    MAX_WEIGHTED_TWEET_LENGTH,
    calculate_weighted_tweet_length,
    is_valid_tweet_url,
)

MENFESS_SIGNATURE = "yuji!"

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTS = ["jpeg", "jpg", "png", "webp"]
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@st.dialog("Status")
def show_menfess_creation_status(status_type: str, message: str) -> None:
    if status_type == "success":
        st.success(message)
    elif status_type == "error":
        st.error(message)


def has_disallowed_entities(text: str) -> bool:
    url_extractor = URLExtract()
    url_extractor.update_when_older(7)
    return "#" in text or "@" in text or url_extractor.has_urls(text)


def is_valid_image(image: UploadedFile) -> bool:
    if image.size > MAX_IMAGE_SIZE_BYTES:
        return False

    _, image_ext = os.path.splitext(image.name)
    image_ext = image_ext[1:]

    if image_ext not in ALLOWED_IMAGE_EXTS:
        return False

    image.seek(0)

    kind = filetype.guess(image)

    if (
        kind is None
        or kind.extension not in ALLOWED_IMAGE_EXTS
        or kind.mime != image.type
        or kind.mime not in ALLOWED_IMAGE_MIME_TYPES
    ):
        return False

    return True


def sign_in(username: str, password: str, error_placeholder: DeltaGenerator) -> None:
    try:
        if authenticate(username, password):
            st.session_state.is_authenticated = True
            st.rerun()
        else:
            error_placeholder.error(
                "Username atau password yang lo masukin salah nih. Coba cek lagi ya!"
            )
    except Exception as e:
        print(e)
        error_placeholder.error(
            "Sign in lagi bermasalah nih :disappointed:. Coba lagi nanti ya!"
        )


def tweet_menfess(text: str, image: UploadedFile | None, qrt: str) -> None:
    final_text = [MENFESS_SIGNATURE]

    try:
        if image:
            if not is_valid_image(image):
                show_menfess_creation_status(
                    "error", "Image-nya ga valid. Coba cek lagi!"
                )
                return

            image_url = upload_image(image)
        else:
            image_url = None

        if text:
            if MENFESS_SIGNATURE in text.lower():
                show_menfess_creation_status(
                    "error",
                    f"Menfess-nya jangan ada reserved keyword ***{MENFESS_SIGNATURE}*** ya! Biar sistem aja yang "
                    f"nambahin ***{MENFESS_SIGNATURE}***-nya.",
                )
                return

            if has_disallowed_entities(text):
                show_menfess_creation_status(
                    "error", "Menfess-nya ga boleh ada #, @, atau URL ya!"
                )
                return

            max_length = MAX_WEIGHTED_TWEET_LENGTH - (len(MENFESS_SIGNATURE) + 1)
            if calculate_weighted_tweet_length(text) > max_length:
                show_menfess_creation_status(
                    "error",
                    f"Menfess-nya ga boleh lebih dari {max_length} karakter ya!",
                )
                return

            final_text.append(text)

        if qrt:
            if not is_valid_tweet_url(qrt):
                show_menfess_creation_status(
                    "error",
                    "QRT-nya ga valid nih. Pastiin lo QRT tweet dari @ug_fess ya!",
                )
                return

            final_text.append(qrt)

        queue_tweet(" ".join(final_text), image_url)

        show_menfess_creation_status(
            "success",
            "Yay! Menfess lo udah masuk antrean, langsung cek ke X aja ya :smiley:",
        )
    except Exception as e:
        print(e)
        show_menfess_creation_status(
            "error",
            "Lagi ga bisa kirim menfess nih :disappointed:. Coba lagi nanti ya!",
        )


def sign_out():
    st.session_state.is_authenticated = False
    st.rerun()


def sign_in_form():
    st.header("Eitss, sign in dulu!", anchor=False)
    st.write(
        "Sign in pake kredensial Student Site ya! Buat verifikasi kalo lo emang anak Gundar."
    )
    st.caption(
        "Tenang aja, username dan password lo ga bakal disimpen kok. UG FESS ga store data apa pun, fully anonymous. Kalo lo masih ragu, "
        "lo bisa cek codebase UG FESS di [github.com/nxgeo/ug-fess](https://github.com/nxgeo/ug-fess)."
    )
    error_placeholder = st.empty()
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Sign in"):
        if username and password:
            sign_in(username, password, error_placeholder)


def main_page():
    st.header("Mau send menfess apa?", anchor=False)
    menfess_submission_form = st.form(
        "menfess_submission_form", clear_on_submit=True, enter_to_submit=False
    )
    text = menfess_submission_form.text_area("Ketikin menfess lo di sini")
    image = menfess_submission_form.file_uploader(
        f"Lo juga bisa upload satu image",
        type=ALLOWED_IMAGE_EXTS,
    )
    qrt = menfess_submission_form.text_input(
        "QRT",
        help="Contoh: https[]()://x.com/ug_fess/status/1845753430381662319",
    )

    if menfess_submission_form.form_submit_button():
        if text or image:
            tweet_menfess(text, image, qrt)

    st.divider()

    st.subheader("Mau sign out?", anchor=False)
    st.write(
        "Kalo lo mau sign out, tinggal refresh (CTRL + R) aja atau klik button :point_down:"
    )

    if st.button("Sign out"):
        sign_out()


if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

st.set_page_config(page_title="UG FESS", page_icon=":flying_saucer:")

if st.session_state.is_authenticated:
    main_page()
else:
    sign_in_form()

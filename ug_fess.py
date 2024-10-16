import sys

sys.dont_write_bytecode = True


from os import environ

from django import setup
from django.apps import apps
from django.conf import settings
import streamlit as st
from streamlit.components.v1 import html
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.uploaded_file_manager import UploadedFile

from auth import authenticate
from content_moderation import (
    has_disallowed_entities,
    has_inappropriate_content,
    has_inappropriate_image,
)
from x import create_tweet, get_tweet_oembed_html, upload_images


if not settings.configured or not apps.ready:
    environ.setdefault("DJANGO_SETTINGS_MODULE", "django_settings")
    setup()


from db.models import Menfess, User


MENFESS_SIGNATURE = "yuji!"

X_MAX_IMAGE_ATTACHMENTS = 4


@st.dialog("Status")
def show_menfess_creation_status(
    status_type: str, message: str, tweet_id: str | None = None
) -> None:
    if status_type == "success":
        st.success(message)

        if tweet_id:
            html(get_tweet_oembed_html(tweet_id), height=390, scrolling=True)
    elif status_type == "error":
        st.error(message)


def sign_in(username: str, password: str, error_placeholder: DeltaGenerator):
    try:
        if authenticate(username, password):
            st.session_state.user = User.objects.get_or_create(username=username)[0]
            st.session_state.is_authenticated = True
            st.rerun()
        else:
            error_placeholder.error(
                "Username atau password yang lo masukin salah nih. Coba cek lagi ya!"
            )
    except Exception:
        error_placeholder.error(
            "Sign in lagi bermasalah nih :disappointed:. Coba lagi nanti ya!"
        )


def tweet_menfess(text: str | None, images: list[UploadedFile] | None):
    try:
        if text:
            if has_disallowed_entities(text):
                show_menfess_creation_status(
                    "error", "Menfess-nya ga boleh ada #, @, atau URL ya!"
                )
                return

            if has_inappropriate_content(text):
                show_menfess_creation_status(
                    "error",
                    "Menfess-nya ga boleh ada konten yang inappropriate ya! Baca lagi rules-nya.",
                )
                return

            if MENFESS_SIGNATURE not in text.lower():
                text = f"{MENFESS_SIGNATURE} {text}"

        if images:
            if len(images) > X_MAX_IMAGE_ATTACHMENTS:
                show_menfess_creation_status(
                    "error", f"Max {X_MAX_IMAGE_ATTACHMENTS} images aja ya!"
                )
                return

            if has_inappropriate_image(images):
                show_menfess_creation_status(
                    "error", "Ga boleh ada adult, racy, atau gory images ya!"
                )
                return

            media_ids = upload_images(images)
        else:
            media_ids = None

        tweet_or_tweets = create_tweet(text, media_ids)

        if isinstance(tweet_or_tweets, list):
            tweet = tweet_or_tweets[0]
        else:
            tweet = tweet_or_tweets

        Menfess.objects.create(tweet_id=tweet.id, user=st.session_state.user)

        show_menfess_creation_status(
            "success", "Yay! Menfess lo udah di-tweet :smiley:", tweet.id
        )
    except Exception:
        show_menfess_creation_status(
            "error",
            "Lagi ga bisa kirim menfess nih :disappointed:. Coba lagi nanti ya!",
        )


def sign_out():
    del st.session_state["user"]
    st.session_state.is_authenticated = False
    st.rerun()


def sign_in_form():
    st.header("Eitss, sign in dulu!", anchor=False)
    st.write(
        "Sign in pake kredensial Student Site ya! Buat verifikasi kalo lo emang anak Gundar."
    )
    st.caption(
        "Tenang aja, password lo ga bakal disimpen kok. Sistem cuma nyimpen username lo aja. Kalo lo masih ragu, "
        "lo bisa cek codebase UG FESS di [github.com/nxgeo/ug-fess](https://github.com/nxgeo/ug-fess)."
    )
    error_placeholder = st.empty()
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Sign in"):
        if username and password:
            sign_in(username, password, error_placeholder)


def main_page():
    st.header("Mau kirim menfess apa?", anchor=False)
    menfess_submission_form = st.form(
        "menfess_submission_form", clear_on_submit=True, enter_to_submit=False
    )
    text = menfess_submission_form.text_area("Ketikin menfess lo di sini:")
    images = menfess_submission_form.file_uploader(
        f"Lo juga bisa upload images (max {X_MAX_IMAGE_ATTACHMENTS}):",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    if menfess_submission_form.form_submit_button():
        if text or images:
            tweet_menfess(text, images)

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

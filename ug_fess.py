from os import environ

from django import setup
import streamlit as st

from auth import authenticate
from x import create_tweet, is_valid_tweet


environ.setdefault("DJANGO_SETTINGS_MODULE", "django_settings")
setup()


from db.models import Menfess, User


X_STATUS_BASE_URL = "https://x.com/ug_fess/status/"


def sign_in(username, password, error_placeholder):
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


def tweet_menfess(text, status_placeholder):
    if not is_valid_tweet(text):
        status_placeholder.error("Menfess-nya ga boleh ada #, @, atau URL ya!")
        return

    try:
        tweet_or_tweets = create_tweet(text)

        if isinstance(tweet_or_tweets, list):
            tweet = tweet_or_tweets[0]
        else:
            tweet = tweet_or_tweets

        Menfess.objects.create(tweet_id=tweet.id, user=st.session_state.user)

        status_placeholder.success(
            "Yay :smiley:! Menfess lo udah di-tweet. "
            f"Cek di [sini]({X_STATUS_BASE_URL}{tweet.id})."
        )
    except Exception:
        status_placeholder.error(
            "Lagi ga bisa kirim menfess nih :disappointed:. Coba lagi nanti ya!"
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

    if st.button("Sign in", disabled=(not username or not password)):
        sign_in(username, password, error_placeholder)


def main_page():
    st.header("Mau kirim menfess apa?", anchor=False)
    status_placeholder = st.empty()
    text = st.text_area("Ketikin menfess lo di sini:")

    if st.button("Submit", disabled=(not text)):
        tweet_menfess(text, status_placeholder)

    st.divider()

    st.subheader("Mau sign out?")
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

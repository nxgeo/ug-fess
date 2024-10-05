from bs4 import BeautifulSoup
from requests import Session


SIGN_IN_URL = "https://studentsite.gunadarma.ac.id/index.php/site/login"
SIGNED_IN_URL = "https://studentsite.gunadarma.ac.id/index.php/default/index"


def fetch_captcha(session: Session) -> tuple[int, int] | None:
    try:
        resp = session.get(SIGN_IN_URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        captcha1 = soup.find("input", {"type": "hidden", "name": "captcha1"})["value"]
        captcha2 = soup.find("input", {"type": "hidden", "name": "captcha2"})["value"]
    except TypeError:
        return None

    return int(captcha1), int(captcha2)


def authenticate(username: str, password: str) -> bool:
    session = Session()

    if (captcha := fetch_captcha(session)) is None:
        raise Exception("Captcha missing")

    captcha1, captcha2 = captcha
    captcha = captcha1 + captcha2  # Solve captcha

    resp = session.post(
        SIGN_IN_URL,
        {
            "username": username,
            "password": password,
            "captcha1": captcha1,
            "captcha2": captcha2,
            "captcha": captcha,
        },
        allow_redirects=False,
    )

    session.close()

    return resp.is_redirect and resp.headers["location"] == SIGNED_IN_URL

from bs4 import BeautifulSoup
from requests import Session


SIGN_IN_URL = "https://v-class.gunadarma.ac.id/login/index.php"


def fetch_login_token(session: Session) -> str | None:
    try:
        resp = session.get(SIGN_IN_URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        login_token = soup.find("input", {"name": "logintoken"})["value"]
    except TypeError:
        return None

    return login_token


def authenticate(username: str, password: str) -> bool:
    email = username.strip() + "@student.gunadarma.ac.id"

    session = Session()

    if (login_token := fetch_login_token(session)) is None:
        raise Exception("Login token missing")

    resp = session.post(
        SIGN_IN_URL,
        {"username": email, "password": password, "logintoken": login_token},
        allow_redirects=False,
    )

    session.close()

    return "MoodleSession" in resp.cookies

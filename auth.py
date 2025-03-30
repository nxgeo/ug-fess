from bs4 import BeautifulSoup
from requests import Session


SIGN_IN_URL = "https://lsp.gunadarma.ac.id/asesmen/login/"


def fetch_login_token(session: Session) -> str | None:
    try:
        resp = session.get(SIGN_IN_URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        login_token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]
    except TypeError:
        return None

    return login_token


def authenticate(username: str, password: str) -> bool:
    session = Session()

    if (login_token := fetch_login_token(session)) is None:
        raise Exception("Login token missing")

    resp = session.post(
        SIGN_IN_URL,
        {"username": username, "password": password, "csrfmiddlewaretoken": login_token},
    )

    session.close()

    return "Data Asesi" in resp.text

from requests import RequestException, Session

STUDENTSITE_URL = "https://studentsite.gunadarma.ac.id"
LOGIN_URL = f"{STUDENTSITE_URL}/api/auth/login"
REQUEST_TIMEOUT = (5, 15)  # Connect timeout, read timeout (seconds).


class AuthenticationUnavailable(RuntimeError):
    """StudentSite could not complete verification; credentials may be valid."""


def authenticate(username: str, password: str) -> bool:
    """Verify credentials; raise AuthenticationUnavailable for upstream failures."""
    username = username.strip()
    if not username or not password:
        return False

    try:
        # Isolate every attempt; never cache another user's session or result.
        with Session() as session:
            response = session.post(
                LOGIN_URL,
                json={"username": username, "password": password},
                headers={
                    "Accept": "application/json",
                    "Origin": STUDENTSITE_URL,
                    "Referer": f"{STUDENTSITE_URL}/login",
                },
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 401:
                return False
            if response.status_code != 200:
                raise AuthenticationUnavailable(
                    f"StudentSite login unavailable (HTTP {response.status_code})."
                )

            try:
                result = response.json()
            except ValueError:
                raise AuthenticationUnavailable(
                    "StudentSite returned an invalid login response."
                ) from None

            if not isinstance(result, dict):
                raise AuthenticationUnavailable(
                    "StudentSite returned an unexpected login response."
                )
            if result.get("success") is False:
                return False

            user = result.get("user")
            if (
                result.get("success") is not True
                or not isinstance(user, dict)
                or not user.get("npm")
            ):
                raise AuthenticationUnavailable(
                    "StudentSite returned an unexpected login response."
                )

            return True
    except RequestException:
        # Do not expose upstream response bodies, cookies, or request details.
        raise AuthenticationUnavailable("Could not connect to StudentSite.") from None

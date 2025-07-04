# utils/github_oauth.py
import secrets
import httpx
from fastapi import Request
from app.utils.constants import GithubConstants


class GithubOAuth:
    @staticmethod
    def generate_state_token(flow_type: str) -> str:
        return f"{secrets.token_urlsafe(16)}-{flow_type}"

    @staticmethod
    def get_auth_url(flow_type: str, state_token: str) -> str:
        return (
            "https://github.com/login/oauth/authorize"
            f"?client_id={GithubConstants.CLIENT_ID}"
            f"&redirect_uri={GithubConstants.REDIRECT_URI}"
            f"&scope={GithubConstants.SCOPE}"
            f"&state={state_token}"
        )

    @staticmethod
    def verify_state_token(
        expected_state: str, received_state: str
    ) -> tuple[bool, str]:
        try:
            received_token, flow_type = received_state.rsplit("-", 1)
            return expected_state == received_token, flow_type
        except Exception:
            return False, ""

    @staticmethod
    async def exchange_code_for_token(code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": GithubConstants.CLIENT_ID,
                    "client_secret": GithubConstants.CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": GithubConstants.REDIRECT_URI,
                },
            )
            response.raise_for_status()
            return response.json().get("access_token")

    @staticmethod
    async def fetch_primary_email(access_token: str) -> str | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code == 200:
                emails = response.json()
                for email in emails:
                    if email.get("primary") and email.get("verified"):
                        return email["email"]
        return None

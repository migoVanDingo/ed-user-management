# constants/github.py
import os


class GithubConstants:
    CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    REDIRECT_URI = os.getenv(
        "GITHUB_REDIRECT_URI"
    )  # e.g., http://localhost:8000/github/callback
    SCOPE = "read:user user:email"

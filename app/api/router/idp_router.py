# routes/github_oauth.py
from fastapi import APIRouter, Request, Response, Query
from fastapi.responses import RedirectResponse, JSONResponse

from app.utils.github_oauth import GithubOAuth


router = APIRouter()


@router.get("/github/login")
async def github_login(response: Response):
    # You can use secure cookie or DB/session storage if needed
    state_token = GithubOAuth.generate_state_token("login")
    response.set_cookie("github_oauth_state", state_token.split("-")[0], httponly=True)
    auth_url = GithubOAuth.get_auth_url("login", state_token)
    return RedirectResponse(auth_url)


@router.get("/github/callback")
async def github_callback(
    request: Request, code: str = Query(...), state: str = Query(...)
):
    expected_state = request.cookies.get("github_oauth_state")
    if not expected_state:
        return JSONResponse(
            status_code=400, content={"error": "Missing or expired state token"}
        )

    is_valid, flow_type = GithubOAuth.verify_state_token(expected_state, state)
    if not is_valid:
        return JSONResponse(status_code=400, content={"error": "Invalid state"})

    try:
        access_token = await GithubOAuth.exchange_code_for_token(code)
        email = await GithubOAuth.fetch_primary_email(access_token)

        if not email:
            return JSONResponse(
                status_code=400, content={"error": "Email not found or not verified"}
            )

        # Lookup or create user, issue token, etc.
        return JSONResponse(content={"email": email, "token": access_token})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

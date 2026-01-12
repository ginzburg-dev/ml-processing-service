from fastapi import Request
from fastapi.responses import RedirectResponse

def require_login(request: Request, next_path: str):
    if not request.session.get("user_id"):
        return RedirectResponse(f"/login?next={next_path}", status_code=302)
    return None

from urllib.parse import unquote, urlparse, quote
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.app.config import MLServiceConfig
from backend.app.database import UserDatabase

router = APIRouter(tags=["auth"])
config = MLServiceConfig(dotenv=True)
database = UserDatabase(config.db_path)

def safe_next(next_: str) -> str:
    if not next_:
        return "/"
    n = unquote(next_)
    if n.startswith("/") and not n.startswith("//"):
        return n
    return "/"

def render_login(error: str, next_: str) -> HTMLResponse:
    html = f"""
<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Login</title>
    <style>
        body {{ font-family: sans-serif; background:#111; color:#eee; height:100vh;
                display:flex; align-items:center; justify-content:center; }}
        .card {{ width: 360px; background:#1b1b1b; border:1px solid #333;
                border-radius:12px; padding:16px; }}
        input {{ width:100%; padding:10px; margin-top:8px; border-radius:8px; box-sizing: border-box;
                border:1px solid #333; background:#0f0f0f; color:#eee; }}
        button {{ width:100%; margin-top:12px; padding:10px; border-radius:8px; border:0; cursor:pointer; }}
        .err {{ color:#ff6b6b; min-height:18px; margin-top:8px; }}
        .muted {{ opacity:0.7; font-size:13px; }}
    </style>
</head>
<body>
    <div class="card">
        <h3 style="margin:0 0 6px 0;">ML Processing Service</h3>
        <div class="muted">Login to continue</div>    
        <form method="post" action="/login">
            <input type="hidden" name="next" value="{next_}" />
            <input name="username" placeholder="Username" autocomplete="username" />
            <input name="password" placeholder="Password" type="password" autocomplete="current-password" />
            <div class="err">{error}</div>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""
    return HTMLResponse(html)

@router.get("/login")
async def login_page(request: Request, next: str = "/"):
    if request.session.get("user_id"):
        return RedirectResponse(safe_next(next), status_code=302)
    return render_login("", next)

@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    user = database.verify_user(username=username, password=password)
    if not user:
        return render_login("Wrong username or password.", next)

    user_id, uname, role = user
    request.session["user_id"] = user_id
    request.session["username"] = uname
    request.session["role"] = role
    return RedirectResponse(safe_next(next), status_code=302)


@router.get("/logout")
async def logout(request: Request):
    next_path = request.headers.get("referer") or "/"
    try:
        parsed = urlparse(next_path)
        # сохраняем путь + query (если был)
        next_path = parsed.path or "/"
        if parsed.query:
            next_path += "?" + parsed.query
    except Exception:
        next_path = "/"

    request.session.clear()

    resp = RedirectResponse(f"/login?next={quote(next_path, safe='')}", status_code=302)
    resp.delete_cookie("session")
    return resp

from html import escape
import secrets

from fastapi.responses import HTMLResponse


# Email capability pages must not be cached, embedded, or load third-party resources.
PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
    "X-Content-Type-Options": "nosniff",
}


# Kept local: email links must not send their token to font/CDN providers.
_EMAIL_PAGE_CSS = """
*{box-sizing:border-box}body{margin:0;color:#151526;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:radial-gradient(ellipse at 85% 10%,#e4d8ff,transparent 40%),radial-gradient(ellipse at 15% 85%,#f9e5f3,transparent 38%),#f2f0fa;line-height:1.5}
main{min-height:100vh;min-height:100svh;display:grid;place-items:center;padding:28px 20px}
.card{width:100%;max-width:460px;padding:34px;border:1px solid #ffffffcc;border-radius:24px;background:#ffffffed;box-shadow:0 24px 70px #462e7f18}
.brand{display:flex;align-items:center;gap:10px;margin-bottom:32px;font-size:22px;font-weight:800;letter-spacing:-.8px}
.brand-icon{display:grid;place-items:center;width:36px;height:36px;border-radius:11px;background:linear-gradient(145deg,#209dc3,#3522d2 75%);color:#fff;font-size:27px;font-weight:400}
.icon{display:grid;place-items:center;width:52px;height:52px;margin-bottom:20px;background:#e9e4fb;color:#4930d9;border-radius:16px;font-size:25px}.success{color:#16765d;background:#dbf2e9}.error{color:#c63b59;background:#fce9ef}
h1{font-size:27px;line-height:1.2;letter-spacing:-.8px;margin:0 0 12px}p{margin:0 0 24px;color:#5f657c;font-size:14px;line-height:1.65}
form{display:grid;gap:17px}label{display:grid;gap:8px;font-size:13px;font-weight:600;color:#37384d}input{width:100%;min-height:45px;padding:12px;border:1px solid #ced3e8;border-radius:10px;background:#fff;color:#151526;font:inherit;font-weight:400}
input:focus-visible{outline:3px solid #4930d922;border-color:#4930d9}button{width:100%;min-height:46px;margin-top:4px;padding:12px 16px;border:0;border-radius:10px;color:#fff;background:#4930d9;font:inherit;font-size:14px;font-weight:700;cursor:pointer}button:hover{background:#30209f}button:focus-visible{outline:3px solid #4930d955;outline-offset:3px}
.hint{margin:22px 0 0;padding-top:18px;border-top:1px solid #e8e8f2;color:#777b90;font-size:12px}.form-error{margin:0;padding:12px 14px;border:1px solid #efced7;border-radius:10px;background:#fce9ef;color:#a82d48;font-size:13px}
@media(max-width:480px){main{padding:20px 16px}.card{padding:26px 24px;border-radius:20px}h1{font-size:25px}.brand{margin-bottom:27px}}
"""


def email_page(title: str, description: str, content: str = "", *, state: str = "default", icon: str = "mail", status_code: int = 200) -> HTMLResponse:
    """Render trusted form markup; titles and descriptions are always escaped."""
    nonce = secrets.token_urlsafe(24)
    paths = {
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
        "lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4m-4 5v2"/>',
        "success": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
        "error": '<circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 3h.01"/>',
    }
    icon_path = paths.get(state, paths.get(icon, paths["mail"]))
    symbol = ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + icon_path + '</svg>')
    icon_class = state if state in {"success", "error"} else ""
    headers = {
        **PAGE_HEADERS,
        "Content-Security-Policy": PAGE_HEADERS["Content-Security-Policy"] + f"; style-src 'nonce-{nonce}'",
    }
    return HTMLResponse(
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{escape(title)} — Wishlist</title><style nonce="{nonce}">{_EMAIL_PAGE_CSS}</style>'
        '</head><body><main><section class="card" aria-labelledby="page-title">'
        '<div class="brand"><span class="brand-icon" aria-hidden="true">♡</span>Wishlist</div>'
        f'<div class="icon {icon_class}" aria-hidden="true">{symbol}</div>'
        f'<h1 id="page-title">{escape(title)}</h1><p>{escape(description)}</p>{content}'
        '</section></main></body></html>',
        status_code=status_code, headers=headers,
    )

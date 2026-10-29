from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import init_db
from app.services.event_reminders import start_reminder_worker, stop_reminder_worker
from app.models.user import UserRegisterRequest
from app.routers import user_routers
from app.routers import auth_router
from app.routers import event_router
from app.routers import reservation_router
from app.routers import gift_router
from app.routers import image_router
from app.routers import marketplace_router
from app.routers import tag_router
from app.routers import contribution_router
from app.routers import email_verification_router
from app.routers import password_reset_router
from app.routers import share_router
from app.routers import gift_question_router
from app.routers import wish_router
from app.routers import wish_share_router


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, error: RequestValidationError):
    fields = [{"loc": item["loc"], "msg": item["msg"], "type": item["type"]} for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": fields})


@app.middleware("http")
async def private_response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("Cache-Control", "private, no-store")
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response



@app.on_event("startup")
def on_startup():
    init_db()
    start_reminder_worker()


@app.on_event("shutdown")
def on_shutdown():
    stop_reminder_worker()


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

app.include_router(user_routers.router)
app.include_router(auth_router.router)
app.include_router(event_router.router)
app.include_router(reservation_router.router)
app.include_router(reservation_router.guest_router)
app.include_router(gift_router.router)
app.include_router(image_router.router)
app.include_router(marketplace_router.router)
app.include_router(tag_router.router)
app.include_router(contribution_router.router)
app.include_router(email_verification_router.router)
app.include_router(password_reset_router.router)
app.include_router(share_router.router)
app.include_router(gift_question_router.router)
app.include_router(wish_router.router)
app.include_router(wish_share_router.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/web", response_class=HTMLResponse)
async def web():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Hello World</title>
        </head>
        <body>
            <h1>Hello World</h1>
            <p>FastAPI is running!</p>
        </body>
    </html>
    """

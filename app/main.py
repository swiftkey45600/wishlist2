from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models.user import UserRegisterRequest
from app.routers import user_routers
from app.routers import auth_router
from app.routers import event_router
from app.routers import gift_router
from app.routers import image_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routers.router)
app.include_router(auth_router.router)
app.include_router(event_router.router)
app.include_router(gift_router.router)
app.include_router(image_router.router)


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

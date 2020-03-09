"""main.py - file where the server resides
08.03.2020 - @yashbonde"""

from fastapi import FastAPI, Request # base imports
from fastapi.staticfiles import StaticFiles # static files on the system
from fastapi.templating import Jinja2Templates # jinja templates
from fastapi.responses import RedirectResponse

# app things
app = FastAPI()
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

# fake
fake_db = {
    "Username": "1234"
}

# routes
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("landing.html", {
        "request": request, 
        "cannot_login": False
    })

@app.get("/login/")
async def login(request: Request, user: str, password: str):
    user_name = user
    pwd_hash = password

    if user_name not in fake_db or fake_db[user_name] != pwd_hash:
        return templates.TemplateResponse("landing.html", {
            "request": request, 
            "cannot_login": True
        })

    else:
        # we have a user and he is authenticated
        return templates.TemplateResponse("landing.html", {
            "request": request, 
            "cannot_login": False
        })

@app.get("/platform/")
async def home_platform(request: Request, user_id: int):
    """take in the user_id and return the rendered template for
    homepage"""
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_first_name": "Robert"
    })
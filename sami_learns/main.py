"""main.py - file where the server resides
08.03.2020 - @yashbonde"""

# base dependencies
import json
from fastapi import FastAPI, Request # base imports
from fastapi.staticfiles import StaticFiles # static files on the system
from fastapi.templating import Jinja2Templates # jinja templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# custom dependencies
from sami_learns.learning_system import book_handler

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
def root(request: Request, cannot_login: bool = False):
    return templates.TemplateResponse("landing.html", {
        "request": request, 
        "cannot_login": cannot_login
    })

@app.get("/login")
def login(request: Request, user: str, password: str):
    username = user
    pwd_hash = password

    # return RedirectResponse('/{}'.format(username))

    if username not in fake_db or fake_db[username] != pwd_hash:
        return templates.TemplateResponse("landing.html", {
            "request": request, 
            "cannot_login": True
        })

    else:
        # we have a user and he is authenticated
        return RedirectResponse('/{}'.format(username))


@app.get("/{username}")
def home_platform(request: Request, username: str):
    """take in the user_id and return the rendered template for
    homepage"""

    # if username not in fake_db:
    #     return RedirectResponse('/')

    documents = [
        {
            "name": "How India is using technology to lift millions out of poverty",
            "url": "{username}/books/12".format(username = username)
        }, {
            "name": "On the theory of evolution and its cultural impacts",
            "url": "{username}/books/22".format(username = username)
        }
    ]

    return templates.TemplateResponse("home.html", {
        "request": request,
        "username": username,
        "documents": documents
    })

# var regex_pat = RegExp('(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)');

class queriesModel(BaseModel):
    queries: list
    book_name: str

@app.post("/{username}/newBook")
def make_new_book(request: Request, username:str,  queries: queriesModel):
    new_book_id = book_handler.make_new_book(book_id, section_id, tune_more_less)
    new_book_id = 12

    return {
        "book_url": "/{username}/books/{book_id}".format(
            username = username,
            book_id = new_book_id
        )
    }
    
fake_books = {
    "12": json.load(open("sample_article_jsons/12.json")),
    "22": json.load(open("sample_article_jsons/22.json")),
}

@app.get("/{username}/books/{book_id}")
def get_book(request: Request, username: str, book_id: int):
    return templates.TemplateResponse("book.html", {
        "request": request,
        "user_home_url": "/{username}".format(username = username),
        "book_id_url": book_id,
        "username": username,
        **fake_books[str(book_id)]
    })

class BookConfigurationsModel(BaseModel):
    more_less: str
    book_id: str
    section_id: str

@app.post("/{username}/books/{book_id}")
def tune_book(request: Request, username: str, book_id: int, book_config: BookConfigurationsModel):
    print("---> {} --> {} --> {}".format(
        book_config.more_less, book_config.book_id, book_config.section_id))
    pass
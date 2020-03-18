"""main.py - file where the server resides
08.03.2020 - @yashbonde"""

# base dependencies
import json
from fastapi import FastAPI, Request # base imports
from fastapi.staticfiles import StaticFiles # static files on the system
from fastapi.templating import Jinja2Templates # jinja templates
from fastapi.responses import RedirectResponse


# custom dependencies
from learning_system import book_handler
from models import fastapi_query_models

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

@app.post("/{username}/newBook")
def make_new_book(request: Request, username:str,  queries: fastapi_query_models.queriesModel):
    # new_book_id = book_handler.make_new_book(queries.book_name, queries.queries)
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

@app.post("/{username}/books/{book_id}")
def tune_book(request: Request, username: str, book_id: int, book_config: fastapi_query_models.BookConfigurationsModel):

    # book_handler.update_book_by_parameters(book_config)
    print("Got tuning parameters: {}".format(book_config))

    return {
        "book_url": "/{username}/books/{book_id}".format(
            username = username,
            book_id = book_id
        )
    }
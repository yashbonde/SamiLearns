"""main.py - file where the server resides
08.03.2020 - @yashbonde"""

# base dependencies
import json
import logging
logging.basicConfig(level=logging.INFO)
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


@app.post("/{username}/newBook")
def make_new_book(request: Request, username:str,  queries: fastapi_query_models.queriesModel):
    new_book_id = '4c20d3St0n3d'
    document_sections = book_handler.make_new_book(queries)
    book = {
        "book_id": new_book_id,
        "book_title": queries.book_name,
        "intro_text": None,
        "document_sections": document_sections
    }
    with open("./sample_article_jsons/4c20d3St0n3d.json", "w") as f:
        f.write(json.dumps(book))
    
    return {
        "book_url": "/{username}/books/{book_id}".format(
            username = username,
            book_id = new_book_id
        )
    }


@app.get("/{username}/books/{book_id}")
def get_book(request: Request, username: str, book_id: str):
    fake_book = json.load(open("./sample_article_jsons/{}.json".format(book_id)))
    return templates.TemplateResponse("book.html", {
        "request": request,
        "user_home_url": "/{username}".format(username = username),
        "book_id_url": book_id,
        "username": username,
        **fake_book
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

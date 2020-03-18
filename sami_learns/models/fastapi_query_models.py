from pydantic import BaseModel

class BookConfigurationsModel(BaseModel):
    more_less: str
    book_id: str
    section_id: str

class queriesModel(BaseModel):
    queries: list
    book_name: str
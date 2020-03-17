"""this is the main handler for books. There are two main functions:
- make new books
- make configuration changes

17.03.2020 - @yashbonde"""

import logging
logging.basicConfig(level=logging.INFO)

def make_new_book(book_name, queries):
    """do the following:
    - register the incoming information in DB
    - send the links to scrapper
    - the scrapper returns the text objects
    - send the text objects to AI for conversion to sections
    - AI returns and sections and records for each one
    - make the final book
    - register the records, sections in the DB
    - return the book object"""
    pass

def update_book_by_parameters(book_id, section_id, tune_more_less):
    """do the following:
    - take the information in DB about this book
    - see which section wants record incremented/decremented
    - change the section accordingly
    - return new book"""
    pass
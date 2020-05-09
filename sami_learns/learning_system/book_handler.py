"""this is the main handler for books. There are two main functions:
- make new books
- make configuration changes

17.03.2020 - @yashbonde"""

import regex as re
import requests
import spacy
from urllib.parse import urlparse
import logging

# custom
from .nlp_feature_extractor import make_scrapped_data, get_aggregate_data
from .infer_sent_model import encoder

# constants to be initialised
URLPAT = re.compile(r'^(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$')
logging.info("Loading Spacy NLP model ... this might take some time!")
NLP = spacy.load("en_core_web_md")
INFERSENT_MODEL = encoder.get_model()

def make_new_book(queries):
    """do the following:
    - register the incoming information in DB
    - send the links to scrapper
    - the scrapper returns the text objects
    - send the text objects to AI for conversion to sections
    - AI returns and sections and records for each one
    - make the final book
    - register the records, sections in the DB
    - return the book object"""

    # get clean urls and generate meta against URLs
    bookname = queries.book_name
    query_links = queries.queries
    queries_cleaned = []
    url_meta = []
    for q in query_links:
        s = re.search(URLPAT, q)
        if s:
            pr = urlparse(s.group(0))
            qc = '{scheme}://{netloc}{path}'.format(
                scheme = pr.scheme, netloc = pr.netloc, path = pr.path
            )
            queries_cleaned.append(qc)
        else:
            logging.info("Removing {} as this does not look like a valid url".format(q))

    # now get html for each of the url
    html_for_urls = []
    for url in queries_cleaned:
        logging.info("Requesting Link: {}".format(url))
        out = requests.get(url).text
        html_for_urls.append(out)
    
    # now perform nlp feature extraction
    data_scrapped = make_scrapped_data(queries_cleaned, html_for_urls, NLP)

    # now send to NLP AI and perform aggregation
    output_data = get_aggregate_data(data_scrapped, INFERSENT_MODEL)

    return output_data

def update_book_by_parameters(book_id, section_id, tune_more_less):
    """do the following:
    - take the information in DB about this book
    - see which section wants record incremented/decremented
    - change the section accordingly
    - return new book"""
    pass

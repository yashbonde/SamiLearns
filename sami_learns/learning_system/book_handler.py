"""this is the main handler for books. There are two main functions:
- make new books
- make configuration changes

17.03.2020 - @yashbonde"""

import regex as re
import requests
import numpy as np
from urllib.parse import urlparse
import logging

# custom
# import nlp_feature_extractor as nlpfe
from .nlp_feature_extractor import get_paragraphs, get_topics

# constants to be initialised
URLPAT = re.compile(r'^(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$')
# logging.info("Loading Spacy NLP model ... this might take some time!")
# # NLP = spacy.load("en_core_web_md")
# NLP = None
# # INFERSENT_MODEL = encoder.get_model()
# INFERSENT_MODEL = None


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
            queries_cleaned.append({
                "cleaned_string": qc,
                "scheme": pr.scheme,
                "netloc": pr.netloc,
                "path": pr.path
            })
        else:
            logging.info("Removing {} as this does not look like a valid url".format(q))

    # get the cleaned parsed data and then aggregate topic wise
    lines_topics = get_paragraphs(queries_cleaned = queries_cleaned, bigram_inclusion_thresh = 0.25)
    topic_document_matrix, new_topics = get_topics(lines_topics)

    # transform to final JSON object
    topic_wise_documents = {}
    for idx in range(len(topic_document_matrix)):
        lt = lines_topics[idx]
        sentence = lt["sentence"]
        topic_assigned = "/".join(new_topics[np.argmax(topic_document_matrix[idx])])
        topic_wise_documents.setdefault(topic_assigned, [])
        topic_wise_documents[topic_assigned].append({
            "sentence": sentence,
            "raw": lt["raw"],
            "master_link": {
                "url": lt["url"]["cleaned_string"],
                "link_name": lt["url"]["netloc"]
            }
        })

    document_sections = []
    idx = 0
    for t, tinfo in topic_wise_documents.items():
        records = []
        for item in tinfo:
            records.append({
                "htmltext": item["sentence"],
                "master_link": item["master_link"]
            })
        document_sections.append({"id": idx, "name": t, "records": records[:4]})
        idx += 1
    return document_sections

def update_book_by_parameters(book_id, section_id, tune_more_less):
    """do the following:
    - take the information in DB about this book
    - see which section wants record incremented/decremented
    - change the section accordingly
    - return new book"""
    pass

"""code for v0.2 of extraction model"""

import os
import copy
import tqdm
import nltk
import spacy
import logging
import requests
import unicodedata
import regex as re
import numpy as np
from bs4 import BeautifulSoup
from collections import Counter
from readability import Document
from urllib.parse import urlparse

import torch
import torch.nn.functional as F
from sklearn.cluster import KMeans

from .model import bert_for_next_sentence #pylint: disable=relative-beyond-top-level

with open("/".join(__file__.split("/")[:-1]) + "/model/stopwords.txt") as f:
    STOPWORDS = f.read().split()
NLP = spacy.load("en_core_web_sm")
BERT_FOR_NEXT_SENTENCE = bert_for_next_sentence.BertNextSentenceModel()

# Basic data scraping and extraction
def filter_para_by_counts(html, min_count = 20):
    parsed_html = BeautifulSoup(html)
    word_counts = []
    para_strings = []
    for node in parsed_html.findAll('p'):
        node_text = node.text.strip()
        if len(node_text.split()) < min_count:
            continue
        word_counts.append(len(node_text.split()))
        para_strings.append(node_text)
    return word_counts, para_strings

def process_paras(para_strings):
    # function to take in the paragraph strings and join them as needed
    pf = []
    while len(para_strings):
        p = para_strings.pop(0).strip()
        while p[-1] == ",":
            p += " " + para_strings.pop(0)
        if p[0] in [",", "."] and pf:
            # need to merge with the previous line
            pf[-1] += p
        else:
            pf.append(p)
    return pf

# to learn about the unicode form in normalise go to this link: https://en.wikipedia.org/wiki/Unicode_equivalence
def basic_cleaning(text):
    out = unicodedata.normalize("NFKD", text)
    for pat, repl in [
        (r"\n+", " "), # multiple new lines
        (r"\s+", " "), # multiple spaces
        (r"\{\\.*\}", ""), # code tags
        (r"\s\.", "."), # spaces before dots
        (r"\[\d+\]$", ""), # reference boxes
        (r"^[a-z]\.", "") # starts with a single smallletter
    ]:
        out = re.sub(pat, repl, out).strip()
    return out

def process_paras_post(para_strings, min_len = 5):
    # function to join the paragraphs in post cleaning
    pf = []
    while len(para_strings):
        p = para_strings.pop(0).strip()
        if p[0].islower() and pf:
            pf[-1] += " " + p
        else:
            pf.append(p)

    pf2 = []
    for p in pf:
        if (p[0] == "(" and p[-1] == ")") or len(p.split()) < min_len:
            continue
        pf2.append(p)
    return pf2

def get_paragraphs(queries_cleaned, bigram_inclusion_thresh = 0.25):
    """queries_cleaned has a list of objects like this: 
    {
        "cleaned_string": qc,
        "scheme": pr.scheme,
        "netloc": pr.netloc,
        "path": pr.path
    }"""
    # now get html for each of the url
    paras = []
    urls = []
    for lidx in tqdm.trange(len(queries_cleaned)):
        l = queries_cleaned[lidx]
        try:
            response = requests.get(l["cleaned_string"])
            doc = Document(response.text)
            _, para_strings = filter_para_by_counts(doc.summary(html_partial = True), 2)
            para_strings = process_paras(copy.deepcopy(para_strings))
            paras.append(para_strings)
            urls.append(l)
        except Exception as e:
            logging.info("Exception in getting: {} | {}".format(l, e))

    # make the pflat list
    pflat = {"pflat": [], "ls": [], "urls": [], "raw": []}
    for pidx, p in enumerate(paras):
        p = list(map(basic_cleaning, p))
        p = process_paras_post(copy.deepcopy(p))
        pflat.get("pflat").extend(p)
        pflat.get("ls").extend([pidx,]*len(p))
        pflat.get("urls").extend([urls.pop(0),]*len(p))
        pflat.get("raw").extend(paras[pidx])

    # make the flattened formatted string to extract bigrams and trigrams
    lemmatizer = lambda x: " ".join([word.lemma_ for word in NLP(x)])
    pflat_lem = [lemmatizer(x) for x in pflat["pflat"]]
    pflat_lem = [" ".join([y for y in x.split() if y not in STOPWORDS + ["-PRON-"]]) for x in pflat_lem]

    flat_str = " ".join(pflat_lem).lower()
    flat_str = re.sub(r"[^a-z\d\s]", "", flat_str)
    flat_str = [x for x in flat_str.split() if x not in STOPWORDS]

    # bigrams and trigrams
    bigram_fd = nltk.FreqDist(nltk.bigrams(flat_str))
    bi_most_common = bigram_fd.most_common()
    trigram_fd = nltk.FreqDist(nltk.ngrams(flat_str, 3))
    tri_most_common = trigram_fd.most_common()

    # extract top bigrams
    bitopics = [(" ".join(x[0]), x[1]) for x in bi_most_common[:100]]
    bimid = [x[1] for x in bitopics][:int(bigram_inclusion_thresh * len(bitopics))][-1]
    bitopics = [x for x in bitopics if x[1] >= bimid]

    # now we make a list of paragraphs with the paragrphs and keywords
    lines_topics = []
    for pidx, p in enumerate(pflat["pflat"]):
        if len(p.split()) < 10:
            continue # skip small sentences
        lem_sent = " ".join([x for x in pflat_lem[pidx].lower().split() if x not in STOPWORDS])
        lem_sent = re.sub(r"[^a-z\d\s]", "", lem_sent)
        tlist = list(filter(
            lambda t: re.findall(t[0], lem_sent), bitopics
        ))
        if tlist:
            lines_topics.append({
                "sentence": p,
                "keyword_counts": [{
                    "key": t[0],
                    "count": len(re.findall(t[0], lem_sent))
                } for t in tlist],
                "url": pflat["urls"][pidx],
                "raw": pflat["raw"][pidx]
            })
    
    return lines_topics

def get_kmeans(strings, frac, random_state):
    logits = BERT_FOR_NEXT_SENTENCE.phrase_sim(strings, 128)
    soft_logits = F.softmax(torch.from_numpy(logits.reshape(len(strings), len(strings), 2)), dim = 1)
    logits_yes_soft = soft_logits[:, :, 0]
    logits_no_soft = soft_logits[:, :, 1]

    # do kmeans
    n_clusters=int(frac * len(logits_yes_soft))
    kmeans = KMeans(n_clusters = n_clusters, random_state=random_state).fit(logits_yes_soft)
    labels = kmeans.labels_
    sorted_labels = np.argsort(labels)
    out = {i:sorted_labels[labels[sorted_labels] == i].tolist() for i in list(set(labels))}
    topics = []
    for k,v in out.items():
        topics.append([strings[i] for i in v])
    return topics

def get_topics(lines_topics):
    # get keyword strings
    strings = []
    for s in [[y["key"] for y in x.get("keyword_counts")] for x in lines_topics]:
        strings.extend(s)
    strings = sorted(list(set(strings)))
    
    # coarse aggregation
    topics = get_kmeans(strings = strings, frac = 0.3, random_state = 9)

    # fine aggregation
    dist = [len(t) for t in topics]
    mu = np.mean(dist)
    std = np.std(dist)
    
    # those outside the distribution
    lbls_out = [i for i,t in enumerate(topics) if mu + std < len(t) or len(t) < mu - std]
    new_topics = []
    while len(lbls_out) > 0:
        top = get_kmeans(strings = topics[lbls_out.pop()], frac = 0.5, random_state = 0)
        new_topics.extend(top)
    
    # those inside the distribution
    lbls_out = [i for i,t in enumerate(topics) if mu + std > len(t) > mu - std]
    new_topics.extend([topics[i] for i in lbls_out])
    topics_all = []
    for t in new_topics:
        topics_all.extend(t)
    topics_all = {k:i for i,k in enumerate(topics_all)}

    logging.info("Final Extracted Topics")
    for t in new_topics:
        logging.info("---> {}".format("/".join(t)))

    # matrix that tells document to keywords
    kwsf = []
    for k in [x["keyword_counts"] for x in lines_topics]:
        arr = np.zeros(len(topics_all))
        arr[[topics_all[i["key"]] for i in k]] = [i["count"] for i in k]
        kwsf.append(arr.tolist())
    kwsf = np.array(kwsf) # [doc x kw]

    # now make a matrix that tells what is the keyword to topics
    topics_oh = []
    for t in new_topics:
        arr = np.zeros(len(topics_all))
        arr[[topics_all[i] for i in t]] = 1.
        topics_oh.append(arr)
    topics_oh = np.array(topics_oh).T # [kw x topics]

    # document to topics
    topic_wise_documents = np.matmul(kwsf, topics_oh)

    return topic_wise_documents, new_topics

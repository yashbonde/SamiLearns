from bs4 import BeautifulSoup
import regex as re
import numpy as np
from collections import Counter

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


def filter_strings_by_tokens(string):
    if re.findall(r"\n+", string):
        return False
    return True


def prepare_meta(paras, nlp):
    sentences = []
    para_ents = []
    for pidx, p in enumerate(paras):
        doc = nlp(p)
        for s in doc.sents:
            for ent in s.ents:
                para_ents.append(ent.string.strip())
            sentences.append({
                "para_id": pidx,
                "raw": s.string.strip(),
                "num_words": len(s.string.split()),
                "entities": {
                    k:round(np.log(v), 4)
                    for k,v in Counter([
                        x.string.strip()
                        for x in s.ents
                    ]).items()
                }
            })
    para_ents = {k:round(np.log(v), 4) for k,v in Counter(para_ents).items()}
    return {
        "num_paras": len(paras),
        "para_dist": para_ents,
        "sentences": sentences
    }

def feature_extractor(html, nlp):
    w, p = filter_para_by_counts(html)
    p = [x for x in p if filter_strings_by_tokens(x)]
    text = prepare_meta(p, nlp)
    return text
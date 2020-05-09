import logging
from bs4 import BeautifulSoup
import regex as re
import numpy as np
from urllib.parse import urlparse
from collections import Counter

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

def filter_strings_by_tokens(string):
    if re.findall(r"\n+", string):
        return False
    return True

def prepare_meta(paras, nlp):
    sentences = []
    para_ents = {}
    for pidx, p in enumerate(paras):
        doc = nlp(p)
        for s in doc.sents:
            ents = {}
            for ent in s.ents:
                if not ent.string.strip().isdigit() and ent.label_ in [
                    "PERSON", "NORP", "FAC", "ORG", "GPE", "LOC", "PRODUCT",
                    "EVENT","WORK_OF_ART", "LAW", "LANGUAGE"
                ]:
                    ent_string = ent.string.strip().lower()
                    ents.setdefault(ent_string, [0, ent.label_])
                    ents[ent_string][0] += 1
                    
                    para_ents.setdefault(ent_string, [0, ent.label_])
                    para_ents[ent_string][0] += 1
            sentences.append({
                "para_id": pidx,
                "raw": s.string.strip(),
                "num_words": len(s.string.split()),
                "entities": ents
            })
    return {
        "num_paras": len(paras),
        "para_dist": para_ents,
        "sentences": sentences
    }

def make_scrapped_data(urls, htmls, spacy_model):
    logging.info("Making the scrapped data ...")
    data_scrapped = []
    for url, out in zip(urls, htmls):
        w, p = filter_para_by_counts(out)
        p = [x for x in p if filter_strings_by_tokens(x)]
        sent = prepare_meta(p, spacy_model)
        urlp = urlparse(url)
        data_scrapped.append({
            "url_meta": {
                "raw": url,
                "netloc": urlp.netloc,
                "path": urlp.path
            },
            "text": sent
        })
    return data_scrapped

# AI Aggregation System Utils
def tojoin(x, y, thresh = 0.4):
    xnoty = x.difference(y)
    ynotx = y.difference(x)
    diff = xnoty.union(ynotx)
    join = list(x) + list(y)
    if len(diff) / len(join) < thresh:
        return True
    return False

def dotsim(a, b):
    return np.sum(np.dot(a, b))    

def cosine(u, v):
    return np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))

def euclidean(a, b):
    return np.sqrt(np.sum((a - b)** 2))

# Main code for AI Aggregation System
def get_meta_and_sentences(data_scrapped):
    cntr = 0
    para_meta = []
    target_y = [] # target for y in tsne
    all_paras = []
    for d in data_scrapped:
        text_feat = d["text"]
        paras = list(set([sent["para_id"] for sent in text_feat["sentences"]]))
        if not paras:
            continue
        word_counts = {}
        sentence_embedding = []
        for p in paras:
            this_para_sent = list(filter(
                lambda sent: sent["para_id"] == p, text_feat["sentences"]
            ))
            all_paras.append(' '.join([x["raw"] for x in this_para_sent]))
            
            # extract Embedding for the paragraphs
            para_entities = {}
            for sent in this_para_sent:
                for ent, val in sent["entities"].items():
                    para_entities.setdefault(ent, [0, val[1]])
                    para_entities[ent][0] += val[0]
            para_meta.append({
                "idx": cntr,
                "para_id": p,
                "urlraw": d["url_meta"]["raw"],
                "netloc": d["url_meta"]["netloc"],
                "entities": para_entities
            })
            cntr += 1
        target_y.append(len(word_counts))
    all_paras = np.array(all_paras)

    return all_paras, para_meta


def aggregate_by_keywords(para_meta):
    # aggregate those with entity
    para_meta_ord = []
    para_counter = {}
    cntr = 0
    for idx, pm in enumerate(para_meta):
        if len(pm["entities"]) > 0:
            # include only if there is some entity in the text
            para_meta_ord.append(pm)
            para_counter[cntr] = idx
            cntr += 1
    para_meta_ord = np.array(para_meta_ord)

    # make ent2idx2ent
    all_entities = []
    for pm in para_meta_ord:
        all_entities.extend(list(pm["entities"].keys()))
    all_entities = list(set(all_entities))
    all_entities_idx = {k:i for i,k in enumerate(all_entities)}
    idx_to_entity = {i:k for k,i in all_entities_idx.items()}

    # base counts matrix
    ndt = np.zeros([len(para_meta_ord), len(all_entities)])
    for pidx, pm in enumerate(para_meta_ord):
        for ent in pm["entities"]:
            eidx = all_entities_idx[ent]
            ndt[pidx][eidx] = pm["entities"][ent][0]

    # get keywords to paragraphs mapping
    keywords_paras = {}
    for kidx, row in enumerate(ndt.T):
        keywords_paras[kidx] = [idx for idx, v in enumerate(row) if v]
    keywords_paras = {k:v for k, v in sorted(keywords_paras.items(), key = lambda x: len(x[1]))[::-1]}

    return para_counter, keywords_paras, all_entities_idx, idx_to_entity


def basic_merging_topics(
        para_counter,
        keywords_paras,
        all_entities_idx,
        idx_to_entity,
        thresh = 0.1
    ):
    para_idx = []
    new_aggr = {}
    kw_done = []
    for kw, paras in keywords_paras.items():
        if kw in kw_done or len(paras) < 2:
            continue
        local_update = []
        for kw2, paras2 in keywords_paras.items():
            if kw2 == kw or len(paras2) < 2:
                continue
            p1, p2 = map(set, [paras, paras2])
            if tojoin(p1, p2, thresh=thresh):
                local_update.append(kw2)
                kw_done.extend([kw, kw2])
        if len(list(local_update)):
            new_aggr[kw] = local_update

    re_aggr = {}
    for k,v in new_aggr.items():
        for vv in v:
            re_aggr.setdefault(vv, [])
            re_aggr[vv].append(k)

    final_aggr = {}
    done = []
    for k,v in new_aggr.items():
        for vv in v:
            if vv in done:
                continue
            final_aggr.setdefault(k, [])
            this_joined = [x for x in v + re_aggr[vv]]
            final_aggr[k] = this_joined
            done.extend(this_joined)
            
    # print("final_aggrfinal_aggrfinal_aggrfinal_aggr", final_aggr)
    reindexed_mappping = {}
    kw_done = []
    for topics in list(final_aggr.values()):
        kw_done.extend(topics)
        topic = " + ".join([idx_to_entity[x] for x in topics])
        paras_corrected = []
        for tidx in topics:
            paras_corrected.extend([para_counter[x] for x in keywords_paras[tidx]])
        reindexed_mappping[topic] = list(set(paras_corrected))

    kw_not_done = [kw for kw in keywords_paras if kw not in kw_done]
    for kw in kw_not_done:
        reindexed_mappping[idx_to_entity[kw]] = list(set([para_counter[x] for x in keywords_paras[kw]]))
    reindexed_mappping = {k:v for k,v in sorted(reindexed_mappping.items(), key = lambda x: len(x[1]))[::-1]}
    return reindexed_mappping


def get_mapping_order(
        reindexed_mappping,
        all_paras,
        model,
        num_sections = 10,
        simfunc = euclidean
    ):
    # first we make the embeddings and global to local hash
    sentences = []
    order_local = []
    for k in list(reindexed_mappping.keys())[:num_sections]:
        sentences.extend(all_paras[reindexed_mappping[k]])
        order_local.extend(reindexed_mappping[k])
    order_local = {gidx:lidx for lidx, gidx in enumerate(order_local)}
    embedding_all_sentences = model.encode(sentences)

    mapping_w_order = {}
    for k in list(reindexed_mappping.keys())[:num_sections]:
        sentidx = [order_local[x] for x in reindexed_mappping[k]]
        emb_curr = embedding_all_sentences[sentidx]
        scores = {}
        for idx, base in enumerate(emb_curr):
            for jdx, targ in enumerate(emb_curr[idx:]):
                score = simfunc(base, targ)
                scores[(idx, idx + jdx)] = score
        if simfunc.__name__ == "euclidean":
            scores = {k:v for k,v in sorted(scores.items(), key = lambda x: x[1])[::-1]}
        else:
            scores = {k:v for k,v in sorted(scores.items(), key = lambda x: x[1])}
        ordered = []
        for pair in scores:
            ordered.extend([p for p in pair if p not in ordered])
        open_order = np.array(reindexed_mappping[k])[ordered][::-1]
        mapping_w_order[k] = open_order.tolist()

    return mapping_w_order


def get_aggregate_data(data_scrapped, inferSent):
    logging.info("Getting meta and all paragraphs scrapped data ...")
    all_paras, para_meta = get_meta_and_sentences(data_scrapped)
    logging.info("Aggregating by keywords ...")
    para_counter, keywords_paras, all_entities_idx, idx_to_entity = aggregate_by_keywords(para_meta)
    logging.info("Basic merging of topics ...")
    reindexed_mappping = basic_merging_topics(
        para_counter,
        keywords_paras,
        all_entities_idx,
        idx_to_entity,
        thresh = 0.1
    )
    logging.info("Get mapping order ...")
    mapping_w_order = get_mapping_order(
        reindexed_mappping,
        all_paras,
        inferSent,
        num_sections = 10,
        simfunc = euclidean
    )

    # now make the returnable data
    document_sections = []
    for sidx, (section_name, order) in enumerate(mapping_w_order.items()):
        records = []
        for idx in order:
            records.append({
                "htmltext": all_paras[idx],
                "master_link": {
                    "url": para_meta[idx]["urlraw"],
                    "link_name": para_meta[idx]["netloc"]
                }
            })
        document_sections.append({
            "id": sidx,
            "name": section_name,
            "records": records[:4]
        })
    return document_sections

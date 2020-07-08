"""file that has BERT for next sentence prediction model"""

import logging
import numpy as np
from tqdm import trange

import torch
import torch.nn.functional as F
from transformers import BertTokenizer, BertForNextSentencePrediction


class BertNextSentenceModel(object):
    def __init__(self):
        self._tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self._model = BertForNextSentencePrediction.from_pretrained('bert-base-uncased')
        self._model.eval()

    def _process_by_batch(self, flat_list, bsize):
        # single large processing is possible but makes the system too slow, so going for batch processing
        batches = [flat_list[i:i+bsize] for i in range(0, len(flat_list), bsize)]
        logits_batched = []
        logging.info("Processing something in Bert ...")
        for bidx in trange(len(batches)):
            b = batches[bidx]
            encoding = self._tokenizer.batch_encode_plus(b, return_tensors='pt', pad_to_max_length = True)
            logits= self._model(**encoding)[0].detach()
            logits_batched.extend(logits.numpy().tolist())
        logits_batched = np.array(logits_batched)
        return logits_batched

    def phrase_sim(self, strings, batch_size = 128):
        perm = [[(x1,x2) for x2 in strings] for x1 in strings]
        perm_flat = []
        for p in perm:
            perm_flat.extend(p)
        logits = self._process_by_batch(perm_flat, batch_size)
        return logits

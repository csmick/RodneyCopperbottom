#!/usr/bin/python3

import os
from random import randrange

class QuoteService(object):

    def __init__(self, root):
        self.quotes = {}
        for fname in os.listdir(root):
            topic, ext = os.path.splitext(fname)
            self.quotes[topic] = {}
            with open(os.path.join(root, fname)) as f:
                for line in f:
                    line = line.strip()
                    speaker, quote = line.split(',', 1)
                    if speaker not in self.quotes[topic].keys():
                        self.quotes[topic][speaker] = []
                    self.quotes[topic][speaker].append(quote)

    def list_topics(self):
        return list(self.quotes.keys())

    def list_speakers(self, topic):
        return list(self.quotes[topic].keys())

    def get_quote(self, topic, speaker):
        quote_index = randrange(0, len(self.quotes[topic][speaker]))
        quote = self.quotes[topic][speaker][quote_index]
        return (speaker, quote)


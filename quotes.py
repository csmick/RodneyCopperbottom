#!/usr/bin/python3

import os
from collections import defaultdict
from random import randrange

class QuoteService(object):

    def __init__(self, root):
        self.quotes = {}
        for fname in os.listdir(root):
            topic, ext = os.path.splitext(fname)
            self.quotes[topic] = defaultdict(list)
            with open(os.path.join(root, fname)) as f:
                for line in f:
                    line = line.strip()
                    character, quote = line.split(',', 1)
                    self.quotes[topic][character].append(quote)

    def list_topics(self):
        return list(self.quotes.keys())

    def list_speakers(self, topic):
        return list(self.quotes[topic].keys())

    def get_quote(self, args):
        topic = args[0] if args else None
        speaker = args[1] if 1 < len(args) else None
        if topic in self.list_topics():
            if speaker:
                if speaker not in self.list_speakers(topic):
                    return 'Available speakers: {}'.format(','.join(map(str, sorted(self.list_speakers(topic)))))
            else:
                speakers = self.list_speakers(topic)
                speaker_index = randrange(0, len(speakers))
                speaker = speakers[speaker_index]
            quote_index = randrange(0, len(self.quotes[topic][speaker]))
            quote = self.quotes[topic][speaker][quote_index]
            return (speaker, quote)
        else:
            return 'Available topics: {}'.format(','.join(map(str, sorted(self.list_topics()))))


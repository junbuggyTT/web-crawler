from bs4 import BeautifulSoup
from collections import defaultdict
import json
from math import log2
import networkx as nx
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from pathlib import Path
import re

class SearchEngineIndex:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.tokens = defaultdict(dict)
        self.tokens_IDF = defaultdict(int)
        self.webpages = defaultdict(dict)
        self.pagerank_scores = defaultdict(float)
        self.stop_words = "a about after again against all am an and any are aren't as at be because been \
            before being below between both but by can't cannot could couldn't did didn't do does doesn't \
                doing don't down during each few for from further had hadn't has hasn't have haven't having \
                    he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm \
                        i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor \
                            not of off on once only or other ought our ours ourselves out over own same shan't she \
                                she'd she'll she's should shouldn't so some such than that that's the their theirs them \
                                    themselves then there there's these they they'd they'll they're they've this those through \
                                        to too under until up very was wasn't we we'd we'll we're we've were weren't what what's \
                                            when when's where where's which while who who's whom why why's with won't would wouldn't \
                                                you you'd you'll you're you've your yours yourself yourselves".split()
    
    def lemmatize(self, token):
        return self.lemmatizer.lemmatize(token)
    
    def process(self, webpage: Path, parent: Path) -> list:
        json_key = str(parent.name + "/" + webpage.name)
            
        with open(webpage, 'r', encoding='utf8') as file:
            content = file.read()

        # Parse HTML content
        soup = BeautifulSoup(content, 'html.parser')

        # Extract text content
        text_content = soup.get_text()

        # Get bold, title, and heading text
        bold_text = [tag.get_text() for tag in soup.find_all('b')]
        title_text = [tag.get_text() for tag in soup.find_all('title')]
        heading_text = [tag.get_text() for tag in soup.find_all(re.compile(r'h[1-3]'))]

        # Combine text content
        all_text = text_content + ' '.join(bold_text) + ' '.join(title_text) + ' '.join(heading_text)
        title_text = ' '.join(title_text)
        heading_text = ' '.join(heading_text)
        bold_text = ' '.join(bold_text)

        # Tokenize text into words
        words = word_tokenize(all_text)
        title_words = word_tokenize(title_text)
        heading_words = word_tokenize(heading_text)
        bold_words = word_tokenize(bold_text)

        tokens = [self.lemmatize(token.lower()) for token in words if token.isalnum() and token not in self.stop_words and len(token) > 1]
        title_tokens = ' '.join([self.lemmatize(token.lower()) for token in title_words if token.isalnum() and token not in self.stop_words and len(token) > 1])
        heading_tokens = ' '.join([self.lemmatize(token.lower()) for token in heading_words if token.isalnum() and token not in self.stop_words and len(token) > 1])
        bold_tokens = ' '.join([self.lemmatize(token.lower()) for token in bold_words if token.isalnum() and token not in self.stop_words and len(token) > 1])
        
        # Link URLs to titles and headings
        self.webpages[json_key]["title"] = title_tokens
        self.webpages[json_key]["heading"] = heading_tokens
        self.webpages[json_key]["bold"] = bold_tokens

        # Unique words
        unique_words = set(tokens)

        # Word counts
        word_counts = {}
        for token in tokens:
            word_counts[token] = word_counts.get(token, 0) + 1

        # Update tokens IDF and dictionary
        for word in unique_words:
            self.tokens_IDF[word] = self.tokens_IDF.get(word, 0) + 1
            self.tokens[word][json_key] = (word_counts[word] / len(tokens))
    
    def compute_pagerank(self):
        # Create a directed graph using NetworkX
        graph = nx.DiGraph()

        # Add edges based on the links between webpages
        for word, webpages in self.tokens.items():
            for webpage, tfidf_score in webpages.items():
                graph.add_edge(webpage, word, weight = tfidf_score)

        # Calculate PageRank scores
        pagerank_dict = nx.pagerank(graph, weight = 'weight')

        # Link webpages to PageRank scores
        for webpage, score in pagerank_dict.items():
            self.pagerank_scores[webpage] = score
    
    def index(self, corpus: Path):
        for file in corpus.iterdir():
            if file.is_dir():
                for webpage in file.iterdir():
                    self.process(webpage, file)
        self.compute_pagerank()

        for key, value in self.tokens_IDF.items():
            for webpage, TF in self.tokens[key].items():
                self.tokens[key][webpage] = TF * log2(37000 / value) * self.pagerank_scores[webpage]
        

if __name__ == '__main__':
    search_engine = SearchEngineIndex()
    path = Path("/Users/junyoon/Downloads/WEBPAGES_RAW")
    search_engine.index(path)

    # Create a json file we can read from
    with open("/Users/junyoon/Downloads/finalindex.json", "w") as outfile: 
        json_dict = {'tfidfs': search_engine.tokens, 'webpages': search_engine.webpages}
        json.dump(json_dict, outfile)

from html import unescape
from lxml import html
from urllib.parse import urljoin, urlparse
import logging
import re

logger = logging.getLogger(__name__)

class Crawler:
    """
    This class is responsible for scraping urls from the next available link in frontier and adding the scraped links to
    the frontier
    """

    def __init__(self, frontier, corpus):
        self.frontier = frontier
        self.corpus = corpus
        self.visited_urls = set()
        # 1) Subdomains and number of URLs it has processed
        self.subdomains = {}
        # 2) Page with the most valid out links
        self.max_out_link = ('', 0)
        # 3) List of downloaded URLs
        self.downloaded_urls = []
        #    Identified traps
        self.traps = []
        # 4) Longest page in number of words
        self.longest_page = ('', 0)
        # 5) Most common words in the entire set of pages
        self.all_words = {}

    def start_crawling(self):
        """
        This method starts the crawling process which is scraping urls from the next available link in frontier and adding
        the scraped links to the frontier
        """
        while self.frontier.has_next_url():
            url = self.frontier.get_next_url()
            logger.info("Fetching URL %s ... Fetched: %s, Queue size: %s", url, self.frontier.fetched, len(self.frontier))
            url_data = self.corpus.fetch_url(url)

            for next_link in self.extract_next_links(url_data):
                if self.is_valid(next_link):
                    if self.corpus.get_file_name(next_link) is not None:
                        self.frontier.add_url(next_link)
                        # Keep track of downloaded URLs (Analytics #3)
                        self.downloaded_urls.append(next_link)
                else:
                    # Keep track of identified traps (Analytics #3)
                    self.traps.append(next_link)
        
        # Analytics
        with open('analytics.txt', 'w') as file:
            # 1) Subdomains and number of URLs it has processed
            file.write('1) Subdomains\n')
            for key, value in self.subdomain.items():
                file.write(f'   {key:20}\t{value}\n')
            
            # 2) Page with the most valid out links
            file.write('\n2) Page With Most Valid Out Links\n')
            file.write(f'   {self.max_out_link[0]}\t{self.max_out_link[1]}\n')

            # 3) List of downloaded URLs
            file.write('\n3) Downloaded URLs\n')
            for url in self.downloaded_urls:
                file.write(f'   {url}\n')
            #    Identified traps
            file.write('\n   Identified Traps\n')
            for trap in self.traps:
                file.write(f'   {trap}\n')

            # 4) Longest page in number of words
            file.write('\n4) Longest Page\n')
            file.write(f'   {self.longest_page[0]}\t({self.longest_page[1]} words)\n')

            # 5) Most common words in the entire set of pages
            file.write('\n5) 50 Most Common Words Across All Pages\n')
            sorted_words = sorted(self.all_words.items(), key = lambda pair : pair[1], reverse = True)
            count = 0
            #    Stops the loop after 50 words
            for word, num_of_words in sorted_words:
                file.write(f'   {word:20}\t({num_of_words})\n')
                count += 1
                if (count == 50):
                    break

    def extract_next_links(self, url_data):
        """
        The url_data coming from the fetch_url method will be given as a parameter to this method. url_data contains the
        fetched url, the url content in binary format, and the size of the content in bytes. This method should return a
        list of urls in their absolute form (some links in the content are relative and needs to be converted to the
        absolute form). Validation of links is done later via is_valid method. It is not required to remove duplicates
        that have already been fetched. The frontier takes care of that.
        """
        output_links = []
        
        if url_data['content']:
            try:
                # Parse HTML content
                tree = html.fromstring(url_data['content'])
                
                # Extract all anchor tags
                links = tree.xpath('//a/@href')
                
                # Convert relative links to absolute links
                base_url = url_data['url']
                for link in links:
                    absolute_link = urljoin(base_url, link)
                    output_links.append(absolute_link)
                
                # Extract text content from HTML and handle HTML entities
                content = unescape(html.tostring(tree, method = 'text', encoding = 'utf8').decode('utf-8'))

                # Tokenize words without HTML tags
                words = re.findall(r'(?<!<)\b\w+\b(?!>)', content)

                # English stop words from https://www.ranks.nl/stopwords
                stop_words = "a about after again against all am an and any are aren't as at be because been \
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
                
                # Tokenize the words in the page
                for word in words: 
                    if word.lower() not in stop_words:
                        self.all_words[word] = self.all_words.get(word, 0) + 1
               
                # Update the longest page if the current page contains more words (Analytics #4)
                if len(words) > self.longest_page[1]:
                    self.longest_page = (absolute_link, len(words))

            except Exception as e:
                logger.error(f"Error extracting links from {url_data['url']}: {e}")
        
        # Update the page if it contains more valid out links than the previous page (Analytics #2)
        if len(output_links) > self.max_out_link[1]:
            self.max_out_link = (absolute_link, len(output_links))

        return output_links

    def is_valid(self, url):
        """
        Function returns True or False based on whether the url has to be fetched or not. This is a great place to
        filter out crawler traps. Duplicated urls will be taken care of by frontier. You don't need to check for duplication
        in this method
        """
        # Parse a URL into 6 components:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False

        # Check for repeating sub-directories
        path_segments = parsed.path.strip("/").split("/")
        if len(path_segments) > 1 and len(path_segments) == len(set(path_segments)):
            return False
        
        # Checking continuously repeating sub-directories implemented
        url_val = parsed.scheme + parsed.netloc + parsed.path + parsed.query
        if url_val not in self.visited_urls:
            self.visited_urls.add(url_val)
        else:
            return False
        
        try:
            if ".ics.uci.edu" in parsed.hostname \
                and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4" \
                                + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
                                + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar" \
                                + "|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
                                + "|thmx|mso|arff|rtf|jar|csv" \
                                + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower()) \
                and len(url) < 120: # Handles checking long URLs
                
                # Keeps track of the visited subdomains and the number of URLs it has processed from each of those subdomains (Analytics #1)
                subdomain = parsed.hostname.split('.')[0]
                self.subdomains[subdomain] = self.subdomains.get(subdomain, 0) + 1
                return True

        except TypeError:
            print("TypeError for ", parsed)
            return False

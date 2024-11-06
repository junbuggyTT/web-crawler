README.md
# ICS Web Crawler
This project is a web crawler designed to fetch, process, and analyze web pages. It features a robust frontier to fetch URLs, index one-grams and two-grams, and query through a simple GUI. The project utilizes Python and various libraries for HTML parsing, tokenization, and indexing.

## Features
- Fetches URLs from a frontier and extracts valid links while maintaining analytics such as subdomains, downloaded URLs, and traps.
- Supports indexing of both one-grams and two-grams with TF-IDF weighting.
- Uses serialization to save and load the frontier's state.
- Uses Tkinter to allow for users to query indexed pages and display relevant results.
- Comprehensive logging for error handling unexpected bugs that may occur during the crawling process.

## Requirements
This project requires Python 3.9, 3.10, or 3.11.

## Getting started
1. Install the required libraries and run the following command:
```
pip install -r requirements.txt
```
2. To execute the one-gram and two-gram indexers:
```
python onegramindex.py
python twogramindex.py
```
3. To run the main script with the path to your corpus:
```
python main.py /path/to/corpus_directory
```
4. To use the GUI:
```
python gui.py
```

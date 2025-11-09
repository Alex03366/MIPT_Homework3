import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scraper import get_book_data, scrape_books

def test_get_book_data_returns_dict():
    test_url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    result = get_book_data(test_url)
    assert isinstance(result, dict)

def test_get_book_data_has_required_keys():
    test_url = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    result = get_book_data(test_url)
    required_keys = ['title', 'price', 'rating', 'stock']
    for key in required_keys:
        assert key in result

def test_scrape_books_returns_list():
    result = scrape_books(is_save=False)
    assert isinstance(result, list)
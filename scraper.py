import time
import requests
import schedule
import re
import os
import pytest
import io
import contextlib
from bs4 import BeautifulSoup
from typing import List, Dict


def get_book_data(book_url: str) -> dict:
    """
    ДОКУМЕНТАЦИЯ
    Получает подробную информацию о книге с указанной страницы.

    Функция парсит HTML-страницу книги, извлекает основные данные (название, цена, рейтинг,
    наличие, описание) и дополнительную информацию из таблицы Product Information.

    Args:
        book_url (str): URL-адрес страницы с книгой для парсинга

    Returns:
        dict: Словарь с данными о книге, содержащий следующие ключи:
            - 'title': название книги (str)
            - 'price': цена в формате строки (str)
            - 'rating': рейтинг в виде числа от 1 до 5 (int)
            - 'stock': количество книг в наличии (int)
            - 'description': описание книги (str)
            - 'upc': универсальный код товара (str)
            - 'product_type': тип продукта (str)
            - 'price_excl_tax': цена без учета налогов (str)
            - 'price_incl_tax': цена с учетом налогов (str)
            - 'tax': сумма налога (str)
            - 'availability': информация о доступности (str)
            - 'num_reviews': количество отзывов (int)
    """



    try:

        response = requests.get(book_url)
        response.raise_for_status()  # Проверяем успешность запроса
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1').text.strip()
        price = soup.find('p', class_='price_color').text.strip()

        rating_element = soup.find('p', class_='star-rating')
        rating_classes = rating_element.get('class', [])
        rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
        rating = 0
        for class_name in rating_classes:
            if class_name in rating_map:
                rating = rating_map[class_name]
                break
        stock_text = soup.find('p', class_='instock availability').text.strip()
        stock_match = re.search(r'(\d+)', stock_text)
        stock = int(stock_match.group(1)) if stock_match else 0

        description_element = soup.find('div', id='product_description')
        description = ""
        if description_element:
            description_sibling = description_element.find_next_sibling('p')
            if description_sibling:
                description = description_sibling.text.strip()
        product_info = {}
        info_table = soup.find('table', class_='table table-striped')
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                header = row.find('th').text.strip()
                value = row.find('td').text.strip()
                product_info[header] = value

        book_data = {
            'title': title,
            'price': price,
            'rating': rating,
            'stock': stock,
            'description': description,
            'upc': product_info.get('UPC', ''),
            'product_type': product_info.get('Product Type', ''),
            'price_excl_tax': product_info.get('Price (excl. tax)', ''),
            'price_incl_tax': product_info.get('Price (incl. tax)', ''),
            'tax': product_info.get('Tax', ''),
            'availability': product_info.get('Availability', ''),
            'num_reviews': int(product_info.get('Number of reviews', 0))
        }

        return book_data

    except requests.RequestException as e:
        print(f"Ошибка при запросе к странице: {e}")
        return {}
    except Exception as e:
        print(f"Ошибка при парсинге данных: {e}")
        return {}

    def scrape_books(is_save: bool = False):

        base_url = "http://books.toscrape.com/catalogue/"
        all_books_data = []
        page_number = 1

        print("Начало сбора данных о книгах...")

        while True:

            if page_number == 1:
                catalog_url = f"{base_url}index.html"
            else:
                catalog_url = f"{base_url}page-{page_number}.html"

            try:
                print(f"Обрабатывается страница {page_number}...")
                response = requests.get(catalog_url)

                if response.status_code == 404:
                    print("Достигнута последняя страница каталога.")
                    break

                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                book_elements = soup.find_all('article', class_='product_pod')

                if not book_elements:
                    print("На странице не найдено книг.")
                    break

                book_urls = []
                for book_element in book_elements:
                    link_element = book_element.find('h3').find('a')
                    if link_element and link_element.get('href'):
                        # Преобразуем относительную ссылку в абсолютную
                        book_relative_url = link_element['href']
                        if book_relative_url.startswith('../../../'):
                            # Убираем префикс и формируем полный URL
                            book_id = book_relative_url.replace('../../../', '')
                            book_full_url = f"{base_url}{book_id}"
                        else:
                            book_full_url = f"{base_url}{book_relative_url}"
                        book_urls.append(book_full_url)

                for i, book_url in enumerate(book_urls, 1):
                    print(f"  Обрабатывается книга {i}/{len(book_urls)}")
                    book_data = get_book_data(book_url)

                    if book_data:
                        all_books_data.append(book_data)
                        print(f"    ✓ Собраны данные: {book_data['title'][:50]}...")
                    else:
                        print(f"    ✗ Ошибка при сборе данных")

                    time.sleep(0.3)
                page_number += 1
                time.sleep(0.5)

            except requests.RequestException as e:
                print(f"Ошибка при загрузке страницы {page_number}: {e}")
                break
            except Exception as e:
                print(f"Неожиданная ошибка на странице {page_number}: {e}")
                break

        print(f"\nСбор данных завершен. Обработано книг: {len(all_books_data)}")
        if is_save and all_books_data:
            try:
                filename = 'books_data.txt'
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(f"Всего книг: {len(all_books_data)}\n")
                    file.write("=" * 80 + "\n\n")

                    for i, book in enumerate(all_books_data, 1):
                        file.write(f"Книга #{i}\n")
                        file.write("-" * 40 + "\n")

                        for key, value in book.items():
                            file.write(f"{key}: {value}\n")

                        file.write("\n" + "=" * 80 + "\n\n")

                print(f"✓ Данные сохранены в файл: {filename}")
                print(f"Путь к файлу: {os.path.abspath(filename)}")

            except Exception as e:
                print(f"✗ Ошибка при сохранении в файл: {e}")

        return all_books_data

    def run_daily_at_nineteen():

        print("Настройка ежедневного сбора данных в 19:00...")
        schedule.every().day.at("19:00").do(scheduled_scraping)
        print("Планировщик запущен. Ожидание времени выполнения...")
        print("Текущее время:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("Следующее выполнение: сегодня в 19:00")
        print("Для остановки нажмите Ctrl+C")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nПланировщик остановлен")

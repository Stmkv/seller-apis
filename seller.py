import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id, client_id, seller_token):
    """Получить список товаров магазина озон"""
    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id, seller_token):
    """Получить артикулы товаров магазина озон
    
    Args:
        client_id(str): id клиента из папки .env
        seller_token{str}: token продавца ozon из папки .env

    Returns:
        offer_ids(list): список содержащий id товаров

    Example:
        >>> get_offer_ids(client_id, seller_token)
    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id, seller_token):
    """Обновить цены товаров
    Args:
        prices(list): Спиок с ценами на товары
        client_id(str): id клиента из папки .env
        seller_token(str): token продавца ozon из папки .env
    Return:
        list: Ответ от API в формате JSON
    Example:
        >>> update_price(prices: list, client_id, seller_token)
    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id, seller_token):
    """Обновить остатки
    Args:
        stocks(list): Список товаров 
        client_id(str): id клиента из папки .env
        seller_token(str): token продавца ozon из папки .env

    Return:
        list: Возвращает список с ответами от API ozon

    Example:
        update_stocks(stocks: list, client_id, seller_token)
    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock():
    """Скачать файл ostatki с сайта casio
    
    Returns:
        watch_remnants(dict): Словаь с остатками товара с сайта https://timeworld.ru

    Example:
        >>> download_stock()

    """
    # Скачать остатки с сайта
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")
    # Создаем список остатков часов:
    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")  # Удалить файл
    return watch_remnants


def create_stocks(watch_remnants, offer_ids):
    '''Создает список остатков по данным с Ozon и словаря watch_remnants

    Args:
        watch_remnants(dict): Список остатков по файлу ostatki.xls
        offer_ids(list): Список остатков в Ozon

    Return:
        stocks(list): Список с остатками в магазине ozon и в файле ostatki.xls

    Example:
        >>> create_stocks(watch_remnants, offer_ids)
    '''
    # Уберем то, что не загружено в seller
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
    return stocks


def create_prices(watch_remnants, offer_ids):
    """Создает цены для товаров

    Args:
        watch_remnants(dict): Список с данными с сайта https://timeworld.ru
        offer_ids(list): Список артикулов товаров с магазина Ozon

    Return:
        price(dict): Сформированный словарь с информацией о стоимости товара

    Example:
        >>> create_prices(watch_remnants, offer_ids)
    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
    """Конвертация строки с ценой в строку с ценой без дробной части.

    Args:
        price (str): Строка, которая будет преобразована.

    Returns:
        str: Преобразованная строка, содержащая лишь цифры.

    Correct example:
        >>> print(price_conversion("1999.00 руб."))
        1999

    Incorrect example:
        >>> print(price_conversion(120))
        print(price_conversion(120))
              ^^^^^^^^^^^^^^^^^^^^^
    """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """Разделить список lst на части по n элементов
    Args:
        lst(list): Список с остаткими
        n(int): На сколько элементов нужно делить

    Return:
        yield: список элементов от i до i + n

    Exemple:
        >>> lsts = (i for i in divide([0, 1, 2, 3, 4, 5], 3)) 
        >>> for lst in lsts:
        >>> print lst
            [0, 1]
            [1, 2]
            [3, 4]
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
    '''Загружает цены
    Args:
        watch_remnants(dict): Список с данными с сайта https://timeworld.ru
        client_id(str): id клиента из папки .env
        seller_token(str): token продавца ozon из папки .env
    Return:
        list: Список обновленных цен на товары
    Example:
        >>> upload_prices(watch_remnants, client_id, seller_token)
    '''
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    '''Загружает остатки
    Args:
        watch_remnants(dict): Список с данными с сайта https://timeworld.ru
        client_id(str): id клиента из папки .env
        seller_token(str): token продавца ozon из папки .env
    Return:
        tuple: Список не отсутсвующих остатков и всех остатков
    Example:
        >>> upload_stocks(watch_remnants, client_id, seller_token)
    '''
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        # Обновить остатки
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        # Поменять цены
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()

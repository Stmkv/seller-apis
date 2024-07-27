# Обновляет цены и остатки товаров в Ozon и Yandex Market
---
Скрипты помогают автоматизировать обновление цен и остатков.

## seller.py

Скрипт может получать доступыне товары с [сайта](https://timeworld.ru).
Обновляет ассортимент на сайте Ozon - данные беруться из [файла](https://timeworld.ru/upload/files/ostatki.zip), а также обновляет цены.

Как запустить:

Необходимо создать папку .env и добавить туда:
```
SELLER_TOKEN = # токен продавца Ozon
CLIENT_ID = # id клиента Ozon
```

После чего необходимо выполнить команду:

`ptyhon selleer.py`

## market.py
Скрипт выгружает товары с [сайта](https://timeworld.ru). Обновляет цены, остатки продовца на Yandex Market.

Как запустить:

Необходимо создать папку .env и добавить туда:
```
FBS_ID = # FBS id магазина
DBS_ID = # DBS id магазина 
MARKET_TOKEN = # token yandex market
WAREHOUSE_FBS_ID = # складской id FBS
WAREHOUSE_DBS_ID = # складской id DBS
```

После чего необходимо выполнить команду:

`ptyhon market.py`

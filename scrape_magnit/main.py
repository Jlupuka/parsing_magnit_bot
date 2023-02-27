import asyncio
import datetime as dt

import aiofiles
import aiohttp
from aiocsv import AsyncWriter
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


async def collect_data(city_code: str = '2406') -> str:
    cut_time = dt.datetime.now().strftime('%d_%m_%Y_%H_%M')  # to save a file

    cookies = {'mg_geo_id': city_code}  # individual city code

    headers = {'User-Agent': UserAgent().random,
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'}

    headers_post = {
        'User-Agent': UserAgent().random,
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://www.magnit.ru/',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.magnit.ru',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
    }

    url = 'https://www.magnit.ru/promo/'

    async with aiohttp.ClientSession() as session:
        response = await session.post(url=url, cookies=cookies, headers=headers)
        soup = BeautifulSoup(await response.text(), 'lxml')
        total_cards = soup.find('p', class_='js-сatalogue__header-text сatalogue__header-text').text.strip().split()[1]
        #  total_cards - total number of products with the discount
        city = soup.find('a', class_='header__contacts-link header__contacts-link_city').text.strip()  # to save a file
        print(city, total_cards)
        products_data = list()  # the list in which such data will be recorded as: page - AJAX page,
        # index - card number, card_title, card_old_price, card_new_price, card_discount, card_sale_data
        for page in range(1, int(total_cards) // 50 + 1):  # divide by 50, because AJAX loads 50 products on 1 page
            data = {'page': page,
                    'FILTER': 'true',
                    'SORT': ''}
            rs = await session.post(url=url, cookies=cookies, headers=headers_post, data=data)
            cards = BeautifulSoup(await rs.text(), 'lxml').find_all('a', class_='card-sale card-sale_catalogue')
            # cards - all cards on the AJAX page
            for index, card in enumerate(cards):
                try:
                    card_title = card.find('div', class_='card-sale__title').text.strip()
                    card_discount = card.find('div', class_='card-sale__discount').text.strip()
                except AttributeError:  # if card_discount is None, an error is displayed
                    # because None has no attribute.text => this is a check,
                    # if this product is with a promotion and in stock, then we work further,
                    # otherwise we go through the cards further
                    continue
                old_price = card.find('div', class_="label__price label__price_old")
                new_price = card.find('div', class_="label__price label__price_new")
                card_old_price = f"{old_price.find('span', class_='label__price-integer').text.strip()}." \
                                 f"{old_price.find('span', class_='label__price-decimal').text.strip()}"
                card_new_price = f"{new_price.find('span', class_='label__price-integer').text.strip()}." \
                                 f"{new_price.find('span', class_='label__price-decimal').text.strip()}"
                card_sale_date = card.find('div', class_="card-sale__date").text.strip().replace('\n', ' - ')
                products_data.append([page, index, card_title, card_old_price,
                                      card_new_price, card_discount, card_sale_date])
            print(f'{page / (int(total_cards) // 50) * 100:.2F}%')
    async with aiofiles.open(f'{city}_{cut_time}.csv', 'w', encoding='utf-8', newline='') as file:
        writer = AsyncWriter(file)
        await writer.writerow(
            [
                'page',
                'index',
                'Продукт',
                'Старая цена',
                'Новая цена',
                'Процент скидки',
                'Время проведения акции',
            ]
        )
        await writer.writerows(
            sorted(products_data, key=lambda elems: int(elems[-2][1:-1]), reverse=True)
        )
    return f'{city}_{cut_time}.csv'


async def main():
    await collect_data()


if __name__ == '__main__':
    asyncio.run(main())

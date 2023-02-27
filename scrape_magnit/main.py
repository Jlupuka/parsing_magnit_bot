from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import datetime as dt
import aiohttp
import asyncio
import aiofiles
from aiocsv import AsyncWriter


async def collect_data(city_code: str = '2406') -> str:
    cut_time = dt.datetime.now().strftime('%d_%m_%Y_%H_%M')

    cookies = {'mg_geo_id': city_code}

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
        total_page = soup.find('p', class_='js-сatalogue__header-text сatalogue__header-text').text.strip().split()[1]
        city = soup.find('a', class_='header__contacts-link header__contacts-link_city').text.strip()
        print(city, total_page)
        products_data = list()
        for page in range(1, int(total_page) // 50 + 1):
            data = {'page': page,
                    'FILTER': 'true',
                    'SORT': ''}
            rs = await session.post(url=url, cookies=cookies, headers=headers_post, data=data)
            cards = BeautifulSoup(await rs.text(), 'lxml').find_all('a', class_='card-sale card-sale_catalogue')
            for index, card in enumerate(cards):
                try:
                    card_title = card.find('div', class_='card-sale__title').text.strip()
                    card_discount = card.find('div', class_='card-sale__discount').text.strip()
                except AttributeError:
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
            print(f'{page / (int(total_page) // 50) * 100:.2F}%')
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

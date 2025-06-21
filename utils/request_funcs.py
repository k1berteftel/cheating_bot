import asyncio
import random
import aiohttp
import json
import re
import os
import lxml
from typing import Literal

from datetime import datetime

from pydantic import BaseModel
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup


class Order(BaseModel):
    id: str
    name: str
    channel_name: str
    link: str
    volume: list
    # страна
    male: str
    speed: str
    # просмотры
    # отписки
    # уведомления
    # время последней подписки
    # отдельная очередь
    start: datetime | None
    status: Literal['выполняется', 'выполнен', 'пауза', 'отмена', 'ошибка']
    price: float
    create: datetime





async def add_fill_task(cookies: str, channel: str, volume: int, male: int, date: datetime, speed: int, sub_speed: int | None = None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        with open(f'cookies/{cookies}', "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto('https://tmsmm.ru/social/telegram/followers/1')
        await asyncio.sleep(1)
        await page.fill('#iTaskT1Channel', channel)

        await page.fill('#iTaskT1Count', str(volume))

        await page.click('#select2-selTasksT1Sex-container', button='left')
        await asyncio.sleep(0.5)
        await page.locator('li[id*="select2-selTasksT1Sex-result"]').nth(male).click()

        await page.click('#select2-selTasksT1Speed-container', button='left')
        await asyncio.sleep(0.5)

        await page.locator('li[id*="select2-selTasksT1Speed-result"]').nth(speed).click()
        if sub_speed:
            await page.fill('#iTaskT1MainSpeedInterval', str(sub_speed))

        await page.evaluate(
            """() => {
                const checkbox = document.getElementById('cTaskT1BackendUnSubscribing');
                if (!checkbox.checked) {
                    checkbox.checked = true;
                    Task.T1.checkBackendUnSubscribing();
                    Task.T1.getSum('#iTaskT1Count', '#iTaskT1Sum', 0, dataForGetSum);
                }
            }"""
        )
        await page.fill('#iTaskT1BackendUnSubscribingPercentageOfUnSubscribes', str(random.randint(5, 7)))
        await asyncio.sleep(0.2)
        await page.fill('#iTaskT1BackendUnSubscribingSpeedIntervalFrom', str(3))
        await asyncio.sleep(0.2)
        await page.fill('#iTaskT1BackendUnSubscribingSpeedIntervalBefore', str(9))
        await asyncio.sleep(1)

        await page.click("label[for='cTaskT1TimeStart']")
        await asyncio.sleep(1)
        await page.fill('#iTaskT1TimeStart', date.strftime('%d.%m.%Y %H:%M'))
        await asyncio.sleep(0.5)
        #await page.click('#bSocialCreateOrder', button='left')

        await asyncio.sleep(5)

        await context.close()
        await browser.close()

#asyncio.run(add_fill_task('/Users/kirill/Desktop/cheating_bot/cookies/Основа.json', 'https', 100, 2, datetime.today().replace(hour=2), 5, 2))


async def get_account_balance(cookies: str) -> float | None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        with open(f'cookies/{cookies}', "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto('https://tmsmm.ru/panel')

        try:
            await page.wait_for_selector("b.ym-hide-content")
            balance = await page.text_content("b.ym-hide-content")
        except Exception as err:
            print(err)
            return None
        await context.close()
        await browser.close()
        return float(balance)


async def get_account_jobs(cookies: str) -> list[Order]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        with open(f'cookies/{cookies}', "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()
        jobs = []
        for i in range(0, 100):
            await page.goto(f'https://tmsmm.ru/social/orders?s=-1&page={i}')
            html = await page.content()
            soup = BeautifulSoup(html, 'lxml')
            paginator = soup.find('ul', class_='pagination')
            if not paginator:
                break
            tasks = soup.find_all('div', class_='detail')
            if not tasks:
                break
            for task in tasks:
                print('Страница', i)
                obj_type = task.find('h5', class_='m-t-0').find('a', href=True)['href'].strip()
                if '/followers/1' not in obj_type:
                    continue
                objects = task.find_all('h5', class_='m-t-5')
                price = float(task.find_all('h5', class_='ym-hide-content')[6].find('span').find('span').text.strip().split(' ')[0])
                print(price)
                time = objects[13].find('span').text.split(':', maxsplit=1)[1].strip()
                jobs.append(
                    dict(
                        id=objects[0].find('span').text.split(':')[1].strip(),
                        name=objects[1].find('span').text.split(':')[1].strip(),
                        channel_name=objects[2].find('span').text.split(':')[1].strip(),
                        link=objects[3].find('a', href=True)['href'],
                        volume=[int(volume) for volume in objects[4].find('span', class_='label').text.strip().split('/')],
                        male=objects[6].find('span').text.split(':')[1].strip(),
                        speed=objects[7].find('span').text.split(':')[1].strip(),
                        start=datetime.strptime(time, '%Y-%m-%d %H:%M:%S') if time != 'нет' else None,
                        status=objects[14].find('span', class_='label').text.strip(),
                        price=price,
                        create=datetime.strptime(objects[15].find('span').text.split(':', maxsplit=1)[1].strip(), '%Y-%m-%d %H:%M:%S')
                    )
                )
        await context.close()
        await browser.close()
    jobs = [Order.model_validate(job) for job in jobs]
    return jobs


async def get_cookies(name: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False
        )
        context = await browser.new_context()
        page: Page = await context.new_page()

        await page.goto("https://tmsmm.ru/login")

        input('Введите enter после входа в аккаунт')

        cookies = await context.cookies()
        with open(f'{name}.json', "w") as f:
            json.dump(cookies, f, indent=2)

        await context.close()
        await browser.close()





#asyncio.run(get_cookies('Дополнительный'))
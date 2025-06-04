import asyncio
import random

import aiohttp
import json
import re

from playwright.async_api import async_playwright, Page


#url = 'https://tmsmm.ru/tasks/t1/add'


async def fill_request(**kwargs):
    #with open('cookies.json', 'r') as f:
        #cookies = json.loads(f.read())[-1]
    #print(cookies)
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('', headers=headers)as response:
            print(response)
            print(response.status)
            print(await response.content.read())
            print(await response.json())


#asyncio.run(fill_request())


async def add_fill_task(channel: str, volume: int, male: int, speed: int, sub_speed: int | None = None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        with open('cookies.json', "r") as f:
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

        await page.click('#bSocialCreateOrder', button='left')

        await asyncio.sleep(5)

        await context.close()
        await browser.close()


async def save_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Открытие страницы
        page: Page = await context.new_page()
        await page.goto("https://tmsmm.ru/panel")

        await asyncio.sleep(100)

        # Получаем куки после авторизации
        cookies = await context.cookies()
        print("Полученные cookies:", cookies)

        # Сохраняем куки в файл
        with open('cookies.json', "w") as f:
            json.dump(cookies, f, indent=2)

        await context.close()
        await browser.close()


#asyncio.run(add_fill_task('ССылка', 500, 2, 4))
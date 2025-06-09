import asyncio
import random
import aiohttp
import json
import re
import os

from playwright.async_api import async_playwright, Page, ProxySettings

from utils.errors import CaptchaError, AuthError
from utils.build_ids import get_random_id


async def add_fill_task(cookies: str, channel: str, volume: int, male: int, speed: int, sub_speed: int | None = None):
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

        await page.click('#bSocialCreateOrder', button='left')

        await asyncio.sleep(5)

        await context.close()
        await browser.close()


async def get_cookies(login: str, password: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--window-position=0,0",
                "--window-size=1920,1080"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
        )
        with open(f'static.json', "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        # Открытие страницы
        log = True
        passed = True
        page: Page = await context.new_page()
        await page.add_init_script("""
            delete navigator.__proto__.webdriver;
            delete navigator.__proto__.__proto__.webdriver;
            delete navigator.__proto__.chrome;
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'navigator', {
                value: {
                    platform: 'Win32',
                    appVersion: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                }
            });
        """)
        await page.goto("https://tmsmm.ru/login", wait_until="networkidle")
        init_url = page.url

        await asyncio.sleep(2)

        await page.fill('#iAuthEmail', value=login)
        await asyncio.sleep(0.5)
        await page.fill('#iAuthPassword', value=password)
        await asyncio.sleep(2)
        try:
            iframe = page.frame_locator('iframe[src*="smartcaptcha"]').nth(1)
            print('elem: \n', iframe)
            await iframe.locator("#js-button").wait_for(state="attached", timeout=10000)

            box = iframe.locator("#js-button")
            await box.wait_for(state="visible", timeout=10000)
            box = await box.bounding_box()
            await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await page.mouse.down()
            await page.mouse.up()
            await page.evaluate("""
                const el = document.getElementById('js-button');
                if (el) {
                    el.setAttribute('aria-checked', 'true');
                    el.click();
                }
            """)
        except Exception as err:
            print(err)
            passed = False
        await asyncio.sleep(2)
        await page.evaluate("document.getElementById('bAuthLogin').click()")
        try:
            locator = page.locator('.alert-danger')
            await locator.wait_for(timeout=10000)
            alert = await locator.text_content()
            print(alert)
            if alert.strip() == 'Поставьте галочку на против текста "Я не робот".':
                passed = False
            if alert.strip() == 'Не удается войти.':
                log = False
        except Exception as err:
            print(err)

        await asyncio.sleep(8)

        cookies = await context.cookies()
        name = get_random_id()
        with open(f'cookies/{name}.json', "w") as f:
            json.dump(cookies, f, indent=2)

        final_url = page.url
        await context.close()
        await browser.close()

        if not passed:
            raise CaptchaError('Captcha pass error')
        print(init_url, final_url, sep='\n')

        if init_url == final_url and not log:
            try:
                os.remove(f'cookies/{name}.json')
            except Exception:
                ...
            raise AuthError('Invalid login or password')
        return f'{name}.json'


#asyncio.run(get_cookies('kkulis985@gmail.com', '128hD8359'))
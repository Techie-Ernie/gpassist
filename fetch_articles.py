from gnews import GNews
from playwright.async_api import async_playwright
from googlenewsdecoder import gnewsdecoder
import time
import asyncio
import os


async def getHCISite(email, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(
            "https://accounts.google.com/signin/v2/identifier?hl=en&flowName=GlifWebSignIn&flowEntry=ServiceLogin"
        )
        await page.get_by_label("Email or phone").fill(email)
        await page.get_by_role("button", name="Next").click()
        await page.get_by_label("Enter your password").fill(password)
        await page.get_by_role("button", name="Next").click()
        time.sleep(10)  # Time to complete 2FA if enabled
        await page.goto("https://sites.google.com/hci.edu.sg/c1gp2025?pli=1&authuser=3")
        # find links in page content


def fetch_google_news():
    google_news = GNews(max_results=10)
    news_dict = {}
    sg_news = google_news.get_news("Singapore")
    for item in sg_news:
        news_dict[item["title"]] = gnewsdecoder(item["url"])["decoded_url"]
    return news_dict


async def getNJCReader():
    news_dict = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://the-njc-reader.vercel.app/")
        cards = await page.locator(".card-title").all()
        for card in cards:
            news_link = await card.get_by_role("link").get_attribute("href")
            news_title = await card.get_by_role("link").inner_text()
            news_dict[news_title] = news_link
        await browser.close()
        return news_dict


# asyncio.run(getHCISite(os.environ.get("HCI_EMAIL"), os.environ.get("HCI_PASSWORD")))

from gnews import GNews
from playwright.async_api import async_playwright
from googlenewsdecoder import gnewsdecoder
import time


async def login_hci(email, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context("data/", headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://accounts.google.com/signin/v2/identifier?hl=en&flowName=GlifWebSignIn&flowEntry=ServiceLogin"
        )
        await page.get_by_label("Email or phone").fill(email)
        await page.get_by_role("button", name="Next").click()
        await page.get_by_label("Enter your password").fill(password)
        await page.get_by_role("button", name="Next").click()
        time.sleep(20)  # Time to complete 2FA if enabled


async def get_hci_site():
    news_dict = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context("data/", headless=True)
        page = await browser.new_page()

        await page.goto(
            url="https://sites.google.com/hci.edu.sg/c1gp2025?pli=1&authuser=3"
        )
        # find links in page content
        topics = []
        cards = await page.query_selector_all(".XqQF9c")

        # time.sleep(2)

        for c in cards:
            link = await c.get_attribute("href")
            topics.append(link)
        print("Available topics: ")

        for x in range(3, len(topics)):
            print(f"{x-2}: {topics[x].split('/')[-1]}")
        # validate input
        topic_number = input("Topic number: ")

        topic = topics[
            int(topic_number) + 2
        ]  # just use first topic to test: should be man and the env
        print(f"ℹ️  Topic: {topic.split('/')[-1]}")
        # can prompt the user for which topic they want to extract data from
        await page.goto(url=topic)
        subtopics = await page.query_selector_all(".aJHbb")

        st_links = []
        for st in subtopics:
            if st.inner_text != "Task":
                st_link = await st.get_attribute("href")
                # print(st_link)
                if st_link and "task" not in st_link and st_link not in st_links:
                    st_links.append(st_link)

        for st_l in st_links:
            await page.goto(url=f"https://sites.google.com{st_l}")
            article_links = await page.query_selector_all(".XqQF9c")
            for article_link in article_links:
                link = await article_link.get_attribute("href")
                news_dict[link] = link
        return news_dict


def get_google_news():
    google_news = GNews(max_results=10)
    news_dict = {}
    sg_news = google_news.get_news("Singapore")
    for item in sg_news:
        news_dict[item["title"]] = gnewsdecoder(item["url"])["decoded_url"]
    return news_dict


async def get_njc_reader():
    news_dict = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        num_pages = int(input("Enter number of pages: "))
        for i in range(1, num_pages + 1):
            await page.goto(f"https://the-njc-reader.vercel.app/articles/{i}")
            cards = await page.locator(".card-title").all()
            for card in cards:
                news_link = await card.get_by_role("link").get_attribute("href")
                news_title = await card.get_by_role("link").inner_text()
                news_dict[news_title] = news_link

        await browser.close()
        return news_dict

from gnews import GNews
from playwright.sync_api import sync_playwright
from googlenewsdecoder import gnewsdecoder
import time


def login_hci(email, password):
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context("data/", headless=True)
        page = browser.new_page()
        page.goto(
            "https://accounts.google.com/signin/v2/identifier?hl=en&flowName=GlifWebSignIn&flowEntry=ServiceLogin"
        )
        page.get_by_label("Email or phone").fill(email)
        page.get_by_role("button", name="Next").click()
        page.get_by_label("Enter your password").fill(password)
        page.get_by_role("button", name="Next").click()
        time.sleep(20)  # Time to complete 2FA if enabled


def get_hci_site():
    news_dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context("data/", headless=True)
        page = browser.new_page()

        page.goto(url="https://sites.google.com/hci.edu.sg/c1gp2025?pli=1&authuser=3")
        # find links in page content
        topics = []
        cards = page.query_selector_all(".XqQF9c")

        # time.sleep(2)

        for c in cards:
            link = c.get_attribute("href")
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
        page.goto(url=topic)
        subtopics = page.query_selector_all(".aJHbb")

        st_links = []
        for st in subtopics:
            if st.inner_text != "Task":
                st_link = st.get_attribute("href")
                # print(st_link)
                if st_link and "task" not in st_link and st_link not in st_links:
                    st_links.append(st_link)

        for st_l in st_links:
            page.goto(url=f"https://sites.google.com{st_l}")
            article_links = page.query_selector_all(".XqQF9c")
            for article_link in article_links:
                link = article_link.get_attribute("href")
                news_dict[link] = link
        return news_dict


def get_google_news():
    google_news = GNews(max_results=10)
    news_dict = {}
    sg_news = google_news.get_news("Singapore")
    for item in sg_news:
        news_dict[item["title"]] = gnewsdecoder(item["url"])["decoded_url"]
    return news_dict


def get_njc_reader(num_pages):
    news_dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # num_pages = int(input("Enter number of pages: "))
        for i in range(1, num_pages + 1):
            page.goto(f"https://the-njc-reader.vercel.app/articles/{i}")
            cards = page.locator(".card-title").all()
            for card in cards:
                news_link = card.get_by_role("link").get_attribute("href")
                news_title = card.get_by_role("link").inner_text()
                news_dict[news_title] = news_link

        browser.close()
        return news_dict

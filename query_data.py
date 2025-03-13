import newspaper
import faiss
import numpy as np
import json
import os
import subprocess
from sentence_transformers import SentenceTransformer
from fetch_articles import get_google_news, get_hci_site, get_njc_reader
import asyncio
from pyfiglet import Figlet


embed_model = SentenceTransformer("all-MiniLM-L6-v2")

ARTICLE_DB_PATH = "articles.json"
FAISS_INDEX_PATH = "faiss_index.bin"

embedding_dim = 384  # MiniLM-L6-v2 output size
index = faiss.IndexFlatL2(embedding_dim)

# Load or create the article database
if os.path.exists(ARTICLE_DB_PATH):
    with open(ARTICLE_DB_PATH, "r", encoding="utf-8") as f:
        article_data = json.load(f)
else:
    article_data = {"articles": []}


# Function to load FAISS index and restore data
def load_faiss_index():
    global index
    if os.path.exists(FAISS_INDEX_PATH) and article_data["articles"]:
        print("✅ Loading FAISS index...")
        index = faiss.read_index(FAISS_INDEX_PATH)


def clear_existing_data():
    if os.path.exists(FAISS_INDEX_PATH):
        f = open(FAISS_INDEX_PATH, "r+")
        f.seek(0)
        f.truncate()
    if os.path.exists(ARTICLE_DB_PATH):
        f = open(ARTICLE_DB_PATH, "r+")
        f.seek(0)
        f.truncate()
        f.write('{"articles": []}')


def scrape_and_store(url):
    if url:
        if any(article["url"] == url for article in article_data["articles"]):
            print(f"⚠️   Article from {url} already stored.")
            return
        try:
            article = newspaper.Article(url)
            article.download()
            article.parse()
            text = article.text

            embedding = embed_model.encode([text])[0]
            if embedding.any():
                # Add to FAISS and article list
                index.add(np.array([embedding], dtype=np.float32))
                article_data["articles"].append({"url": url, "text": text})
                # Save FAISS index and article database
                faiss.write_index(index, FAISS_INDEX_PATH)
                with open(ARTICLE_DB_PATH, "w", encoding="utf-8") as f:
                    json.dump(article_data, f, indent=4)
                print(f"✅ Stored article from {url}")
        except newspaper.ArticleException as error:
            print("An exception occured: ", error)
            pass
    else:
        # Upload essay instead of article

        # Add to FAISS and article list
        index.add(np.array([embedding], dtype=np.float32))
        article_data["articles"].append({"url": url, "text": text})
        # Save FAISS index and article database
        faiss.write_index(index, FAISS_INDEX_PATH)
        with open(ARTICLE_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(article_data, f, indent=4)
        print(f"✅ Stored article from {url}")


def answer_question(question):
    if not article_data["articles"]:
        return "❌ No articles stored yet."

    q_embedding = embed_model.encode([question])[0].reshape(1, -1)
    _, nearest = index.search(q_embedding, 3)
    retrieved_articles = [
        article_data["articles"][i]["text"]
        for i in nearest[0]
        if i < len(article_data["articles"])
    ]
    # nearest[0] returns the closest n articles

    if not retrieved_articles:
        return "❌ No relevant articles found."

    context = "\n\n".join(retrieved_articles)
    prompt = f"""
    You are an AI assistant tasked with answering the following question using the provided news articles. You may include external knowledge but not speculation or invented facts.
    If you cannot answer, just say that you do not know instead of giving false information.
    ### Articles:
    {context}


    ### Question:
    {question}

    ### Answer:
    """.strip()

    llama_cmd = ["ollama", "run", "llama3.2", prompt]

    response = subprocess.run(llama_cmd, capture_output=True, text=True)

    return response.stdout.strip()


async def main():
    f = Figlet(font="slant")
    print(f.renderText("GPAssist"))
    news_dict = {}
    select = int(
        input(
            "1. Get articles from Google News \n2. Get articles from The NJC Reader \n3. Get articles from HCI GP microsite \n4. Clear current database of articles\n\n"
        )
    )
    match (select):
        case 1:
            print("Scraping articles from Google News...")
            news_dict = get_google_news()
        case 2:
            news_dict = await get_njc_reader()
        case 3:
            news_dict = await get_hci_site()
        case 4:
            clear_existing_data()
    load_faiss_index()

    for url in news_dict.values():
        scrape_and_store(url)

    while True:
        print(answer_question(input("Question: ")))


if __name__ == "__main__":
    # clear_existing_data()
    asyncio.run(main())

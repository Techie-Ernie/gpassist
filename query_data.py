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
from google_docs import get_doc_content

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
        f = open(FAISS_INDEX_PATH, "w")
        f.write("")
        f.close()

    if os.path.exists(ARTICLE_DB_PATH):
        f = open(ARTICLE_DB_PATH, "w")
        f.write('{"articles": []}')
        f.close()


def scrape_and_store(mode, url=None):
    text = ""
    if mode == "article":
        if url:
            if any(article["url"] == url for article in article_data["articles"]):
                print(f"⚠️   Article from {url} already stored.")
                return
            try:
                article = newspaper.Article(url)
                article.download()
                article.parse()
                text += article.text
            except newspaper.ArticleException as error:
                print("An exception occured: ", error)
                pass
    elif mode == "essay":
        # Upload essay instead of article
        text = input("Paste essay text: \n")
    elif mode == "docs":
        # Google Docs
        if url:
            text = get_doc_content(url)
        else:
            print("Need valid URL")
    embedding = embed_model.encode([text])[0]
    if embedding.any() and text:
        # Add to FAISS and article list
        index.add(np.array([embedding], dtype=np.float32))
        article_data["articles"].append({"url": url, "text": text})
        # Save FAISS index and article database
        faiss.write_index(index, FAISS_INDEX_PATH)
        with open(ARTICLE_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(article_data, f, indent=4)
        print(f"✅ Stored article from {url}")


def answer_question(question):
    print("answering qn")
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
    f = open("context.txt", "a")
    f.write(context)
    f.close()
    prompt = f"""
    You are an AI assistant tasked with answering the following question using the provided information. You may include external knowledge but do not speculate or invent facts.
    If you cannot answer, just say that you do not know instead of giving false information. If given a question that asks for your opinion, give a clear stand and explain your stand using the information you have been provided.
    ### Information:
    {context}


    ### Question:
    {question}

    ### Answer:
    """.strip()

    llama_cmd = ["ollama", "run", "llama3.2", prompt]

    response = subprocess.run(llama_cmd, capture_output=True, text=True)
    return response.stdout


async def main():

    mode = None
    f = Figlet(font="slant")
    print(f.renderText("GPAssist"))
    news_dict = {}
    select = int(
        input(
            "1. Ask the chatbot\n 2. Get articles from Google News \n3. Get articles from The NJC Reader \n4. Get articles from HCI GP microsite \n5. Paste an essay\n6. Import from Google Docs\n7. Clear current database of articles\n\n"
        )
    )
    match (select):
        case 1:
            pass
        case 2:
            mode = "article"
            print("Scraping articles from Google News...")
            news_dict = get_google_news()
        case 3:
            mode = "article"
            news_dict = await get_njc_reader()
        case 4:
            mode = "article"
            news_dict = await get_hci_site()

        case 5:
            mode = "essay"
            scrape_and_store(mode)
            load_faiss_index()
            while True:
                print(answer_question(input("Question: ")))
        case 6:
            mode = "docs"
            url = input("Google Docs URL: ")
            scrape_and_store(mode, url)
        case 7:
            clear_existing_data()

    load_faiss_index()

    for url in news_dict.values():
        scrape_and_store(mode, url)
    prompt = ""
    while prompt != "exit":
        prompt = input("Question:")
        print(answer_question(prompt))


if __name__ == "__main__":
    # clear_existing_data()
    asyncio.run(main())

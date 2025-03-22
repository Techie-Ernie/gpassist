import streamlit as st
from fetch_articles_sync import (
    get_google_news,
    get_njc_reader,
    get_hci_topics,
    get_hci_site,
)
from query_data import scrape_and_store, load_faiss_index

st.set_page_config(page_title="Import Data", page_icon="📈")

st.markdown("# Import Data")
st.sidebar.header("Import Data")
selection = st.selectbox(
    "Options:",
    [
        "Google News",
        "The NJC Reader",
        "HCI GP Microsite",
        "Import from Google Docs",
        "Paste your own essay ",
    ],
)
news_dict = {}

match (selection):
    case "Google News":
        news_dict = get_google_news()
        # st.write(news_dict)
    case "The NJC Reader":
        num_pages = st.text_input("Number of pages: ")
        if num_pages:
            with st.spinner("Please wait...", show_time=True):
                news_dict = get_njc_reader(int(num_pages))
            st.success("Got all news articles!")

            # st.write(news_dict)
    case "HCI GP Microsite":
        topic_text = ""
        topics = get_hci_topics()
        _ = ""

        for x in range(3, len(topics)):
            _ += f"{x-2}: {topics[x].split('/')[-1]}\n\n"
        st.text_area("Available topics", _, height=400, disabled=True)
        st.write(topic_text)
        topic_number = st.text_input("Topic Number: ")
        if topic_number:
            print("getting news_dict")
            with st.spinner("Please wait...", show_time=True):
                st.write(get_hci_site(int(topic_number), topics))
            st.success("Done!")
    case "Import from Google Docs":
        doc_url = st.text_input("Google Docs URL: ")
        if doc_url:
            scrape_and_store("docs", doc_url)
    case "Paste your own essay":
        essay = st.text_input("Essay: ")
        if essay:
            scrape_and_store("essay")
if len(news_dict) > 2:
    with st.spinner("Storing articles...", show_time=True):
        load_faiss_index()

        for url in news_dict.values():
            scrape_and_store("article", url)
    st.success("Stored all articles!")

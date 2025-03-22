import streamlit as st
from fetch_articles import get_google_news, get_njc_reader

st.set_page_config(page_title="Import Data", page_icon="📈")

st.markdown("# Import Data")
st.sidebar.header("Import Data")
st.write("""Import data for the LLM to reference""")
mode = st.selectbox(
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


if mode == "Google News":
    news_dict = get_google_news()
    st.write(news_dict)
"""
elif mode == "The NJC Reader":
    num_pages = st.text_input("Number of pages: ")
    news_dict = get_njc_reader(num_pages)
    st.write(news_dict)
"""

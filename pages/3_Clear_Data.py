import streamlit as st
from query_data import clear_existing_data


def double_confirm():
    st.error("Do you really want to do this?")
    st.button("Yes", on_click=clear_existing_data)


st.button("Clear data", on_click=double_confirm)

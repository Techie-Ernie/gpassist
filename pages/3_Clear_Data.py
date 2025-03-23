import streamlit as st
from query_data import clear_existing_data


@st.dialog("Confirm")
def confirm():
    if st.button("Yes"):
        clear_existing_data()


if st.button("Clear existing data"):
    confirm()
    st.success("Cleared!")

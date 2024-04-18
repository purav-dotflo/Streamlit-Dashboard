import streamlit as st

from pages import overall_stats, personal_stats


st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

page = PAGES[selection]
page.app()

st.title("Welcome to dotflo internal dashboard!")
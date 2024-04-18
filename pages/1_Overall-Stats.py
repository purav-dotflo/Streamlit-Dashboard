import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json  
from dateutil.parser import parse
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Streamlit Firestore Dashboard", layout="wide")

service_account_key_path = json.loads(st.secrets["firebase_service"])
try:
    firebase_admin.get_app()
except ValueError as e:
    cred = credentials.Certificate(service_account_key_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

users_ref = db.collection('users')
search_stats_ref = db.collection('search-usage')


@st.cache_data(ttl=600)
def overall_users_usage_bar_graph():
    global users_ref
    users = users_ref.stream()
    excluded_users = ["Purav Biyani", "Spencer Tate", "Nemath Ahmed"]

    data = []

    for user in users:
        user_data = user.to_dict()
        if user_data.get('displayName') in excluded_users:
            continue
        search_stats_ref = db.collection('search-usage').document(user.id)
        search_stats_doc = search_stats_ref.get()
        if search_stats_doc.exists:
            search_stats = search_stats_doc.to_dict()
            total_searches = search_stats.get('personProfileSearches', 0) + search_stats.get('customSearches', 0) + search_stats.get('companyProfileSearches', 0) + search_stats.get('linkedInSearches', 0)
            data.append({
                "User": user_data.get('displayName'),
                "Total Searches": total_searches
            })
    
    df = pd.DataFrame(data)
    df = df.sort_values("Total Searches", ascending=True)

    fig = px.bar(df, x="Total Searches", y="User", orientation='h', title="Total Searches by Users")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig)

@st.cache_data(ttl=600)
def get_overall_stats():
    global users_ref
    users = users_ref.stream()
    excluded_users = ["Purav Biyani", "Spencer Tate", "Nemath Ahmed"]

    total_users = 0
    total_worksheets = 0
    for user in users:
        total_users += 1
        if user.to_dict().get('displayName') in excluded_users:
            continue
        worksheets_ref = db.collection('worksheets').document(user.id)
        worksheets_doc = worksheets_ref.get()
        if worksheets_doc.exists:
            user_data = worksheets_doc.to_dict()
            total_worksheets += len(user_data)
    
    return {"total_users": total_users, "total_worksheets": total_worksheets}

@st.cache_data(ttl=600)
def get_overall_usage_stats():
    global users_ref
    global search_stats_ref
    users_ref = db.collection('users')
    users = users_ref.stream()

    total_users = 0
    total_searches = 0
    total_profile_enrichments = 0
    total_custom_research_prompts = 0
    total_company_profiles = 0
    total_linkedin_profiles = 0

    excluded_users = ["Purav Biyani", "Spencer Tate", "Nemath Ahmed"]

    for user in users:
        user_data = user.to_dict()
        display_name = user_data.get('displayName', '')

        if display_name in excluded_users:
            continue

        total_users += 1

        search_stats_doc = search_stats_ref.document(user.id).get()
        if search_stats_doc.exists:
            search_stats = search_stats_doc.to_dict()
            total_profile_enrichments += search_stats.get('personProfileSearches', 0) 
            total_custom_research_prompts += search_stats.get('customSearches', 0)  
            total_company_profiles += search_stats.get('companyProfileSearches', 0)
            total_linkedin_profiles += search_stats.get('linkedInSearches', 0)
        
    total_searches += total_profile_enrichments + total_custom_research_prompts + total_company_profiles + total_linkedin_profiles

    return {
        "total_users": total_users,
        "total_searches": total_searches,
        "total_profile_enrichments": total_profile_enrichments,
        "total_custom_research_prompts": total_custom_research_prompts,
        "total_company_profiles": total_company_profiles,
        "total_linkedin_profiles": total_linkedin_profiles
    }


with st.container():
    st.title("Overall Stats")

overall_stats = get_overall_stats()
overall_usage_stats = get_overall_usage_stats()

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown(f"Total Users: {overall_stats['total_users']}")

with col2:
    with st.container(border=True):
        st.markdown(f"Total Worksheets: {overall_stats['total_worksheets']}")

with st.subheader("Overall Usage Bar Graph"):
    with st.container():
        overall_users_usage_bar_graph()


st.subheader("Overall Usage Stats")
with st.container(border=True):
    col3, col4, col5, col6, col7 = st.columns(5)
    
    with col3:
        with st.container(border=True):
            st.markdown("Total Searches")
            st.markdown(overall_usage_stats["total_searches"])
    
    with col4:
        with st.container(border=True):
            st.markdown("Person Profiles")
            st.markdown(overall_usage_stats["total_profile_enrichments"])
    
    with col5:
        with st.container(border=True):
            st.markdown("Company Profiles")
            st.markdown(overall_usage_stats["total_company_profiles"])
    
    with col6:
        with st.container(border=True):
            st.markdown("Custom Prompts")
            st.markdown(overall_usage_stats["total_custom_research_prompts"])
    
    with col7:
        with st.container(border=True):
            st.markdown("LinkedIn Searches")
            st.markdown(overall_usage_stats["total_linkedin_profiles"])

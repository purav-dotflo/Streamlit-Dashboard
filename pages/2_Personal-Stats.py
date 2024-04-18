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
worksheet_doc_ref = db.collection('worksheets')
search_stats_ref = db.collection('search-usage')


@st.cache_data(ttl=660)
def get_users():
    global users_ref
    users = users_ref.stream()
    return {user.id: user.to_dict().get('displayName', 'No Name') for user in users}
    
@st.cache_data(ttl=600)
def get_user_trials(user_id):
    global users_ref
    user_doc = users_ref.document(user_id).get()
    plan = user_doc.to_dict().get('current_plan', 'No Plan')
    trial_activation = user_doc.to_dict().get('trial_activated_date')
    days_left = 0
    
    if trial_activation:
        trial_activation_date = datetime.strptime(trial_activation, "%Y-%m-%dT%H:%M:%S.%f")
        trial_end_date = trial_activation_date + timedelta(days=14)
        current_date = datetime.now()
        
        days_left = (trial_end_date - current_date).days
        
        if days_left < 0:
            days_left = 0

    return plan, days_left

@st.cache_data(ttl=600)
def update_user_plan(user_id, new_plan):
    global users_ref
    update_data = {'current_plan': new_plan}
    get_update_user_plan_counter += 1

    if new_plan.lower() == 'trial':
        update_data['trial_activated_date'] = datetime.now().isoformat()
    elif new_plan.lower() == 'premium':
        update_data['last_plan_upgrade_date'] = datetime.now().isoformat()

    try:
        users_ref.update(update_data)
        st.success(f"Plan updated to {new_plan} for user ID: {user_id}.")
        if new_plan.lower() == 'trial':
            st.success("Trial activation date updated.")
        elif new_plan.lower() == 'premium':
            st.success("Last plan upgrade date updated.")
    except Exception as e:
        st.error(f"Failed to update user plan: {e}")

@st.cache_data(ttl=600)
def get_worksheets(user_id):
    global worksheet_doc_ref
    worksheet_doc = worksheet_doc_ref.document(user_id).get()
    return worksheet_doc.to_dict() if worksheet_doc.exists else {}

@st.cache_data(ttl=600)
def get_user_stats(user_id):
    global search_stats_ref
    search_doc = search_stats_ref.document(user_id).get()
    if not search_doc.exists:
        return {
            "Total Searches": 0,
            "Person Profiles Enriched": 0,
            "Company Profiles Enriched": 0,
            "Custom Research Prompts": 0,
            "LinkedIn Profile Enriched": 0
        }
    person_profile_searches = search_doc.to_dict().get('personProfileSearches', 0)
    company_profile_searches = search_doc.to_dict().get('companyProfileSearches', 0)
    custom_searches = search_doc.to_dict().get('customSearches', 0)
    linkedin_searches = search_doc.to_dict().get('linkedInSearches', 0)
    return {
        "Total Searches": person_profile_searches + company_profile_searches + custom_searches + linkedin_searches,
        "Person Profiles Enriched": person_profile_searches,
        "Company Profiles Enriched": company_profile_searches,
        "Custom Research Prompts":  custom_searches,
        "LinkedIn Profile Enriched": linkedin_searches
    }

st.title("Personal Stats")
selected_user_id = st.sidebar.selectbox('Select a User', options=list(get_users().keys()), format_func=lambda x: get_users()[x])

if selected_user_id:
    st.subheader(f"Worksheets for {get_users()[selected_user_id]}")
    user_stats = get_user_stats(selected_user_id)
    user_worksheets = get_worksheets(selected_user_id)
    if user_worksheets:
        for worksheet_id, worksheet_data in user_worksheets.items():
            with st.expander(f"Worksheet: {worksheet_data.get('name', worksheet_id)}"):
                st.write(f"Rows: {worksheet_data.get('numRows', 'N/A')}")
                custom_research_prompts = worksheet_data.get("customResearchPrompts", {})
                if custom_research_prompts:
                    st.json(custom_research_prompts)
    else:
        st.write("No worksheets found.")

with st.sidebar:
    with st.container(border=True):
        st.subheader("Update Plan")
        with st.container():
            new_plan = st.selectbox("Select Plan", options=["Trial", "Inactive", "Premium"])
            # activation_date = st.date_input("Activation Date", min_value=datetime.now().date())

            if st.button("Update Plan"):
                update_user_plan(selected_user_id, new_plan)

    user_stats = get_user_stats(selected_user_id)
    if not user_stats:
        st.write("No search data found for this user.")
    else:
        user_plan = get_user_trials(selected_user_id)
        if not user_plan:
            st.write("No plan found for this user.")
        else:
            with st.container(border=True):
                st.markdown(f"**Plan:** {user_plan[0]}")
                st.markdown(f"**Trial Ends in:** {user_plan[1]} days")
        with st.expander("Total Searches", expanded=True):
            st.markdown(f"{user_stats['Total Searches']}")

        with st.expander("Person Profiles Enriched", expanded=True):
            st.markdown(f"{user_stats['Person Profiles Enriched']}")

        with st.expander("Company Profiles Enriched", expanded=True):
            st.markdown(f"{user_stats['Company Profiles Enriched']}")

        with st.expander("Custom Research Prompts", expanded=True):
            st.markdown(f"{user_stats['Custom Research Prompts']}")

        with st.expander("LinkedIn Profile Enriched", expanded=True):
            st.markdown(f"{user_stats['LinkedIn Profile Enriched']}")

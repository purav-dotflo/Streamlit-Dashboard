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

@st.cache_data(ttl=600)
def get_users():
    users_ref = db.collection('users')
    users = users_ref.stream()
    return {user.id: user.to_dict().get('displayName', 'No Name') for user in users}


@st.cache_data(ttl=600)
def overall_users_usage_bar_graph():
    users_ref = db.collection('users')
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


def get_user_trials(user_id):
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    plan = user_doc.to_dict().get('current_plan', 'No Plan')
    trial_activation = user_doc.to_dict().get('trial_activated_date')
    days_left = 0
    
    if trial_activation:
        # trial_activation_date = datetime.strptime(trial_activation, "%Y-%m-%dT%H:%M:%S.%fZ")
        try:
            trial_activation_date = datetime.strptime(trial_activation, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            trial_activation_date = datetime.strptime(trial_activation, "%Y-%m-%dT%H:%M:%S.%f")
        trial_end_date = trial_activation_date + timedelta(days=14)
        current_date = datetime.now()
        
        days_left = (trial_end_date - current_date).days
        
        if days_left < 0:
            days_left = 0

    return plan, days_left


def update_user_plan(user_id, new_plan):
    user_ref = db.collection('users').document(user_id)
    update_data = {'current_plan': new_plan}

    if new_plan.lower() == 'trial':
        update_data['trial_activated_date'] = datetime.now().isoformat()
    elif new_plan.lower() == 'premium':
        update_data['last_plan_upgrade_date'] = datetime.now().isoformat()

    try:
        user_ref.update(update_data)
        st.success(f"Plan updated to {new_plan} for user ID: {user_id}.")
        if new_plan.lower() == 'trial':
            st.success("Trial activation date updated.")
        elif new_plan.lower() == 'premium':
            st.success("Last plan upgrade date updated.")
    except Exception as e:
        st.error(f"Failed to update user plan: {e}")


@st.cache_data(ttl=600)
def get_worksheets(user_id):
    worksheet_doc_ref = db.collection('worksheets').document(user_id)
    worksheet_doc = worksheet_doc_ref.get()
    return worksheet_doc.to_dict() if worksheet_doc.exists else {}

@st.cache_data(ttl=600)
def get_feedback():
    feedback_ref = db.collection('v4-feedback')
    feedback_docs = feedback_ref.stream()
    return [doc.to_dict() for doc in feedback_docs]

@st.cache_data(ttl=600)
def get_overall_stats():
    users_ref = db.collection('users')
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

        search_stats_ref = db.collection('search-usage').document(user.id)
        search_stats_doc = search_stats_ref.get()
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

@st.cache_data(ttl=600)
def get_user_stats(user_id):
    search_ref = db.collection('search-usage').document(user_id)
    search_doc = search_ref.get()
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

st.sidebar.title("Navigation")
selected_user_id = st.sidebar.selectbox('Select a User', options=list(get_users().keys()), format_func=lambda x: get_users()[x])

with st.container():
    st.title("Dashboard")

overall_stats = get_overall_stats()
overall_usage_stats = get_overall_usage_stats()

with st.expander("Overall Stats"):
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

    # with st.sidebar:
    #     st.subheader("Feedback")
    #     feedback_list = get_feedback()  
    #     if not feedback_list:
    #         st.write("No feedback found.")
    #     else:
    #         for feedback in feedback_list:
    #             dialog_texts = feedback["dialogContent"]
    #             feedback_type = feedback["feedbackType"]

    #             summary = "Feedbacks"

    #             with st.expander(summary):
    #                 for dialog in dialog_texts:
    #                     dialog_text = dialog["text"]
    #                     st.markdown(f"**Dialog:** {dialog_text}")

    #                     if feedback_type == "thumbsUp":
    #                         st.markdown("👍")
    #                     elif feedback_type == "thumbsDown":
    #                         st.markdown("👎")

with st.sidebar:
    st.subheader("Update Plan")
    with st.container():
        new_plan = st.selectbox("Select Plan", options=["Trial", "Inactive", "Premium"])
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



## feedback
## number of users (plan)

## better UI
## bar graph of usage (users vs searches)
## auth signins
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json  # In case we need to pretty-print JSON data

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
    
    total_users = 0
    total_worksheets = 0
    for user in users:
        total_users += 1
        worksheets_ref = db.collection('worksheets').document(user.id)
        worksheets_doc = worksheets_ref.get()
        if worksheets_doc.exists:
            user_data = worksheets_doc.to_dict()
            total_worksheets += len(user_data)
    
    return {"total_users": total_users, "total_worksheets": total_worksheets}

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
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Users", value=overall_stats["total_users"])
    with col2:
        st.metric(label="Total Worksheets", value=overall_stats["total_worksheets"])

if selected_user_id:
    st.subheader(f"Worksheets for {get_users()[selected_user_id]}")
    user_stats = get_user_stats(selected_user_id)
    if user_stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(label="Total Searches", value=user_stats["Total Searches"])
        with col2:
            st.metric(label="Person Profiles Enriched", value=user_stats["Person Profiles Enriched"])
        with col3:
            st.metric(label="Company Profiles Enriched", value=user_stats["Company Profiles Enriched"])
        with col4:
            st.metric(label="Custom Research Prompts", value=user_stats["Custom Research Prompts"])
        with col5:
            st.metric(label="LinkedIn Profiles Enriched", value=user_stats["LinkedIn Profile Enriched"])
    else:
        st.write("No search data found for this user.")
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
    st.subheader("Feedback")
    feedback_list = get_feedback()  
    if not feedback_list:
        st.write("No feedback found.")
    else:
        for feedback in feedback_list:
            dialog_texts = feedback["dialogContent"]
            feedback_type = feedback["feedbackType"]

            summary = "Feedbacks"

            with st.expander(summary):
                for dialog in dialog_texts:
                    dialog_text = dialog["text"]
                    st.markdown(f"**Dialog:** {dialog_text}")

                    if feedback_type == "thumbsUp":
                        st.markdown("👍")
                    elif feedback_type == "thumbsDown":
                        st.markdown("👎")







## feedback
## number of users (plan)
## better UI
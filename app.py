import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json  # In case we need to pretty-print JSON data
import yaml

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
    for feedback in feedback_list:
        st.write(feedback)





## feedback
## number of users (plan)
## better UI
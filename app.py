import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(page_title="Streamlit Firestore Dashboard", layout="wide")

service_account_key_path = "service.json"
try:
    firebase_admin.get_app()
except ValueError as e:
    cred = credentials.Certificate(service_account_key_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_users():
    users_ref = db.collection('users')
    users = users_ref.stream()  
    user_options = {user.id: user.to_dict().get('displayName', 'No Name') for user in users}  
    return user_options


def get_worksheets(user_id):
    worksheet_doc_ref = db.collection('worksheets').document(user_id)
    worksheet_doc = worksheet_doc_ref.get()  
    
    if worksheet_doc.exists:
        return worksheet_doc.to_dict()  
    else:
        return {}  

def get_worksheet_details(worksheet_id, user_id):
    try:
        worksheet_ref = db.collection('worksheets').document(user_id)
        doc = worksheet_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            st.error("Worksheet not found.")
            return None
    except FirebaseError as e:
        st.error("Firebase error: " + str(e))
        return None


st.subheader('Select a User')
user_options = get_users()
selected_user_id = st.selectbox('', options=list(user_options.keys()), format_func=lambda x: user_options[x])

if selected_user_id:
    st.subheader('Worksheets')
    worksheets = get_worksheets(selected_user_id)
    for worksheet in worksheets:
        st.write(worksheet)
        worksheet_details = get_worksheet_details(worksheet, selected_user_id)
        if worksheet_details:
            st.write(worksheet_details)



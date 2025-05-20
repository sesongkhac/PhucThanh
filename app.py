
import os
import streamlit as st
import pdfplumber
import docx
import requests

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Đọc JSON từ biến môi trường
service_json = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")
creds_dict = json.loads(service_json)
creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)


DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "mistralai/mistral-7b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

st.set_page_config(page_title="Chatbot PCCC", layout="wide")

def extract_text(file_path):
    text = ""
    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    elif file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    return text

def ask_openrouter(context, question):
    prompt = f"{context}\n\nCâu hỏi: {question}\nTrả lời:"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý AI trả lời bằng tiếng Việt, chính xác, rõ ràng."},
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Lỗi {response.status_code}: {response.text}"

st.title("💬 Chatbot PCCC (ghi nhớ tài liệu)")
st.markdown("Tải tài liệu 📄 (.txt, .docx, .pdf) hoặc đặt câu hỏi trực tiếp")

# Giao diện upload
uploaded_file = st.file_uploader("Tải tài liệu (tùy chọn)", type=["txt", "docx", "pdf"])
if uploaded_file:
    saved_path = os.path.join(DATA_DIR, uploaded_file.name)
    with open(saved_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ Đã lưu tài liệu: {uploaded_file.name}")

# Tổng hợp nội dung từ tất cả các file đã lưu
context = ""
for filename in os.listdir(DATA_DIR):
    file_path = os.path.join(DATA_DIR, filename)
    context += extract_text(file_path) + "\n"

# Giao diện câu hỏi
question = st.text_input("Nhập câu hỏi:")
if question:
    with st.spinner("🔎 Đang trả lời..."):
        answer = ask_openrouter(context, question)
    st.success("🟢 Trả lời:")
    st.write(answer)

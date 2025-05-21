
import os
import requests
import base64
import streamlit as st
import pdfplumber
import docx
from datetime import datetime
from io import BytesIO

# GitHub + OpenRouter cấu hình
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
UPLOAD_PATH = "uploads"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "mistralai/mistral-7b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# === GitHub tương tác ===
def upload_file_to_github(file_data, filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{UPLOAD_PATH}/{filename}"
    encoded = base64.b64encode(file_data).decode("utf-8")
    payload = {"message": f"Add {filename}", "content": encoded}
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.put(url, json=payload, headers=headers)
    return r.status_code in [200, 201]

def list_files_in_repo():
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{UPLOAD_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    return r.json() if r.status_code == 200 else []

def fetch_raw_file_text(file_url):
    r = requests.get(file_url)
    return r.content if r.status_code == 200 else b""

# === Xử lý văn bản ===
def extract_text_bytes(file_bytes, filename):
    if filename.endswith(".txt"):
        return file_bytes.decode("utf-8")
    elif filename.endswith(".docx"):
        doc = docx.Document(BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs)
    elif filename.endswith(".pdf"):
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            return "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
    return ""

def ask_openrouter(context, question):
    prompt = f"{context}\n\nCâu hỏi: {question}\nTrả lời:"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý AI tiếng Việt, trả lời chính xác, thân thiện."},
            {"role": "user", "content": prompt}
        ]
    }
    r = requests.post(API_URL, headers=HEADERS, json=payload)
    return r.json()["choices"][0]["message"]["content"].strip() if r.status_code == 200 else f"Lỗi {r.status_code}: {r.text}"

# === UI Streamlit ===
st.set_page_config(page_title="Chatbot PCCC", layout="wide")
st.title("🧠 Chatbot PCCC - Phong cách Chat như Zalo")

# Tải file
with st.expander("📤 Tải tài liệu"):
    uploaded = st.file_uploader("Chọn tài liệu (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
    if uploaded:
        fname = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{uploaded.name}"
        if upload_file_to_github(uploaded.getvalue(), fname):
            st.success(f"✅ Đã lưu vào GitHub: {fname}")

# Nạp nội dung các file làm context
context = ""
files = list_files_in_repo()
for f in files:
    if f["name"].endswith((".txt", ".docx", ".pdf")):
        raw = fetch_raw_file_text(f["download_url"])
        context += extract_text_bytes(raw, f["name"]) + "\n"

# Giao diện Chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown("### 💬 Đối thoại cùng chatbot")

for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("ai"):
        st.markdown(msg["bot"])

prompt = st.chat_input("Nhập câu hỏi tại đây...")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("🤖 Đang suy nghĩ..."):
        response = ask_openrouter(context, prompt)

    with st.chat_message("ai"):
        st.markdown(response)

    st.session_state.chat_history.append({"user": prompt, "bot": response})

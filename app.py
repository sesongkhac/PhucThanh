
import os
import streamlit as st
import pdfplumber
import docx
import requests

# Render tự cung cấp PORT qua biến môi trường
port = int(os.environ.get("PORT", 8501))
st.set_page_config(page_title="Chatbot PCCC", layout="wide")

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "mistralai/mistral-7b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def extract_text(file):
    text = ""
    if file.name.endswith(".txt"):
        text = file.read().decode("utf-8")
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
    elif file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    return text

def ask_openrouter(context, question):
    prompt = f"Nội dung tài liệu:\n{context}\n\nCâu hỏi: {question}\nTrả lời:"
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

st.title("💬 Chatbot PCCC (OpenRouter)")
st.markdown("Tải tài liệu 📄 (.txt, .docx, .pdf) và đặt câu hỏi")

uploaded_file = st.file_uploader("Tải tài liệu", type=["txt", "docx", "pdf"])
question = st.text_input("Nhập câu hỏi:")

if uploaded_file and question:
    content = extract_text(uploaded_file)
    if content:
        with st.spinner("Đang tạo phản hồi..."):
            answer = ask_openrouter(content, question)
        st.success("🟢 Trả lời:")
        st.write(answer)
    else:
        st.warning("Không đọc được nội dung từ tài liệu.")

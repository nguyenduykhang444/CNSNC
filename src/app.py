import os
import dotenv
import google.generativeai as genai
import streamlit as st

# 🧩 Tải biến môi trường từ file .env
dotenv.load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

# ⚙️ Cấu hình Gemini
if not api_key:
    st.error("❌ Không tìm thấy GOOGLE_API_KEY trong file .env")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-pro")

# 📁 Hàm tải dữ liệu từ thư mục 'data'
def load_data():
    data = ""
    data_dir = "data"
    if not os.path.exists(data_dir):
        st.warning(f"⚠️ Thư mục '{data_dir}' không tồn tại. Vui lòng tạo và thêm file .txt.")
        return data
    files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
    if not files:
        st.warning("⚠️ Không tìm thấy file .txt nào trong thư mục 'data'.")
        return data
    for file in files:
        try:
            with open(os.path.join(data_dir, file), "r", encoding="utf-8") as f:
                data += f.read() + "\n"
        except Exception as e:
            st.error(f"Lỗi khi đọc file {file}: {e}")
    return data

# 🌊 Giao diện chính
st.set_page_config(page_title="Chatbot Hỏi-Đáp Gemini", page_icon="🦐", layout="wide")

st.title("🦐 Chatbot Hỏi-Đáp về Quy Trình Nuôi Tôm (Gemini)")

data = load_data()
if not data:
    st.info("💡 Hãy thêm các file .txt chứa nội dung quy trình vào thư mục `data/` để chatbot có dữ liệu nền.")

# 🧠 Nhập câu hỏi
question = st.text_area("💬 Nhập câu hỏi của bạn:", placeholder="Ví dụ: Khi nào cần thay nước ao nuôi tôm?", height=100)

# 🔘 Gửi câu hỏi
if st.button("🚀 Gửi câu hỏi", type="primary"):
    if not question.strip():
        st.warning("⚠️ Bạn chưa nhập câu hỏi.")
    elif not data.strip():
        st.error("❌ Không có dữ liệu nền. Vui lòng thêm file .txt vào thư mục 'data'.")
    else:
        with st.spinner("🤖 Đang xử lý câu hỏi..."):
            try:
                prompt = (
                    f"Dựa vào nội dung quy trình chăm sóc tôm thẻ chân trắng sau đây:\n\n"
                    f"--BẮT ĐẦU DỮ LIỆU--\n{data}\n--KẾT THÚC DỮ LIỆU--\n\n"
                    f"Chỉ trả lời câu hỏi dựa trên dữ liệu được cung cấp. Câu hỏi: {question}"
                )
                response = model.generate_content(prompt)
                st.success("✅ Trả lời:")
                st.write(response.text)
            except Exception as e:
                st.error(f"❌ Lỗi khi gọi API: {e}")
                st.info("Kiểm tra lại kết nối mạng hoặc giới hạn token của dữ liệu.")

# 📘 Gợi ý
st.markdown("---")
st.markdown("**📎 Gợi ý:** Hãy đặt các file `.txt` vào thư mục `data/` (cùng cấp với file này).")
st.markdown("**Ví dụ:** `data/quytrinhchamsoc.txt`, `data/kiemtrathucan.txt`, ...")

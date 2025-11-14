import os
import dotenv
import google.generativeai as genai
import streamlit as st
import re            
import random        


# --- CẤU HÌNH GEMINI ---
dotenv.load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("❌ Không tìm thấy GOOGLE_API_KEY. Vui lòng thiết lập trong .env hoặc Streamlit Secrets.")
        st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error(f"Lỗi khi cấu hình Gemini: {e}")
    st.stop()


# --- HÀM LOAD DỮ LIỆU ---
@st.cache_data(ttl=600)
def load_data():
    """Tải và nối tất cả dữ liệu từ các file .txt trong thư mục 'data'."""
    data_dir = "data"
    data = ""
    if not os.path.exists(data_dir):
        st.warning(f"⚠️ Thư mục '{data_dir}' chưa tồn tại. Chatbot sẽ chạy ở chế độ thông thường.")
        return None
    
    files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
    if not files:
        st.warning("⚠️ Chưa có file .txt trong thư mục 'data/'. Chatbot sẽ chạy ở chế độ thông thường.")
        return None
    
    for file in files:
        try:
            with open(os.path.join(data_dir, file), "r", encoding="utf-8") as f:
                data += f.read() + "\n\n"
        except Exception as e:
            st.error(f"Lỗi khi đọc file {file}: {e}")
            
    return data.strip() if data else None


# --- ĐẶT QUY TẮC CHO MODEL ---
def initialize_chat(data):
    """Khởi tạo phiên chat mới với bối cảnh (system prompt) nếu có."""
    default_greeting = "Chào bạn! Hiện tại tôi chưa có dữ liệu về nuôi tôm. Tôi có thể giúp gì cho bạn (ở chế độ thông thường)?"   
    if data:
        SYSTEM_PROMPT = f"""
        Bạn là một trợ lý AI chuyên gia về quy trình nuôi tôm thẻ chân trắng.
        Nhiệm vụ của bạn là trả lời các câu hỏi của người dùng CHỈ DỰA TRÊN NỘI DUNG SAU ĐÂY:

        --- NỘI DUNG THAM KHẢO ---
        {data}
        --- KẾT THÚC NỘI DUNG ---

        QUY TẮC TUYỆT ĐỐI:
        1. Chỉ trả lời dựa vào "NỘI DUNG THAM KHẢO"đã cung cấp.
        2. Nếu câu hỏi không thể trả lời bằng nội dung trên, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin này trong tài liệu."
        3. Không tự ý bịa đặt thông tin hoặc lấy kiến thức bên ngoài.
        4. Trả lời một cách ngắn gọn, chính xác và chuyên nghiệp.
        5. Khi mô tả về một bệnh mà có thẻ [IMAGE_PATH_DIR: ...], BẠN PHẢI GIỮ NGUYÊN thẻ đó trong câu trả lời.
        """
        try:
            chat = model.start_chat(history=[
                {"role": "user", "parts": [SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Xin chào! Bạn cần hỗ trợ gì hôm nay?"]}
            ])
            st.session_state.context_loaded = True
            return chat
        except Exception as e:
            st.error(f"Lỗi khi bắt đầu chat với model: {e}")
            st.stop()
    st.session_state.context_loaded = False
    return model.start_chat(history=[
        {"role": "user", "parts": ["Xin chào"]},
        {"role": "model", "parts": [default_greeting]}
    ])

# --- HÀM XỬ LÝ VÀ HIỂN THỊ TIN NHẮN (VĂN BẢN + ẢNH) ---
def display_message_with_images(text_content):
    """
    Hiển thị nội dung text, tìm thẻ ảnh, và hiển thị ảnh ngẫu nhiên nếu có.
    """
    image_tag_pattern = r"\[IMAGE_PATH_DIR:\s*(.*?)\s*\]"
    dir_paths = re.findall(image_tag_pattern, text_content)
    clean_text = re.sub(image_tag_pattern, "", text_content).strip()
    if clean_text:
        st.markdown(clean_text)

    for dir_path in dir_paths:
        if os.path.isdir(dir_path):
            try:
                image_files = [
                    f for f in os.listdir(dir_path) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
                ]             
                if image_files:
                    random_image = random.choice(image_files)
                    full_image_path = os.path.join(dir_path, random_image)
                    st.image(full_image_path, width=200)
                else:
                    st.warning(f"⚠️ Thư mục '{dir_path}' được tìm thấy nhưng không chứa file ảnh nào.")
            except Exception as e:
                st.error(f"Lỗi khi truy cập hoặc đọc ảnh từ thư mục '{dir_path}': {e}")
        else:
            st.warning(f"⚠️ Chatbot đã trả về đường dẫn ảnh, nhưng thư mục '{dir_path}' không tồn tại trên máy chủ.")  
        

# --- GIAO DIỆN CHÍNH---
st.set_page_config(page_title="Chatbot Nuôi Tôm", page_icon="🦐", layout="wide")
st.title("🦐 Chatbot Hỏi-Đáp về Quy Trình Nuôi Tôm")



# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("Thiết lập")
    if st.button("🗑️ Xóa lịch sử & Tải lại ngữ cảnh", use_container_width=True):
        if "chat" in st.session_state:
            del st.session_state.chat
        st.cache_data.clear()
        st.rerun()

# --- TẢI DỮ LIỆU VÀ KHỞI TẠO CHAT ---
if "chat" not in st.session_state:
    loaded_shrimp_data = load_data()
    st.session_state.chat = initialize_chat(loaded_shrimp_data)
if st.session_state.context_loaded:
    st.status("Đã tải bối cảnh từ thư mục `data/`", state="complete")
else:
    st.status("Không tìm thấy dữ liệu. Chatbot đang chạy ở chế độ chung.", state="error")

# --- KHUNG HIỂN THỊ LỊCH SỬ CHAT ---
chat_container = st.container(height=400)
for turn in st.session_state.chat.history:
    if "NỘI DUNG THAM KHẢO" in turn.parts[0].text:
        continue
        
    role = "assistant" if turn.role == "model" else "user"
    with chat_container.chat_message(role):
        display_message_with_images(turn.parts[0].text)



# --- KHUNG NHẬP LIỆU ---
if prompt := st.chat_input("Hỏi về quy trình nuôi tôm..."):
    
    with chat_container.chat_message("user"):
        display_message_with_images(prompt) 
    
    try:
        chat = st.session_state.chat
        with st.spinner("Bot đang suy nghĩ..."):
            response = chat.send_message(prompt)
        
        with chat_container.chat_message("assistant"):

            display_message_with_images(response.text)
            
    except Exception as e:
        st.error(f"❌ Lỗi khi gửi tin nhắn: {e}")


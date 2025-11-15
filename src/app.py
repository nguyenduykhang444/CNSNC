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
                {"role": "model", "parts": ["Xin chào! Tôi là trợ lý chuyên về nuôi tôm. Bạn cần hỗ trợ gì hôm nay?"]} # Sửa lời chào
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

# --- HÀM XỬ LÝ VĂN BẢN VÀ CHỌN ẢNH (DÙNG CACHE) ---
@st.cache_data(ttl=3600)
def get_processed_display_parts(text_content):
    image_tag_pattern = r"\[IMAGE_PATH_DIR:\s*(.*?)\s*\]"
    dir_paths = re.findall(image_tag_pattern, text_content)
    clean_text = re.sub(image_tag_pattern, "", text_content).strip()
    chosen_image_path = None
    if dir_paths:
        dir_path = dir_paths[0]
        if os.path.isdir(dir_path):
            try:
                image_files = [
                    f for f in os.listdir(dir_path) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
                ]             
                if image_files:
                    random_image = random.choice(image_files)
                    chosen_image_path = os.path.join(dir_path, random_image)
                else:
                    st.warning(f"⚠️ Thư mục '{dir_path}' được tìm thấy nhưng không chứa file ảnh nào.")
            except Exception as e:
                st.error(f"Lỗi khi truy cập hoặc đọc ảnh từ thư mục '{dir_path}': {e}")
        else:
            st.warning(f"⚠️ Chatbot đã trả về đường dẫn ảnh, nhưng thư mục '{dir_path}' không tồn tại trên máy chủ.")  
    return clean_text, chosen_image_path
        
# --- GIAO DIỆN CHÍNH---
st.set_page_config(page_title="Chatbot Nuôi Tôm", page_icon="🦐", layout="wide")
st.title("🦐 Chatbot Hỏi-Đáp về Quy Trình Nuôi Tôm")

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("Thiết lập")
    if st.button("🗑️ Xóa lịch sử & Tải lại ngữ cảnh", use_container_width=True):
        if "chat" in st.session_state:
            del st.session_state.chat
        if "display_messages" in st.session_state:
            del st.session_state.display_messages     
        st.cache_data.clear() 
        st.rerun()
# --- TẢI DỮ LIỆU VÀ KHỞI TẠO CHAT ---
if "chat" not in st.session_state:
    loaded_shrimp_data = load_data()
    st.session_state.chat = initialize_chat(loaded_shrimp_data)
    st.session_state.display_messages = []
    for turn in st.session_state.chat.history:
        if "NỘI DUNG THAM KHẢO" in turn.parts[0].text:
            continue
        role = "assistant" if turn.role == "model" else "user"
        if role == "assistant":
            clean_text, image_path = get_processed_display_parts(turn.parts[0].text)
            st.session_state.display_messages.append(
                {"role": role, "text": clean_text, "image": image_path}
            )
        else:
            st.session_state.display_messages.append(
                {"role": role, "text": turn.parts[0].text, "image": None}
            )
if st.session_state.context_loaded:
    st.status("Đã tải bối cảnh từ thư mục `data/`", state="complete")
else:
    st.status("Không tìm thấy dữ liệu. Chatbot đang chạy ở chế độ chung.", state="error")

# --- KHUNG HIỂN THỊ LỊCH SỬ CHAT ---
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        if msg["text"]:
            st.markdown(msg["text"])
        if msg["image"]:
            try:
                st.image(msg["image"], width=300)
            except Exception as e:
                st.error(f"Lỗi khi hiển thị ảnh {msg['image']}: {e}")

# --- KHUNG NHẬP LIỆU ---
if prompt := st.chat_input("Hỏi về quy trình nuôi tôm..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.display_messages.append(
        {"role": "user", "text": prompt, "image": None}
    )
    try:
        chat = st.session_state.chat
        with st.spinner("Bot đang suy nghĩ..."):
            response = chat.send_message(prompt)
        last_bot_message_text = chat.history[-1].parts[0].text
        clean_text, image_path = get_processed_display_parts(last_bot_message_text)
        st.session_state.display_messages.append(
            {"role": "assistant", "text": clean_text, "image": image_path}
        )
        st.rerun() 
            
    except Exception as e:
        st.error(f"❌ Lỗi khi gửi tin nhắn: {e}")
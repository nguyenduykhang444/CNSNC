import os
import dotenv
import google.generativeai as genai
import streamlit as st
import re            
import random        

# --- QUẢN LÝ LỊCH SỬ ---
import json
from datetime import datetime

HISTORY_FILE = "chat_history.json"

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_chat_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
        1. Chỉ trả lời dựa vào "NỘI DUNG THAM KHẢO" đã cung cấp.
        2. Nếu câu hỏi không thể trả lời bằng nội dung trên, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin này trong tài liệu."
        3. Không tự ý bịa đặt thông tin hoặc lấy kiến thức bên ngoài.
        4. Trả lời một cách ngắn gọn, chính xác và chuyên nghiệp.
        5. Khi mô tả về một bệnh mà có thẻ [IMAGE_PATH_DIR: ...], BẠN PHẢI GIỮ NGUYÊN thẻ đó trong câu trả lời.
        """
        try:
            chat = model.start_chat(history=[
                {"role": "user", "parts": [SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Đã hiểu! Tôi là trợ lý chuyên về quy trình nuôi tôm. Tôi đã sẵn sàng trả lời các câu hỏi dựa trên tài liệu bạn cung cấp."]}
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

## --- HÀM XỬ LÝ VÀ HIỂN THỊ TIN NHẮN (VĂN BẢN + ẢNH) ---
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

# --- GIAO DIỆN ---
st.set_page_config(page_title="Chatbot Nuôi Tôm", page_icon="🦐", layout="wide")
st.title("🦐 Chatbot Hỏi-Đáp về Quy Trình Nuôi Tôm")

# --- BIẾN LƯU LỊCH SỬ CHAT ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_chat_history()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- THANH BÊN (SIDEBAR) ---
# --- GIAO DIỆN THANH BÊN (SIDEBAR) QUẢN LÝ LỊCH SỬ TRÒ CHUYỆN ---
with st.sidebar:
    st.header("💬 Lịch sử trò chuyện")
    all_chats = st.session_state.all_chats  # Lấy danh sách tất cả các hội thoại đã lưu

    # --- HIỂN THỊ THÔNG BÁO NẾU CHƯA CÓ LỊCH SỬ ---
    if not all_chats:
        st.info("Chưa có lịch sử chat nào.")
    else:
        # --- DUYỆT QUA TỪNG HỘI THOẠI ĐÃ LƯU ---
        for chat_id, chat_info in list(all_chats.items()):
            col1, col2 = st.columns([8, 1])  # Chia cột để hiển thị tên & nút tùy chọn

            # --- MỞ LẠI MỘT HỘI THOẠI ---
            with col1:
                if st.button(chat_info["title"], key=f"open_{chat_id}"):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.chat = chat_info["history"]
                    st.rerun()

            # --- MỞ MENU TÙY CHỌN (ĐỔI TÊN / XÓA) ---
            with col2:
                if st.button("⋮", key=f"menu_{chat_id}"):
                    st.session_state.selected_chat = chat_id

            # --- XỬ LÝ KHI NGƯỜI DÙNG CHỌN MENU ---
            if st.session_state.get("selected_chat") == chat_id:
                # Đổi tên hội thoại
                new_name = st.text_input("Đổi tên:", value=chat_info["title"], key=f"rename_{chat_id}")
                if st.button("Lưu", key=f"save_{chat_id}"):
                    all_chats[chat_id]["title"] = new_name
                    save_chat_history(all_chats)
                    st.session_state.selected_chat = None
                    st.rerun()

                # Xóa hội thoại
                if st.button("🗑️ Xóa", key=f"delete_{chat_id}"):
                    del all_chats[chat_id]
                    save_chat_history(all_chats)
                    st.session_state.selected_chat = None
                    st.rerun()

                st.markdown("<span style='color:red;'>❗ Xóa là mất vĩnh viễn</span>", unsafe_allow_html=True)
                st.divider()

    # --- HƯỚNG DẪN THÊM DỮ LIỆU VÀ ẢNH ---
    st.markdown("---")
    st.info("💡 Thêm các file `.txt` vào thư mục `data/`.\n\n💡 Thêm ảnh vào thư mục `data/Images/` (hoặc đường dẫn bạn đã định nghĩa trong file .txt).")

    # --- TẠO HỘI THOẠI MỚI ---
    st.markdown("---")
    if st.button("➕ Tạo hội thoại mới"):
        new_id = str(datetime.now().timestamp())
        all_chats[new_id] = {"title": f"Hội thoại {len(all_chats)+1}", "history": []}
        save_chat_history(all_chats)
        st.session_state.current_chat_id = new_id
        st.session_state.chat = []
        st.rerun()

    # --- XÓA TOÀN BỘ LỊCH SỬ & TẢI LẠI NGỮ CẢNH ---
    st.markdown("---")
    if st.button("🗑️ Xóa lịch sử & Tải lại ngữ cảnh", use_container_width=True):
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

if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.all_chats:
    for msg in st.session_state.all_chats[st.session_state.current_chat_id]["history"]:
        role = "assistant" if msg["role"] == "assistant" else "user"
        with chat_container.chat_message(role):
            display_message_with_images(msg["text"])

# --- KHUNG NHẬP LIỆU VÀ HIỂN THỊ TRẢ LỜI CÓ HÌNH ẢNH ---
if prompt := st.chat_input("Hỏi về quy trình nuôi tôm..."):
    # Hiển thị câu hỏi của người dùng
    with chat_container.chat_message("user"):
        display_message_with_images(prompt)

    try:
        chat = st.session_state.chat
        with st.spinner("Bot đang suy nghĩ..."):
            response = chat.send_message(prompt)  # Gửi câu hỏi tới Gemini model

        # Lấy nội dung trả lời (text + thẻ hình ảnh)
        response_text = ""
        if hasattr(response, "text"):
            response_text = response.text
        elif hasattr(response, "parts"):
            # Trường hợp model trả về nhiều phần
            response_text = " ".join([part.text for part in response.parts if hasattr(part, "text")])

        # Hiển thị trả lời và hình ảnh
        if response_text:
            # Tách text và thẻ ảnh ra hiển thị
            display_message_with_images(response_text)
        else:
            st.warning("🤖 Bot trả lời trống.")

        # --- Lưu lịch sử chat ---
        if st.session_state.current_chat_id:
            cid = st.session_state.current_chat_id
            if cid not in st.session_state.all_chats:
                st.session_state.all_chats[cid] = {"title": f"Hội thoại {len(st.session_state.all_chats)+1}", "history": []}

            st.session_state.all_chats[cid]["history"].append({"role": "user", "text": prompt})
            st.session_state.all_chats[cid]["history"].append({"role": "assistant", "text": response_text})
            save_chat_history(st.session_state.all_chats)

    except Exception as e:
        st.error(f"❌ Lỗi khi gửi tin nhắn: {e}")

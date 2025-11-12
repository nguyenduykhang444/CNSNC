import os
import dotenv
import google.generativeai as genai
import streamlit as st
import re            
import random        
import json
from datetime import datetime

# --- KHỞI TẠO CÁC BIẾN QUẢN LÝ ---
HISTORY_FILE = "../chat_history.json"  # dùng file ngoài src/
SYSTEM_PROMPT_KEY = "NỘI DUNG THAM KHẢO"

# --- CÁC HÀM QUẢN LÝ LỊCH SỬ CHAT VÀ LƯU TRỮ JSON ---

def load_all_chats():
    """Tải tất cả lịch sử chat từ file JSON (an toàn)."""
    # Nếu file chưa tồn tại, tạo file rỗng 
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}

    try:
        # Nếu file rỗng, trả về dict rỗng 
        if os.path.getsize(HISTORY_FILE) == 0:
            return {}

        # Đọc JSON
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        #  Nếu dữ liệu không phải dict, reset 
        if not isinstance(data, dict):
            st.warning("⚠️ Dữ liệu JSON không đúng định dạng, đã reset.")
            return {}

        chats = {}
        for chat_id, chat_data in data.items():
            history = []
            for msg in chat_data.get("history", []):
                history.append(
                    genai.types.Content(
                        role=msg.get("role", "user"),
                        parts=[genai.types.Part.from_text(msg.get("text", ""))]
                    )
                )

            chat_object = genai.GenerativeModel("gemini-2.5-flash").start_chat(history=history)
            chats[chat_id] = {
                "name": chat_data.get("name", "Cuộc trò chuyện mới"),
                "chat_object": chat_object,
                "initial_greeting": chat_data.get("initial_greeting", "Chào bạn!")
            }

        return chats

    except Exception as e:
        st.warning(f"⚠️ Lỗi khi đọc JSON, đã reset dữ liệu: {e}")
        return {}

def save_all_chats(all_chats):
    """Lưu tất cả lịch sử chat vào file JSON."""
    data_to_save = {}
    for chat_id, chat_data in all_chats.items():
        # Chuyển đổi đối tượng genai.Chat.history thành cấu trúc JSON đơn giản
        simple_history = [
            {"role": msg.role, "text": msg.parts[0].text}
            for msg in chat_data["chat_object"].history
        ]
        
        data_to_save[chat_id] = {
            "name": chat_data["name"],
            "history": simple_history,
            "initial_greeting": chat_data.get("initial_greeting", "Chào bạn!")
        }
    
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Lỗi khi lưu lịch sử chat: {e}")

def get_default_chat_name(history):
    """Tạo tên chat mặc định dựa trên tin nhắn đầu tiên."""
    # Bỏ qua tin nhắn khởi tạo SYSTEM_PROMPT
    user_msgs = [m.parts[0].text for m in history if m.role == "user" and SYSTEM_PROMPT_KEY not in m.parts[0].text]
    if user_msgs:
        first_msg = user_msgs[0].strip()
        return first_msg[:40] + "..." if len(first_msg) > 40 else first_msg
    return f"Cuộc trò chuyện mới - {datetime.now().strftime('%H:%M')}"

def rename_chat(chat_id, new_name):
    """Đổi tên cuộc trò chuyện và lưu lại."""
    if chat_id in st.session_state.all_chats and new_name:
        st.session_state.all_chats[chat_id]["name"] = new_name.strip()
        save_all_chats(st.session_state.all_chats)

def delete_chat(chat_id):
    """Xóa một cuộc trò chuyện và lưu lại."""
    if chat_id in st.session_state.all_chats:
        del st.session_state.all_chats[chat_id]
        save_all_chats(st.session_state.all_chats)
        
        # Nếu xóa chat hiện tại, bắt đầu chat mới
        if st.session_state.current_chat_id == chat_id or not st.session_state.all_chats:
            st.session_state.current_chat_id = None # Đặt về None để kích hoạt new_chat_session
            st.rerun()
        else:
             # Đảm bảo chat hiện tại là một chat còn lại
            st.session_state.current_chat_id = list(st.session_state.all_chats.keys())[0]
            st.rerun()
            
def select_chat(chat_id):
    """Chọn một cuộc trò chuyện từ lịch sử."""
    st.session_state.current_chat_id = chat_id
    st.rerun()

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
        return None        
    files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
    if not files:
        return None  
    for file in files:
        try:
            with open(os.path.join(data_dir, file), "r", encoding="utf-8") as f:
                data += f.read() + "\n\n"
        except Exception as e:
            st.error(f"Lỗi khi đọc file {file}: {e}")            
    return data.strip() if data else None

# --- ĐẶT QUY TẮC CHO MODEL ---
def new_chat_session():
    """Khởi tạo phiên chat mới với bối cảnh (system prompt) nếu có."""
    chat_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
    loaded_data = load_data()
    default_greeting = "Chào bạn! Hiện tại tôi chưa có dữ liệu về nuôi tôm. Tôi có thể giúp gì cho bạn (ở chế độ thông thường)?"
    
    if loaded_data:
        SYSTEM_PROMPT = f"""
        Bạn là một trợ lý AI chuyên gia về quy trình nuôi tôm thẻ chân trắng.
        Nhiệm vụ của bạn là trả lời các câu hỏi của người dùng CHỈ DỰA TRÊN NỘI DUNG SAU ĐÂY:

        --- {SYSTEM_PROMPT_KEY} ---
        {loaded_data}
        --- KẾT THÚC NỘI DUNG ---

        QUY TẮC TUYỆT ĐỐI:
        1. Chỉ trả lời dựa vào "{SYSTEM_PROMPT_KEY}" đã cung cấp.
        2. Nếu câu hỏi không thể trả lời bằng nội dung trên, hãy nói: "Xin lỗi, tôi không tìm thấy thông tin này trong tài liệu."
        3. Không tự ý bịa đặt thông tin hoặc lấy kiến thức bên ngoài.
        4. Trả lời một cách ngắn gọn, chính xác và chuyên nghiệp.
        5. Khi mô tả về một bệnh mà có thẻ [IMAGE_PATH_DIR: ...], BẠN PHẢI GIỮ NGUYÊN thẻ đó trong câu trả lời.
        """
        initial_history = [
             {"role": "user", "parts": [SYSTEM_PROMPT]},
             {"role": "model", "parts": ["Đã hiểu! Tôi là trợ lý chuyên về quy trình nuôi tôm. Tôi đã sẵn sàng trả lời các câu hỏi dựa trên tài liệu bạn cung cấp."]}
        ]
        
        initial_chat = model.start_chat(history=initial_history)
        st.session_state.context_loaded = True
        initial_name = f"Cuộc trò chuyện mới - {datetime.now().strftime('%H:%M')}"
        initial_greeting = "Chào bạn! Bạn cần hỗ trợ gì hôm nay?"
    else:  
        # Chế độ chung
        initial_chat = model.start_chat(history=[])
        st.session_state.context_loaded = False
        initial_name = f"Chat chung - {datetime.now().strftime('%H:%M')}"
        initial_greeting = default_greeting
        
    st.session_state.all_chats[chat_id] = {
        "name": initial_name,
        "chat_object": initial_chat,
        "initial_greeting": initial_greeting
    }
    st.session_state.current_chat_id = chat_id
    
    # Lưu lại ngay sau khi tạo chat mới
    save_all_chats(st.session_state.all_chats)
    st.rerun()

# --- HÀM XỬ LÝ VÀ HIỂN THỊ TIN NHẮN (VĂN BẢN + ẢNH) ---
def display_message_with_images(text_content):
    """
    Hiển thị nội dung text, tìm thẻ ảnh, và hiển thị ảnh ngẫu nhiên nếu có.
    """
    image_tag_pattern = r"\[IMAGE_PATH_DIR:\s*(.*?)\s*\]"
    dir_paths = re.findall(image_tag_pattern, text_content)
    # Thay thế thẻ ảnh bằng chú thích trước khi hiển thị
    clean_text = re.sub(image_tag_pattern, lambda m: f"*[Xem ảnh minh họa tại {m.group(1)}]*", text_content).strip()
    
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
                    st.image(full_image_path, width=200, caption=f"Ảnh minh họa từ thư mục: {dir_path}")  
            except Exception as e:
                st.error(f"Lỗi khi truy cập hoặc đọc ảnh từ thư mục '{dir_path}': {e}")

# --- GIAO DIỆN LỊCH SỬ CHAT TRONG SIDEBAR ---
def render_history_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.subheader("Đoạn chat") # Thêm icon

    all_chats = st.session_state.get("all_chats", {})
    if not all_chats:
        st.sidebar.caption("Chưa có cuộc trò chuyện nào được lưu.")
        return

    chats_to_remove = []

    # đảm bảo có dict lưu trạng thái edit (nếu cần)
    if "rename_open" not in st.session_state:
        st.session_state["rename_open"] = {}

    for idx, (chat_id, chat_data) in enumerate(list(all_chats.items())):
        name = chat_data.get("name", f"Chat {idx+1}")

        # tạo 2 cột: tên chọn và nút 3 chấm
        # Tăng tỉ lệ col1 để tên dài dễ đọc hơn
        col1, col2 = st.sidebar.columns([0.80, 0.20]) 

        # Cột chọn chat (toàn bộ nút hiển thị tên) 
        with col1:
            # key có idx để tránh trùng
            if st.button(name, key=f"select_{chat_id}_{idx}", use_container_width=True, help="Click để mở đoạn chat này"):
                st.session_state["current_chat_id"] = chat_id

        # Cột 3 chấm (expander chứa đổi tên + xóa) 
        exp_key = f"expander_{chat_id}_{idx}"
        with col2:
            # Dùng icon/emoji rõ ràng hơn cho expander
            with st.expander("⚙️", expanded=False, key=exp_key): 
                # Không lặp lại tên chat, chỉ dùng để chứa hành động
                st.caption(f"Tùy chọn cho: **{name}**") # Tên chat làm tiêu đề hướng dẫn
                st.markdown("---")

                # input đổi tên
                input_key = f"rename_input_{chat_id}_{idx}"
                if input_key not in st.session_state:
                    st.session_state[input_key] = name

                new_name = st.text_input(
                    "", value=st.session_state[input_key],
                    key=input_key,
                    label_visibility="collapsed", # Ẩn label mặc định
                    placeholder="✎ Đổi tên mới" # Placeholder rõ ràng hơn
                )

                col_save, col_delete = st.columns([0.6, 0.4])
                with col_save:
                    if st.button("Lưu", key=f"rename_button_{chat_id}_{idx}", use_container_width=True): # Thêm icon
                        new_name_stripped = (new_name or "").strip()
                        if new_name_stripped and new_name_stripped != name:
                            # gọi hàm rename_chat nếu có, ngược lại cập nhật trực tiếp
                            try:
                                rename_chat(chat_id, new_name_stripped)
                            except NameError: # Thay NameError cho Exception chung
                                st.session_state["all_chats"][chat_id]["name"] = new_name_stripped
                            # cập nhật session_state input để phản ánh tên mới
                            st.session_state[input_key] = new_name_stripped

                with col_delete:
                    if st.button("Xóa", key=f"delete_{chat_id}_{idx}", use_container_width=True): # Thêm icon
                        chats_to_remove.append(chat_id)

    # Xử lý xóa sau khi duyệt xong vòng lặp (tránh chỉnh sửa dict khi đang iterate)
    for chat_id in chats_to_remove:
        try:
            # Nếu hàm delete_chat tồn tại
            delete_chat(chat_id) 
        except NameError: # Thay NameError cho Exception chung
            # fallback: xóa trực tiếp trong session_state
            if chat_id in st.session_state.get("all_chats", {}):
                del st.session_state["all_chats"][chat_id]
        # nếu xóa chat đang mở, bỏ current_chat_id
        if st.session_state.get("current_chat_id") == chat_id:
            st.session_state["current_chat_id"] = None
        
# --- GIAO DIỆN CHÍNH---
st.set_page_config(page_title="Chatbot Nuôi Tôm", page_icon="🦐", layout="wide")
st.title("🦐 Chatbot Hỏi-Đáp về Quy Trình Nuôi Tôm")

# --- BIẾN LƯU LỊCH SỬ CHAT ---
if 'all_chats' not in st.session_state:
    st.session_state['all_chats'] = load_all_chats()

if 'current_chat_id' not in st.session_state or st.session_state.current_chat_id is None:
    if st.session_state.all_chats:
        # Load chat mới nhất (hoặc chat đầu tiên)
        st.session_state.current_chat_id = list(st.session_state.all_chats.keys())[0]
    else:
        # Nếu chưa có chat nào, tạo chat mới
        new_chat_session()

# Lấy chat object hiện tại
current_chat_data = st.session_state.all_chats[st.session_state.current_chat_id]
current_chat = current_chat_data["chat_object"]

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("Thiết lập")

    # --- NÚT CUỘC TRÒ CHUYỆN MỚI ---
    if st.button("✨ Cuộc Trò Chuyện Mới", use_container_width=True, help="Bắt đầu một phiên hỏi đáp hoàn toàn mới."):
        new_chat_session()
    
    # --- NÚT TẢI LẠI NGỮ CẢNH (Rerun toàn bộ) ---
    
    if st.button("🔄 Khởi động lại", use_container_width=True, help="Xóa cache và khởi động lại toàn bộ ứng dụng."):
        st.cache_data.clear()
        st.rerun()

    

    # Hiển thị lịch sử chat
    render_history_sidebar()
    # --- HƯỚNG DẪN THÊM DỮ LIỆU VÀ ẢNH ---
    st.markdown("---")
    st.info("💡 Thêm các file `.txt` vào thư mục `data/`.\n\n💡 Thêm ảnh vào thư mục `data/Images/` (hoặc đường dẫn bạn đã định nghĩa trong file .txt).")


# --- KIỂM TRA TÌNH TRẠNG DỮ LIỆU ---
is_context_loaded = SYSTEM_PROMPT_KEY in current_chat.history[0].parts[0].text if current_chat.history else False

if is_context_loaded:
    st.status("✅ Đã tải bối cảnh chuyên sâu từ thư mục `data/`", state="complete")
else:
    st.status("❌ Không tìm thấy dữ liệu. Chatbot đang chạy ở chế độ chung.", state="error")

# --- KHUNG HIỂN THỊ LỊCH SỬ CHAT ---
chat_container = st.container(height=600, border=True)

history = current_chat.history

# Lọc bỏ tin nhắn System Prompt để không hiển thị ra giao diện
history_to_display = [
    turn for turn in history 
    if not (turn.role == "user" and SYSTEM_PROMPT_KEY in turn.parts[0].text) and 
       not (turn.role == "model" and turn.parts[0].text.startswith("Đã hiểu! Tôi là trợ lý chuyên về quy trình nuôi tôm."))
]

# Nếu là chat mới (chỉ có System Prompt), hiển thị lời chào
if len(history_to_display) == 0:
    with chat_container.chat_message("assistant"):
        st.markdown(current_chat_data["initial_greeting"])

# Hiển thị tin nhắn
for turn in history_to_display:
    role = "assistant" if turn.role == "model" else "user"
    with chat_container.chat_message(role):
        display_message_with_images(turn.parts[0].text)



# --- KHUNG NHẬP LIỆU ---
if prompt := st.chat_input("Hỏi về quy trình nuôi tôm..."):
    # Hiển thị tin nhắn User
    with chat_container.chat_message("user"):
        display_message_with_images(prompt)

    # Gửi tin nhắn đến model
    try:
        with st.spinner("Bot đang suy nghĩ..."):
            response = current_chat.send_message(prompt)  

        # Hiển thị tin nhắn Model
        with chat_container.chat_message("assistant"):
            display_message_with_images(response.text)
    
        # Cập nhật tên chat nếu là tin nhắn đầu tiên (sau khi system prompt)
        # Sử dụng len(history) để kiểm tra số lượng tin nhắn đã gửi đi
        if len(history) == (3 if is_context_loaded else 1): 
            new_name = get_default_chat_name(current_chat.history)
            rename_chat(st.session_state.current_chat_id, new_name)
            
        # LƯU LẠI LỊCH SỬ SAU MỖI LẦN TRÒ CHUYỆN
        save_all_chats(st.session_state.all_chats)

    except Exception as e:
        st.error(f"❌ Lỗi khi gửi tin nhắn: {e}")

import google.generativeai as genai
import os
import dotenv

dotenv.load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("❌ Lỗi: Không tìm thấy GOOGLE_API_KEY trong file .env")
    exit()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-pro")

except Exception as e:
    print(f"❌ Lỗi khi cấu hình Gemini: {e}")
    print("Vui lòng kiểm tra lại API Key và kết nối mạng.")
    exit()

def load_data():
    """Tải tất cả nội dung từ các file .txt trong thư mục 'data'."""
    docs = []
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        print(f"⚠️ Cảnh báo: Thư mục '{data_dir}' không tồn tại. Chatbot sẽ không có dữ liệu.")
        return ""
        
    for file in os.listdir(data_dir):
        if file.endswith(".txt"):
            try:
                with open(os.path.join(data_dir, file), "r", encoding="utf-8") as f:
                    docs.append(f.read())
            except Exception as e:
                print(f"Lỗi khi đọc file {file}: {e}")
                
    if not docs:
        print("⚠️ Cảnh báo: Không tìm thấy file .txt nào trong thư mục 'data'.")
        
    return "\n".join(docs)

print("Đang tải dữ liệu tôm...")
data = load_data()

if not data:
    print("Bot khởi động nhưng không có dữ liệu nền. Vui lòng thêm file .txt vào thư mục 'data'.")

print("✅ Bot đã sẵn sàng! (gõ 'thoát' để dừng)")

while True:
    question = input("🦐 Bạn muốn hỏi gì? ")
    if question.lower() in ["thoát", "exit", "quit"]:
        print("🤖 Tạm biệt!")
        break

    if not data:
        print("🤖 Lỗi: Không có dữ liệu nền để trả lời. Vui lòng kiểm tra thư mục 'data'.")
        continue
    
    prompt = f"Dựa vào nội dung quy trình chăm sóc tôm thẻ chân trắng sau đây:\n\n--BẮT ĐẦU DỮ LIỆU--\n{data}\n--KẾT THÚC DỮ LIỆU--\n\nChỉ trả lời câu hỏi dựa trên dữ liệu được cung cấp. Câu hỏi: {question}"
    
    try:
        response = model.generate_content(prompt)
        
        print("🤖 Trả lời:", response.text, "\n")
        
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi khi gọi API: {e}")
        print("Vui lòng kiểm tra lại câu hỏi hoặc giới hạn token của dữ liệu.")
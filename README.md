# Dự án Chatbot RAG: Quy trình Nuôi Tôm

## Giới thiệu

Đây là một dự án chatbot học thuật sử dụng mô hình RAG (Retrieval-Augmented Generation) và Google Gemini API. Chatbot được huấn luyện để trả lời các câu hỏi liên quan đến quy trình, kỹ thuật và bệnh lý trong nuôi tôm thẻ chân trắng, dựa trên một tập dữ liệu (knowledge base) được cung cấp.

---

## Cài đặt Môi trường

Để chạy dự án, bạn cần cài đặt các thư viện Python được liệt kê trong `requirements.txt`.

**1. Python 3.10+: Dự án được khuyến nghị chạy với Python 3.10 trở lên.**



**2. Cài đặt thư viện:**

  * **Trên Windows:**

    ```bash
    pip install -r requirements.txt
    ```

  * **Trên macOS:** (Sử dụng `pip3.13` nếu bạn dùng Python 3.13)

    ```bash
    pip3.13 install -r requirements.txt
    ```

**3. Cấu hình API Key:**

Tạo một file `.env` ở thư mục gốc và thêm khóa API của bạn:

```
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

-----

## Cách chạy Chatbot

Đảm bảo bạn đã cài đặt các thư viện và đang ở trong môi trường ảo.

  * **Trên Windows:**

    ```bash
    streamlit run src/app.py
    ```

  * **Trên macOS:** (Sử dụng `python3.13` nếu bạn dùng Python 3.13)

    ```bash
    python3.13 -m streamlit run src/app.py
    ```

-----

## Thành viên Nhóm

  * **NGUYỄN DUY KHANG** (M5125015)
  * **NGUYỄN TRƯƠNG NGỌC THẢO LOAN** (M5125016)
  * **NGUYỄN THỊ ANH THƯ** (M5125025)

## File .env
GOOGLE_API_KEY=AIzaSyC2sJD72M7NL2IVOOhQCzpEFXa0V_FMLe4

## File .gitignore
venv/
.env
# CI/CD Deployment Hub

Công cụ trung gian viết bằng **Python + Flask**, giúp tự động hóa việc triển khai code từ **GitLab** đến các server.  
Cung cấp giao diện web để quản lý tập trung nhiều dự án, deploy tự động hoặc thủ công.

---

## ✨ Tính năng nổi bật
- **Quản lý tập trung**: Deploy nhiều dự án, nhiều server từ một nơi duy nhất.  
- **Tự động hóa**: Tích hợp với **GitLab Webhook**, tự động deploy khi có code mới.  
- **Deploy thủ công**: Giao diện web cho phép kích hoạt deploy bất kỳ lúc nào.  
- **Giao diện quản lý**: Thêm, sửa, xóa cấu hình dự án trực tiếp trên dashboard.  
- **Bảo mật & xác thực**:
  - Kết nối SSH bằng **Key** hoặc **Password**.
  - Hệ thống **Login**, phân quyền **Admin/User**.
  - Token bí mật để xác thực webhook từ GitLab.

---

## 📂 Cấu trúc thư mục

```bash
ci_cd_hub/
│
├── app.py            # File Flask chính, chạy ứng dụng web
├── deploy.py         # Logic SSH & deploy
├── create_admin.py   # Script tạo tài khoản admin đầu tiên
├── config.json       # Cấu hình các dự án cần deploy
├── users.json        # Lưu thông tin user (đã mã hóa)
├── requirements.txt  # Thư viện Python cần thiết
│
└── templates/
    ├── index.html    # Dashboard chính
    ├── login.html    # Trang đăng nhập
    └── admin.html    # Trang quản trị user
```

---

## ⚙️ Cài đặt & cấu hình

### 1. Chuẩn bị môi trường
Yêu cầu **Python 3.6+**.  
Tạo môi trường ảo và cài dependencies:

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Tạo tài khoản Admin đầu tiên
Trước khi chạy server, cần tạo admin:

```bash
python create_admin.py
```

Script sẽ yêu cầu nhập **username** và **password**, sau đó lưu vào `users.json`.

### 3. Khởi động ứng dụng
Chạy Flask server:

```bash
python app.py
```

Mặc định ứng dụng lắng nghe tại:  
👉 `http://0.0.0.0:5010`  

### 4. Đăng nhập & cấu hình dự án
- Đăng nhập bằng tài khoản admin (Bước 2).  
- Trên Dashboard, chọn **“+ Thêm dự án mới”** và nhập thông tin:
  - **Project ID**: định danh duy nhất (vd: `my-web-app`).  
  - **Tên dự án**: hiển thị trên dashboard.  
  - **Nhánh Git**: nhánh deploy (`main`, `develop`, ...).  
  - **GitLab Webhook Secret**: token bí mật để xác thực.  
  - **Thông tin Server**: host, user, port và xác thực (SSH key hoặc password).

### 5. Cấu hình GitLab Webhook (tùy chọn)
Để bật **deploy tự động** từ GitLab:

1. Vào **Settings → Webhooks** trong GitLab project.  
2. URL:  

   ```
   http://<IP_CUA_HUB>:5000/webhook/<PROJECT_ID>
   ```
   - `<IP_CUA_HUB>`: IP server chạy CI/CD Hub.  
   - `<PROJECT_ID>`: ID dự án đã cấu hình ở Dashboard.  

3. Secret Token: nhập đúng **Webhook Secret** đã cấu hình.  
4. Trigger: chọn **Push events** (và nhánh tương ứng).  
5. Nhấn **Add Webhook**.

Từ nay, mỗi lần push code vào nhánh đó → CI/CD Hub sẽ tự động deploy.

---

## 🔒 Lưu ý bảo mật
- Chạy trong **mạng nội bộ** hoặc sau firewall.  
- Nếu cần public ra Internet → nên đặt sau **Nginx Reverse Proxy** + **SSL**.  
- Token bí mật (`gitlab_webhook_secret`) bắt buộc để ngăn webhook giả mạo.  

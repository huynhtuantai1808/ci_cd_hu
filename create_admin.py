import json
import getpass
from werkzeug.security import generate_password_hash

def create_admin_user():
    """
    Script tiện ích để tạo người dùng admin đầu tiên.
    """
    users_file = 'users.json'
    
    print("--- Tạo tài khoản Admin đầu tiên ---")
    
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"users": {}}
        
    username = input("Nhập tên đăng nhập cho admin: ").strip()
    if not username:
        print("Tên đăng nhập không được để trống.")
        return
        
    if username in data.get('users', {}):
        overwrite = input(f"Tài khoản '{username}' đã tồn tại. Bạn có muốn ghi đè (thay đổi mật khẩu)? (y/n): ").lower()
        if overwrite != 'y':
            print("Đã hủy.")
            return

    password = getpass.getpass("Nhập mật khẩu cho admin: ")
    password_confirm = getpass.getpass("Xác nhận lại mật khẩu: ")
    
    if password != password_confirm:
        print("Mật khẩu không khớp. Vui lòng thử lại.")
        return
        
    if not password:
        print("Mật khẩu không được để trống.")
        return

    # Tạo hash và lưu
    password_hash = generate_password_hash(password)
    
    data['users'][username] = {
        "id": username,
        "username": username,
        "password_hash": password_hash,
        "is_admin": True
    }
    
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nThành công! Đã tạo/cập nhật tài khoản admin '{username}'.")
        print("Bây giờ bạn có thể khởi chạy server và đăng nhập.")
    except Exception as e:
        print(f"Lỗi khi ghi file: {e}")

if __name__ == '__main__':
    create_admin_user()

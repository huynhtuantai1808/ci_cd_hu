# -*- coding: utf-8 -*-
import json
import paramiko # Thư viện để kết nối SSH

def trigger_deployment(project_id):
    """
    Hàm chính thực hiện logic deployment.
    1. Đọc file cấu hình.
    2. Tìm thông tin dự án cần deploy.
    3. Kết nối đến server qua SSH.
    4. Thực thi các lệnh deploy trên server.
    5. Trả về kết quả và log.
    """
    try:
        # Đọc file cấu hình
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        return False, "Lỗi: Không tìm thấy tệp config.json."

    project = config.get('projects', {}).get(project_id)
    if not project:
        return False, f"Lỗi: Không tìm thấy dự án với ID '{project_id}' trong config.json."

    server_config = project.get('server')
    if not server_config:
        return False, f"Lỗi: Thiếu thông tin server cho dự án '{project_id}'."

    # Lấy thông tin cần thiết từ config
    hostname = server_config['host']
    port = server_config.get('port', 22)
    username = server_config['user']
    key_filename = server_config.get('ssh_key_path') # Đường dẫn đến private key
    project_path = project['project_path_on_server']
    branch = project['branch']

    log_output = []

    # Khởi tạo SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        log_output.append(f"Đang kết nối đến server {hostname}...")
        
        # Kết nối SSH sử dụng key
        ssh.connect(hostname, port=port, username=username, key_filename=key_filename)
        
        log_output.append("Kết nối thành công.")
        
        # Các lệnh sẽ được thực thi trên server
        commands = [
            f"echo '--- Bắt đầu deploy cho nhánh {branch} ---'",
            f"cd {project_path}",
            "echo '--- Đang kiểm tra trạng thái Git ---'",
            "git status",
            "echo '--- Đang reset các thay đổi cục bộ (nếu có) ---'",
            "git reset --hard",
            f"echo '--- Đang chuyển sang nhánh {branch} ---'",
            f"git checkout {branch}",
            f"echo '--- Đang kéo code mới nhất từ GitLab (origin/{branch}) ---'",
            f"git pull origin {branch}",
            "echo '--- Deploy hoàn tất ---'"
        ]
        
        # Bạn có thể thêm các lệnh khác ở đây, ví dụ:
        # commands.append("pip install -r requirements.txt")
        # commands.append("npm install")
        # commands.append("pm2 restart my-app")
        
        full_command = " && ".join(commands)
        
        # Thực thi lệnh
        stdin, stdout, stderr = ssh.exec_command(full_command)
        
        # Đọc log output
        stdout_log = stdout.read().decode('utf-8')
        stderr_log = stderr.read().decode('utf-8')
        
        log_output.append("\n--- LOG TỪ SERVER ---\n")
        if stdout_log:
            log_output.append(stdout_log)
        if stderr_log:
            log_output.append(f"--- LỖI TỪ SERVER ---\n{stderr_log}")
            return False, "\n".join(log_output)
            
        return True, "\n".join(log_output)

    except Exception as e:
        error_message = f"Đã xảy ra lỗi trong quá trình deploy: {str(e)}"
        log_output.append(error_message)
        print(error_message)
        return False, "\n".join(log_output)
    finally:
        # Luôn đóng kết nối SSH sau khi hoàn tất
        if ssh.get_transport() and ssh.get_transport().is_active():
            ssh.close()
            log_output.append("\nĐã đóng kết nối SSH.")

# -*- coding: utf-8 -*-
import json
import paramiko # Thư viện để kết nối SSH

def trigger_deployment(project_id):
    """
    Hàm chính thực hiện logic deployment.
    Hỗ trợ cả xác thực bằng SSH Key và Password.
    """
    try:
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

    hostname = server_config.get('host')
    port = server_config.get('port', 22)
    username = server_config.get('user')
    auth_method = server_config.get('auth_method', 'key') # Mặc định là 'key'
    project_path = project.get('project_path_on_server')
    branch = project.get('branch')

    log_output = []
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        log_output.append(f"Đang kết nối đến server {hostname}...")
        
        # Lựa chọn phương thức kết nối
        if auth_method == 'password':
            password = server_config.get('password')
            if not password:
                return False, "Lỗi: Phương thức xác thực là 'password' nhưng không có mật khẩu được cung cấp."
            log_output.append("Đang xác thực bằng mật khẩu...")
            ssh.connect(hostname, port=port, username=username, password=password)
        else: # Mặc định hoặc auth_method == 'key'
            key_filename = server_config.get('ssh_key_path')
            if not key_filename:
                 return False, "Lỗi: Phương thức xác thực là 'SSH Key' nhưng không có đường dẫn key nào được cung cấp."
            log_output.append("Đang xác thực bằng SSH key...")
            ssh.connect(hostname, port=port, username=username, key_filename=key_filename)

        log_output.append("Kết nối thành công.")
        
        commands = [
            f"echo '--- Bắt đầu deploy cho nhánh {branch} ---'",
            f"cd {project_path}",
            "git status",
            "git reset --hard",
            f"git checkout {branch}",
            f"git pull origin {branch}",
            "echo '--- Deploy hoàn tất ---'"
        ]
        
        full_command = " && ".join(commands)
        stdin, stdout, stderr = ssh.exec_command(full_command)
        
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
        if ssh.get_transport() and ssh.get_transport().is_active():
            ssh.close()
            log_output.append("\nĐã đóng kết nối SSH.")


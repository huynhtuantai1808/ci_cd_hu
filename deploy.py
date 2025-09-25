# -*- coding: utf-8 -*-
import json
import paramiko # Thư viện để kết nối SSH

def trigger_deployment(project_id):
    """
    Hàm chính thực hiện logic deployment, bao gồm cả việc chạy các lệnh sau deploy.
    """
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        return False, "Lỗi: Không tìm thấy tệp config.json."

    project = config.get('projects', {}).get(project_id)
    if not project:
        return False, f"Lỗi: Không tìm thấy dự án với ID '{project_id}'."

    server_config = project.get('server')
    if not server_config:
        return False, f"Lỗi: Thiếu thông tin server cho dự án '{project_id}'."

    hostname = server_config.get('host')
    port = server_config.get('port', 22)
    username = server_config.get('user')
    auth_method = server_config.get('auth_method', 'key')
    project_path = project.get('project_path_on_server')
    branch = project.get('branch')
    post_deploy_commands = project.get('post_deploy_commands', [])

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
            ssh.connect(hostname, port=port, username=username, password=password, timeout=10)
        else:
            key_filename = server_config.get('ssh_key_path')
            if not key_filename:
                 return False, "Lỗi: Phương thức xác thực là 'SSH Key' nhưng không có đường dẫn key."
            ssh.connect(hostname, port=port, username=username, key_filename=key_filename, timeout=10)

        log_output.append("Kết nối thành công.")
        
        # --- Bước 1: Git Commands ---
        # Nối các lệnh lại với nhau để chạy trong cùng một session
        git_commands = [
            f"cd {project_path}", # Chuyển vào thư mục dự án
            f"echo '--- Bắt đầu cập nhật code cho nhánh {branch} ---'",
            "git status",
            "git reset --hard",
            f"git checkout {branch}",
            f"git pull origin {branch}",
            "echo '--- Cập nhật code hoàn tất ---'"
        ]
        
        full_git_command = " && ".join(git_commands)
        log_output.append(f"\n$ {full_git_command}")
        stdin, stdout, stderr = ssh.exec_command(full_git_command)
        
        exit_status = stdout.channel.recv_exit_status() # Đợi lệnh hoàn tất
        stdout_log = stdout.read().decode('utf-8').strip()
        stderr_log = stderr.read().decode('utf-8').strip()
            
        if stdout_log: log_output.append(stdout_log)
        if stderr_log: log_output.append(f"LỖI: {stderr_log}")
            
        if exit_status != 0:
            log_output.append(f"Lệnh Git thất bại với mã lỗi {exit_status}. Dừng deploy.")
            return False, "\n".join(log_output)

        # --- Bước 2: Post-deployment Commands ---
        if post_deploy_commands:
            log_output.append("\n--- Bắt đầu thực thi các lệnh tùy chỉnh ---")
            # Nối các lệnh tùy chỉnh, đảm bảo chúng cũng chạy trong thư mục dự án
            post_deploy_chain = f"cd {project_path} && " + " && ".join(post_deploy_commands)
            
            log_output.append(f"\n$ {post_deploy_chain}")
            stdin, stdout, stderr = ssh.exec_command(post_deploy_chain)
            
            exit_status = stdout.channel.recv_exit_status() # Đợi lệnh hoàn tất
            stdout_log = stdout.read().decode('utf-8').strip()
            stderr_log = stderr.read().decode('utf-8').strip()

            if stdout_log: log_output.append(stdout_log)
            if stderr_log: log_output.append(f"LỖI: {stderr_log}")

            if exit_status != 0:
                log_output.append(f"Lệnh tùy chỉnh thất bại với mã lỗi {exit_status}. Dừng deploy.")
                return False, "\n".join(log_output)
        
        log_output.append("\n--- Deploy hoàn tất thành công ---")
        return True, "\n".join(log_output)

    except Exception as e:
        error_message = f"Đã xảy ra lỗi nghiêm trọng: {str(e)}"
        log_output.append(error_message)
        print(error_message)
        return False, "\n".join(log_output)
    finally:
        if ssh.get_transport() and ssh.get_transport().is_active():
            ssh.close()
            log_output.append("\nĐã đóng kết nối SSH.")


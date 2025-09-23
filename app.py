# -*- coding: utf-8 -*-
import json
import subprocess
import uuid
from flask import Flask, render_template, request, jsonify
from deploy import trigger_deployment

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# --- Các hàm xử lý Cấu hình ---

def get_config():
    """Đọc và trả về dữ liệu cấu hình từ tệp config.json."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"projects": {}} # Trả về cấu trúc trống nếu không tìm thấy file

def save_config(config):
    """Ghi dữ liệu cấu hình vào tệp config.json."""
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu file config: {e}")
        return False

# --- Các Route cho Giao diện và Deploy ---

@app.route('/')
def index():
    """Route chính, hiển thị giao diện người dùng (GUI)."""
    config = get_config()
    projects = config.get('projects', {})
    return render_template('index.html', projects=projects)

@app.route('/webhook/<project_id>', methods=['POST'])
def webhook(project_id):
    """Endpoint để nhận tín hiệu (webhook) từ GitLab."""
    gitlab_token = request.headers.get('X-Gitlab-Token')
    config = get_config()
    project = config.get('projects', {}).get(project_id)

    if not project:
        return jsonify({"status": "error", "message": "Project not found"}), 404
    if project.get('gitlab_webhook_secret') != gitlab_token:
        return jsonify({"status": "error", "message": "Invalid secret token"}), 403

    print(f"Webhook received for project: {project_id}. Starting deployment...")
    success, log = trigger_deployment(project_id)
    
    if success:
        return jsonify({"status": "success", "message": "Deployment triggered successfully"})
    else:
        return jsonify({"status": "error", "message": "Deployment failed", "log": log}), 500

@app.route('/deploy/<project_id>', methods=['POST'])
def manual_deploy(project_id):
    """Endpoint để kích hoạt deploy thủ công từ giao diện người dùng."""
    print(f"Manual deployment requested for project: {project_id}")
    success, log = trigger_deployment(project_id)
    return jsonify({"success": success, "log": log})

# --- Các API Endpoint để quản lý Cấu hình (CRUD) ---

@app.route('/api/projects', methods=['POST'])
def add_project():
    """API để thêm một dự án mới."""
    data = request.json
    config = get_config()
    
    project_id = data.get('id')
    if not project_id:
        return jsonify({"success": False, "message": "Project ID là bắt buộc."}), 400
    
    if 'projects' not in config:
        config['projects'] = {}
        
    if project_id in config['projects']:
        return jsonify({"success": False, "message": f"Project ID '{project_id}' đã tồn tại."}), 409
        
    new_project = {
        "id": project_id,
        "name": data.get("name", ""),
        "branch": data.get("branch", "main"),
        "project_path_on_server": data.get("project_path_on_server", ""),
        "gitlab_webhook_secret": data.get("gitlab_webhook_secret", ""),
        "server": {
            "host": data.get("server_host", ""),
            "user": data.get("server_user", ""),
            "port": int(data.get("server_port", 22)),
            "auth_method": data.get("auth_method", "key"),
            "ssh_key_path": data.get("server_ssh_key_path", ""),
            "password": data.get("server_password", "")
        }
    }
    
    config['projects'][project_id] = new_project
    if save_config(config):
        return jsonify({"success": True, "message": "Thêm dự án thành công."})
    else:
        return jsonify({"success": False, "message": "Lỗi khi lưu cấu hình."}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """API để cập nhật một dự án đã có."""
    data = request.json
    config = get_config()

    if project_id not in config.get('projects', {}):
        return jsonify({"success": False, "message": "Không tìm thấy dự án."}), 404

    project_to_update = config['projects'][project_id]

    project_to_update['name'] = data.get("name", project_to_update.get('name'))
    project_to_update['branch'] = data.get("branch", project_to_update.get('branch'))
    project_to_update['project_path_on_server'] = data.get("project_path_on_server", project_to_update.get('project_path_on_server'))
    
    if data.get("gitlab_webhook_secret"):
        project_to_update['gitlab_webhook_secret'] = data.get("gitlab_webhook_secret")

    server_info = project_to_update.get('server', {})
    server_info['host'] = data.get("server_host", server_info.get('host'))
    server_info['user'] = data.get("server_user", server_info.get('user'))
    server_info['port'] = int(data.get("server_port", server_info.get('port')))
    server_info['auth_method'] = data.get("auth_method", server_info.get('auth_method', 'key'))
    server_info['ssh_key_path'] = data.get("server_ssh_key_path", server_info.get('ssh_key_path'))

    if data.get("server_password"):
        server_info['password'] = data.get("server_password")
    
    project_to_update['server'] = server_info

    if save_config(config):
        return jsonify({"success": True, "message": "Cập nhật dự án thành công."})
    else:
        return jsonify({"success": False, "message": "Lỗi khi lưu cấu hình."}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """API để xóa một dự án."""
    config = get_config()
    
    if project_id not in config.get('projects', {}):
        return jsonify({"success": False, "message": "Không tìm thấy dự án."}), 404
        
    del config['projects'][project_id]
    
    if save_config(config):
        return jsonify({"success": True, "message": "Xóa dự án thành công."})
    else:
        return jsonify({"success": False, "message": "Lỗi khi lưu cấu hình."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


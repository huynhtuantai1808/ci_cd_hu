# -*- coding: utf-8 -*-
import json
import subprocess
from flask import Flask, render_template, request, jsonify
from deploy import trigger_deployment

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Hàm để đọc cấu hình từ file config.json
def get_config():
    """Đọc và trả về dữ liệu cấu hình từ tệp config.json."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"projects": {}} # Trả về cấu trúc trống nếu không tìm thấy file

@app.route('/')
def index():
    """
    Route chính, hiển thị giao diện người dùng (GUI).
    Trang này sẽ liệt kê tất cả các dự án từ file config.json.
    """
    config = get_config()
    projects = config.get('projects', {})
    # Truyền danh sách dự án vào template 'index.html' để render
    return render_template('index.html', projects=projects.values())

@app.route('/webhook/<project_id>', methods=['POST'])
def webhook(project_id):
    """
    Endpoint để nhận tín hiệu (webhook) từ GitLab.
    Khi có một sự kiện (ví dụ: merge request), GitLab sẽ gửi một request đến URL này.
    URL ví dụ: http://<your_server_ip>:5000/webhook/my-web-app
    """
    # Lấy token từ header của request mà GitLab gửi đến
    gitlab_token = request.headers.get('X-Gitlab-Token')
    
    config = get_config()
    project = config.get('projects', {}).get(project_id)

    if not project:
        return jsonify({"status": "error", "message": "Project not found"}), 404

    # Xác thực token để đảm bảo request đến từ GitLab
    if project['gitlab_webhook_secret'] != gitlab_token:
        return jsonify({"status": "error", "message": "Invalid secret token"}), 403

    print(f"Webhook received for project: {project_id}. Starting deployment...")
    
    # Kích hoạt quá trình deploy
    success, log = trigger_deployment(project_id)
    
    if success:
        print(f"Deployment for {project_id} successful.")
        return jsonify({"status": "success", "message": "Deployment triggered successfully"})
    else:
        print(f"Deployment for {project_id} failed. Log: {log}")
        return jsonify({"status": "error", "message": "Deployment failed", "log": log}), 500

@app.route('/deploy/<project_id>', methods=['POST'])
def manual_deploy(project_id):
    """
    Endpoint để kích hoạt deploy thủ công từ giao diện người dùng.
    """
    print(f"Manual deployment requested for project: {project_id}")
    success, log = trigger_deployment(project_id)
    return jsonify({"success": success, "log": log})

if __name__ == '__main__':
    # Chạy ứng dụng web, lắng nghe trên tất cả các địa chỉ IP của máy
    # và sử dụng cổng 5000.
    app.run(host='0.0.0.0', port=5000, debug=True)

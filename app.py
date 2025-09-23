# -*- coding: utf-8 -*-
import json
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from deploy import trigger_deployment

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
# SECRET_KEY là bắt buộc để sử dụng session trong Flask
app.config['SECRET_KEY'] = os.urandom(24)

# --- Các hàm xử lý file JSON ---

def get_data(filename):
    """Hàm chung để đọc dữ liệu từ một file JSON."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Trả về cấu trúc mặc định nếu file không tồn tại hoặc rỗng
        if 'users' in filename:
            return {"users": {}}
        return {"projects": {}}

def save_data(filename, data):
    """Hàm chung để ghi dữ liệu vào một file JSON."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu file {filename}: {e}")
        return False

# --- Decorators cho việc xác thực và phân quyền ---

def login_required(f):
    """Decorator để đảm bảo người dùng đã đăng nhập."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Bạn cần đăng nhập để truy cập trang này.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator để đảm bảo người dùng là Admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Bạn không có quyền truy cập trang quản trị.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Route cho Đăng nhập / Đăng xuất ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users_data = get_data('users.json')
        user = users_data.get('users', {}).get(username)

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            flash(f"Chào mừng {user['username']}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('login'))

# --- Route cho Giao diện chính và Deploy ---

@app.route('/')
@login_required
def index():
    """Route chính, hiển thị giao diện người dùng (GUI)."""
    config = get_data('config.json')
    projects = config.get('projects', {})
    return render_template('index.html', projects=projects)

@app.route('/deploy/<project_id>', methods=['POST'])
@login_required
def manual_deploy(project_id):
    print(f"Manual deployment for '{project_id}' requested by user '{session['username']}'")
    success, log = trigger_deployment(project_id)
    return jsonify({"success": success, "log": log})

# --- Route cho Webhook (không yêu cầu login session) ---

@app.route('/webhook/<project_id>', methods=['POST'])
def webhook(project_id):
    """Endpoint để nhận tín hiệu (webhook) từ GitLab."""
    gitlab_token = request.headers.get('X-Gitlab-Token')
    config = get_data('config.json')
    project = config.get('projects', {}).get(project_id)

    if not project:
        return jsonify({"status": "error", "message": "Project not found"}), 404
    if project.get('gitlab_webhook_secret') != gitlab_token:
        return jsonify({"status": "error", "message": "Invalid secret token"}), 403

    print(f"Webhook received for project: {project_id}. Starting deployment...")
    success, log = trigger_deployment(project_id)
    
    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Deployment failed", "log": log}), 500

# --- Trang Admin và API quản lý User ---

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users_data = get_data('users.json')
    users = users_data.get('users', {})
    return render_template('admin.html', users=users)

@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def add_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)

    if not username or not password:
        return jsonify({"success": False, "message": "Tên đăng nhập và mật khẩu là bắt buộc."}), 400

    users_data = get_data('users.json')
    if username in users_data['users']:
        return jsonify({"success": False, "message": f"Tên đăng nhập '{username}' đã tồn tại."}), 409
    
    users_data['users'][username] = {
        "id": username,
        "username": username,
        "password_hash": generate_password_hash(password),
        "is_admin": is_admin
    }
    
    if save_data('users.json', users_data):
        return jsonify({"success": True, "message": "Thêm người dùng thành công."})
    else:
        return jsonify({"success": False, "message": "Lỗi khi lưu dữ liệu người dùng."}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    data = request.json
    users_data = get_data('users.json')
    
    if user_id not in users_data['users']:
        return jsonify({"success": False, "message": "Không tìm thấy người dùng."}), 404

    user = users_data['users'][user_id]
    if 'password' in data and data['password']:
        user['password_hash'] = generate_password_hash(data['password'])
    
    if 'is_admin' in data:
        # Không cho phép admin tự bỏ quyền của chính mình
        if user_id == session['user_id'] and not data['is_admin']:
            return jsonify({"success": False, "message": "Bạn không thể tự tước quyền Admin của chính mình."}), 403
        user['is_admin'] = data['is_admin']

    if save_data('users.json', users_data):
        return jsonify({"success": True, "message": "Cập nhật người dùng thành công."})
    else:
        return jsonify({"success": False, "message": "Lỗi khi lưu dữ liệu người dùng."}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        return jsonify({"success": False, "message": "Bạn không thể xóa chính mình."}), 403
        
    users_data = get_data('users.json')
    if user_id not in users_data['users']:
        return jsonify({"success": False, "message": "Không tìm thấy người dùng."}), 404
        
    del users_data['users'][user_id]
    
    if save_data('users.json', users_data):
        return jsonify({"success": True, "message": "Xóa người dùng thành công."})
    else:
        return jsonify({"success": False, "message": "Lỗi khi lưu dữ liệu người dùng."}), 500

# --- API quản lý Project (Đã thêm decorator @login_required) ---

@app.route('/api/projects', methods=['POST'])
@login_required
def add_project():
    data = request.json
    config = get_data('config.json')
    project_id = data.get('id')
    # ... (phần còn lại của hàm không đổi)
    if not project_id: return jsonify({"success": False, "message": "Project ID là bắt buộc."}), 400
    if 'projects' not in config: config['projects'] = {}
    if project_id in config['projects']: return jsonify({"success": False, "message": f"Project ID '{project_id}' đã tồn tại."}), 409
    new_project = { "id": project_id, "name": data.get("name", ""), "branch": data.get("branch", "main"), "project_path_on_server": data.get("project_path_on_server", ""), "gitlab_webhook_secret": data.get("gitlab_webhook_secret", ""), "server": { "host": data.get("server_host", ""), "user": data.get("server_user", ""), "port": int(data.get("server_port", 22)), "auth_method": data.get("auth_method", "key"), "ssh_key_path": data.get("server_ssh_key_path", ""), "password": data.get("server_password", "") } }
    config['projects'][project_id] = new_project
    if save_data('config.json', config): return jsonify({"success": True, "message": "Thêm dự án thành công."})
    else: return jsonify({"success": False, "message": "Lỗi khi lưu cấu hình."}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    data = request.json
    config = get_data('config.json')
    # ... (phần còn lại của hàm không đổi)
    if project_id not in config.get('projects', {}): return jsonify({"success": False, "message": "Không tìm thấy dự án."}), 404
    project_to_update = config['projects'][project_id]
    project_to_update['name'] = data.get("name", project_to_update.get('name'))
    project_to_update['branch'] = data.get("branch", project_to_update.get('branch'))
    project_to_update['project_path_on_server'] = data.get("project_path_on_server", project_to_update.get('project_path_on_server'))
    if data.get("gitlab_webhook_secret"): project_to_update['gitlab_webhook_secret'] = data.get("gitlab_webhook_secret")
    server_info = project_to_update.get('server', {})
    server_info['host'] = data.get("server_host", server_info.get('host'))
    server_info['user'] = data.get("server_user", server_info.get('user'))
    server_info['port'] = int(data.get("server_port", server_info.get('port')))
    server_info['auth_method'] = data.get("auth_method", server_info.get('auth_method', 'key'))
    server_info['ssh_key_path'] = data.get("server_ssh_key_path", server_info.get('ssh_key_path'))
    if data.get("server_password"): server_info['password'] = data.get("server_password")
    project_to_update['server'] = server_info
    if save_data('config.json', config): return jsonify({"success": True, "message": "Cập nhật dự án thành công."})
    else: return jsonify({"success": False, "message": "Lỗi khi lưu cấu hình."}), 500
    
@app.route('/api/projects/<project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    config = get_data('config.json')
    # ... (phần còn lại của hàm không đổi)
    if project_id not in config.get('projects', {}): return jsonify({"success": False, "message": "Không tìm thấy dự án."}), 404
    del config['projects'][project_id]
    if save_data('config.json', config): return jsonify({"success": True, "message": "Xóa dự án thành công."})
    else: return jsonify({"success": False, "message": "Lỗi khi lưu cấu hình."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


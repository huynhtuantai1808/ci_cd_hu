Python CI/CD Deployment Hub 1. Giới thiệu Đây là một công cụ trung gian
(hub) được xây dựng bằng Python và Flask để tự động hóa quá trình triển
khai (deploy) code từ GitLab đến các máy chủ của bạn.

Mục đích chính:

Tập trung hóa: Quản lý việc deploy nhiều dự án, nhiều server tại một nơi
duy nhất.

Tự động hóa: Tự động deploy code mới nhất khi có sự kiện merge request
hoặc push trên GitLab thông qua Webhook.

Kiểm soát: Cung cấp giao diện web (GUI) để theo dõi và kích hoạt deploy
thủ công một cách dễ dàng.

2.  Cấu trúc thư mục ci_cd_hub/ \| \|-- app.py \# Ứng dụng Flask chính,
    xử lý route, GUI và webhook. \|-- deploy.py \# Chứa logic kết nối
    SSH và thực thi lệnh deploy trên server. \|-- config.json \# Tệp cấu
    hình các dự án và thông tin server. **QUAN TRỌNG!** \|--
    requirements.txt \# Danh sách các thư viện Python cần thiết. \|--
    README.md \# Tệp hướng dẫn này. \| `-- templates/`-- index.html \#
    Tệp HTML cho giao diện người dùng (GUI).

3.  Yêu cầu cài đặt Python 3.6+

pip (trình quản lý gói của Python)

git được cài đặt trên cả máy chủ deploy và máy chủ chạy hub này.

4.  Hướng dẫn cài đặt và cấu hình Bước 1: Tải mã nguồn và cài đặt thư
    viện Mở terminal (hoặc Command Prompt) và clone project này về máy
    của bạn (hoặc tải về và giải nén).

Di chuyển vào thư mục ci_cd_hub.

Tạo một môi trường ảo (khuyến khích) để tránh xung đột thư viện:

python -m venv venv

Kích hoạt môi trường ảo:

Trên Windows: venv`\Scripts`{=tex}`\activate`{=tex}

Trên macOS/Linux: source venv/bin/activate

Cài đặt các thư viện cần thiết:

pip install -r requirements.txt

Bước 2: Cấu hình SSH Key (Rất quan trọng!) Để hub có thể kết nối đến các
server deploy một cách tự động mà không cần mật khẩu, bạn phải thiết lập
SSH Key-based Authentication.

Trên máy sẽ chạy CI/CD Hub:

Kiểm tra xem bạn đã có SSH key chưa bằng cách chạy ls -la \~/.ssh. Nếu
bạn thấy các tệp id_rsa và id_rsa.pub, hãy bỏ qua bước tạo key.

Nếu chưa có, tạo một cặp key mới:

ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

(Nhấn Enter để chấp nhận các giá trị mặc định).

Copy Public Key lên các Server Deploy:

Lấy nội dung public key của bạn:

cat \~/.ssh/id_rsa.pub

Copy toàn bộ nội dung output.

Trên từng server deploy, đăng nhập bằng user sẽ thực hiện deploy (ví dụ:
deploy_user), và dán nội dung key vừa copy vào cuối tệp
\~/.ssh/authorized_keys.

# Trên server deploy

echo "nội_dung_public_key_dán_vào_đây" \>\> \~/.ssh/authorized_keys

Kiểm tra kết nối: Từ máy chạy Hub, thử kết nối SSH đến server deploy.
Bạn không nên bị hỏi mật khẩu.

ssh deploy_user@192.168.1.100

Bước 3: Chỉnh sửa tệp config.json Đây là nơi bạn định nghĩa tất cả các
dự án và server của mình.

Mở tệp config.json và chỉnh sửa cho phù hợp.

my-web-app, data-processing-service là các ID định danh duy nhất cho dự
án.

name: Tên hiển thị trên GUI.

branch: Nhánh Git sẽ được deploy (ví dụ: main, develop).

project_path_on_server: Đường dẫn tuyệt đối đến thư mục dự án trên
server deploy. User deploy phải có quyền ghi/đọc trên thư mục này.

gitlab_webhook_secret: Một chuỗi bí mật ngẫu nhiên và phức tạp. Bạn sẽ
dùng nó ở bước tiếp theo.

server:

host: IP hoặc domain của server deploy.

user: User dùng để SSH vào server.

ssh_key_path: Đường dẫn tuyệt đối đến tệp private key trên máy chạy Hub
(thường là \~/.ssh/id_rsa, nhưng bạn có thể thay đổi nếu cần).

Bước 4: Cấu hình GitLab Webhook Vào dự án của bạn trên GitLab.

Đi đến Settings \> Webhooks.

URL:
http://`<IP_CUA_MAY_CHAY_HUB>`{=html}:5000/webhook/`<PROJECT_ID>`{=html}

Thay `<IP_CUA_MAY_CHAY_HUB>`{=html} bằng địa chỉ IP của máy đang chạy
script Python này.

Thay `<PROJECT_ID>`{=html} bằng ID bạn đã định nghĩa trong config.json
(ví dụ: my-web-app).

Secret token: Dán chuỗi bí mật bạn đã tạo ở gitlab_webhook_secret vào
đây.

Trigger: Chọn các sự kiện bạn muốn kích hoạt deploy. Ví dụ: Push events
(cho nhánh main) hoặc Merge request events.

Nhấn Add webhook. Bạn có thể nhấn Test để kiểm tra xem GitLab có kết nối
được đến Hub của bạn không.

5.  Sử dụng Chạy Hub: Trong thư mục ci_cd_hub (đã kích hoạt môi trường
    ảo), chạy lệnh:

python app.py

Hub sẽ bắt đầu chạy và lắng nghe ở cổng 5000.

Truy cập Giao diện Web: Mở trình duyệt và truy cập:
http://`<IP_CUA_MAY_CHAY_HUB>`{=html}:5000 Bạn sẽ thấy danh sách các dự
án đã cấu hình.

Deploy:

Tự động: Khi có sự kiện trên GitLab (ví dụ: bạn merge code vào nhánh
main), GitLab sẽ tự động gửi tín hiệu đến Hub và quá trình deploy sẽ bắt
đầu. Bạn có thể xem log trong cửa sổ terminal đang chạy app.py.

Thủ công: Trên giao diện web, nhấn nút Deploy thủ công bên cạnh dự án
bạn muốn. Log deploy sẽ hiện ra ngay bên dưới.

6.  Lưu ý về Bảo mật Script này được thiết kế để chạy trong một mạng nội
    bộ, đáng tin cậy.

Không để cổng 5000 của Hub này truy cập được trực tiếp từ Internet mà
không có các biện pháp bảo vệ như tường lửa, reverse proxy (Nginx), và
xác thực người dùng.

Token bí mật (gitlab_webhook_secret) giúp xác thực rằng yêu

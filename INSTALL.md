# Hướng dẫn cho Codex / Claude Code

Mục tiêu: cài **cả Room MCP lẫn Event Router MCP**, cùng hai skill, vào máy của khách. Khách đã yêu cầu cài bộ này thì thực hiện các bước trong phạm vi đó; không yêu cầu lại quyền cho thao tác chuẩn bị thông thường.

1. Tải hoặc clone repo vào một thư mục cố định thuộc tài khoản hiện tại, ví dụ `%LOCALAPPDATA%/AidolAgent/kit`. Nếu không có Git, tải archive chính thức từ GitHub rồi giải nén. Không chạy server từ thư mục tạm vì cấu hình lưu đường dẫn tuyệt đối.
2. Kiểm tra Python 3.11+ và Google Chrome. Nếu thiếu, hướng dẫn khách hoặc dùng công cụ cài đặt được phép của môi trường; không khẳng định cài xong khi chưa kiểm tra. Không tắt bảo vệ trình duyệt hoặc thay đổi cấu hình bảo mật hệ thống.
3. Chạy `python install.py` trong thư mục repo. Script tạo `.venv`, cài requirements, sao lưu các file cấu hình hiện có rồi thêm hai MCP và hai skill cho Codex/Claude Code. Nếu một cấu hình không đọc được, sửa đúng định dạng với khách trước khi tiếp tục; không xóa toàn bộ cấu hình agent.
4. Hướng dẫn khách mở lại agent hoặc reconnect MCP. Công cụ được nạp từ đầu phiên nên không hứa phiên hiện tại đã thấy ngay công cụ mới.
5. Đọc skill tương ứng. Gọi `room_inspect` để mở cửa sổ Chrome **hiển thị** riêng của khách; nếu chưa đăng nhập, nói rõ khách đăng nhập ngay cửa sổ vừa mở. Kiểm tra tên tài khoản trước khi thao tác. Không đọc cookie/token ra báo cáo. Nếu Chrome chưa có, hướng dẫn cài; không mở trình duyệt ẩn rồi đợi khách đăng nhập ở nơi khác.
6. Event Router: khách tải bộ cài tương thích từ GitHub Releases, cài và mở ứng dụng, đóng bản cũ trước khi dùng. Gọi `router_status`. Nếu chưa đăng nhập Router, hướng dẫn khách đăng nhập ngay ứng dụng.
7. Ưu tiên dùng phòng khách đang thuê nếu phù hợp. Chỉ thuê mới sau khi chọn Simple/Pro và biết chi phí được khách cho phép. Mã kết nối nằm ở nút **Mã Event Router** trong phòng. Dùng thao tác UI hỗ trợ để lấy mã và gọi `router_connect_room`; đối chiếu trạng thái/session. Không coi đang chờ là đã kết nối.
8. Khách tự đăng nhập Shopee/TikTok, mở bảng sản phẩm và xử lý CAPTCHA. Nếu chỉ cài đặt, dừng sau khi xác nhận MCP chạy; không tự ghim hay gửi comment lên phiên thật.
9. Phản hồi text bằng Brain cần Room API `ar_…` và tốn Tun Coin. Hướng dẫn khách nhập vào ô che của Router; chỉ test/bật khi khách đồng ý. Speech mặc định tắt. Khách đặt overlay đúng ô bình luận rồi mới xác nhận.

## Cấu hình và gỡ

Script thêm `mcp_servers.aidol_room`, `mcp_servers.aidol_event_router` vào `~/.codex/config.toml`; thêm `aidol-room`, `aidol-event-router` vào `~/.claude.json`; cài skill vào `.codex/skills` và `.claude/skills`. Không thêm mật khẩu, ALC, key API hay quyền hệ thống.

Nếu chuyển thư mục, chạy lại `install.py`. Muốn gỡ, dừng MCP rồi xóa đúng hai mục cấu hình và hai thư mục skill, giữ nguyên mục khác. File backup có hậu tố `.aidol-backup-*`; bản sao skill trong thư mục `aidol-backups` của từng agent. Việc gỡ không tự xóa dữ liệu phòng hoặc khóa API của khách.

Tùy chọn nâng cao: `AIDOL_BROWSER_CDP` chỉ nhận endpoint loopback khi người dùng đã chuẩn bị trình duyệt tương thích. Mặc định không cần cài cổng CDP thủ công. Upload media yêu cầu `AIDOL_UPLOAD_ROOT` trỏ đúng thư mục khách cho phép; không cấp mặc định cả ổ đĩa.

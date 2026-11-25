# Aidol Agent Kit — Room + Event Router

Bộ MCP và skill chính thức để Codex / Claude Code hỗ trợ khách sử dụng **Aidol Room Cloud** và **Aidol Event Router**.

## Nói một câu với agent

Gửi link repo này cho Codex hoặc Claude Code và yêu cầu:

> Đọc INSTALL.md của repo này, cài cả hai MCP và hai skill Aidol cho tài khoản của tôi. Sau đó giúp tôi kết nối Room với Event Router. Hãy hướng dẫn tôi ở những bước cần đăng nhập hoặc thao tác thủ công.

Agent đọc [INSTALL.md](INSTALL.md), tải bộ vào thư mục cố định trên máy khách, cài dependencies, sao lưu và thêm cấu hình. Khởi động lại agent sau khi cài để nạp công cụ mới. Repo không tự cấp quyền hay cài đặt chỉ bằng việc mở một đường link.

## Hai MCP và hai skill

| Thành phần | Chức năng |
| --- | --- |
| Aidol Room MCP | Xem kho, thuê phòng được cho phép, nhập thiết lập qua giao diện, thao tác Studio Pro và lấy link OBS bằng nút sao chép |
| Aidol Event Router MCP | Nối mã ALC, theo dõi kết nối, chuẩn bị ghim, gửi mã sản phẩm và cấu hình phản hồi bình luận text bằng Room API |
| `aidol-room-live` | Hướng dẫn chọn Simple / Studio Pro, dùng phòng đúng tài khoản, kiểm tra đầu ra |
| `aidol-event-router` | Hướng dẫn nối đúng phòng, kiểm tra ghim và phản hồi, hướng dẫn khách tại bước thủ công |

### Simple và Studio Pro

**Simple** được khuyến nghị cho nhân vật nói, nhép môi và phản hồi sự kiện. Không có template hay xóa phông tích hợp; nhân vật nền xanh vẫn ra nền xanh để khách xử lý trong OBS.

**Studio Pro** có thiết kế bố cục trên web và đổi cảnh theo kịch bản; hiện là **beta**, có thể chưa ổn định, chỉ xuất **720p**. Agent phải hỏi lựa chọn trước khi thuê mới, giữ nguyên lựa chọn khi dùng lại phòng.

## Phần mềm khách tự tải

Windows: tải **AidolEventRouter_Agent_Setup_1.5.9.exe** ở [GitHub Releases](https://github.com/Fast-Tony/aidol-agent-kit/releases). Cài và mở phần mềm, tự đăng nhập. Bản Router cũ chưa có cầu nối cần được nâng cấp.

Nếu dùng bộ repo này cho cả Room và Router, chạy `python install.py` sau khi cài ứng dụng; không cần chạy thêm trình thiết lập Router-only. Cả hai cách đều dùng cùng tên cấu hình Router nên không tạo hai kết nối độc lập.

MCP repo cần Python 3.11+ và Google Chrome. Agent chuẩn bị môi trường Python riêng; khách không cần sửa code. Bộ `.exe` Router riêng đã kèm Python cho ứng dụng đó.

## Quyền và chi phí

- Chỉ thao tác tài khoản/phòng của khách đang đăng nhập. Không có tài khoản admin hay quyền SSH trong repo.
- Thuê máy và API Brain có thể tiêu Tun Coin; chỉ thực hiện trong phạm vi khách đồng ý. Không tự bật live hoặc tiêu coin chỉ vì cài skill.
- ALC là mã kết nối một lần. API Room `ar_…` dùng cho Brain là khóa riêng, nhập trong ô che của Router. Không đưa các khóa vào GitHub, MCP config hay báo cáo.
- Khách tự đăng nhập nền tảng, xử lý CAPTCHA và đặt đúng ô bình luận. Agent không tự vượt qua các bước này.
- Chấp nhận lệnh chưa chứng minh live/ghim/post thành công. Skill yêu cầu kiểm tra đầu ra thực tế.

MCP Event Router hiện hỗ trợ Windows. Room MCP không dùng lại cookie từ cửa sổ Chrome khác: nó mở một cửa sổ riêng có lưu phiên để khách đăng nhập đúng chỗ. macOS Router không nằm trong lần phát hành này.

## Kiểm tra

```powershell
python -m unittest discover -s room -p "test_*.py"
python -m unittest discover -s tests -p "test_*.py"
```

Kiểm thử tự động không chứng minh phiên live hay ghim sản phẩm thật đã thành công. Xem ghi chú release để biết phạm vi thử nghiệm và hạn chế.

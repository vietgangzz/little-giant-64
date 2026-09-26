# Little Giant 64: kịch bản video demo (~60 s, 2560×1440, 60 fps)

Video giới thiệu game cho team. Có cả hai map: **Hạ Long Skies** và **Vịnh Hạ Long**.
Mọi cảnh đều là gameplay thật chạy trong engine. Bot chơi bằng input thật, còn camera và phụ đề
do một "đạo diễn" trong game (`scripts/qa/trailer.gd`) điều khiển. Movie Maker của Godot ghi từng
khung hình ở 60 fps cố định, nên hình mượt tuyệt đối, không phụ thuộc máy nhanh hay chậm.

Phụ đề nằm trong một viên thuốc tối ở mép dưới, giống video tham khảo. Âm thanh là âm thanh
gốc của game: nhạc Kevin MacLeod cộng tiếng hiệu ứng thật.

## Phần 1: Hạ Long Skies (~30 s)

| # | Thời lượng | Hình ảnh | Phụ đề |
|---|---|---|---|
| 1 | 3.5 s | Màn hình tựa đề. Logo cầu vồng **LITTLE GIANT 64**; camera lượn quanh trống đồng, mascot vẫy tay | — |
| 2 | 4.5 s | Cận cảnh mascot: camera xoay từ mặt trước ra sau lưng để thấy **áo choàng cờ Việt Nam** bay; mascot vẫy rồi nhảy múa | *Mascot VGANG, dựng, rig và animate trong Blender* |
| 3 | 5 s | Gameplay camera sau lưng: chạy nhặt xu, **nhảy 3 bậc lộn nhào**, lướt, **dậm đất** tung bụi | *Nhảy 3 bậc · lộn nhào · lướt · dậm đất* |
| 4 | 4.5 s | Đội **khối "?"** tung 5 đồng xu, rồi nhảy lên **trống đồng lò xo** bay lên đảo trên trời | *Khối ? tung xu · trống đồng lò xo* |
| 5 | 5.5 s | Leo đỉnh **ruộng bậc thang** rồi lấy sao. Cảnh **STAR GET!**: mascot giơ sao lên, có cầu vồng chữ | *8 ngôi sao đồng Đông Sơn* |
| 6 | 5 s | Ba cảnh máy quay bay: **Chùa Một Cột** với ống tre, **thác nước**, **cột đá vôi** với khối đá dậm | *Hạ Long Skies · 146 đồng xu · 8 sao* |
| 7 | 2.5 s | Bước lên **thuyền buồm**, màn hình mờ dần | *Lên thuyền → Vịnh Hạ Long* |

## Phần 2: Vịnh Hạ Long (~23 s)

| # | Thời lượng | Hình ảnh | Phụ đề |
|---|---|---|---|
| 8 | 4 s | Flycam từ trên cao lướt xuống vịnh xanh ngọc, rồng đang bay giữa các cột đá. Thẻ chương **MAP 2 · VỊNH HẠ LONG** | (thẻ chương) |
| 9 | 3.5 s | Chạy dọc lối ván **làng chài nổi**, nhặt xu giữa các nhà bè | *Làng chài nổi trên vịnh* |
| 10 | 3.5 s | Bên trong **hang Sửng Sốt**: thạch nhũ, tinh thể phát sáng, nắng rọi từ giếng trời; mascot nhảy lên các cột măng đá | *Hang Sửng Sốt* |
| 11 | 3.5 s | **Đạp tường** leo khe giữa Hòn Trống và Hòn Mái | *Đạp tường · Hòn Trống Mái* |
| 12 | 3 s | Nhảy lên lưng **rồng** ở Bến rồng | *Cưỡi rồng bay quanh vịnh!* |
| 13 | 6 s | Cưỡi rồng lên cao sát đỉnh **Ti Tốp**, nhảy xuống chòi, **STAR GET!** | — |

## Phần 3: Kết (~8.5 s)

| # | Thời lượng | Hình ảnh | Phụ đề |
|---|---|---|---|
| 14 | 5 s | **ALL STARS!** trên trống đồng: mascot nhảy múa, pháo giấy, tiếng cồng, camera xoay quanh | — |
| 15 | 3.5 s | Thẻ kết màu mực: **LITTLE GIANT 64**, *Made with ♥ by VG TEAM · Blender · Godot* | — |

## Cách quay lại

```bash
tools/record_trailer.sh     # quay 3 đoạn bằng Movie Maker rồi dựng ra build/trailer/little-giant-64-trailer.mp4
```

Mỗi đoạn được quay riêng bằng lệnh
`godot --path . --write-movie <clip>.avi --resolution 2560x1440 -- --trailer=<skies|halong|finale>`.
Đạo diễn in mốc khung hình của từng cảnh (`SHOT <tên> <khung bắt đầu> <khung kết thúc>`). Script
dựng dùng các mốc này để cắt đúng độ dài từng cảnh, nối có chuyển cảnh mờ, rồi mã hóa
H.264 2560×1440 60 fps kèm âm thanh AAC.

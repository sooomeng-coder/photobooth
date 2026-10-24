/**
 * 포토부스 → 구글 드라이브 업로드 (v4.26)
 *
 * 설치 (한 번만):
 * 1. https://script.google.com → 새 프로젝트 → 이 파일 내용을 전부 붙여넣고 저장
 * 2. 오른쪽 위 [배포] → [새 배포] → 톱니바퀴에서 "웹 앱"
 *    - 실행 사용자: 나
 *    - 액세스 권한: 모든 사용자
 *    → [배포] → 권한 허용 (안전하지 않음 경고 → 고급 → 이동)
 * 3. 나오는 "웹 앱 URL"(https://script.google.com/macros/s/.../exec)을 복사
 * 4. 아이패드 앱 촬영 화면 ⚙ 길게 누르기 → [업로드 주소] → 붙여넣기 (또는 Claude에게 주소를 보내면 앱에 넣어 줌)
 *
 * 사진은 내 드라이브 / 302호 포토부스 촬영 / 10시·11시·12시·1시·2시·3시·4시 (행사 시간 밖은 '테스트') 에 JPEG로 쌓임.
 */
const FOLDER_NAME = '302호 포토부스 촬영';
const FOLDER_ID = '1MNpe5VLiScdTg2kXxJsl0DqzKJ4mN33w';  // 미리 만들어 둔 폴더 (10시~4시, 테스트 하위 폴더 있음)

function doPost(e) {
  try {
    const d = JSON.parse(e.postData.contents);
    let root;
    try { root = DriveApp.getFolderById(FOLDER_ID); } catch (x) { root = folder_(DriveApp.getRootFolder(), FOLDER_NAME); }
    // v4.29: 시간대별 폴더 (10시 11시 12시 1시 2시 3시 4시). 행사 시간(10~16시) 밖은 '테스트'
    const h = Number(Utilities.formatDate(new Date(), 'Asia/Seoul', 'H'));
    const day = folder_(root, h >= 10 && h <= 16 ? ((h % 12) || 12) + '시' : '테스트');
    if (day.getFilesByName(d.name).hasNext()) return out_({ ok: true, dup: true });  // 같은 사진 두 번 안 올림
    const blob = Utilities.newBlob(Utilities.base64Decode(d.data), d.mime || 'image/jpeg', d.name);
    const f = day.createFile(blob);
    return out_({ ok: true, id: f.getId() });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  }
}

function doGet() { return out_({ ok: true, ping: true }); }

function folder_(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}
function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

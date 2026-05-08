# 부동산정보 일괄 조회

지번 주소를 입력하면 **건축물 표제부 / 호별 면적 / 개별공시지가**를 자동 조회해 엑셀로 다운로드하는 Streamlit 웹앱.

## 기능

- 🏢 **건축물 정보 조회** — 같은 지번의 모든 동 + 집합건물 호별 전유·공용면적까지 펼침
- 💰 **개별공시지가 조회** — 최근 3개년 공시지가 + 지목 + 용도지역 + 면적
- 📥 결과는 사용자 입력 양식 그대로 카테고리별 그룹 헤더로 정리된 엑셀로 내려받기

## 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
공공 API 키 두 개가 필요합니다.

| 키 | 발급처 |
|---|---|
| `DATA_GO_KR_KEY` | [공공데이터포털 — 건축물대장정보 서비스](https://www.data.go.kr) (활용신청 필요) |
| `VWORLD_API_KEY` | [VWorld 오픈 API](https://www.vworld.kr) — 지오코딩(주소→PNU) + 토지특성(공시지가/면적) |

> 주소 변환은 VWorld 지오코딩을 사용합니다. juso.go.kr(도로명주소 API)은 해외 IP에서 차단/timeout이 발생해 클라우드 배포에 부적합.

템플릿을 복사해 키를 채워넣습니다:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# 편집기로 secrets.toml 열고 실제 키 입력
```

### 3. 실행
```bash
streamlit run app.py
```
브라우저에서 http://localhost:8501 자동 열림.

## 배포 (Streamlit Community Cloud)

1. 이 저장소를 GitHub에 push
2. https://share.streamlit.io 에서 GitHub 연동 → 저장소 선택 → `app.py` 지정
3. **Settings → Secrets**에 두 개 키 입력 (`secrets.toml`과 동일 형식):
   ```toml
   DATA_GO_KR_KEY = "..."
   VWORLD_API_KEY = "..."
   ```
4. Deploy 클릭 → 5분 내 공개 URL 생성

## 구조

```
.
├── app.py             # Streamlit UI (탭 2개 + OK저축은행 톤 디자인)
├── main.py            # 건축물 면적 조회 로직 (라이브러리 + CLI)
├── landprice.py       # 개별공시지가 조회 로직
├── requirements.txt
├── .streamlit/
│   ├── config.toml             # 테마 색상
│   ├── secrets.toml.example    # API 키 템플릿
│   └── secrets.toml            # 실제 키 (gitignore됨)
└── .gitignore
```

## 데이터 출처

- 국토교통부 건축물대장정보 서비스 (`apis.data.go.kr`)
- VWorld 지오코딩 (`api.vworld.kr/req/address`) — 주소 → PNU 변환
- VWorld 토지특성정보 (`api.vworld.kr/ned`) — 공시지가·면적·지목·용도지역

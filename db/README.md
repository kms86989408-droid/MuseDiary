#MuseDiary

## Tech Stack
* **Database**: MongoDB

### 📊 Database Structure (JSON)

### 📊 Database Structure (JSON)

```javascript

const moodMapping = {
    happy: 10,
    angry: 1,
    love: 10,  //sad=2
    pleasure: 6,
  };

const userSchema = {
    ID: "String",
    email: "String",
    PW: "String"

    // 2. Number by moodMapping
    moodScore: {
        type: "Number",
        // When user click 'happy', enter 10
    },

    comment: "String",
    date: { type: "Date", default: Date.now }
};


# MuseDiary Database (JSON)

MongoDB 데이터 구조를 JSON 중심으로 정리한 문서입니다.

## Database Summary

```json
{
  "database": "MongoDB",
  "collections": ["users", "diary_entries", "songs"],
  "referenceData": ["mood_mapping"]
}
```

## Schema Definition

```json
{
  "users": {
    "_id": "ObjectId",
    "id": "String (required, unique)",
    "email": "String (required, unique)",
    "pw": "String (required, bcrypt hash)",
    "createdAt": "Date (optional, default: Date.now)"
  },
  "diary_entries": {
    "_id": "ObjectId",
    "userId": "ObjectId (required, ref: users._id)",
    "analysisData": [
      {
        "content": "String (required)",
        "createdAt": "Date (optional, default: Date.now)",
        "mood": "String (required, enum: happy|angry|sad|pleasure)",
        "song": "String (optional, ref: songs._id)"      
      }
    ],
  },
  "mood_mapping": {
    "userId": "String (required, ref: users.id)",
    "happy": "Number",
    "angry": "Number",
    "sad": "Number",
    "pleasure": "Number"
  }
}
```

## Seed Data Source

- 서버 시작 시 `app.py`의 main 블록에서 DB를 초기화한 뒤 시드 데이터를 자동 삽입합니다.
- 실제 시드 소스는 `db/seed_data.py`입니다.
- `db/dummy-data.csv`는 참고용 샘플 텍스트이며 런타임에서 직접 로드하지 않습니다.

## Sample Documents

```json
{
  "users": {
    "_id": "ObjectId('66f0...')",
    "id": "muse_user",
    "email": "muse@example.com",
    "pw": "$2b$12$...",
    "createdAt": "2026-03-04T10:00:00.000Z"
  },
  "diary_entries": {
    "_id": "ObjectId('66f1...')",
    "userId": "ObjectId('66f0...')",
    "songId": "ObjectId('66f2...')",
    "analysisData": [
      {
        "content": "오늘은 기분이 정말 좋았다.",
        "createdAt": "2026-03-04T10:20:00.000Z",
        "mood": "happy"
      },
      {
        "content": "짜증난다.",
        "createdAt": "2026-03-05T10:20:10.000Z",
        "mood": "angry"
      },
      {
        "content": "기분이 정말 별로.",
        "createdAt": "2026-03-06T10:20:23.000Z",
        "mood": "sad"
      }
    ]
  },
  "songs": {
    "_id": "ObjectId('66f2...')",
    "userId": "ObjectId('66f0...')",
    "songTitle": "좋은 날",
    "createdAt": "2026-03-04T10:15:00.000Z"
  },
  "mood_mapping": {
    "happy": 10,
    "angry": 1,
    "sad": 2,
    "pleasure": 6
  },

}
```

## Index Policy

```json
{
  "users": [
    { "key": { "id": 1 }, "unique": true },
    { "key": { "email": 1 }, "unique": true }
  ],
  "diary_entries": [
    { "key": { "userId": 1, "createdAt": -1 } },
    { "key": { "mood": 1 } },
    { "key": { "songId": 1 } }
  ],
  "songs": [
    { "key": { "userId": 1, "createdAt": -1 } },
    { "key": { "userId": 1, "songTitle": 1 } }
  ]
}
```

## 곡(노래) · 사용자 연계

- **songs** 컬렉션: 사용자 ID(`userId`)별로 곡을 저장합니다.
- **곡제목**: `songTitle` 필드로 저장하며, 한 사용자 기준으로 곡 제목 검색·연계가 가능합니다.
- **diary_entries**에서 `songId`로 해당 일기와 곡을 연결할 수 있습니다.
- 흐름: 곡 노래 수신 → `songs`에 `userId` + `songTitle` 저장 → 필요 시 일기(`diary_entries`)의 `songId`로 연계.

---

## Backend contract (what to implement)

Backend 요청사항을 DB 기준으로 정리한 것입니다.

### 1. Song → diary-entries (append)

- **요구**: diary-entries 를 쓸 때 **Song 을 append** 해야 함.
- **의미**: 일기 저장/업데이트 시 해당 일기와 연결된 **곡 정보를 반드시 포함**.
- **구현**:
  - `diary_entries` 문서에 **`songId`** 필드 사용 (이미 스키마에 있음).
  - 새 일기 문서 생성 시: `songId: ObjectId(songs._id)` 포함.
  - 기존 문서에 `$push` 로 `analysisData` 만 넣는 경우에도, **문서 수준에서 `songId` 를 set/update** 하도록 하면 됨 (해당 일기와 연결된 곡이 있을 때).
- **선택**: 나중에 “일기 한 줄마다 다른 곡”이 필요하면 `analysisData[]` 각 항목에 `songId` 를 두는 방식으로 확장 가능. 현재 스키마는 문서당 하나의 `songId`.

### 2. DB → diary-entries & mood mapping

- **DB → diary-entries**
  - 쓰기: `users._id` → `diary_entries.userId`, (선택) `songs._id` → `diary_entries.songId`.
  - 읽기: `diary_entries.userId` 로 사용자별 일기 조회, `diary_entries.songId` 로 곡 정보 조인.
- **mood mapping**
  - `diary_entries.analysisData[].mood`: 문자열 enum (`happy` | `angry` | `sad` | `pleasure`).
  - `mood_mapping` 컬렉션: 같은 `userId` 기준으로 mood 별 **카운트** (숫자) 저장.  
    예: `{ userId, happy: 10, angry: 1, sad: 2, pleasure: 6 }`.
  - 흐름: 일기 저장 시 `analysisData` 에 mood 문자열 저장 → 동일 유저의 `mood_mapping` 에 해당 mood 키에 대해 `$inc` 로 1 증가.

### 3. DB docs

- 이 README 가 **DB 스키마·컬렉션·인덱스·샘플·백엔드 계약**의 단일 문서.
- 스키마/필드 변경 시 이 문서를 먼저 수정하고, 백엔드와 공유.

---

## Current Code Gap

```json
{
  "appPyStatus": {
    "loginIdField": "currently uses `id` (recommended: `username`)",
    "registerDuplicateCheck": "not implemented",
    "usersCreatedAtSave": "not implemented",
    "diaryEntriesWriteFlow": "not implemented",
    "diaryEntriesSongAppend": "songId not set when writing diary_entries"
  }
}
```

#MuseDiary

## Tech Stack
* **Database**: MongoDB

### 📊 Database Structure (JSON)

### 📊 Database Structure (JSON)

```javascript

const moodMapping = {
    happy: 10,
    angry: 1,
    love: 10,
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
    "username": "String (required, unique)",
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
        "mood": "String (required, enum: happy|angry|sad|pleasure)"
      }
    ],
    "songId": "ObjectId (optional, ref: songs._id)"
  },
  "songs": {
    "_id": "ObjectId",
    "userId": "ObjectId (required, ref: users._id)",
    "songTitle": "String (required)",
    "createdAt": "Date (optional, default: Date.now)"
  },
  "mood_mapping": {
    "happy": "Number",
    "angry": "Number",
    "love": "Number",
    "pleasure": "Number"
  }
}
```

## Sample Documents

```json
{
  "users": {
    "_id": "ObjectId('66f0...')",
    "username": "muse_user",
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
    { "key": { "username": 1 }, "unique": true },
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

## Current Code Gap

```json
{
  "appPyStatus": {
    "loginIdField": "currently uses `id` (recommended: `username`)",
    "registerDuplicateCheck": "not implemented",
    "usersCreatedAtSave": "not implemented",
    "diaryEntriesWriteFlow": "not implemented"
  }
}
```

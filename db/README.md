# MuseDiary Database (JSON)

MongoDB 데이터 구조를 JSON 중심으로 정리한 문서입니다.

## Database Summary

```json
{
  "database": "MongoDB",
  "collections": ["users", "diary_entries"],
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
    ]
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
    { "key": { "mood": 1 } }
  ]
}
```

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

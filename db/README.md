#MuseDiary

## Tech Stack
* **Database**: MongoDB

### 📊 Database Structure (JSON)

우리의 서비스는 MongoDB를 사용하며, 'users' 컬렉션의 데이터 구조는 다음과 같습니다.

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `ID` | String | 사용자 ID | "Gyutae" |
| `email` | String | 사용자 이메일 | "test@gmail.com" |
| `PW` | String | 해시된 비밀번호 | "$2b$12..." |
| `mood` | Object | mood | { "happy": happy, "angry": angry, "love": love, "pleasure": pleasure } |
| `comment` | String | comment | "Such a wonderful day!" |
| `Date` | Date | Created Date | 2026-03-04 |
import csv
import datetime
import os
import re

MOOD_KEYS = ("happy", "angry", "sad", "pleasure")
USER_LINE_PATTERN = re.compile(r"^id:(\S+)\s+pw:(\S+)\s+email:(\S+)$")
DEFAULT_SEED_PATH = os.path.join(os.path.dirname(__file__), "dummy-data.csv")


def _parse_datetime(raw_value):
    normalized = raw_value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(normalized)


def _parse_user_line(line):
    match = USER_LINE_PATTERN.match(line.strip())
    if not match:
        return None
    user_id, password, email = match.groups()
    return {"id": user_id, "pw": password, "email": email}


def _parse_entry_line(line):
    stripped = line.strip()
    if not stripped.startswith("(") or not stripped.endswith(")"):
        return None
    if stripped.lower().startswith("(id,"):
        return None

    row_text = stripped[1:-1]
    row = next(csv.reader([row_text], skipinitialspace=True))
    if len(row) != 5:
        raise ValueError(f"Invalid entry format: {line}")

    user_id, mood, content, created_at, song = row
    mood = mood.strip()
    if mood not in MOOD_KEYS:
        raise ValueError(f"Unsupported mood '{mood}' in line: {line}")

    return {
        "userId": user_id.strip(),
        "mood": mood,
        "content": content.strip(),
        "createdAt": _parse_datetime(created_at.strip()),
        "song": song.strip(),
    }


def _load_seed_file(seed_file_path):
    with open(seed_file_path, "r", encoding="utf-8") as file:
        lines = [line.rstrip("\n") for line in file]

    users = []
    entries = []
    for line in lines:
        if not line.strip():
            continue

        parsed_user = _parse_user_line(line)
        if parsed_user:
            users.append(parsed_user)
            continue

        parsed_entry = _parse_entry_line(line)
        if parsed_entry:
            entries.append(parsed_entry)

    if not users:
        raise ValueError("No user seed data found in dummy-data.csv")
    if not entries:
        raise ValueError("No diary entry seed data found in dummy-data.csv")

    return users, entries


def _create_user_documents(users, bcrypt):
    now = datetime.datetime.utcnow()
    return [
        {
            "id": user["id"],
            "email": user["email"],
            "pw": bcrypt.generate_password_hash(user["pw"]),
            "createdAt": now,
        }
        for user in users
    ]


def _create_diary_documents(users, entries):
    grouped = {user["id"]: [] for user in users}
    for entry in entries:
        if entry["userId"] not in grouped:
            grouped[entry["userId"]] = []
        grouped[entry["userId"]].append(
            {
                "content": entry["content"],
                "createdAt": entry["createdAt"],
                "mood": entry["mood"],
                "song": entry["song"],
            }
        )

    return [{"userId": user_id, "analysisData": data} for user_id, data in grouped.items()]


def _create_mood_mapping_documents(diary_documents):
    mappings = []
    for diary in diary_documents:
        counts = {key: 0 for key in MOOD_KEYS}
        for entry in diary.get("analysisData", []):
            mood = entry.get("mood")
            if mood in counts:
                counts[mood] += 1
        mappings.append({"userId": diary["userId"], **counts})
    return mappings


def seed_database(db, bcrypt, seed_file_path=DEFAULT_SEED_PATH):
    users, entries = _load_seed_file(seed_file_path)
    user_docs = _create_user_documents(users, bcrypt)
    diary_docs = _create_diary_documents(users, entries)
    mood_mapping_docs = _create_mood_mapping_documents(diary_docs)

    db.users.insert_many(user_docs)
    db.diary_entries.insert_many(diary_docs)
    db.mood_mapping.insert_many(mood_mapping_docs)

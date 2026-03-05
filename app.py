from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bs4 import BeautifulSoup
import jwt
import datetime
import os
import random
import re
import requests
from dotenv import load_dotenv
from db.seed_data import seed_database

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
secret_key = os.getenv("SECRET_KEY")

if not mongo_uri:
    raise ValueError("MONGO_URI is not set in .env")
if not secret_key:
    raise ValueError("SECRET_KEY is not set in .env")

client = MongoClient(mongo_uri)
db = client.get_default_database()

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
bcrypt = Bcrypt(app) # bcrypt 초기화

MOOD_CONFIG = {
    "happy": {
        "template": "happy.html",
        "playlist_url": os.getenv("GENIE_PLAYLIST_HAPPY", "https://www.genie.co.kr/playlist/detailView?plmSeq=31070"),
    },
    "angry": {
        "template": "angry.html",
        "playlist_url": os.getenv("GENIE_PLAYLIST_ANGRY", "https://www.genie.co.kr/playlist/detailView?plmSeq=17505"),
    },
    "sad": {
        "template": "sad.html",
        "playlist_url": os.getenv("GENIE_PLAYLIST_SAD", "https://www.genie.co.kr/playlist/detailView?plmSeq=31065"),
    },
    "pleasure": {
        "template": "pleasure.html",
        "playlist_url": os.getenv("GENIE_PLAYLIST_PLEASURE", "https://www.genie.co.kr/playlist/detailView?plmSeq=17266"),
    },
}

# 홈
@app.route("/")
def home():
    return redirect(url_for("login"))

# 로그인 페이지
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or request.form
    id = data.get("id")
    pw = data.get("pw")

    if not id or not pw:
        return "ID or PW 누락", 400

    user = db.users.find_one({"id" : id})
    if user and bcrypt.check_password_hash(user["pw"], pw):
        session["userId"] = user["id"]

        token = jwt.encode({
            "user_id" : user["id"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config["SECRET_KEY"], algorithm="HS256")

        response = make_response(redirect(url_for("daily_mood"))) # 로그인 성공 메인페이지 이동
        response.set_cookie(
            "token",
            token,
            httponly=True,
            samesite="LAX"
        )
        return response
    return "로그인실패", 401

# 회원가입
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json(silent=True) or request.form
    id = data.get("id")
    email = data.get("email")
    pw = data.get("pw")

    if not id or not email or not pw:
        return "ID, Email, PW 누락", 400

    # 중복 ID / Email 확인


    hash_pw = bcrypt.generate_password_hash(pw) # pw 해쉬암호화

    db.users.insert_one({
        "id" : id,
        "email" : email,
        "pw" : hash_pw
    })
    return redirect(url_for("login"))


@app.route("/daily-mood", methods=["GET", "POST"])
def daily_mood():
    if request.method == "POST":
        userId = session.get("userId")  # 사용자 로그인 Id get
        
        mood = request.form.get("mood") # 기분 아이콘 
        content = request.form.get("content","") # 한줄 일기
        createdAt = datetime.datetime.now().strftime("%Y-%m-%d'T'%H:%M:%S") # 현재 날짜 시간

        mood_info = MOOD_CONFIG.get(mood)
        if not mood_info:
            return "잘못된 mood 값입니다.", 400

        song = "추천곡 없음"
        singer = ""

        try:
            tracks = crawl_genie_playlist(mood_info["playlist_url"])
            if tracks:
                picked = random.choice(tracks)
                song = picked["song"]
                singer = picked["singer"]
        except Exception as e:
            print(f"[{mood}] 크롤링 실패: {e}")

        # diary_entries 입력
        song_for_save = f"{song} - {singer}" if singer else song
        diaryEntriesData = {
            "content" :content,
            "createdAt" : createdAt,
            "mood" : mood,
            "song" : song_for_save
        }
        db.diary_entries.update_one(
            {"userId" : userId},
            {"$push":{"analysisData" : diaryEntriesData}},
            upsert = True
        )

        # print("args:", request.args)
        # print("form:", request.form)

        db.mood_mapping.update_one(
            {"userId" : userId},
            {"$inc" : {mood : 1}},
            upsert = True
        )
        return render_template(mood_info["template"], singer=singer, song=song)

        # return redirect(url_for("daily_mood"))
    return render_template("daily_mood.html")


@app.route("/count", methods=["GET", "POST"])
def count():
    user_id = session.get("userId")
    entries = db.diary_entries.find_one({"userId": user_id}) or {}
    entries_data = entries.get("analysisData", [])  # analysisData 데이터 조회
    mood_mapping = db.mood_mapping.find_one({"userId": user_id}) or {}

    if not user_id:
        return redirect(url_for("login"))

    mood_counts = db.mood_mapping.find_one({"userId": user_id}) or {}

    if request.method == "POST":
        print(f"테스트입니다.{entries_data}, {mood_mapping}")
        return redirect(url_for("ai_report"))

    return render_template(
        "count.html",
        count_happy=mood_counts.get("happy", 0),
        count_angry=mood_counts.get("angry", 0),
        count_sad=mood_counts.get("sad", 0),
        count_pleasure=mood_counts.get("pleasure", 0),
        recommend_happy="-",
        recommend_angry="-",
        recommend_sad="-",
        recommend_pleasure="-",
    )
    

    
@app.route("/happy")
def happy():
    return render_template("happy.html")


@app.route("/angry")
def angry():
    return render_template("angry.html")


@app.route("/sad")
def sad():
    return render_template("sad.html")


@app.route("/pleasure")
def pleasure():
    return render_template("pleasure.html")

@app.route("/ai_report")
def ai_report():
    user_name = session.get("userId", "000")
    return render_template("ai_report.html", user_name=user_name)
    


# 크롤링
def crawl_genie_playlist(playlist_url):
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    res = requests.get(playlist_url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    tracks = []
    seen = set()
    rows = soup.select("table.list-wrap tbody tr")

    for row in rows:
        title_el = row.select_one("a.title")
        if not title_el:
            continue
        artist_el = row.select_one("a.artist")
        song = normalize_song_text(title_el.get_text(" ", strip=True))
        singer = normalize_song_text(artist_el.get_text(" ", strip=True)) if artist_el else ""

        if not song:
            continue
        key = (song, singer)
        if key in seen:
            continue
        seen.add(key)
        tracks.append({"song": song, "singer": singer})

    # 일부 페이지 구조가 다를 때 fallback
    if not tracks:
        scraps = soup.select("table.list-wrap a.title") or soup.select("a.title")
        for i in scraps:
            song = normalize_song_text(i.get_text(" ", strip=True))
            if not song or song in seen:
                continue
            seen.add(song)
            tracks.append({"song": song, "singer": ""})

    return tracks


def normalize_song_text(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^\s*TITLE\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

if __name__ == "__main__":
    client.drop_database(db.name)
    print('데이터 초기화완료!')
    try:
        seed_database(db, bcrypt)
        print("초기데이터 삽입 성공!!")
    except Exception as e:
        print(f"초기데이터 삽입 실패: {e}")
        raise
    app.run("0.0.0.0", port=8080, debug=True)


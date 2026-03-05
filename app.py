from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bs4 import BeautifulSoup
import jwt
import datetime
import os
import random
import requests
from dotenv import load_dotenv

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

        # diary_entries 입력
        diaryEntriesData = {
            "content" :content,
            "createdAt" : datetime.datetime.now().strftime("%Y-%m-%d'T'%H:%M:%S"), # 현재 날짜 시간
            "mood" : mood
        }
        db.diary_entries.update_one(
            {"userId" : userId},
            {"$push":{"analysisData" : diaryEntriesData}},
            upsert = True
        )
        print("args:", request.args)
        print("form:", request.form)
        db.mood_mapping.update_one(
            {"userId" : userId},
            {"$inc" : {mood : 1}},
            upsert = True
        )
        mood_info = MOOD_CONFIG.get(mood)
        if not mood_info:
            return "잘못된 mood 값입니다.", 400

        song = "추천곡 없음"
        singer = "-"

        try:
            titles = crawl_genie_playlist(mood_info["playlist_url"])
            if titles:
                picked = random.choice(titles)
                if " - " in picked:
                    song, singer = [x.strip() for x in picked.split(" - ", 1)]
                else:
                    song = picked
                    singer = "Unknown Artist"
        except Exception as e:
            print(f"[{mood}] 크롤링 실패: {e}")

        return render_template(mood_info["template"], singer=singer, song=song)

        # return redirect(url_for("daily_mood"))
    return render_template("daily_mood.html")


@app.route("/count", methods=["GET", "POST"])
def count():
    if request.method == "GET":
        user_id = session.get("userId")
        mood_counts = db.mood_mapping.find_one({"userId": user_id}) or {}

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

# 크롤링
def crawl_genie_playlist(playlist_url):
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    res = requests.get(playlist_url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    songs = []
    scraps = soup.select("table.list-wrap a.title")

    if not scraps:
        scraps = soup.select("a.title")

    for i in scraps :
        k = i.get_text(strip=True)
        if k:
            songs.append(k)
    seen = set()
    titles = [x for x in songs if not (x in seen or seen.add(x))]
    return titles

if __name__ == "__main__":
    app.run("0.0.0.0", port=8080, debug=True)

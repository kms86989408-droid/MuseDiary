from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client. # name 대기

app = Flask(__name__)
app.secret_key = "secret-key" # 세션 암호화 * 키 변경 예정
bcrypt = Bcrypt(app) # bcrypt 초기화

login_manager = LoginManager()
login_manager.init_app(app) # login_manager 애플리케이션과 연계
login_manager.login_view = "login" # 로그인 안했을때 이동할 route

# 로그인 페이지
@app.route("/login")
def home():
    return render_template("index.html")

# 회원가입
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        ID = request.form["id"]
        email = request.form["email"]
        pw = request.form["PW"]

    # 중복 ID / Email 확인
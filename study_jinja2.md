# Jinja2 사용

```
from jinja2 import Template

# 템플릿
template = Template('Hello, {{ name }}!')

# 데이터
data = {'name' : 'Jihyun'}

# 렌더링 : 템플릿에 데이터를 삽입하여 최종 HTML 생성
result = template.render(data)
print(result) # 출력: Hello, Jihyun!
```

### 데이터 출력하기 : `{{ }}` (Variable)

백엔드에서 넘겨준 변수 값을 HTML 화면에 그대로 보여줄 때 사용한다.

```
<h1>안녕하세요, {{ name }}님!</h1>
<p>당신의 등급은 {{ user_level }}입니다.</p>
```

### 제어문 사용하기 : `{% %}` (Tag)

조건문(if문)이나 반복문(for문)을 사용할 때 쓴다.

반드시 `{% endif %}` 나 `{% endfor %}` 로 닫아줘야 한다.

#### 조건문 (if)

로그인 여부에 따라 버튼을 다르게 보여줄 때 유용하다.

```
{% if is_logged_in %}
    <button onclick="handleLogout()">로그아웃</button>
{% else %}
    <button onclick="handleLogin()">로그인</button>
    <button onclick="handleSignUp()">회원가입</button>
{% endif %}
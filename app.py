import random
import uuid
from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

# 임시 데이터 저장소 (서버가 꺼지면 리셋되지만 무료 서버용으로 적합)
events = {}


# --- 화면 스타일 디자인 (CSS) ---
COMMON_STYLE = """
<style>
    body { font-family: 'Malgun Gothic', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; color: #333; }
    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1, h2 { color: #1e3a8a; text-align: center; }
    .form-group { margin-bottom: 15px; }
    label { display: block; margin-bottom: 5px; font-weight: bold; }
    input[type="text"], input[type="number"] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
    button { width: 100%; padding: 12px; background-color: #2563eb; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
    button:hover { background-color: #1d4ed8; }
    .event-card { border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; margin-top: 20px; background-color: #ff-f; position: relative; }
    .btn-close { background-color: #10b981; margin-bottom: 5px; }
    .btn-close:hover { background-color: #059669; }
    .btn-delete { background-color: #ef4444; }
    .btn-delete:hover { background-color: #dc2626; }
    .link-box { background: #f3f4f6; padding: 10px; border-radius: 6px; word-break: break-all; font-size: 14px; margin: 10px 0; border: 1px dashed #cbd5e1; }
    .badge { display: inline-block; padding: 4px 8px; background: #dbeafe; color: #1e40af; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-closed { background: #fee2e2; color: #991b1b; }
    ul { padding-left: 20px; }
</style>
"""

# --- 1. 관리자 페이지 화면 ---
ADMIN_TEMPLATE = (
    """
<!DOCTYPE html>
<html>
<head>
    <title>이벤트 관리자</title>
    """
    + COMMON_STYLE
    + """
</head>
<body>
    <div class="container">
        <h1>🛠️ 이벤트 관리 시스템</h1>
        <form action="/admin/create" method="POST">
            <div class="form-group">
                <label>🎁 상품 이름</label>
                <input type="text" name="prize_name" placeholder="예: 교촌치킨 허니콤보" required>
            </div>
            <div class="form-group">
                <label>🏆 당첨 인원 수</label>
                <input type="number" name="winner_count" min="1" value="1" required>
            </div>
            <button type="submit">이벤트 만들기</button>
        </form>

        <h2>[ 생성된 이벤트 목록 ]</h2>
        {% if not events %}
            <p style="text-align: center; color: #666;">아직 만든 이벤트가 없습니다.</p>
        {% endif %}
        {% for id, ev in events.items() %}
            <div class="event-card">
                <h3>{{ ev.prize_name }} 
                    {% if ev.closed %}
                        <span class="badge badge-closed">마감됨</span>
                    {% else %}
                        <span class="badge">모집중</span>
                    {% endif %}
                </h3>
                <p><b>선택 인원:</b> {{ ev.winner_count }}명 / <b>현재 참여자:</b> {{ ev.participants|length }}명</p>
                
                <div class="link-box">
                    🔗 참가 링크: <a href="{{ ev.user_url }}" target="_blank">{{ ev.user_url }}</a>
                </div>

                {% if not ev.closed %}
                    <form action="/admin/close/{{ id }}" method="POST" style="margin-bottom: 5px;">
                        <button type="submit" class="btn-close">🚫 마감 및 추첨하기</button>
                    </form>
                {% else %}
                    <div style="background: #f0fdf4; padding: 10px; border-radius: 6px; border: 1px solid #bbf7d0;">
                        <b>🏆 당첨자 결과:</b>
                        {% if ev.winners %}
                            <span style="color: #16a34a; font-weight: bold;">{{ ev.winners|join(', ') }}</span>
                        {% else %}
                            <span style="color: #666;">참여자가 없어서 뽑지 못했습니다.</span>
                        {% endif %}
                    </div>
                {% endif %}

                <form action="/admin/delete/{{ id }}" method="POST" style="margin-top: 10px;">
                    <button type="submit" class="btn-delete">🗑️ 삭제</button>
                </form>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""
)

# --- 2. 사용자 응모 페이지 화면 ---
USER_TEMPLATE = (
    """
<!DOCTYPE html>
<html>
<head>
    <title>이벤트 참여</title>
    """
    + COMMON_STYLE
    + """
</head>
<body>
    <div class="container">
        <h1>🎁 이벤트에 도전하세요!</h1>
        <div style="text-align: center; margin-bottom: 20px; background: #eff6ff; padding: 15px; border-radius: 8px;">
            <h2 style="margin: 0 0 10px 0; color: #2563eb;">{{ event.prize_name }}</h2>
            <p style="margin: 0;">총 <b>{{ event.winner_count }}명</b>에게 선물을 드립니다!</p>
        </div>

        {% if event.closed %}
            <div style="background: #fee2e2; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #fca5a5;">
                <h3 style="color: #dc2626; margin-top: 0;">아쉽게도 마감된 이벤트입니다 🚫</h3>
                <b>🏆 최종 당첨자:</b> <span style="font-size: 18px; color: #b91c1c;">{{ event.winners|join(', ') if event.winners else '없음' }}</span>
            </div>
        {% else %}
            <form action="/submit/{{ event_id }}" method="POST">
                <div class="form-group">
                    <label>📝 내 닉네임 또는 이름</label>
                    <input type="text" name="username" placeholder="이름을 적어주세요" required>
                </div>
                <button type="submit">이벤트 응모하기 🚀</button>
            </form>
            <p style="text-align: center; color: #666; font-size: 14px;">현재 {{ event.participants|length }}명이 줄을 섰어요!</p>
        {% endif %}
    </div>
</body>
</html>
"""
)


# --- 로직 함수들 (서버 기능) ---


@app.route("/")
def home():
    return redirect(url_for("admin_page"))


@app.route("/admin")
def admin_page():
    return render_template_string(ADMIN_TEMPLATE, events=events)


@app.route("/admin/create", methods=["POST"])
def create_event():
    prize_name = request.form.get("prize_name")
    winner_count = int(request.form.get("winner_count", 1))
    event_id = str(uuid.uuid4())[:8]

    # Render 환경의 호스트 이름 자동 계산
    user_url = request.host_url + f"event/{event_id}"

    events[event_id] = {
        "prize_name": prize_name,
        "winner_count": winner_count,
        "participants": [],
        "winners": [],
        "closed": False,
        "user_url": user_url,
    }
    return redirect(url_for("admin_page"))


@app.route("/admin/close/<event_id>", methods=["POST"])
def close_event(event_id):
    if event_id in events and not events[event_id]["closed"]:
        ev = events[event_id]
        ev["closed"] = True
        pt = ev["participants"]
        count = ev["winner_count"]

        if pt:
            # 참여자가 설정된 인원보다 적으면 참여자 전원 당첨
            actual_count = min(len(pt), count)
            ev["winners"] = random.sample(pt, actual_count)

    return redirect(url_for("admin_page"))


@app.route("/admin/delete/<event_id>", methods=["POST"])
def delete_event(event_id):
    if event_id in events:
        del events[event_id]
    return redirect(url_for("admin_page"))


@app.route("/event/<event_id>")
def user_page(event_id):
    if event_id not in events:
        return "<h3>존재하지 않거나 삭제된 이벤트입니다. ❌</h3>", 404
    return render_template_string(
        USER_TEMPLATE, event=events[event_id], event_id=event_id
    )


@app.route("/submit/<event_id>", methods=["POST"])
def submit_entry(event_id):
    if event_id not in events:
        return "이벤트가 존재하지 않습니다.", 404

    ev = events[event_id]
    if ev["closed"]:
        return "이미 마감된 이벤트입니다.", 400

    username = request.form.get("username", "").strip()
    if username and username not in ev["participants"]:
        ev["participants"].append(username)

    return f"""
    <script>
        alert("{username}님, 응모 완료되었습니다! 이 창을 닫고 결과를 기다려주세요.");
        window.location.href = "/event/{event_id}";
    </script>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

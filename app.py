from flask import Flask, request, jsonify
import secrets
import random

app = Flask(__name__)

# 이벤트 저장소
events = {}

@app.route("/")
def home():
    return """
    <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
        <h1>🎁 실시간 추첨 이벤트 페이지</h1>
        <p>이벤트에 참여하시려면 공유받은 전용 링크로 접속해주세요.</p>
        <hr style="width: 300px;">
        <a href='/admin' style="color: #007bff; text-decoration: none; font-weight: bold;">🛠️ 관리자 페이지 바로가기</a>
    </div>
    """

# ---------------- 관리자 페이지 ----------------
@app.route("/admin")
def admin_panel():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>🛠️ 이벤트 관리자</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; background-color: #f8f9fa; }
            h1, h3 { color: #333; }
            input { padding: 10px; width: calc(100% - 24px); margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
            .btn-create { background-color: #007bff; color: white; width: 100%; }
            .btn-close { background-color: #28a745; color: white; }
            .btn-delete { background-color: #dc3545; color: white; margin-left: 5px; }
            .btn-close:disabled { background-color: #6c757d; cursor: not-allowed; }
            .event-card { background: white; border: 1px solid #e0e0e0; border-radius: 8px; margin: 20px 0; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .status-badge { inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white; }
            .status-ongoing { background-color: #28a745; }
            .status-closed { background-color: #dc3545; }
        </style>
    </head>
    <body>
        <h1>🛠️ 이벤트 관리 시스템</h1>
        <hr>
        
        <h3>✨ 새 이벤트 생성</h3>
        <input id="title" placeholder="🎁 상품 이름 (예: 스타벅스 아메리카노)">
        <input id="limit" placeholder="🎯 당첨 인원 수" type="number" min="1">
        <button class="btn-create" onclick="create()">이벤트 만들기</button>

        <h3>📋 생성된 이벤트 목록</h3>
        <div id="list"></div>

        <script>
        // 현재 사이트의 도메인 주소를 자동으로 알아내기 위함 (렌더 배포 시 매우 편리!)
        const baseUrl = window.location.origin;

        async function create() {
            let title = document.getElementById("title").value.trim();
            let limit = document.getElementById("limit").value;

            if (!title || !limit) {
                alert("상품 이름과 당첨 인원을 모두 입력해주세요!");
                return;
            }

            let res = await fetch("/create", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({title, limit})
            });

            let data = await res.json();
            alert("🎉 이벤트 생성 완료!");
            
            // 입력창 비우기
            document.getElementById("title").value = "";
            document.getElementById("limit").value = "";
            load();
        }

        async function load() {
            let res = await fetch("/events");
            let data = await res.json();

            let html = "";
            let keys = Object.keys(data).reverse(); // 최신 생성된 이벤트가 위로 오도록 정렬

            if (keys.length === 0) {
                html = "<p style='color: #888;'>생성된 이벤트가 없습니다.</p>";
            }

            for (let c of keys) {
                let ev = data[c];
                let fullLink = `${baseUrl}/event/${c}`;
                let statusBadge = ev.closed ? '<span class="status-badge status-closed">마감됨</span>' : '<span class="status-badge status-ongoing">진행중</span>';

                html += `
                <div class="event-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; font-size: 18px;">🎁 ${ev.title}</h4>
                        ${statusBadge}
                    </div>
                    <p style="margin: 10px 0 5px 0; color: #555;">🎯 목표 당첨 인원: <b>${ev.limit}명</b></p>
                    <p style="margin: 5px 0 15px 0; color: #555;">👥 현재 참여자 수: <b>${ev.participants.length}명</b></p>
                    
                    <div style="background: #f1f3f5; padding: 8px; border-radius: 4px; font-size: 13px; margin-bottom: 15px;">
                        🔗 참가 링크: <a href="/event/${c}" target="_blank" style="word-break: break-all;">${fullLink}</a>
                    </div>

                    <button class="btn-close" onclick="closeEvent('${c}')" ${ev.closed ? 'disabled' : ''}>
                        ${ev.closed ? '🎰 추첨 완료' : '🚫 마감 및 추첨'}
                    </button>
                    <button class="btn-delete" onclick="deleteEvent('${c}')">🗑️ 삭제</button>

                    <h5 style="margin: 15px 0 5px 0; color: #333;">🏆 당첨자 결과</h5>
                    <p style="margin: 0; color: #007bff; font-weight: bold;">
                        ${ev.winners.length ? ev.winners.join(", ") : (ev.closed ? "참가자 없음" : "아직 추첨 전입니다.")}
                    </p>
                </div>
                `;
            }

            document.getElementById("list").innerHTML = html;
        }

        async function closeEvent(code) {
            if (confirm("이벤트를 마감하고 즉시 당첨자를 추첨하시겠습니까?")) {
                let res = await fetch("/close/" + code, { method: "POST" });
                let data = await res.json();
                alert(data.msg);
                load();
            }
        }

        async function deleteEvent(code) {
            if (confirm("정말로 이 이벤트를 목록에서 완전히 삭제하시겠습니까?\\n(참여자 및 당첨자 데이터가 모두 사라집니다.)")) {
                let res = await fetch("/delete/" + code, { method: "DELETE" });
                let data = await res.json();
                alert(data.msg);
                load();
            }
        }

        load();
        </script>
    </body>
    </html>
    """

# ---------------- 이벤트 생성 API ----------------
@app.route("/create", methods=["POST"])
def create():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    
    try:
        limit = int(data.get("limit", 1))
    except (ValueError, TypeError):
        limit = 1

    # 렌더 환경에서 링크 주소가 너무 길어지지 않게 토큰 길이 조절
    code = secrets.token_urlsafe(4)

    events[code] = {
        "title": title,
        "limit": limit,
        "participants": [],
        "winners": [],
        "closed": False
    }

    return jsonify({"success": True, "link": f"/event/{code}"})

# ---------------- 이벤트 목록 API ----------------
@app.route("/events")
def get_events():
    return jsonify(events)

# ---------------- 참가 페이지 ----------------
@app.route("/event/<code>")
def event(code):
    if code not in events:
        return """
        <div style="text-align:center; margin-top:50px; font-family:sans-serif;">
            <h2>❌ 존재하지 않거나 삭제된 이벤트입니다.</h2>
            <a href="/">홈으로 가기</a>
        </div>
        """

    ev = events[code]
    disabled_attr = "disabled" if ev["closed"] else ""
    placeholder_text = "이미 마감된 이벤트입니다." if ev["closed"] else "닉네임을 입력하세요"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>🎁 이벤트 참여</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; margin-top: 60px; background-color: #f8f9fa; }}
            .container {{ max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            input {{ padding: 12px; width: calc(100% - 26px); margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; }}
            button {{ padding: 12px; width: 100%; background-color: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: bold; cursor: pointer; }}
            button:disabled {{ background-color: #6c757d; cursor: not-allowed; }}
            #msg {{ font-weight: bold; margin-top: 15px; color: #28a745; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="margin-top:0;">🎁 이벤트 참여하기</h2>
            <h3 style="color: #007bff;">{ev['title']}</h3>
            <p style="color:#666;">당첨 인원: {ev['limit']}명</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            
            <input id="name" placeholder="{placeholder_text}" {disabled_attr}>
            <button id="btn-join" onclick="join()" {disabled_attr}>이벤트 응모하기</button>
            
            <p id="msg"></p>
        </div>

        <script>
        async function join() {{
            let nameInput = document.getElementById("name");
            let name = nameInput.value.trim();

            if (!name) {{
                alert("닉네임을 입력해주세요!");
                return;
            }

            let res = await fetch("/join/{code}", {{
                method:"POST",
                headers:{{"Content-Type":"application/json"}},
                body: JSON.stringify({{name}})
            }});

            let data = await res.json();
            let msgEl = document.getElementById("msg");
            msgEl.innerText = data.msg;

            if (data.success) {{
                msgEl.style.color = "#28a745";
                nameInput.value = ""; // 입력창 초기화
            }} else {{
                msgEl.style.color = "#dc3545";
            }}
        }}
        </script>
    </body>
    </html>
    """

# ---------------- 참가 처리 API ----------------
@app.route("/join/<code>", methods=["POST"])
def join(code):
    if code not in events:
        return jsonify({"success": False, "msg": "이벤트를 찾을 수 없습니다."})

    if events[code]["closed"]:
        return jsonify({"success": False, "msg": "이미 마감된 이벤트입니다."})

    data = request.get_json() or {}
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"success": False, "msg": "닉네임을 입력해주세요."})

    if name in events[code]["participants"]:
        return jsonify({"success": False, "msg": "이미 이 닉네임으로 참여하셨습니다."})

    events[code]["participants"].append(name)
    return jsonify({"success": True, "msg": "🎉 참여가 정상적으로 완료되었습니다!"})

# ---------------- 마감 & 자동 추첨 API ----------------
@app.route("/close/<code>", methods=["POST"])
def close(code):
    if code not in events:
        return jsonify({"msg": "존재하지 않는 이벤트입니다."}), 404

    event_data = events[code]
    if event_data["closed"]:
        return jsonify({"msg": "이미 마감된 이벤트입니다."})

    event_data["closed"] = True
    participants = event_data["participants"]
    limit = event_data["limit"]

    if len(participants) == 0:
        event_data["winners"] = []
        return jsonify({"msg": "참가자가 아무도 없어 추첨 없이 마감되었습니다."})

    # 랜덤 추첨 (참여자 수가 제한보다 적으면 참여자 전원 당첨)
    event_data["winners"] = random.sample(
        participants,
        min(limit, len(participants))
    )

    return jsonify({"msg": "🎰 마감 및 당첨자 추첨이 완료되었습니다!"})

# ---------------- 이벤트 삭제 API ----------------
@app.route("/delete/<code>", methods=["DELETE"])
def delete_event(code):
    if code in events:
        del events[code]
        return jsonify({"msg": "🗑️ 이벤트가 목록에서 안전하게 삭제되었습니다."})
    return jsonify({"msg": "이벤트를 찾을 수 없습니다."}), 404

# 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from openai import OpenAI
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from collections import defaultdict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# .env 파일에서 환경 변수를 읽어옵니다.
api_key = os.getenv("api_key")
host = os.getenv("host")
user = os.getenv("user")
password = os.getenv("password")
db = os.getenv("db")
assistant_id = os.getenv("assistant_id")

app = Flask(__name__)
CORS(app)  # 모든 출처에서의 요청을 허용합니다.

# OpenAI API 키 설정
client = OpenAI(api_key=api_key)



# 제한할 요청 수
REQUEST_LIMIT = 10  # 테스트 목적으로 1로 설정 (원래는 10개)

# IP 주소별 요청 횟수를 저장하는 사전
request_counts = defaultdict(lambda: {'count': 0, 'last_request': None, 'false_count': 0})

# IP 주소별 스레드 ID를 저장하는 사전
thread_ids = {}

def reset_request_count(ip):
    request_counts[ip]['count'] = 0
    request_counts[ip]['last_request'] = datetime.now()
    request_counts[ip]['false_count'] = 0

def is_new_day(last_request):
    return datetime.now() - last_request > timedelta(days=1)  # 테스트 목적으로 5초로 설정 (원래는 days=1)

# MySQL 데이터베이스 연결 설정 함수
def get_database_connection():
    return pymysql.connect(host=host, user=user , password=password, db=db, charset="utf8mb4")

# 새로운 스레드 생성 함수
def create_new_thread():
    response = client.beta.threads.create()
    # response의 구조를 출력해보자
    print(response)
    # response 객체의 속성에 맞게 접근
    return response.id

# AI 응답을 가져오는 함수
def get_ai_response(user_input, thread_id):
    try:
        assistant_id

        message = client.beta.threads.messages.create(
            thread_id,
            role="user",
            content=user_input,
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        run_id = run.id

        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id,
            )
            if run.status == "completed":
                break
            else:
                time.sleep(2)

        thread_messages = client.beta.threads.messages.list(thread_id)
        ai_response = thread_messages.data[0].content[0].text.value

        return ai_response

    except Exception as e:
        return str(e)

# sendMessage 라우터
@app.route('/sendMessage', methods=['POST'])
def send_message():
    data = request.get_json()
    user_input = data.get('user_input')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]

    # 요청 횟수 가져오기
    request_data = request_counts[ip]
    count = request_data['count']
    last_request = request_data['last_request']
    false_count = request_data['false_count']

    # 하루가 지났는지 확인하여 요청 횟수 초기화
    if last_request is None or is_new_day(last_request):
        reset_request_count(ip)

    # false_count가 3 이상이면 차단
    if false_count >= 3:
        return jsonify({"description": "너무 많은 잘못된 응답으로 인해 차단되었습니다."})


    # 요청 횟수 확인
    if count >= REQUEST_LIMIT:
        return jsonify({"description": "질문이 초과했습니다ㅠㅠ"})


    # 요청 횟수 증가
    request_counts[ip]['count'] += 1
    request_counts[ip]['last_request'] = datetime.now()

    # IP 주소별 스레드 ID 가져오기
    if ip not in thread_ids:
        thread_id = create_new_thread()
        thread_ids[ip] = thread_id
    else:
        thread_id = thread_ids[ip]

    # AI 응답 가져오기
    ai_response = get_ai_response(user_input, thread_id)

    # 'False' 응답 횟수 증가
    if ai_response.strip().lower() == 'false':
        request_counts[ip]['false_count'] += 1

    # 데이터베이스에 저장
    try:
        db_connection = get_database_connection()
        cursor = db_connection.cursor()
        query = "INSERT INTO portpolio.portpolio_input (ip, comments, answer) VALUES (%s, %s, %s)"
        cursor.execute(query, (str(ip), user_input, ai_response))
        db_connection.commit()
        return jsonify({"description": ai_response})

    except Exception as e:
        return jsonify({"description": "데이터 저장 중 오류가 발생하였습니다: " + str(e)})

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

        if 'db_connection' in locals() and db_connection:
            db_connection.close()


if __name__ == '__main__':
    print("Flask 애플리케이션이 실행되었습니다.")
    app.run(prot=5000, debug=True)

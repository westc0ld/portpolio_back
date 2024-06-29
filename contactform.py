from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# .env 파일 로드
load_dotenv()

# .env 파일에서 환경 변수 읽어오기
host = os.getenv("host")
user = os.getenv("user")
password = os.getenv("password")
db = os.getenv("db")

# MySQL 데이터베이스 연결 설정 함수
def get_database_connection():
    return pymysql.connect(host=host, user=user, password=password, database=db, charset='utf8mb4')

# 이메일 전송 및 데이터베이스 저장 엔드포인트
@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        # 클라이언트로부터 전송된 JSON 데이터 추출
        data = request.json
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        message = data.get('message')

        # MySQL 데이터베이스에 연결
        db_connection = get_database_connection()
        cursor = db_connection.cursor()

        # 데이터베이스에 데이터 삽입
        insert_query = "INSERT INTO contactform (name, email, phone, message) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (name, email, phone, message))
        db_connection.commit()

        return jsonify({"message": "이메일 전송 및 데이터 저장이 성공적으로 완료되었습니다."})

    except Exception as e:
        return jsonify({"error": "데이터 저장 중 오류가 발생하였습니다: " + str(e)})

    finally:
        # 리소스 정리
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()

if __name__ == '__main__':
    app.run(debug=True)

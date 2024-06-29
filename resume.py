from flask import Flask, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 정적 파일 경로 설정 (예시로 static 폴더 사용)
app.config['UPLOAD_FOLDER'] = 'static'

# 파일 다운로드 API 엔드포인트
@app.route('/download-resume', methods=['GET'])
def download_resume():
    try:
        filename = 'resume.pdf'  # 다운로드할 파일 이름
        return send_file(f"{app.config['UPLOAD_FOLDER']}/{filename}", as_attachment=True)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)

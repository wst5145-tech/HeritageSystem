import os
from flask import Flask, jsonify, request
import pymysql
from dotenv import load_dotenv

# 加载 .env 文件中的配置
load_dotenv()

app = Flask(__name__)

try:
    app.json.ensure_ascii = False
except Exception:
    app.config['JSON_AS_ASCII'] = False

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
   "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "heritage_db"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
    "connect_timeout": 10,
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

def fetch_all(sql, params=None):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params or [])
            return cursor.fetchall()
    finally:
        if conn:
            conn.close()

# 允许前端跨域访问
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/api/health", methods=["GET"])
def health():
    try:
        fetch_all("SELECT 1")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route("/api/all", methods=["GET"])
def get_all():
    try:
        data = fetch_all("SELECT * FROM heritage")
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "database error", "detail": str(e)}), 500

@app.route("/api/search", methods=["GET"])
def search():
    dynasty = request.args.get("dynasty", "").strip()
    h_type = request.args.get("heritage_type", "").strip()
    keyword = request.args.get("keyword", "").strip()
    sql = "SELECT * FROM heritage WHERE 1=1"
    params = []
    
    if dynasty:
        sql += " AND dynasty = %s"
        params.append(dynasty)
    if h_type:
        sql += " AND heritage_type = %s"
        params.append(h_type)
    if keyword:
        sql += " AND heritage_name LIKE %s"
        params.append(f"%{keyword}%")
        
    try:
        data = fetch_all(sql, params)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "database error", "detail": str(e)}), 500

@app.route("/api/meta", methods=["GET"])
def meta():
    heritage_types = ["古遗址", "古建筑", "古墓葬", "石窟寺", "文物保护遗迹"]
    try:
        rows = fetch_all("SELECT DISTINCT dynasty FROM heritage WHERE dynasty IS NOT NULL AND dynasty != '' ORDER BY dynasty")
        dynasties = [row["dynasty"] for row in rows]
        return jsonify({
            "heritage_types": heritage_types,
            "dynasties": dynasties
        })
    except Exception as e:
        return jsonify({"error": "database error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
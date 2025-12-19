from flask import Flask, request, jsonify
from flask_cors import CORS
from executor import run_code

app = Flask(__name__)
CORS(app)

@app.route('/execute', methods=['POST'])
def execute():
    code = request.json.get('code', '')
    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400
    
    return jsonify(run_code(code))

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
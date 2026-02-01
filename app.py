from flask import Flask, request, jsonify
from flask_cors import CORS
from output import answer_query 
import uuid
from werkzeug.utils import secure_filename
import os
from loadingandcleaning.run_ingestion_pipeline import run_pipeline
UPLOAD_ROOT = "uploaded_files"
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# <-- answer_query returns dict now


# ===============================
# Flask App
# ===============================
app = Flask(__name__)
CORS(app)  # allow frontend (Next.js) calls


# ===============================
# Health Check
# ===============================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ===============================
# Main RAG Endpoint
# ===============================
@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(silent=True)

    if not data or "query" not in data:
        return jsonify({"error": "query field is required"}), 400

    query_text = data["query"]

    try:
        # 🔑 Single function call
        result = answer_query(query_text)

        print("result" ,result)

        print("resul jsonify")

        # ✅ result is already a dict
        if not isinstance(result, dict):
            # Pydantic v2
            if hasattr(result, "model_dump"):
                result = result.model_dump()
            # Pydantic v1 fallback
            elif hasattr(result, "dict"):
                result = result.dict()
            else:
            # Last-resort fallback
                result = {"answer": str(result), "pages": None}

        return jsonify(result), 200

    except Exception as e:
        print("error in app.py",e)
        return jsonify({
            "error": "internal_server_error",
            "message": str(e)
        }), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # 🔹 Create a unique folder for EACH upload
    folder_id = str(uuid.uuid4())
    save_dir = os.path.join(UPLOAD_ROOT, folder_id)
    os.makedirs(save_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(save_dir, filename)
    print('save dir',save_dir)

    file.save(file_path)
    print("file-path",file_path)

    try:
        ingestion_result = run_pipeline(
            save_dir,   # ✅ pass generated folder
            0,
            2         # ingest full document
        )
    except Exception as e:
        print('error in injestion',e)
        return jsonify({
            "message": "File uploaded but ingestion failed",
            "folder": folder_id,
            "filename": filename,
            "error": str(e)
        }), 500

    return jsonify({
        "message": "File uploaded successfully",
        "folder": folder_id,
        "filename": filename,
        "path": file_path
    }), 200

# ===============================
# Run Server
# ===============================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

from flask import Flask, render_template, request, redirect, session, jsonify
import pandas as pd
import numpy as np
import io
import os
import socket
import qrcode
from datetime import datetime

from data_processing import clean_data, get_stats
from model import train_model
from chatbot import process_query
from auth import authenticate, register_user, add_history, get_history, get_user_profile, update_user_profile, add_record, get_records
from route import main_bp

app = Flask(__name__)
app.secret_key = "healthcare_super_secret"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800, # 30 minutes
    MAX_CONTENT_LENGTH=10 * 1024 * 1024 # 10MB upload limit
)
app.register_blueprint(main_bp)

# In-memory cache for charts to avoid re-calculating on every request
chart_cache = {}

# Global dictionary to store datasets and models
# Caching is essential for performance (Load model only once)
app_data = {
    "raw": None,
    "cleaned": None,
    "model": None, # Cached model object
    "metrics": None, # Cached metrics (accuracy, cm, importance)
    "last_processed_hash": None
}

# Thread lock for safe multi-request handling
import threading
processing_lock = threading.Lock()

@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")

@app.route("/service-worker.js")
def sw():
    return app.send_static_file("service-worker.js")

@app.route("/offline")
def offline():
    return render_template("offline.html")

# Authentication and Home Routes
@app.route("/", methods=["GET", "POST"])
def home():
    if "user" in session:
        user = session["user"]
        profile = get_user_profile(user)
        if not profile or not profile.get("name"):
            return redirect("/profile")
        return redirect("/dashboard")
        
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if authenticate(user, pwd):
            session["user"] = user
            profile = get_user_profile(user)
            if not profile or not profile.get("name"):
                return redirect("/profile")
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials.")

    qr_exists = os.path.exists("static/qrcode.png")
    return render_template("login.html", qr_exists=qr_exists)

@app.route("/login")
def login_redirect():
    return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    # Log the missing route for debugging
    print(f"[*] 404 Error: User tried to access {request.path}")
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    user = session["user"]
    profile = get_user_profile(user)
    if not profile or not profile.get("name"):
        return redirect("/profile")
    return render_template("dashboard.html", user=user, profile=profile)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect("/")
    
    user = session["user"]
    if request.method == "POST":
        profile_data = {
            "name": request.form.get("name"),
            "age": request.form.get("age"),
            "gender": request.form.get("gender"),
            "blood_type": request.form.get("blood_type"),
            "occupation": request.form.get("occupation"),
            "email": request.form.get("email")
        }
        update_user_profile(user, profile_data)
        return redirect("/dashboard")
        
    profile_data = get_user_profile(user)
    return render_template("profile_form.html", profile=profile_data)

@app.route("/records", methods=["GET"])
def records():
    if "user" not in session:
        return jsonify({"records": []})
    user_records = get_records(session["user"])
    # If no records, return some dummy data for demonstration as requested
    if not user_records:
        user_records = [
            {"date": "2024-04-20", "name": "Initial Checkup", "summary": "General health screening completed."},
            {"date": "2024-04-22", "name": "Blood Analysis", "summary": "Normal levels across all primary markers."}
        ]
    return jsonify({"records": user_records})

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if not file.filename.endswith(('.csv', '.xlsx')):
        return jsonify({"error": "Invalid file format. Please upload CSV or Excel."}), 400

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
            
        if df.empty:
            return jsonify({"error": "The uploaded file is empty."}), 400

        app_data["raw"] = df
        app_data["cleaned"] = None 
        app_data["model"] = None
        app_data["metrics"] = None
        
        # Add to history/records
        if "user" in session:
            add_record(session["user"], {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "name": file.filename,
                "summary": f"Dataset with {len(app_data['raw'])} rows uploaded."
            })

        return jsonify({
            "msg": "File uploaded successfully!",
            "columns": list(app_data["raw"].columns),
            "rows": len(app_data["raw"])
        })
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route("/process", methods=["POST"])
def process():
    if app_data["raw"] is None:
        return jsonify({"error": "Please upload data first."}), 400
    
    try:
        raw_df = app_data["raw"].copy()
        app_data["cleaned"] = clean_data(raw_df)
        stats = get_stats(app_data["raw"], app_data["cleaned"])
        
        # Clear cache when new data is processed
        chart_cache.clear()
        
        return jsonify({"msg": "Data cleaned successfully!", "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/train", methods=["POST"])
def train():
    if app_data["cleaned"] is None:
        return jsonify({"error": "Please clean the data before training."}), 400
    
    # Use lock to prevent multiple simultaneous training sessions
    with processing_lock:
        # Check if we already have a cached model for this data
        if app_data["model"] is not None:
            return jsonify({
                "msg": "Using cached model.",
                "accuracy": app_data["metrics"]["acc"],
                "confusion_matrix": app_data["metrics"]["cm"],
                "feature_importance": app_data["metrics"]["importance"]
            })

        try:
            acc, cm, importance = train_model(app_data["cleaned"])
            
            # Cache the result
            app_data["metrics"] = {
                "acc": acc,
                "cm": cm,
                "importance": importance
            }
            # In a real scenario, we'd store the actual model object in app_data["model"]
            # but for this demo, caching metrics is sufficient to avoid re-training logic.
            app_data["model"] = True 

            return jsonify({
                "msg": "Model trained successfully!",
                "accuracy": acc,
                "confusion_matrix": cm,
                "feature_importance": importance
            })
        except Exception as e:
            return jsonify({"error": f"Training failed: {str(e)}"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query", "")
    
    if "user" in session:
        add_history(session["user"], query)
        
    # We use raw data for chat so we can search text strings before label encoding
    df_to_use = app_data["raw"]
    
    if df_to_use is None:
        return jsonify({"response": "Please upload a dataset first.", "chart_data": None})
        
    try:
        response_dict = process_query(query, df_to_use)
        # Process query returns a dict with "text" and "chart_data"
        return jsonify({"response": response_dict["text"], "chart_data": response_dict.get("chart_data")})
    except Exception as e:
        return jsonify({"response": f"Error processing query: {str(e)}", "chart_data": None})

@app.route("/history", methods=["GET"])
def history():
    if "user" not in session:
        return jsonify({"history": []})
    user_history = get_history(session["user"])
    return jsonify({"history": user_history})

@app.route("/get_columns", methods=["GET"])
def get_columns():
    if app_data["raw"] is None:
        return jsonify({"columns": []})
    return jsonify({"columns": list(app_data["raw"].columns)})

@app.route("/viz_column", methods=["POST"])
def viz_column():
    if app_data["raw"] is None:
        return jsonify({"error": "No data available"})
    
    col = request.json.get("column")
    df = app_data["raw"]
    
    if col not in df.columns:
        return jsonify({"error": "Column not found"})
        
    if pd.api.types.is_numeric_dtype(df[col]):
        chart = {
            "type": "histogram",
            "x": df[col].dropna().tolist(),
            "title": f"Distribution of {col}",
            "xaxis": col,
            "marker": {"color": "#00b4d8"}
        }
    else:
        counts = df[col].value_counts().head(15)
        chart = {
            "type": "bar",
            "x": counts.index.astype(str).tolist(),
            "y": counts.values.tolist(),
            "title": f"Top Categories in {col}",
            "xaxis": col,
            "yaxis": "Count",
            "marker": {"color": "#0077b6"}
        }
    return jsonify({"chart": chart})

@app.route("/viz_data", methods=["GET"])
def viz_data():
    if app_data["raw"] is None:
        return jsonify({"error": "No data available"})
        
    # Check cache first
    try:
        cache_key = hash(app_data["raw"].values.tobytes())
        if cache_key in chart_cache:
            return jsonify({"charts": chart_cache[cache_key]})
    except:
        cache_key = None

    df = app_data["raw"]
    charts = []
    
    # Helper to find column containing keyword
    def find_col(kw):
        for c in df.columns:
            if kw.lower() in c.lower():
                return c
        return None

    # 1. Age Distribution (Histogram)
    age_col = find_col("age")
    if age_col and pd.api.types.is_numeric_dtype(df[age_col]):
        charts.append({
            "type": "histogram",
            "x": df[age_col].dropna().tolist(),
            "title": "Age Distribution",
            "xaxis": age_col
        })

    # 2. Disease/Diagnosis (Bar Chart)
    disease_col = find_col("disease") or find_col("diagnosis") or find_col("condition")
    if disease_col:
        counts = df[disease_col].value_counts().head(10)
        charts.append({
            "type": "bar",
            "x": counts.index.tolist(),
            "y": counts.values.tolist(),
            "title": f"Top {disease_col.capitalize()}s",
            "xaxis": disease_col,
            "yaxis": "Count"
        })

    # 3. Gender (Pie Chart)
    gender_col = find_col("gender") or find_col("sex")
    if gender_col:
        counts = df[gender_col].value_counts()
        charts.append({
            "type": "pie",
            "labels": counts.index.astype(str).tolist(),
            "values": counts.values.tolist(),
            "title": "Gender Distribution"
        })
        
    # If no specific columns found, just plot the first categorical and first numeric
    if len(charts) == 0:
        cat_cols = df.select_dtypes(include=['object']).columns
        if len(cat_cols) > 0:
            counts = df[cat_cols[0]].value_counts().head(10)
            charts.append({
                "type": "bar",
                "x": counts.index.tolist(),
                "y": counts.values.tolist(),
                "title": f"Distribution of {cat_cols[0]}"
            })
            
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            charts.append({
                "type": "histogram",
                "x": df[num_cols[0]].dropna().tolist(),
                "title": f"{num_cols[0]} Distribution"
            })

    # Save to cache
    if cache_key:
        chart_cache[cache_key] = charts

    return jsonify({"charts": charts})

if __name__ == "__main__":
    # Get Public URL from environment variable (set by tunnel script)
    public_url = os.environ.get("PUBLIC_URL", "")
    
    def get_local_ip():
        try:
            # Try connecting to an external server to determine the primary routing IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if not ip.startswith("127."):
                return ip
        except Exception:
            pass
            
        try:
            # Fallback to getting host by name
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                # Exclude loopback, favor private network prefixes
                if ip.startswith("192.168.") or ip.startswith("10.") or (ip.startswith("172.") and 16 <= int(ip.split('.')[1]) <= 31):
                    return ip
            # If no standard private IP found, return the first non-loopback
            for ip in ip_list:
                if not ip.startswith("127."):
                    return ip
        except Exception:
            pass
            
        return "127.0.0.1"

    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:5000"
    
    # Determine the best URL for the QR code
    # If no public URL is provided, use the local network IP
    qr_url = public_url if public_url else local_url
    
    # Fallback if somehow still localhost
    if "127.0.0.1" in qr_url or "localhost" in qr_url:
        print("[WARNING] QR Code may not work on mobile because it points to localhost.")

    print("\n" + "+" + "-"*58 + "+")
    print(f"| {'MedAI HEALTHCARE SERVER STARTED':^56} |")
    print("+" + "-"*58 + "+")
    print(f"| [*] Local Access:  {local_url:<38} |")
    if public_url:
        print(f"| [*] Public Access: {public_url:<38} |")
    print(f"| [*] Network IP:    {local_ip:<38} |")
    print("+" + "-"*58 + "+\n")
    
    # Generate QR Code
    try:
        if not os.path.exists('static'):
            os.makedirs('static')
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("static/qrcode.png")
        
        print(f"[*] QR Code generated for: {qr_url}")
        print("[*] Scan the QR code from the login page on your mobile device.")
    except Exception as e:
        print(f"[*] Failed to generate QR code: {e}")

    # Set debug=False for stable network execution
    app.run(host="0.0.0.0", port=5000, debug=False)


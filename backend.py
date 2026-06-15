import os
import json
from flask import Flask, render_template, jsonify, request, session
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='.')
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-gallery-key-123987")

LOCAL_MEDIA_FOLDER = "static/local_media"
DB_FILE_PATH = "users_cache.json"

# Load persistent users from local storage cache to prevent re-registration requirement
if os.path.exists(DB_FILE_PATH):
    try:
        with open(DB_FILE_PATH, 'r') as f:
            USER_DB = json.load(f)
    except Exception:
        USER_DB = {}
else:
    USER_DB = {}

if not os.path.exists(LOCAL_MEDIA_FOLDER):
    os.makedirs(LOCAL_MEDIA_FOLDER)

def save_user_db():
    """Writes user credential registrations to disk securely."""
    try:
        with open(DB_FILE_PATH, 'w') as f:
            json.dump(USER_DB, f)
    except Exception as e:
        print(f"Error saving user data checkpoint: {e}")

def get_media_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in {'mp4', 'mov', 'avi'}:
        return "video"
    return "image"

def init_user_cloudinary():
    """Applies the global system environment Cloudinary configuration directly."""
    if os.getenv("CLOUDINARY_CLOUD_NAME"):
        cloudinary.config(
            cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key = os.getenv("CLOUDINARY_API_KEY"),
            api_secret = os.getenv("CLOUDINARY_API_SECRET"),
            secure = True
        )
        return True
    return False

# --- AUTHENTICATION API ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not all([username, password]):
        return jsonify({"success": False, "error": "Username and password are required for registration."}), 400
        
    if username in USER_DB:
        return jsonify({"success": False, "error": "Username already exists. Please Sign In instead."}), 400
        
    # Save user records persistently
    USER_DB[username] = {
        "password": password
    }
    save_user_db()
    
    session['user'] = username
    return jsonify({"success": True, "username": username})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username in USER_DB and USER_DB[username]['password'] == password:
        session['user'] = username
        return jsonify({"success": True, "username": username})
        
    return jsonify({"success": False, "error": "Invalid username or password"}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"success": True})

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    if 'user' in session and (session['user'] in USER_DB or os.getenv("CLOUDINARY_CLOUD_NAME")):
        return jsonify({"authenticated": True, "username": session['user']})
    return jsonify({"authenticated": False})

# --- BACKEND API ROUTES (PROTECTED) ---

@app.route('/api/media', methods=['GET'])
def get_media():
    if 'user' not in session or not init_user_cloudinary():
        return jsonify({"success": False, "error": "Unauthorized Access"}), 401
        
    current_user = session['user']
    try:
        grouped_media = {}
        
        def process_resources(resources, res_type):
            for asset in resources:
                full_folder_path = asset.get('folder', '')
                if not full_folder_path and '/' in asset['public_id']:
                    full_folder_path = asset['public_id'].rsplit('/', 1)[0]
                
                # Enforce strict ownership: user can only see items under their username prefix folder
                if not full_folder_path or not full_folder_path.startswith(f"{current_user}/"):
                    continue
                    
                # Extract clean user folder name by stripping out the 'username/' prefix
                display_folder = full_folder_path.split(f"{current_user}/", 1)[1]
                if not display_folder:
                    display_folder = "General"
                    
                if display_folder not in grouped_media:
                    grouped_media[display_folder] = []
                    
                grouped_media[display_folder].append({
                    "url": asset['secure_url'],
                    "type": res_type,
                    "resolution": f"{asset.get('width', 'N/A')}x{asset.get('height', 'N/A')}",
                    "created_at": asset['created_at'],
                    "public_id": asset['public_id']
                })

        # Fetch limited list of assets and sort/filter on incoming structures
        img_res = cloudinary.api.resources(resource_type="image", max_results=100, type="upload", prefix=f"{current_user}/")
        process_resources(img_res.get('resources', []), "image")
        
        vid_res = cloudinary.api.resources(resource_type="video", max_results=100, type="upload", prefix=f"{current_user}/")
        process_resources(vid_res.get('resources', []), "video")
        
        for folder in grouped_media:
            grouped_media[folder].sort(key=lambda x: x['created_at'], reverse=True)
            
        return jsonify({"success": True, "folders": grouped_media})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_media():
    if 'user' not in session or not init_user_cloudinary():
        return jsonify({"success": False, "error": "Unauthorized Access"}), 401
        
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file selected"}), 400
        
    file = request.files['file']
    folder = request.form.get('folder', 'General').strip()
    current_user = session['user']
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400

    if file:
        resource_type = get_media_type(file.filename)
        # Sandbox target folders directly into specific active user folders
        scoped_folder = f"{current_user}/{folder}"
        try:
            upload_result = cloudinary.uploader.upload(
                file, 
                folder=scoped_folder,
                resource_type=resource_type
            )
            return jsonify({
                "success": True,
                "folder": folder,
                "media": {
                    "url": upload_result['secure_url'],
                    "type": resource_type,
                    "resolution": f"{upload_result.get('width', 'N/A')}x{upload_result.get('height', 'N/A')}"
                }
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/media/delete', methods=['POST'])
def delete_media_item():
    if 'user' not in session or not init_user_cloudinary():
        return jsonify({"success": False, "error": "Unauthorized Access"}), 401
        
    data = request.get_json() or {}
    public_id = data.get('public_id', '').strip()
    res_type = data.get('type', 'image').strip()
    current_user = session['user']
    
    if not public_id:
        return jsonify({"success": False, "error": "Missing target asset tracking token parameters"}), 400
        
    # Enforce deletion boundaries: item public_id must begin with user namespace prefix
    if not public_id.startswith(f"{current_user}/"):
        return jsonify({"success": False, "error": "Unauthorized asset modification operation block."}), 403
        
    try:
        cloudinary.uploader.destroy(public_id, resource_type=res_type)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/folder/delete', methods=['POST'])
def delete_folder():
    if 'user' not in session or not init_user_cloudinary():
        return jsonify({"success": False, "error": "Unauthorized Access"}), 401
        
    data = request.get_json() or {}
    folder_name = data.get('folder', '').strip()
    current_user = session['user']
    
    if not folder_name:
        return jsonify({"success": False, "error": "Missing folder target info"}), 400
        
    scoped_prefix = f"{current_user}/{folder_name}"
    try:
        cloudinary.api.delete_resources_by_prefix(prefix=f"{scoped_prefix}/")
        try:
            cloudinary.api.delete_folder(folder=scoped_prefix)
        except Exception:
            pass
            
        return jsonify({"success": True, "deleted": folder_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
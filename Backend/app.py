import os
import time

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)

from functools import wraps
import importlib.util
import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

# Define fallback implementations
def init_cloudinary():
    pass

def upload_media_file(file, user, tag):
    return {"error": "Media service unavailable"}

def delete_media_file(public_id, resource_type="image"):
    return {"error": "Media service unavailable"}

def get_media_resources(user):
    return {"resources": []}

# Try to import from services
try:
    service_path = os.path.join(
        os.path.dirname(__file__),
        "services",
        "cloudinary_service.py"
    )
    
    if os.path.isfile(service_path):
        spec = importlib.util.spec_from_file_location(
            "cloudinary_service",
            service_path
        )
        service_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(service_module)
        init_cloudinary = service_module.init_cloudinary
        upload_media_file = service_module.upload_media_file
        delete_media_file = service_module.delete_media_file
        get_media_resources = service_module.get_media_resources
except (ImportError, AttributeError):
    service_path = os.path.join(
        os.path.dirname(__file__),
        "services",
        "cloudinary_service.py"
    )

    if os.path.isfile(service_path):
        spec = importlib.util.spec_from_file_location(
            "cloudinary_service",
            service_path
        )
        service_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(service_module)
        init_cloudinary = service_module.init_cloudinary
        upload_media_file = service_module.upload_media_file
        delete_media_file = service_module.delete_media_file
        get_media_resources = service_module.get_media_resources


load_dotenv()


app = Flask(__name__)


app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "change_this_secret_key"
)


# In-memory user registry
USERS_DB = {}


# Initialize Cloudinary
init_cloudinary()



# ---------------- AUTH CHECK ----------------

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'user' not in session:

            if request.is_json or request.path.startswith('/api/'):

                return jsonify({
                    "error":
                    "Unauthorized endpoint access."
                }), 401


            return redirect("/")

        return f(*args, **kwargs)

    return decorated_function



# ---------------- AUTH APIs ----------------


@app.route('/api/register', methods=['POST'])
def register():

    data = request.get_json() or {}

    username = data.get(
        'username',
        ''
    ).strip()

    password = data.get(
        'password',
        ''
    ).strip()


    if not username or not password:

        return jsonify({
            "success": False,
            "message":
            "Username and password required."
        }),400


    if username in USERS_DB:

        return jsonify({
            "success": False,
            "message":
            "User already exists."
        }),400


    USERS_DB[username] = password


    session['user'] = username


    return jsonify({
        "success": True,
        "message":
        "Registration successful."
    })




@app.route('/api/login', methods=['POST'])
def login():

    data = request.get_json() or {}

    username = data.get(
        'username',
        ''
    ).strip()


    password = data.get(
        'password',
        ''
    ).strip()



    if (
        username in USERS_DB
        and
        USERS_DB[username] == password
    ):

        session['user'] = username


        return jsonify({
            "success": True,
            "message":
            "Login successful."
        })


    return jsonify({
        "success": False,
        "message":
        "Invalid credentials."
    }),401




@app.route('/logout')
def logout():

    session.pop(
        'user',
        None
    )

    return redirect('/')

# ---------------- PAGE ROUTES ----------------


@app.route("/")
@login_required
def index():

    return render_template(
        "index.html"
    )



@app.route("/home")
@login_required
def home_page():

    return render_template(
        "home.html"
    )



@app.route("/contact")
@login_required
def contact_page():

    return render_template(
        "contact.html"
    )





# ---------------- MEDIA API ----------------


@app.route(
    "/api/media",
    methods=["GET"]
)
@login_required
def get_media():

    try:

        current_user = session.get(
            "user"
        )


        resources = get_media_resources(
            current_user
        )


        return jsonify(
            resources
        )


    except Exception as e:


        return jsonify(
            {
                "error": str(e)
            }
        ),500





@app.route(
    "/api/upload",
    methods=["POST"]
)
@login_required
def upload_media():


    if "file" not in request.files:

        return jsonify(
            {
                "error":
                "No file found"
            }
        ),400



    file = request.files["file"]


    tag = request.form.get(
        "tag",
        "General"
    )


    if file.filename == "":

        return jsonify(
            {
                "error":
                "No selected file"
            }
        ),400



    current_user = session.get(
        "user"
    )


    result = upload_media_file(
        file,
        current_user,
        tag
    )


    return jsonify(
        result
    )





@app.route(
    "/api/delete-asset",
    methods=["POST"]
)

@login_required
def delete_asset():


    data = request.get_json() or {}


    public_id = data.get(
        "public_id"
    )


    resource_type = data.get(
        "resource_type",
        "image"
    )


    if not public_id:


        return jsonify(
            {
                "error":
                "Missing asset id"
            }
        ),400




    result = delete_media_file(
        public_id,
        resource_type
    )


    return jsonify(
        result
    )





# ---------------- RUN APP ----------------


if __name__ == "__main__":


    app.run(
        debug=True
    )
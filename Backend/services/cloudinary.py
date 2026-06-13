import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

try:
    # Import via importlib to avoid static import errors in editors/environments
    # where python-dotenv is not installed.
    import importlib

    load_dotenv = importlib.import_module("dotenv").load_dotenv
except Exception:
    # If python-dotenv isn't available, provide a no-op fallback so the
    # module can still be imported (useful in some editors).
    def load_dotenv():
        return False


load_dotenv()



# ---------------- CLOUDINARY CONFIG ----------------

def init_cloudinary():

    cloudinary.config(

        cloud_name=os.getenv(
            "CLOUDINARY_CLOUD_NAME"
        ),

        api_key=os.getenv(
            "CLOUDINARY_API_KEY"
        ),

        api_secret=os.getenv(
            "CLOUDINARY_API_SECRET"
        ),

        secure=True
    )





# ---------------- UPLOAD FUNCTION ----------------


def upload_media_file(
        file,
        username,
        folder
):

    filename = file.filename.lower()


    if filename.endswith(
        (
            ".mp4",
            ".mov",
            ".avi",
            ".mkv"
        )
    ):

        resource_type = "video"

    else:

        resource_type = "image"



    user_tag = (
        f"{username}___{folder}"
    )



    try:


        result = cloudinary.uploader.upload(

            file,

            resource_type=resource_type,

            tags=[
                user_tag
            ]

        )


        return {

            "success": True,

            "url":
            result.get(
                "secure_url"
            ),

            "type":
            resource_type,

            "resolution":
            f"{result.get('width','N/A')}x{result.get('height','N/A')}"

        }



    except Exception as e:


        return {

            "success": False,

            "error":
            str(e)

        }





# ---------------- GET MEDIA ----------------


def get_media_resources(username):


    media_list = []


    prefix = (
        f"{username}___"
    )


    # images

    images = cloudinary.api.resources(

        resource_type="image",

        max_results=100,

        tags=True

    )


    for img in images.get(
        "resources",
        []
    ):


        tags = img.get(
            "tags",
            []
        )


        if not tags:
            continue


        tag = tags[0]


        if not tag.startswith(
            prefix
        ):
            continue



        folder = tag.replace(
            prefix,
            "",
            1
        )



        media_list.append({

            "public_id":
            img["public_id"],


            "url":
            img["secure_url"],


            "type":
            "image",


            "resolution":
            f"{img.get('width','N/A')}x{img.get('height','N/A')}",


            "folder_id":
            folder,


            "created_at":
            img["created_at"]

        })




    # videos

    videos = cloudinary.api.resources(

        resource_type="video",

        max_results=100,

        tags=True

    )



    for vid in videos.get(
        "resources",
        []
    ):


        tags = vid.get(
            "tags",
            []
        )


        if not tags:
            continue


        tag = tags[0]



        if not tag.startswith(
            prefix
        ):
            continue



        folder = tag.replace(
            prefix,
            "",
            1
        )



        media_list.append({

            "public_id":
            vid["public_id"],


            "url":
            vid["secure_url"],


            "type":
            "video",


            "resolution":
            f"{vid.get('width','N/A')}x{vid.get('height','N/A')}",


            "folder_id":
            folder,


            "created_at":
            vid["created_at"]

        })



    media_list.sort(

        key=lambda x:
        x["created_at"],

        reverse=True

    )


    return media_list





# ---------------- DELETE FUNCTION ----------------


def delete_media_file(
        public_id,
        resource_type="image"
):


    try:


        cloudinary.uploader.destroy(

            public_id,

            resource_type=
            resource_type

        )


        return {

            "success":
            True

        }



    except Exception as e:


        return {

            "success":
            False,

            "error":
            str(e)

        }
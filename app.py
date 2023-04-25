import json
import os
import zipfile
from functools import wraps

import cachecontrol as cachecontrol
import cv2
import easyocr
import google
import matplotlib.pyplot as plt
import numpy as np
import requests
import tensorflow as tf
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    session,
    abort,
    redirect,
    request,
    jsonify,
    send_file,
)
from google.oauth2 import id_token

from classes.User import User, db
from google_auth import get_flow

load_dotenv(".env")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

app = Flask(__name__)
app.secret_key = json.load(open("client_secret.json", "r"))["web"]["client_secret"]

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mariadb+mariadbconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
db.init_app(app)

flow, GOOGLE_CLIENT_ID = get_flow()

plate_model = tf.keras.models.load_model("models/plate.h5")
vehicle_model = tf.keras.models.load_model("models/vehicle.h5")


def login_is_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect("/login")
        else:
            return f()

    return wrapper


@app.route("/")
def home():  # put application's code here
    return render_template("index.html")


@app.route("/scan")
@login_is_required
def scan():
    return render_template("scan.html")


@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["POST"])
def register():
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = google.oauth2.id_token.verify_oauth2_token(
        id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID
    )

    # Check if user already exists
    user = User.query.filter_by(google_id=id_info["sub"]).first()
    if user is not None:
        return redirect("/")
    else:
        # Add the user to the database
        User.create_user(
            google_id=id_info["sub"],
            name=id_info["name"],
            email=id_info["email"],
            picture=id_info["picture"],
        )

    return redirect("/")


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = google.oauth2.id_token.verify_oauth2_token(
        id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info["sub"]

    # Verify if the user exists in the database
    user = User.query.filter_by(google_id=session["google_id"]).first()

    if user is None:
        # Present a privacy policy and ask for consent
        return render_template("privacy.html")
    else:
        # Log the user in
        return redirect("/")


@app.route("/download")
@login_is_required
def download():
    # Create a zip file
    with zipfile.ZipFile("images.zip", "w") as zip_file:
        # Write each file in the images directory to the zip file
        for filename in os.listdir("images"):
            zip_file.write(os.path.join("images", filename))

    # Send the zip file to the user
    response = send_file("images.zip", as_attachment=True)

    # Delete the zip file
    os.remove("images.zip")

    return response


@app.route("/predict", methods=["POST", "GET"])
@login_is_required
def predict():
    # Get the image from the request
    image = request.files["image"].read()

    # Convert the image to a numpy array
    image = np.frombuffer(image, np.uint8)

    # Create a copy of the image
    image_copy = image.copy()

    # Decode the image using the TIFF flag
    image = cv2.imdecode(
        image, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
    )

    # Get the number of files in the images folder excluding the CSV file
    num_files = len([file for file in os.listdir("images") if file.endswith(".tiff")])

    # Save the image to disk with incremented file name
    cv2.imwrite(f"images/image_{num_files + 1}.tiff", image)

    # Resize the image to (224, 224)
    image = cv2.resize(image, (224, 224))

    # Normalize the image
    image = image / 255.0

    # Remove the alpha channel if the image has it
    if image.shape[-1] == 4:
        image = image[..., :3]

    # Make a prediction with the model
    vehicle_prediction = vehicle_model.predict(image[np.newaxis, ...])
    xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = vehicle_prediction[0]
    xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = (
        xmin_vehicle * image.shape[1],
        ymin_vehicle * image.shape[0],
        xmax_vehicle * image.shape[1],
        ymax_vehicle * image.shape[0],
    )
    xmin_vehicle, ymin_vehicle, xmax_vehicle, ymax_vehicle = (
        int(xmin_vehicle),
        int(ymin_vehicle),
        int(xmax_vehicle),
        int(ymax_vehicle),
    )

    plate_prediction = plate_model.predict(image[np.newaxis, ...])
    xmin_plate, ymin_plate, xmax_plate, ymax_plate = plate_prediction[0]
    xmin_plate, ymin_plate, xmax_plate, ymax_plate = (
        xmin_plate * image.shape[1],
        ymin_plate * image.shape[0],
        xmax_plate * image.shape[1],
        ymax_plate * image.shape[0],
    )
    xmin_plate, ymin_plate, xmax_plate, ymax_plate = (
        int(xmin_plate),
        int(xmin_plate),
        int(xmax_plate),
        int(ymax_plate),
    )

    # Create a CSV file with image name and prediction
    with open("images/data.csv", "a") as f:
        # Write the values to the CSV file
        f.write(
            f"image_{num_files + 1}.tiff,{xmin_plate},{ymin_plate},{xmax_plate},{ymax_plate},Plate\n",
        )
        f.write(
            f"image_{num_files + 1}.tiff,{xmin_vehicle},{ymin_vehicle},{xmax_vehicle},{ymax_vehicle},Vehicle\n"
        )

    image_copy = np.frombuffer(image_copy, np.uint8)
    image_copy = cv2.imdecode(
        image_copy, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH
    )
    image_copy = cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)
    # Get the coordinates of the plate
    xmin_roi, ymin_roi, xmax_roi, ymax_roi = plate_prediction[0]
    # Scale the coordinates according to the image size
    xmin_roi, ymin_roi, xmax_roi, ymax_roi = (
        xmin_roi * image_copy.shape[1],
        ymin_roi * image_copy.shape[0],
        xmax_roi * image_copy.shape[1],
        ymax_roi * image_copy.shape[0],
    )
    # Convert the coordinates to integers
    xmin_roi, ymin_roi, xmax_roi, ymax_roi = (
        int(xmin_roi),
        int(ymin_roi),
        int(xmax_roi),
        int(ymax_roi),
    )

    # Crop the image
    plate = image_copy[ymin_roi - 20: ymax_roi + 20, xmin_roi - 20: xmax_roi + 20]
    plt.imshow(cv2.cvtColor(plate, cv2.COLOR_BGR2RGB))
    plt.show()
    reader = easyocr.Reader(["en"])
    result = reader.readtext(plate, detail=0)

    most_rep = ''

    if len(result) > 0:
        for res in result:
            digit_count = sum(c.isdigit() for c in res)
            if digit_count > sum(c.isdigit() for c in most_rep):
                most_rep = res

    result = most_rep
    result = result.replace("-", " ")
    # Verify if the first three characters are digits
    if result[:3].isdigit():
        pass
    else:
        # Find which character is not a digit
        for i, char in enumerate(result[:3]):
            if not char.isdigit():
                # If the character is a 'i' or 'I' replace it with a '1'
                if char == "i" or char == "I":
                    result = result[:i] + "1" + result[i + 1:]
                # If the character is a 'o' or 'O' replace it with a '0'
                elif char == "o" or char == "O":
                    result = result[:i] + "0" + result[i + 1:]
                # If the character is a 's' or 'S' replace it with a '5'
                elif char == "s" or char == "S":
                    result = result[:i] + "5" + result[i + 1:]
                # If the character is a 'z' or 'Z' replace it with a '7'
                elif char == "z" or char == "Z":
                    result = result[:i] + "7" + result[i + 1:]
                # If the character is a 'q' or 'Q' replace it with a '9'
                elif char == "q" or char == "Q":
                    result = result[:i] + "9" + result[i + 1:]
                # If the character is a 'b' or 'B' replace it with a '8'
                elif char == "b" or char == "B":
                    result = result[:i] + "8" + result[i + 1:]
                # If the character is a 'g' or 'G' replace it with a '6'
                elif char == "g" or char == "G":
                    result = result[:i] + "6" + result[i + 1:]
                # If the character is a 't' or 'T' replace it with a '7'
                elif char == "t" or char == "T":
                    result = result[:i] + "7" + result[i + 1:]
                # If the character is a 'l' or 'L' replace it with a '1'
                elif char == "l" or char == "L":
                    result = result[:i] + "1" + result[i + 1:]
                # If the character is a 'e' or 'E' replace it with a '3'
                elif char == "e" or char == "E":
                    result = result[:i] + "3" + result[i + 1:]
                # If the character is a 'j' or 'J' replace it with a '1'
                elif char == "j" or char == "J":
                    result = result[:i] + "1" + result[i + 1:]
                # If the character is a 'p' or 'P' replace it with a '9'
                elif char == "p" or char == "P":
                    result = result[:i] + "9" + result[i + 1:]
    # Verify if the 5th and 6th characters are alpha or an alpha and a space
    if (result[4:6].isalpha()) or (result[4:6].isalpha() and result[5] == " "):
        pass
    else:
        # Find which character is not a character
        for i, char in enumerate(result[4:6]):
            # If the digit is a '0' replace it with a 'D'
            if char == "0":
                result = result[:i + 4] + "D" + result[i + 5:]
            # If the digit is a '1' replace it with a 'I'
            elif char == "1":
                result = result[:i + 4] + "I" + result[i + 5:]
            # If the digit is a '2' replace it with a 'Z'
            elif char == "2":
                result = result[:i + 4] + "Z" + result[i + 5:]
            # If the digit is a '3' replace it with a 'E'
            elif char == "3":
                result = result[:i + 4] + "E" + result[i + 5:]
            # If the digit is a '4' replace it with a 'A'
            elif char == "4":
                result = result[:i + 4] + "A" + result[i + 5:]
            # If the digit is a '5' replace it with a 'S'
            elif char == "5":
                result = result[:i + 4] + "S" + result[i + 5:]
            # If the digit is a '6' replace it with a 'G'
            elif char == "6":
                result = result[:i + 4] + "G" + result[i + 5:]
            # If the digit is a '7' replace it with a 'T'
            elif char == "7":
                result = result[:i + 4] + "T" + result[i + 5:]
            # If the digit is a '8' replace it with a 'B'
            elif char == "8":
                result = result[:i + 4] + "B" + result[i + 5:]
            # If the digit is a '9' replace it with a 'P'
            elif char == "9":
                result = result[:i + 4] + "P" + result[i + 5:]
    # Verify if the resultt of the characters are digits
    if result[6:].isdigit():
        pass
    else:
        # Find which character is not a digit
        for i, char in enumerate(result[:3]):
            if not char.isdigit():
                # If the character is a 'i' or 'I' replace it with a '1'
                if char == "i" or char == "I":
                    result = result[:i] + "1" + result[i + 1:]
                # If the character is a 'o' or 'O' replace it with a '0'
                elif char == "o" or char == "O":
                    result = result[:i] + "0" + result[i + 1:]
                # If the character is a 's' or 'S' replace it with a '5'
                elif char == "s" or char == "S":
                    result = result[:i] + "5" + result[i + 1:]
                # If the character is a 'z' or 'Z' replace it with a '2'
                elif char == "z" or char == "Z":
                    result = result[:i] + "2" + result[i + 1:]
                # If the character is a 'q' or 'Q' replace it with a '9'
                elif char == "q" or char == "Q":
                    result = result[:i] + "9" + result[i + 1:]
                # If the character is a 'b' or 'B' replace it with a '8'
                elif char == "b" or char == "B":
                    result = result[:i] + "8" + result[i + 1:]
                # If the character is a 'g' or 'G' replace it with a '6'
                elif char == "g" or char == "G":
                    result = result[:i] + "6" + result[i + 1:]
                # If the character is a 't' or 'T' replace it with a '7'
                elif char == "t" or char == "T":
                    result = result[:i] + "7" + result[i + 1:]
                # If the character is a 'l' or 'L' replace it with a '1'
                elif char == "l" or char == "L":
                    result = result[:i] + "1" + result[i + 1:]
                # If the character is a 'e' or 'E' replace it with a '3'
                elif char == "e" or char == "E":
                    result = result[:i] + "3" + result[i + 1:]
                # If the character is a 'j' or 'J' replace it with a '1'
                elif char == "j" or char == "J":
                    result = result[:i] + "1" + result[i + 1:]
                # If the character is a 'p' or 'P' replace it with a '9'
                elif char == "p" or char == "P":
                    result = result[:i] + "9" + result[i + 1:]
    formatted_plate = "{}-{}-{}".format(result[:3], result[4:5], result[6:])
    formatted_plate = formatted_plate.replace(" ", "")
    formatted_plate = formatted_plate.upper()
    response = {
        "plate": plate_prediction.tolist(),
        "vehicle": vehicle_prediction.tolist(),
        "license_plate": formatted_plate,
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)

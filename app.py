import os
import zipfile

import cv2
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

model = tf.keras.models.load_model('models/vehicle_classification_2022-12-24_14-34-13.h5')


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')


@app.route('/scan')
def scan():
    return render_template('scan.html')


@app.route('/guide')
def guide():
    return render_template('guide.html')


@app.route('/download')
def download():
    # Create a zip file
    with zipfile.ZipFile("images.zip", "w") as zip_file:
        # Write each file in the images directory to the zip file
        for filename in os.listdir("images"):
            zip_file.write(os.path.join("images", filename))

    # Send the zip file to the user
    return send_file("images.zip", as_attachment=True)


@app.route('/predict', methods=['POST', 'GET'])
def predict():
    # Get the image from the request
    image = request.files['image'].read()

    # Convert the image to a numpy array
    image = np.frombuffer(image, np.uint8)

    # Decode the image using the TIFF flag
    image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)

    # Get the number of files in the images folder excluding the CSV file
    num_files = len([file for file in os.listdir('images') if file.endswith('.tiff')])

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
    prediction = model.predict(image[np.newaxis, ...])

    # Create a CSV file with image name and prediction
    with open('images/data.csv', 'a') as f:
        # Get the prediction values
        xmin, xmax, ymin, ymax = prediction[0]
        # Multiply the values by the image width and height
        xmin, xmax, ymin, ymax = xmin * image.shape[1], xmax * image.shape[1], ymin * image.shape[0], ymax * \
                                 image.shape[0]
        # Convert the values to integers
        xmin, xmax, ymin, ymax = int(xmin), int(xmax), int(ymin), int(ymax)
        # Write the values to the CSV file
        f.write(f"image_{num_files + 1}.tiff,{xmin},{xmax},{ymin},{ymax}\n")

    print(prediction)
    response = {"prediction": prediction.tolist()}
    return jsonify(response)


if __name__ == '__main__':
    app.run(host='192.168.0.94')

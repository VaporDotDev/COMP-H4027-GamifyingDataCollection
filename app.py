import cv2
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, request, jsonify

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


@app.route('/predict', methods=['POST', 'GET'])
def predict():
    # Get the image from the request
    image = request.files['image'].read()

    # Convert the image to a numpy array
    image = np.frombuffer(image, np.uint8)

    # Decode the image
    image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)

    # Resize the image to (224, 224)
    image = cv2.resize(image, (224, 224))

    # Normalize the image
    image = image / 255.0

    # Make a prediction with the model
    prediction = model.predict(image[np.newaxis, ...])

    print(prediction)
    response = {"prediction": prediction.tolist()}
    return jsonify(response)


if __name__ == '__main__':
    app.run(host='192.168.0.94')

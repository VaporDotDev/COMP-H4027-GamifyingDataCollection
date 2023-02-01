from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')


@app.route('/scan')
def scan():
    return render_template('scan.html')


@app.route('/guide')
def guide():
    return render_template('guide.html')


if __name__ == '__main__':
    app.run()

from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('./webpage/index.html')

@app.route('/styles.css')
def stylesheet():
    return send_file('./webpage/styles.css')

if __name__ == "__main__":
    app.run()
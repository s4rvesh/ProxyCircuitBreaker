import random
import time

from flask import Flask

app = Flask(__name__)


@app.route("/")
def homePage():
    return {"msg": "Hello"}, 200


@app.route("/success")
def success_endpoint():
    return {
               "msg": "Success endpoint",
           }, 200


@app.route("/failure")
def faulty_endpoint():
    return {
               "msg": "Failure endpoint"
           }, 500


@app.route("/timeout")
def timeout_endpoint():
    time.sleep(10)
    return {"msg": "Timeout endpoint"}, 504


@app.route("/random")
def fail_randomly_endpoint():
    r = random.randint(0, 1)
    if r == 0:
        return {"msg": "Success message"}, 200

    return {"msg": "Fail sometimes"}, 500


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)

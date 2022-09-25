import http
import requests

proxy = {"http": "http://localhost:9097"}

faulty_endpoint = "http://127.0.0.1:5000/failure"
success_endpoint = "http://127.0.0.1:5000/success"
random_status_endpoint = "http://127.0.0.1:5000/random"

# response = requests.get(success_endpoint, proxies=proxy)
response = requests.get(faulty_endpoint, proxies=proxy)
print(response)

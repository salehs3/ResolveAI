import requests

r = requests.get("http://127.0.0.1:8000/cases/1")
a = requests.get("http://127.0.0.1:8000/cases/")

print(a.text)

# payload = {
#     "name":"Saleem",
#     "email":"saleemapi@asd.com",
#     "status":"open"
# }

# p = requests.post("http://127.0.0.1:8000/cases/",json=payload)

# print(p.status_code)
# print(p.json())
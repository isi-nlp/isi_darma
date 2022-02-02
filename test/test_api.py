from requests import post


# some dummy stuff
RTG_API = 'http://localhost:6060/translate'
source = {"source":["Comment allez-vous?", "Bonne journée"]}
response = post(RTG_API, json=source)
print(response.json())


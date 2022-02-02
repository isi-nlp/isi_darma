from requests import post


# some dummy stuff
RTG_API = 'http://localhost:6060/translate'
source = {"source":["Comment allez-vous?", "Bonne journée", "안녕하세요", "지금 기분이 어때?"]}
response = post(RTG_API, json=source)
print(response.json())


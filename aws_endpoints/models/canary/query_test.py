import requests

texts = [
    "Hello there!", 
    "I wanted to throw the hamburger in his face.",
    "I love you so much!",
    "I hate you so much!",
]

for text in texts:

    input_json = {
        "text": text,
    }
    response = requests.get('http://0.0.0.0:7860/generate', json=input_json)

    print(response.json())
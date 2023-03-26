import requests

MODERATOR_ENDPOINT = "http://128.9.37.116:5050/moderation-prediction-classifier"

def get_moderator_response(comment):
    data = {"0":
            { "comment": comment}
            }
    response = requests.post(MODERATOR_ENDPOINT, json=data)
    return response.json()["0"]["score"]

if __name__ == "__main__":
    comments = ["I hate you",
               "holy shit this subreddit is full of idiots",
               "it's pretty tough to find good housing in this city"]

    for c in comments:
        print(get_moderator_response(c))

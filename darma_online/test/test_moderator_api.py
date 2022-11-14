import requests

MODERATOR_ENDPOINT = "http://127.0.0.1:5050"

def get_moderator_response(comment):
    response = requests.post(MODERATOR_ENDPOINT, data=comment)
    return response.json()["0"]["score"]


if __name__ == "__main__":
    comments = ["I hate you",
               "holy shit this subreddit is full of idiots",
               "it's pretty tough to find good housing in this city"]

    for c in comments:
        print(get_moderator_response(c))

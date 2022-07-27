from flask import Flask
from flask import make_response
from flask import request, jsonify, abort
import json
import requests
from googleapiclient import discovery

app = Flask(__name__)

API_KEY = 'AIzaSyBNjKi76fE1-SBofnijokOSySiD4S_cGNc'
client = discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=API_KEY,
        discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        # static_discovery=False,
        )

import time
def tox_score(text):
  analyze_request = {
    'comment': { 'text': str(text) },
    'requestedAttributes': {'TOXICITY': {}, 'OBSCENE': {}, 'INSULT':{}, 'IDENTITY_ATTACK':{}}
  }
  time.sleep(1)
  try:
    response = client.comments().analyze(body=analyze_request).execute()
    result = []
    result.append({"type": "TOXICITY","score": round(response['attributeScores']['TOXICITY']['summaryScore']['value'], ndigits=2)})
    result.append({"type": "OBSCENE","score": round(response['attributeScores']['OBSCENE']['summaryScore']['value'], ndigits=2)})
    result.append({"type": "INSULT","score": round(response['attributeScores']['INSULT']['summaryScore']['value'], ndigits=2)})
    result.append({"type": "IDENTITY_ATTACK","score": round(response['attributeScores']['IDENTITY_ATTACK']['summaryScore']['value'], ndigits=2)})

    return result
  except Exception as e:
    return ("ERROR",str(e))


@app.route("/ping/")
def ping():
  return "pong"

@app.route("/v1/toxicity/types/")
def tox_type():
    response = {
        '1': 'TOXICITY',
        '2': 'OBSCENE',
        '3': 'INSULT',
        '4': 'IDENTITY_ATTACK'
    }
    return jsonify(response)

@app.route("/v1/toxicity/", methods = ['POST'])
def toxicity():
    try:
        if not request.json :
            return jsonify({"ERROR": "Error: Input json not found"})
        else:
            content_type = request.headers.get('Content-Type')
            if (content_type == 'application/json'):
                result = {}
                result['thread'] = [] 

                thread = request.json['thread']

                for item in thread:
                    post_res = {}
                    post_res["postId"] = item["postId"]
                    post_res["userId"] = item["userId"]
                    post_res['comments'] = []

                    comments_list = item['comments']

                    for com in comments_list:
                        if com['request-label'] == True:
                            com_res = {}
                            com_res['userId'] = com["userId"]
                            com_res['commentId'] = com["commentId"]
                            com_res['behaviours'] = tox_score(com['content'])

                            post_res['comments'].append(com_res) 
                    
                    if len(post_res['comments'])>0:
                        result['thread'].append(post_res)

                return jsonify(result)
            else:
                return jsonify({"Error": "Content-Type not supported!"})
    except Exception as e:
        return "Exception occured:" + str(e)

if __name__ == '__main__':
   app.run(debug = True, host = '0.0.0.0', port=5001)


#commands
#curl -X POST -H "Content-type: application/json" -d "{\"id\" : \"100\", \"title\" : \"comment comment some comment\"}" "localhost:5001/v1/toxicity/"


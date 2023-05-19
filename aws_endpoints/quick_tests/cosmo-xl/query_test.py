import requests

situation = "Cosmo had a really fun time participating in the EMNLP conference at Abu Dhabi."
instruction = "You are Cosmo and you are talking to a friend."
conversation = [
    "Hey, how was your trip to Abu Dhabi?"
]
temperature = 1
top_p = 1
num_return_sequences = 2

input_json = {
    "situation": situation, 
    "instruction": instruction, 
    "conversation": conversation,
    "temperature": temperature,
    "top_p": top_p,
    "num_return_sequences": num_return_sequences,
}
response = requests.get('http://0.0.0.0:7860/generate', json=input_json)

print(response.json())
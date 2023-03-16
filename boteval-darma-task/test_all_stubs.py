"""
Simulate conversations between our moderator and the final speaker. 
Generate intermediate predictions (chain of thought)s
"""
import json 
import openai 
import os
from bots import GPTBot
from typing import List 
from tqdm import tqdm 

api_key = os.environ.get('OPENAI_KEY', '')
openai.api_key = api_key
engine = "gpt-3.5-turbo"

MEDIATOR_PERSONAS = {
    "interest1": "you are a mediator that tries to understand the interests of participants in a conversation and make sure that they have a constructive conversation. keep your responses short. redirect to the conversation to the topic if the participants agree to your suggestions. Mediate the following conversation formatted as 'moderator: {response}'"
}

MODERATED_USER_PERSONAS= {
    "default": "generate a single response to the following conversation as <speaker_id>, who is initially resistant to changing their original stance. Focus on <speaker_id>'s interests and emotional state." 
}

N_TURNS = 2

with open("persona_configs.json", "r") as f: 
    persona_configs = json.load(f)

def generate_conversation(mediator_prompt, moderated_user_prompt, init_conv:List[str], n_turns: int): 
    # initialize context for mediator 
    mediator_messages = [
        {"role": "system", "content": mediator_prompt},
        {"role": "user", "content": "\n".join(init_conv)},
    ]

    # initialize context for moderated user 
    moderated_user_messages = [
        {"role": "system", "content": moderated_user_prompt},
    ]
    
    
    for idx in range(n_turns): 
        
        # mediator generates  response 
        mediator_response = generate_response(engine, mediator_messages)
        
        # add response to the context for both mediator and moderated user 
        mediator_messages.append({"role": "assistant", "content": mediator_response})
        
        if idx == 0: 
            moderated_user_messages.append({"role": "user", "content": "\n".join(init_conv + [mediator_response])})    
        else: 
            moderated_user_messages.append({"role": "user", "content": mediator_response})

        # moderated user responds to mediator 
        moderated_user_response = generate_response(engine, moderated_user_messages)
        
        # add response to the context for both medaitor and moderated user 
        mediator_messages.append({"role": "user", "content": moderated_user_response})
        moderated_user_messages.append({"role": "assistant", "content": moderated_user_response})    
        
        
    conversation = [] 
    # first turn is mediator prompt and the second turn is the conversation context  
    for msg in mediator_messages[2:]: 
        conversation.append(msg["content"])
    
    return {
        "mediator_prompt": mediator_prompt,
        "moderated_user_prompt": moderated_user_prompt, 
        "init_conv": init_conv,
        "continued_conversation": conversation
    }


def generate_response(engine, messages): 
    response = openai.ChatCompletion.create(
        model=engine,
        messages=messages
    ) 
    return response["choices"][0]["message"]["content"]
    
   
datapath = "chat_topics_eng.json"
with open(datapath, "r") as f: 
    data = json.load(f)

bot_persona = "interest1"
user_persona = "default"
mediator_prompt = MEDIATOR_PERSONAS[bot_persona]
base_moderated_user_prompt = MODERATED_USER_PERSONAS[user_persona]

results = {} 
for idx, topic in tqdm(enumerate(data)): 
    id_ = topic["id"]
    conv = topic["conversation"]
    reformatted_conv = []
    for idx, turn in enumerate(conv): 
        turn_text = f"{turn['speaker_id']}: {turn['text']}"
        reformatted_conv.append(turn_text)
        
    topic["reformatted_conversation"] = reformatted_conv
    topic["last_speaker"] = turn['speaker_id']
    
    moderated_user_prompt = base_moderated_user_prompt.replace("<speaker_id>", topic["last_speaker"])
    
    generated_conversation = generate_conversation(mediator_prompt, moderated_user_prompt, reformatted_conv, n_turns = N_TURNS)

    # import pdb; pdb.set_trace() 
    results[f"{bot_persona}-{user_persona}-{id_}"] = generated_conversation
    
    if idx == 0: 
        print("\n".join(generated_conversation["init_conv"]))
        print("\n".join(generated_conversation["continued_conversation"]))
    
    if idx == 5: 
        break 
    
with open("chatgpt_self-talk_test.json", "w") as f: 
    json.dump(results, f, indent=4)
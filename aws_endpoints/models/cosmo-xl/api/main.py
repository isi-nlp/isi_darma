import time
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

app = FastAPI()

class Item(BaseModel):
    situation: str 
    instruction: str 
    conversation: List[str] 
    temperature: float
    top_p: float
    num_return_sequences: int

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("allenai/cosmo-xl")
model = AutoModelForSeq2SeqLM.from_pretrained("allenai/cosmo-xl").to(device)

def set_input(situation_narrative, role_instruction, conversation_history):
    input_text = " <turn> ".join(conversation_history)

    if role_instruction != "":
        input_text = "{} <sep> {}".format(role_instruction, input_text)

    if situation_narrative != "":
        input_text = "{} <sep> {}".format(situation_narrative, input_text)

    return input_text

def generate(situation_narrative, role_instruction, conversation_history, temperature, top_p, num_return_sequences):
    """
    situation_narrative: the description of situation/context with the characters included (e.g., "David goes to an amusement park")
    role_instruction: the perspective/speaker instruction (e.g., "Imagine you are David and speak to his friend Sarah").
    conversation_history: the previous utterances in the conversation in a list
    """

    input_text = set_input(situation_narrative, role_instruction, conversation_history) 

    inputs = tokenizer([input_text], return_tensors="pt").to(device)
    outputs = model.generate(
        inputs["input_ids"], 
        max_new_tokens=128, 
        temperature=temperature, 
        top_p=top_p,
        do_sample=True, 
        num_return_sequences=num_return_sequences,
    )
    responses = tokenizer.batch_decode(outputs, skip_special_tokens=True, clean_up_tokenization_spaces=False)

    return responses

@app.get("/generate")
def generate_responses(input: Item):
    time_0 = time.time()
    responses = generate(
        input.situation, 
        input.instruction, 
        input.conversation,
        input.temperature,
        input.top_p,
        input.num_return_sequences,
    )
    time_elapsed = time.time() - time_0
    return {"responses": responses, "time_elapsed": time_elapsed}
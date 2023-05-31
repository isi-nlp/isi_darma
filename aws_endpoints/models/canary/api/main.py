import time
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

import sys
sys.path.append("../prosocial-dialog")
import re
from model.canary import Canary

app = FastAPI()

class Item(BaseModel):
    text: str

canary = Canary()

def parse_output(output):
    safety_label = re.match("__[\w]*__", output)
    safety_label = safety_label[0] if safety_label else None

    rots = re.match("__[\w]*__ (.*)", output)
    rots = rots[1].split(',') if rots else None

    return safety_label, rots

@app.get("/generate")
def generate_responses(input: Item):
    time_0 = time.time()
    output = canary.chirp(input.text)[0]
    safety_label, rots = parse_output(output)
    time_elapsed = time.time() - time_0

    return {"safety_label": safety_label, "rots": rots, "time_elapsed": time_elapsed}

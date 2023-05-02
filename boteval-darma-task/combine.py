#  combine multiple json files in a directory into one 

import json
from pathlib import Path 
import os 
from argparse import ArgumentParser

def combine(dir_path):
    """Combine multiple json files in a directory into one. 
    """
    # get all json files in the directory 
    json_files = [pos_json for pos_json in os.listdir(dir_path) if pos_json.endswith('.json')]

    # combine json files into one 
    combined_json = []
    for json_file in json_files:
        with open(os.path.join(dir_path, json_file)) as f:
            combined_json.append(json.load(f))

    # write combined json to file 
    with open(os.path.join(dir_path, "combined.json"), "w") as f:
        json.dump(combined_json, f, indent=4)
        
        
parser = ArgumentParser()
parser.add_argument("-d", "--dir", dest="dir_path", help="directory path")

args = parser.parse_args()

combine(args.dir_path)
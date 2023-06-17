from mturk_analysis import get_annotated_datafiles_for_dates, extract_data_of_interest, ITERATION_DATES
from argparse import ArgumentParser
from pathlib import Path 
from loguru import logger
import json 


def format_to_chat_seed(chat, idx):
    
    conversation = [] 
    users = [] 
    for msg in chat["messages"]: 
        conversation.append({
            "text": msg["text"], 
            "speaker_id": msg["data"]["speaker_id"], 
            "user_id": msg["user_id"], 
            "is_seed": msg["is_seed"]
        })
        
        if msg["user_id"] not in users and msg["user_id"] not in ["context", "Moderator"]: 
            users.append(msg["user_id"])
        
    topic_id = chat["topic_id"]
    thread_id = chat["messages"][0]["thread_id"]
        
    if args.idx < 6: 
        result = {
            "id": f"chat{topic_id}-{thread_id}", 
            "name": f"chat {topic_id} - controversy", 
            "conversation": conversation, 
            "target_user": None, 
            "meta": {
                "thread_id": thread_id,
                "topic_id": topic_id,
                "users": users, 
                "ratings": {
                    "coherency": chat["coherency"],
                    "engaging": chat["engaging"],
                    "convincing": chat["convincing"],
                    "understanding": chat["understanding"],
                }
            }
        }
    else: 
        result = {
            "id": f"chat{topic_id}-{thread_id}", 
            "name": f"chat {topic_id} - controversy", 
            "conversation": conversation, 
            "target_user": None, 
            "meta": {
                "thread_id": thread_id,
                "topic_id": topic_id,
                "users": users, 
                "ratings": {
                    "engaging": chat["engaging"],
                    "fair": chat["fair"],
                    "respectful": chat["respectful"],
                    "specific": chat["specific"],
                    "likeability": chat["likeability"],
                    "agreement": chat["agreement"],
                }
            }
        }
    
    return result 


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--idx', type=int, help="iteration index", default=3)
    parser.add_argument('--output', type=str, default='mturk_chat_seed.json')
    args = parser.parse_args()
    dates = ITERATION_DATES[args.idx]
    fns = get_annotated_datafiles_for_dates(dates)

    all_mturk_results = []
    for fn in fns:
        try:
            mturk_result = extract_data_of_interest(fn, args.idx)
            if mturk_result:
                all_mturk_results += mturk_result
        except Exception as e:
            logger.exception(e)
            print(e)
            print(fn)
        
    
    chats_for_survey = []
    for chat in all_mturk_results: 
        chats_for_survey.append(format_to_chat_seed(chat, args.idx))
       
    # add iteration index to output 
    orig_path = Path(args.output)
    output_path = Path(orig_path).with_name(name=f'{orig_path.stem}_it{args.idx}{orig_path.suffix}')
        
    with open(output_path, 'w') as f: 
        json.dump(chats_for_survey, f, indent=4)

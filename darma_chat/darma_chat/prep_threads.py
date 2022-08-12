"""
Prepare dataset
 1. Anonymize
"""

import argparse
import json
import logging as log
from functools import lru_cache
from io import StringIO
from tqdm.auto import tqdm
from markdown import Markdown
from darma_chat.translator import RtgApiTranslator


log.basicConfig(level=log.INFO)

ANON_IDS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
DEF_MT_API = 'http://54.68.184.232:6060/many-eng/v1/translate'

mt: RtgApiTranslator = None

def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()


Markdown.output_formats["plain"] = unmark_element
unmarker = Markdown(output_format="plain")
unmarker.stripTopLevelTags = False



def unmarkdown(text: str):
    try:
        return unmarker.convert(text)
    except Exception as e:
        log.error(f"Error while remove markdown tags {e}")
        return text

def unmarkdwon_thread(thread):
    """Convert markdown to plaintext"""
    for msg in thread['conversation']:
        msg['text'] = unmarkdown(msg['text'])


def anonymize_thread(thread):
    """Anonymize thread (in-place)"""
    mapping = {}
    for msg in thread['conversation']:
        speaker_id = msg['speaker_id']
        if speaker_id not in mapping:
           mapping[speaker_id] = ANON_IDS[len(mapping)]
        msg['speaker_id'] = mapping[speaker_id]
    thread['target_user'] = mapping[thread['target_user']]
    return msg, mapping


@lru_cache(maxsize=5000)
def translate_text(text:str, ssplit=True):
    """Translate the text. Split sentences if necessary"""
    return mt.translate(text=text)


def translate_thread(thread):
    for msg in thread['conversation']:
        msg['text_orig'] = msg['text']
        msg['text'] = translate_text(msg['text'])


def add_bool_arg(parser, key, default=True, help:str=None):
    parser.add_argument(f'--{key}', action='store_true', help=help, default=default)
    parser.add_argument(f'--no-{key}', dest=key, action='store_false', help=help, default=not default)
    #parser.set_defaults(key=default)

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--inp', required=True, help="Input file path")
    parser.add_argument('-o', '--out', required=True, help="Output path")
    parser.add_argument('-mt-api', '--mt-api', help="MT API URL",
                        default=DEF_MT_API)
    add_bool_arg(parser, key='mt', help='Machine translate text')

    args = vars(parser.parse_args())
    log.info(f"{args['inp']} --> {args['out']}")

    global mt
    mt = RtgApiTranslator(api_url=args['mt_api'])

    with open(args['inp'], encoding='utf', errors='replace') as inp:
        threads = json.load(inp)
    log.info(f'Found {len(threads)} in {args["inp"]}')

    total_msgs = 0
    with tqdm(threads, 'threads', unit='thread') as pbar:
        for thread in pbar:
            unmarkdwon_thread(thread)
            anonymize_thread(thread)
            if args['mt']:
                translate_thread(thread)
            msg_count = len(thread['conversation'])
            pbar.set_postfix_str(f'msgs total:{total_msgs} this:{msg_count}')
            total_msgs += msg_count

    with open(args['out'], 'w', encoding='utf', errors='replace') as out:
        json.dump(threads, out, ensure_ascii=False, indent=2)
    log.info("Done")


if __name__ == '__main__':
    main()

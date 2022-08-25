#!/usr/bin/env python
"""
Serves (Mephisto) chat admin using Flask HTTP server
"""

import os
import sys
import platform
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging as log
from functools import lru_cache
import time
import json
from pathlib import Path
from typing import List, Dict, Mapping, Tuple, Union
import copy

import flask
from flask import Flask, request, send_from_directory, Blueprint
import boto3
from ruamel.yaml import YAML

from .utils import max_RSS, format_bytes


log.basicConfig(level=log.INFO)
yaml = YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)

FLOAT_POINTS = 4
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

bp = Blueprint('admin', __name__, template_folder='templates', static_folder='static')


MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'


sys_info = {
    'Python Version': sys.version,
    'Platform': platform.platform(),
    'Platform Version': platform.version(),
    'Processor':  platform.processor(),
    'CPU Memory Used': max_RSS()[1],
    #'GPU': '[unavailable]',
}


def render_template(*args, **kwargs):
    return flask.render_template(*args, environ=os.environ, **kwargs)


def jsonify(obj):

    if obj is None or isinstance(obj, (int, bool, str)):
        return obj
    elif isinstance(obj, float):
        return round(obj, FLOAT_POINTS)
    elif isinstance(obj, dict):
        return {key: jsonify(val) for key, val in obj.items()}
    elif isinstance(obj, list):
        return [jsonify(it) for it in obj]
    #elif isinstance(ob, np.ndarray):
    #    return _jsonify(ob.tolist())
    else:
        log.warning(f"Type {type(obj)} maybe not be json serializable")
        return obj


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(bp.root_path, 'static', 'favicon'), 'favicon.ico')

@app.template_filter('ctime')
def timectime(s):
    return time.ctime(s) # datetime.datetime.fromtimestamp(s)


@app.template_filter('flat_single')
def flatten_singleton(obj):
    res = obj
    try:
        if len(obj) == 0:
            res = ''
        elif len(obj) == 1:
            res = obj[0]
    except:
        pass
    return res


######### BEGIN Services ##############
class DashboardService:

    def __init__(self, chat_dir: Union[Path, str], mturk=None):
        """_summary_

        Args:
            chat_dir (Path): path to directory where json files are stored by ISI darma_chat (offline protocol)
            mturk (botocore.client.MTurk, optional): Mturk client
        """
        if not isinstance(chat_dir, Path):
            chat_dir = Path(chat_dir)
        assert chat_dir.exists(), f'{chat_dir} not found'
        log.info(f'Looking for chats in {chat_dir}/*/*.json')
        chat_files = list(sorted(chat_dir.glob('*/*.json'), reverse=True))
        log.info(f'found {len(chat_files)}')
        self.chat_files: Dict[str, Path]  = {p.name.rstrip('.json'): p for p in chat_files}
        assert len(self.chat_files) == len(chat_files), f'Chat file names in {chat_dir} are not unique'
        self._chat_info = None
        self.mturk = mturk

    @property
    def chat_info(self):
        if self._chat_info is None:
            self._chat_info = {}
            for chat_id, path in self.chat_files.items():
                stat = path.stat()
                self._chat_info[chat_id] = dict(
                    path=path, size=format_bytes(stat.st_size),
                    modified=time.ctime(stat.st_mtime))
        return self._chat_info

    @lru_cache(maxsize=128)
    def get_chat(self, chat_id):
        chat_file = self.chat_files[chat_id]
        with open(chat_file, encoding='utf8', errors='replace') as fobj:
            return json.load(fobj)

    def list_qualification_types(self, max_results=100, query: str=''):
        data = self.mturk.list_qualification_types(
            MustBeRequestable=True, MustBeOwnedByCaller=True,
            MaxResults=max_results)
        qtypes = data['QualificationTypes']
        if query:
            query = query.lower()
            qtypes = [qt for qt in qtypes
                    if query in qt['Name'].lower() or query in qt['Description']]
        return qtypes

    def list_HITS(self, qual_id:str, max_results=100):
        return self.mturk.list_hits_for_qualification_type(
            QualificationTypeId=qual_id,
            MaxResults=max_results)

    def list_assignments(self, HIT_id: str, max_results=100):
        return self.mturk.list_assignments_for_hit(
            HITId=HIT_id, MaxResults=max_results)

    def approve_assignment(self, assignment_id):
        # this will pay the worker
        raise Exception('Not implemented yet')
        #log.info(f'Approving assingment {assignment_id}')
        #self.mturk.approve_assignment(AssignmentId=assignment_id)


    def qualify_worker(self, worker_id: str, qual_id: str, send_email=True):
        log.info(f"Qualifying worker: {worker_id} for {qual_id}")
        return self.mturk.associate_qualification_with_worker(
            QualificationTypeId=qual_id,
            WorkerId=worker_id,
            IntegerValue=1,
            SendNotification=True
            )

    def disqualify_worker(self, worker_id: str, qual_id: str, reason: str=None):
        log.info(f"Disqualifying worker: {worker_id} for {qual_id}")
        return self.mturk.disassociate_qualification_with_worker(
            QualificationTypeId=qual_id,
            WorkerId=worker_id,
            Reason=None
            )

######### END Services ##############


def get_mturk_client(sandbox=False, endpoint_url=MTURK_SANDBOX, **props):

    params = copy.deepcopy(props)
    if sandbox:
        params["endpoint_url"] = endpoint_url
    log.info(f'creating mturk with {params}')
    return boto3.client('mturk', **params)


def attach_admin_dashboard(config):

    chat_dir = config['chat_dir']
    mturk = get_mturk_client(config['mturk'])
    dboard = DashboardService(chat_dir=chat_dir, mturk=mturk)


    @bp.route('/')
    def index():
        args = dict(chats=dboard.chat_info.items())
        return render_template('index.html', **args)


    @bp.route("/review/<chat_id>", methods=["GET"])
    def review_chat(chat_id):
        if request.method != 'GET':
            return "Only GET method supported", 400
        if not chat_id:
            return "chat_id required", 400
        if chat_id not in dboard.chat_files:
            return f"chat ID {chat_id} unknown", 400
        chat_data = dboard.get_chat(chat_id)
        return render_template('chatui.html', data=chat_data, chat_id=chat_id)

    @bp.route("/mturk/qualification", methods=["GET"])
    def mturk_qualifications():
        qtypes = dboard.list_qualification_types(max_results=100)
        meta = dict(endpoint_url = dboard.mturk.meta.endpoint_url)
        return render_template('mturk_qualifications.html', qtypes=qtypes, meta=meta)

    @bp.route("/mturk/qualification/<qual_id>", methods=["GET"])
    def mturk_qualification(qual_id):
        data = dboard.list_HITS(qual_id=qual_id,max_results=100)
        return render_template('mturk_HITs.html', data=data, qual_id=qual_id)

    @bp.route("/mturk/qualification/<qual_id>", methods=["DELETE"])
    def delete_qualification(qual_id):
        data = dboard.mturk.delete_qualification_type(QualificationTypeId=qual_id)
        return jsonify(data), 200

    @bp.route("/mturk/HIT/<HIT_id>", methods=["GET"])
    def mturk_assignments(HIT_id):
        data = dboard.list_assignments(HIT_id=HIT_id,max_results=100)
        return jsonify(data), 200

    @bp.route("/mturk/HIT/<HIT_id>", methods=["DELETE"])
    def delete_hit(HIT_id):
        data = dboard.mturk.delete_hit(HITId=HIT_id)
        return jsonify(data), 200

    @bp.route('/about')
    def about():
        sys_info['CPU Memory Used'] = max_RSS()[1]
        return render_template('about.html', sys_info=sys_info)


def parse_args():
    parser = ArgumentParser(
        prog="chat-admin",
        description="Deploy a chat admin UI",
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('config', type=Path, help='Path to config file', default='conf.yml')
    parser.add_argument("-d", "--debug", action="store_true", help="Run Flask server in debug mode")
    parser.add_argument("-p", "--port", type=int, help="port to run server on", default=6060)
    parser.add_argument("-ho", "--host", help="Host address to bind.", default='0.0.0.0')
    parser.add_argument("-b", "--base", help="Base prefix path for all the URLs. E.g., /v1")
    args = vars(parser.parse_args())
    return args


# uwsgi can take CLI args too
# uwsgi --http 127.0.0.1:5000 --module chat_app.app:app # --pyargv "--foo=bar"
cli_args = parse_args()
config_file: Path = cli_args['config']
assert config_file.exists() and config_file.is_file(), f'{config_file} is not a valid config file'
config = yaml.load(config_file)

attach_admin_dashboard(config=config)

app.register_blueprint(bp, url_prefix=cli_args.get('base'))
if cli_args.pop('debug'):
    app.debug = True

# register a home page if needed
if cli_args.get('base'):
    @app.route('/')
    def home():
        return render_template('home.html', demo_url=cli_args.get('base'))


def main():
    log.info(f"System Info: ${sys_info}")
    # CORS(app)  # TODO: insecure
    app.run(port=cli_args["port"], host=cli_args["host"])
    # A very useful tutorial is found at:
    # https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3


if __name__ == "__main__":
    main()
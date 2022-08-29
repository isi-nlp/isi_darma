#!/usr/bin/env python
"""
Serves (Mephisto) chat admin using Flask HTTP server
"""

import os
import profile
import sys
import platform
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging as log
import time
import json
from pathlib import Path
from typing import List, Dict, Mapping, Tuple, Union
import copy

import flask
from flask import Flask, request, send_from_directory, Blueprint
import boto3
from ruamel.yaml import YAML
from cachetools import cached, TTLCache



from .utils import max_RSS, format_bytes


log.basicConfig(level=log.INFO)
yaml = YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)

FLOAT_POINTS = 4
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

bp = Blueprint('admin', __name__, template_folder='templates', static_folder='static')


MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
AWS_CACHE_TTL = 60 * 1 # seconds
AWS_CACHE_MAXSIZE = 64
AWS_MAX_RESULTS = 100
FS_CACHE_TTL = 60 * 3 # seconds


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

    def __init__(self, chat_dir: Union[Path, str]):
        """_summary_

        Args:
            chat_dir (Path): path to directory where json files are stored by ISI darma_chat (offline protocol)
        """
        log.info(f'Chat dir {chat_dir}')
        if not isinstance(chat_dir, Path):
            chat_dir = Path(chat_dir)

        if not chat_dir.exists():
            log.warning(f'{chat_dir} not found. Creating now')
            chat_dir.mkdir(parents=True, exist_ok=True)
        self.chat_dir = chat_dir

    @property
    @cached(cache=TTLCache(maxsize=1, ttl=FS_CACHE_TTL))
    def chat_files(self) -> Dict[str, Path]:
        log.info(f'Scanning chat files:: {self.chat_dir}/*/*.json')
        chat_paths = list(sorted(self.chat_dir.glob('*/*.json'), reverse=True))
        log.info(f'found {len(chat_paths)}')
        chat_lookups: Dict[str, Path]  = {p.name.rstrip('.json'): p for p in chat_paths}
        if len(chat_lookups) != len(chat_paths):
            log.warning(f'Chat file names in {self.chat_dir} are not unique')
        return chat_lookups

    @property
    @cached(cache=TTLCache(maxsize=1, ttl=FS_CACHE_TTL))
    def chat_info(self):
        _chat_info = {}
        for chat_id, path in self.chat_files.items():
            stat = path.stat()
            _chat_info[chat_id] = dict(
                path=path, size=format_bytes(stat.st_size),
                modified=time.ctime(stat.st_mtime))
        return _chat_info

    @cached(cache=TTLCache(maxsize=256, ttl=FS_CACHE_TTL))
    def get_chat(self, chat_id):
        chat_file = self.chat_files[chat_id]
        with open(chat_file, encoding='utf8', errors='replace') as fobj:
            chat = json.load(fobj)
        return chat


class MTurkService:

    def __init__(self, client) -> None:
        self.client = client

    @property
    def endpoint_url(self) -> str:
        return self.client.meta.endpoint_url


    def get_assignment(self, assignment_id):
        return self.client.get_assignment(AssignmentId=assignment_id)['Assignment']

    def list_qualification_types(self, max_results=AWS_MAX_RESULTS, query: str=''):
        data = self.client.list_qualification_types(
            MustBeRequestable=True, MustBeOwnedByCaller=True,
            MaxResults=max_results)
        qtypes = data['QualificationTypes']
        if query:
            query = query.lower()
            qtypes = [qt for qt in qtypes
                    if query in qt['Name'].lower() or query in qt['Description']]
        return qtypes

    def list_HITS(self, qual_id:str, max_results=AWS_MAX_RESULTS):
        return self.client.list_hits_for_qualification_type(
            QualificationTypeId=qual_id,
            MaxResults=max_results)

    def list_workers_for_qualtype(self, qual_id:str, max_results=AWS_MAX_RESULTS):
        return self.client.list_workers_with_qualification_type(
            QualificationTypeId=qual_id,
            MaxResults=max_results)

    def list_all_hits(self, max_results=AWS_MAX_RESULTS, next_token=None):
        args = dict(MaxResults=max_results)
        if next_token:
            args['NextToken'] = next_token
        return self.client.list_hits(**args)

    def list_assignments(self, HIT_id: str, max_results=AWS_MAX_RESULTS):
        return self.client.list_assignments_for_hit(
            HITId=HIT_id, MaxResults=max_results)

    def qualify_worker(self, worker_id: str, qual_id: str, send_email=True):
        log.info(f"Qualifying worker: {worker_id} for {qual_id}")
        return self.client.associate_qualification_with_worker(
            QualificationTypeId=qual_id,
            WorkerId=worker_id,
            IntegerValue=1,
            SendNotification=send_email
            )

    def disqualify_worker(self, worker_id: str, qual_id: str, reason: str=None):
        log.info(f"Disqualifying worker: {worker_id} for {qual_id}")
        return self.client.disassociate_qualification_from_worker(
            QualificationTypeId=qual_id,
            WorkerId=worker_id,
            Reason=reason
            )

######### END Services ##############


def get_mturk_client(sandbox=False, endpoint_url=MTURK_SANDBOX, profile=None, **props):

    params = copy.deepcopy(props)
    if sandbox:
        params["endpoint_url"] = endpoint_url
    if profile:
        boto3.setup_default_session(profile_name=profile)
    log.info(f'creating mturk with {params}')
    return boto3.client('mturk', **params)


class MTurkController:

    def __init__(self, mturk: MTurkService, where:str):
        """Registers mechanical turk controller

        Args:
            mturk (_type_): MTurk service object
            where (_type_): live or sandbox
        """
        assert where in ('live', 'sandbox')
        self.where = where
        self.mturk = mturk
        self.meta = dict(mturk_where=where, mturk_endpoint_url=self.mturk.endpoint_url)

    def register_routes(self, router):
        log.info(f'Registering routes {self.where}')
        rules = [
            ('/', self.home, dict(methods=["GET"])),
            ('/qualification/', self.list_qualifications, dict(methods=["GET"])),
            ('/qualification/<qual_id>', self.get_qualification, dict(methods=["GET"])),
            ('/qualification/<qual_id>', self.delete_qualification, dict(methods=['DELETE'])),
            ('/HIT/', self.list_HITs, dict(methods=["GET"])),
            ('/HIT/<HIT_id>', self.get_HIT,dict(methods=["GET"])),
            ('/HIT/<HIT_id>', self.delete_hit, dict(methods=['DELETE'])),
            ('/assignment/<asgn_id>/approve', self.approve_assignment, dict(methods=["POST"])),
            ('/worker/<worker_id>/qualification', self.qualify_worker, dict(methods=["POST", "PUT"])),
            ('/worker/<worker_id>/qualification', self.disqualify_worker, dict(methods=["DELETE"])),
        ]
        for path, view_func, opts in rules:
            router.add_url_rule(f"/mturk/{self.where}{path}", view_func=view_func,
                                endpoint=self.where + '_' + view_func.__name__, **opts)

    def render_template(self, *args, **kwargs):
        return render_template(*args, meta=self.meta, **kwargs)

    def home(self):
        return self.render_template('mturk/home.html')

    def list_qualifications(self):
        qtypes = self.mturk.list_qualification_types(max_results=AWS_MAX_RESULTS)
        return self.render_template('mturk/qualifications.html', qtypes=qtypes)

    def get_qualification(self, qual_id):
        HITs = self.mturk.list_HITS(qual_id=qual_id,max_results=AWS_MAX_RESULTS)
        workers = self.mturk.list_workers_for_qualtype(qual_id=qual_id, max_results=AWS_MAX_RESULTS)
        data = dict(HITs=HITs['HITs'], workers=workers['Qualifications'])
        return self.render_template('mturk/qualification.html', data=data, qual_id=qual_id)

    def delete_qualification(self, qual_id):
        data = self.mturk.mturk.delete_qualification_type(QualificationTypeId=qual_id)
        return jsonify(data), 200

    def list_HITs(self):
        data = self.mturk.list_all_hits()
        return self.render_template('mturk/HITs.html', data=data)

    def get_HIT(self, HIT_id):
        data = self.mturk.list_assignments(HIT_id=HIT_id, max_results=100)
        qtypes = self.mturk.list_qualification_types(max_results=100)
        return self.render_template('mturk/HIT.html', data=data, HIT_id=HIT_id, qtypes=qtypes)

    def delete_hit(self, HIT_id):
        data = self.mturk.client.delete_hit(HITId=HIT_id)
        return jsonify(data), data.get('HTTPStatusCode', 200)

    def approve_assignment(self, asgn_id):
        #RequesterFeedback=feedback # any feed back message to worker
        data = self.mturk.client.approve_assignment(AssignmentId=asgn_id)
        return jsonify(data), data.get('HTTPStatusCode', 200)

    def qualify_worker(self, worker_id):
        qual_id = request.form.get('QualificationTypeId')
        log.info(f"Qualify: worker: {worker_id}  to qualification: {qual_id}")
        if not qual_id:
            return 'ERROR: QualificationTypeId argument is requires', 400
        data = self.mturk.qualify_worker(worker_id=worker_id, qual_id=qual_id)
        return jsonify(data), data.get('HTTPStatusCode', 200)

    def disqualify_worker(self, worker_id, qual_id):
        log.info(f"Disqualify: worker: {worker_id} from qualification: {qual_id}")
        reason = request.values.get('reason', '')
        data = self.mturk.disqualify_worker(worker_id=worker_id,qual_id=qual_id, reason=reason)
        return jsonify(data), data.get('HTTPStatusCode', 200)


def attach_admin_dashboard(config, router):

    chat_dir = config['chat_dir']
    mturk_profle = config.get('mturk_profile')

    dboard = DashboardService(chat_dir=chat_dir)
    mturk_sanbdox = MTurkController(
        mturk=MTurkService(client=get_mturk_client(sandbox=True, profile=mturk_profle)),
        where='sandbox')
    mturk_live = MTurkController(
        mturk=MTurkService(client=get_mturk_client(sandbox=False, profile=mturk_profle)),
        where='live')
    mturk_sanbdox.register_routes(router)
    mturk_live.register_routes(router)

    @router.route('/')
    def index():
        args = dict(chats=dboard.chat_info.items())
        return render_template('index.html', **args)


    @router.route("/review/<chat_id>", methods=["GET"])
    def review_chat(chat_id):
        if request.method != 'GET':
            return "Only GET method supported", 400
        if chat_id not in dboard.chat_files:
            return f"chat ID {chat_id} unknown", 400
        chat_data = dboard.get_chat(chat_id)
        mturk_asgn_id = chat_data.get('mturk', {}).get('assignment_id')
        params = dict(data=chat_data, chat_id=chat_id)
        if mturk_asgn_id:
            sandbox = chat_data['mturk'].get('sandbox', True)
            mturk = mturk_sanbdox.mturk if sandbox else mturk_live.mturk
            assignment = mturk.get_assignment(assignment_id=mturk_asgn_id)
            chat_data['mturk'].update(assignment)
            params['qtypes'] = mturk.list_qualification_types(max_results=AWS_MAX_RESULTS)
            params['mturk_where'] = 'sandbox' if sandbox else 'live'
        return render_template('chatui.html', **params)

    @router.route('/about')
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
    # for security reasons we only bind it to loopback
    #parser.add_argument("-ho", "--host", help="Host address to bind.", default='127.0.0.1')
    args = vars(parser.parse_args())
    return args


# uwsgi can take CLI args too
# uwsgi --http 127.0.0.1:5000 --module chat_app.app:app # --pyargv "--foo=bar"
cli_args = parse_args()
config_file: Path = cli_args['config']
assert config_file.exists() and config_file.is_file(), f'{config_file} is not a valid config file'
config = yaml.load(config_file)

attach_admin_dashboard(config=config, router=bp)
app.register_blueprint(bp, url_prefix=cli_args.get('base'))

if cli_args.pop('debug'):
    app.debug = True

def main():
    log.info(f"System Info: ${sys_info}")
    # CORS(app)  # TODO: insecure
    app.run(port=cli_args["port"], host='127.0.0.1')
    # A very useful tutorial is found at:
    # https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3


if __name__ == "__main__":
    main()
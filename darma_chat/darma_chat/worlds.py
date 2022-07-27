#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import time
import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import random
import numpy as np
import logging as log
from pprint import pprint
from typing import TYPE_CHECKING


from parlai.core.agents import create_agent_from_shared
from parlai.core.message import Message
from parlai.core.worlds import validate
from parlai.crowdsourcing.utils.acceptability import AcceptabilityChecker
from parlai.crowdsourcing.utils.worlds import CrowdOnboardWorld, CrowdTaskWorld
from parlai.crowdsourcing.utils.mturk import get_mturk_id_from_mephisto_wrapper

from darma_chat.bot_agent import TurkLikeAgent
from darma_chat.constants import (
    ONBOARD_FAIL,
    ONBOARD_SUCCESS,
)
from darma_chat.translator import DialogTranslator, get_translator
from darma_chat.utils import Compatibility, DarmaContextGenerator


if TYPE_CHECKING:
    from mephisto.abstractions.blueprints.parlai_chat.parlai_chat_task_runner import (
        MephistoAgentWrapper)

class ModelChatOnboardWorld(CrowdOnboardWorld):
    """
    This onboarding world displays a sample conversation with checkboxes of the same
    annotations as in the real HIT, but it is not a live conversation (all utterances
    are displayed at once).

    constants.py has the task data with correct answers in json form
    (opt['onboard_task_data']). User gets to try again onboard_failures_max_allowed
    times and is soft banned if they fail more than that.
    """

    def __init__(self, opt, agent: "MephistoAgentWrapper"):
        super().__init__(opt, agent)

        self.opt = opt
        self.skip_onboarding = opt['skip_onboarding']

        self.onboard_task_data = opt['onboard_task_data']
        self.status = 'DISCONNECT'
        self.onboard_statistics = opt['onboard_statistics']
        self.statistics_condition = opt['statistics_condition']
        self.max_onboard_time = opt['max_onboard_time']
        self.onboarding_qualification = opt['onboarding_qualification']
        self.worker_id = get_mturk_id_from_mephisto_wrapper(self.agent)
        self.annotations = None

    def parley(self):

        if not self.skip_onboarding:

            log.info(
                f'{self.__class__.__name__}: starting parley for worker_id: {self.worker_id}')

            # We are rendering a frontend based on the initial task data, so we just
            # wait for the results to come in
            act = self.agent.act(timeout=self.max_onboard_time)
            self.status = self._handle_act(act)
            self.agent.observe(
                {'id': 'SYSTEM', 'text': '', 'final_status': self.status}
            )
            if self.status == ONBOARD_FAIL:
                start_time = time.time()
                # After soft ban, we just block in while loop until worker goes
                # away (Disconnects or returns the HIT as asked on the frontend)
                while time.time() - start_time < self.max_onboard_time:
                    _ = self.agent.act(timeout=self.max_onboard_time)
                    time.sleep(0.5)
            return None

        else:

            self.episodeDone = True  # Send the user directly to the HIT
            self.status = ONBOARD_SUCCESS  # Approve user by default
            self.agent.observe(
                {'id': 'SYSTEM', 'text': '', 'final_status': self.status}
            )

    def _handle_act(self, act):
        if 'task_data' not in act:
            log.info(
                f'{self.__class__.__name__}: {self.worker_id} had no data submitted')
            return ONBOARD_FAIL

        self.annotations = act['task_data'].get('annotations')
        log.info('Onboarding annotation results: ', self.annotations)

        if act['task_data']['success']:
            log.info(
                f'Worker {self.worker_id} successfully passed the onboarding task.')

            # This will end the onboarding and send them directly to the HIT
            self.episodeDone = True
            # save informed consent details (signature and date)
            consent_data_folder = self.opt['consent_data_folder']
            os.makedirs(consent_data_folder, exist_ok=True)
            consent_datapath = os.path.join(
                consent_data_folder, "consent_log.jsonl")
            with open(consent_datapath, 'w+') as f_jsonl:
                act['worker_id'] = self.worker_id
                data_str = json.dumps(act)
                f_jsonl.write(data_str + "\n")
            return ONBOARD_SUCCESS
        else:
            log.info(f'Worker {self.worker_id} failed onboarding.')
            # Grant the failed qualification, then sleep as we want worker to return
            self.agent.mephisto_agent.get_worker().grant_qualification(
                self.onboarding_qualification, 0
            )
            return ONBOARD_FAIL

    def shutdown(self):
        super().shutdown()
        if not self.skip_onboarding:
            with self.statistics_condition:
                if self.status not in self.onboard_statistics:
                    self.onboard_statistics[self.status] = 0
                self.onboard_statistics[self.status] += 1

    def get_custom_task_data(self):
        return self.annotations


class BaseModelChatWorld(CrowdTaskWorld, ABC):
    def __init__(self, opt, agent, bot,  mt: Optional[DialogTranslator]=None):
        super().__init__(opt, agent)

        # num_turns turns for a single side, and really it appears to be
        # (num_turns + 1) * 2 total b/c of the "Hi!" and first bot utterance

        num_turns = opt['num_turns']
        max_resp_time = opt['max_resp_time']

        self.opt = opt
        self.bot = bot
        self.mt: DialogTranslator = mt
        self.task_turn_idx = 0
        self.num_turns = num_turns

        self.agent.agent_id = 'Speaker 1'
        # self.agent.agent_id = ""
        self.bot.agent_id = 'BOT'
        # self.bot.agent_id = ""
        self.target_user = ""

        self.dialog = []
        self.tag = f'conversation_id {agent.mephisto_agent.db_id}'
        self.task_type = 'sandbox' if opt['is_sandbox'] else 'live'
        self.chat_done = False
        self.check_acceptability = opt['check_acceptability']
        self.acceptability_checker = AcceptabilityChecker()
        self.block_qualification = opt['block_qualification']

        self.final_chat_data = None
        # TODO: remove this attribute once chat data is only stored in the Mephisto
        #  TaskRun for this HIT (see .get_custom_task_data() docstring for more
        #  information)

        # below are timeout protocols
        self.max_resp_time = max_resp_time  # in secs
        log.info(
            f'Creating {self.__class__.__name__} for tag {self.tag} with {num_turns} turns.'
        )

    def __add_problem_data_to_utterance(self, p, turn_idx: int):
        """
        Attach problem data to the bot's prior utterance, given by turn_idx.
        """
        log.info(p)
        assert (
            self.dialog[turn_idx]['agent_idx'] == 1
        ), 'Problem data must be attached to a bot utterance.'
        assert (
            'problem_data' not in self.dialog[turn_idx]
        ), "Don't overwrite existing problem data!"
        self.dialog[turn_idx]['problem_data'] = p

    def parley(self):
        log.info(f'{self.__class__.__name__}:{self.tag}: is at turn'
                 '{self.task_turn_idx}, with {self.num_turns} pairs of turns needed...'
        )

        if self.task_turn_idx == 0:
            self._run_initial_turn()
            self.task_turn_idx += 1
            return

        """Otherwise, we proceed accordingly"""
        log.info(f'{self.__class__.__name__}:{self.tag}: '
                 'About to act with task turn idx: {self.task_turn_idx}')
        acts = [None, None]

        self.agent.agent_id = self.target_user
        for idx, agent in enumerate([self.agent, self.bot]):
            if not self.chat_done:
                acts[idx] = agent.act(timeout=self.max_resp_time)
                if self.mt:
                    text = acts[idx]['text']
                    acts[idx]['text_orig'] = text
                    mt_fn = self.mt.maybe_preprocess if idx == 0\
                        else self.mt.maybe_postprocess
                    text = mt_fn(text)
                    # agent's act is a custom datatype, which requires force_set
                    # but bot's act is a dict, which dont have force_set()
                    if hasattr(acts[idx], 'force_set'):
                        acts[idx].force_set('text', text)
                    else:
                        acts[idx]['text'] = mt_fn(text)
                if agent == self.bot and\
                    hasattr(self.bot, 'agent_id') and self.bot.agent_id:
                    # Set speaker name as self.bot_agent_id otherwise, at frontend bot name such as "TransformerGenerator" would appear
                    Compatibility.backward_compatible_force_set(acts[idx], 'id', self.bot.agent_id)
                acts[idx] = Message(Compatibility.maybe_fix_act(acts[idx])).json_safe_payload()
                log.info(f'Got act for agent idx {idx}, act was: {acts[idx]} '
                         'and self.task_turn_idx: {self.task_turn_idx}.')

            if acts[idx].get('task_data', {}).get('final_rating') is not None:

                self.chat_done = True
                # agent ends chat after exceeding minimum number of turns

                # Human has just responded. Any problem data received now will be
                # regarding the bot's prior utterance
                turn_idx = -1
                # Attach the problem data and final rating to the last utterance, since
                # the human hasn't said anything since then
                p = acts[idx]['task_data'].get('problem_data_for_prior_message')
                if p is not None:
                    self.__add_problem_data_to_utterance(p, turn_idx=turn_idx)
                self.dialog[turn_idx]['final_rating'] = acts[idx]['task_data']['final_rating']

                # Save the final chat data
                date_folder = time.strftime('%Y_%m_%d')
                time_string = time.strftime('%Y%m%d_%H%M%S')
                chat_data_subfolder = os.path.join(self.opt['chat_data_folder'], date_folder)
                os.makedirs(chat_data_subfolder, exist_ok=True)
                chat_data_path = os.path.join(chat_data_subfolder,
                    f'{time_string}_{np.random.randint(0, 1000)}_{self.task_type}.json')
                self.final_chat_data = self.get_final_chat_data()
                self.agent.mephisto_agent.state.messages.append({
                        'final_chat_data': self.final_chat_data,
                        'data': {},
                        'packet_type': None,
                        'timestamp': None,
                    }
                )
                # Append the chat data directly to the agent state's message list in
                # order to prevent the worker from seeing a new text response in the UI.
                # Add some dummy keys for compatibility with all agent state messages
                # TODO: remove this when no longer saving data to disk manually
                with open(chat_data_path, 'w+') as f_json:
                    data_str = json.dumps(self.final_chat_data)
                    f_json.write(data_str)
                log.info(f'{self.__class__.__name__}:{self.tag}: Data saved at '
                    f'{chat_data_path} for model: {self.bot.worker_id}.')

                # Soft-block the worker if there were acceptability violations
                acceptability_violations = self.final_chat_data['acceptability_violations'][0]
                if acceptability_violations is not None and acceptability_violations != '':
                    log.info(f'**NOTE** Acceptability violations detected: {acceptability_violations}')
                    # Grant the failed qualification
                    self.agent.mephisto_agent.get_worker().grant_qualification(
                        self.block_qualification, 1)
                return
            else:
                # if idx == 1:
                #     user_name= "BOT"
                # else:
                #     user_name = self.target_user
                utterance_data = {
                    'agent_idx': idx,
                    # Get rid of annotations HTML if it's the bot response
                    'text': acts[idx]['text'].split('<br>')[0],
                    'id': acts[idx].get('id', 'NULL_ID'),  # In case model doesn't set id
                }
                self.dialog.append(utterance_data)
                if idx == 0:
                    # Human has just responded. Any problem data received now will be
                    # regarding the bot's prior utterance
                    p = acts[idx]['task_data'].get(
                        'problem_data_for_prior_message')
                    if p is not None:
                        turn_idx = -2
                        # Attach the problem data to the second-to-last utterance, since
                        # the last utterance is what the human just said
                        self.__add_problem_data_to_utterance(p, turn_idx=turn_idx)

                self._postprocess_acts(acts=acts, agent_idx=idx)
                for other_agent in [self.agent, self.bot]:
                    if other_agent != agent:
                        other_agent.observe(validate(acts[idx]))

                log.info(f'[agent {idx}] self.task_turn_idx: '
                         '{self.task_turn_idx}, self.dialog is: {self.dialog}')

                self.task_turn_idx += 1

    @abstractmethod
    def _run_initial_turn(self) -> None:
        """
        Runs logic for the first turn of the human and the bot.
        """
        pass

    def _postprocess_acts(self, acts: List[dict], agent_idx: int):
        """
        Optionally perform further processing of the acts.

        Useful for subclasses. Will be executed after saving act data to self.dialog but
        before showing the act to the other agent.
        """
        pass

    def shutdown(self):

        if self.chat_done:
            self.opt['run_statistics'][self.bot.worker_id] += 1
            log.info('Runs completed per model: ' + ', '.join(
                f'{model}: {count:d}' for model, count in self.opt['run_statistics'].items()))

        self.agent.shutdown()

    def episode_done(self):
        return self.chat_done

    def get_final_chat_data(self) -> Dict[str, Any]:
        """
        Return specific info about the conversation, the context, acceptability, etc.
        """

        if self.check_acceptability:
            human_messages, violation_types = self._prepare_acceptability_checking()
            violations_string = self.acceptability_checker.check_messages(
                messages=human_messages,
                is_worker_0=False,
                violation_types=violation_types,
            )
        else:
            violations_string = None

        data = {
            'dialog': self.dialog,
            'workers': [get_mturk_id_from_mephisto_wrapper(self.agent)],
            'bad_workers': [],
            'acceptability_violations': (violations_string,),
            'hit_ids': [self.agent.mephisto_agent.task_run_id],
            'assignment_ids': [self.agent.mephisto_agent.assignment_id],
            'task_description': {
                'annotations_config': self.opt['annotations_config'],
                'model_nickname': self.bot.worker_id,
                'model_file': self.bot.model_agent.opt.get('model_file'),
                'model_opt': self.bot.model_agent.opt,
            },
        }
        # TODO: once the analysis scripts are fully switched over to DataBrowser, remove
        #  the 'workers' and 'assignment_ids' keys, which will now be duplicated in the
        #  returned Unit
        # TODO: 'bad_workers' is for compatibility. Before, it was only non-empty if a
        #  worker abandoned, returned, etc. a HIT, but now we don't even save chat
        #  data in that case. Remove this key once fully once on DataBrowser
        if self.check_acceptability:
            data['acceptability_violations'] = (violations_string,)
            # Make a tuple for compatibility with a human/human conversation in
            # which we check both sides for acceptability

        return data

    def get_custom_task_data(self):
        """
        Retrieves the final chat data for storage in the Mephisto database.

        TODO: the final chat data is currently stored both in
         mephisto.blueprint.chat_data_folder and in the Mephisto database. It'd be best
         to remove the chat_data_folder arg completely, and to move the current logic in
         self.get_final_chat_data() into this method, in order to have a single storage
         location.
        """
        return self.final_chat_data

    def _prepare_acceptability_checking(self) -> Tuple[List[str], List[str]]:
        """
        Return the list of human messages and the list of acceptability types to check.
        """
        human_messages = [
            message['text'] for message in self.dialog if message['agent_idx'] == 0
        ]
        violation_types = ['min_words', 'all_caps', 'exact_match', 'safety']
        return human_messages, violation_types


class ModelChatWorld(BaseModelChatWorld):
    """
    Version of BaseModelChatWorld for chatting without images.

    Has support for features that are currently not supported by the image-chat version
    of this task, like personas and BST-style seed utterances.
    """

    def __init__(self, opt, agent, bot, context_info: Optional[dict] = None,
                 mt: Optional[DialogTranslator]=None):
        super().__init__(opt, agent=agent, bot=bot, mt=mt)

        if context_info is not None:
            self.context_info = context_info
        else:
            self.context_info = {}

    def _run_initial_turn(self) -> None:
        """
        Run the initial turn for both the human and the bot.

        Optionally show the bot its persona. If we are in BST conversation mode, show 2
        previous BST utterances to both the human and the bot; if we are in Meena-like
        conversation mode, show "Hi!" to the human and the bot and let the bot respond
        accordingly.
        """

        control_msg = {"episode_done": False}
        if self.opt['conversation_start_mode'] == "empty":
            pass

        elif self.opt['conversation_start_mode'] == "custom":
            log.info(
                "Use custom dialogue seeds to start conversations with some context")
            log.info(f"Context info: {self.context_info}")

            dialogue = self.context_info["conversation"]

            # make each turn in the context be from the bot except for the target user
            self.target_user = self.context_info["target_user"]
            for idx, turn in enumerate(dialogue):

                msg = {
                    'episode_done': False,
                    'id': turn['speaker_id'],
                    'text': turn['text'],
                    'fake_start': True,
                    'agent_idx': 0 if turn['speaker_id'] == self.target_user else 1,
                }
                # if turn["speaker_id"] == self.target_user:
                #     msg['id'] = self.agent.agent_id
                # else:
                #     msg['id'] = self.bot.agent_id

                self.dialog.append(msg)
                self.agent.observe(validate(msg))
                self.bot.observe(validate(msg))

                # bot responds to the last turn
                if idx == len(dialogue) - 1:
                    first_bot_act = self.bot.act()
                    first_bot_act = Compatibility.backward_compatible_force_set(
                        first_bot_act, 'id', self.bot.agent_id
                    )

                    self.agent.observe(validate(first_bot_act))

                    bot_utterance_data = {
                        'agent_idx': 1,
                        'text': first_bot_act['text'],
                        'id': "BOT",
                    }
                    self.dialog.append(bot_utterance_data)
        else:
            raise ValueError(
                f"Conversation start mode {self.opt['conversation_start_mode']} "
                f"not recognized!"
            )

    def get_final_chat_data(self) -> Dict[str, Any]:
        """
        Add non-image-chat-specific fields to the final chat data.
        """
        data = super().get_final_chat_data()
        context_data = {
            'context_dataset': self.context_info.get('context_dataset'),
            'person1_seed_utterance': self.context_info.get('person1_seed_utterance'),
            'person2_seed_utterance': self.context_info.get('person2_seed_utterance'),
            'additional_context': self.context_info.get('additional_context'),
        }
        data.update(context_data)
        return data

    def _prepare_acceptability_checking(self) -> Tuple[List[str], List[str]]:
        """
        Apply acceptability checking params specific to BST-style conversation.

        The BST mode starts the conversation with two previous utterances, so there
        should be no new greeting. Also, the first human response is one of the previous
        utterances, so it shouldn't get checked.
        """
        human_messages, violation_types = super()._prepare_acceptability_checking()
        if self.opt['conversation_start_mode'] == 'blended_skill_talk':
            violation_types.append('penalize_greetings')
            human_messages = human_messages[1:]
        return human_messages, violation_types


def make_onboarding_world(opt, agent):
    return ModelChatOnboardWorld(opt, agent)


def validate_onboarding(data):
    """
    Check the contents of the data to ensure they are valid.
    """
    log.info(f"Validating onboarding data {data}")
    messages = data['outputs']['messages']
    if len(messages) == 0:
        return False
    status_message = messages[-2]
    if status_message is None:
        return False
    final_status = status_message.get('final_status')
    return final_status == ONBOARD_SUCCESS


def get_bot_worker(opt: Dict[str, Any], model_name: str) -> TurkLikeAgent:
    """
    Return a bot agent.

    Agent behaves like a crowdsource worker but actually wraps around a dialogue model.
    """
    semaphore = opt['semaphore']
    shared_bot_agents = opt['shared_bot_agents']
    num_turns = opt['num_turns']
    bot_agent = create_agent_from_shared(shared_bot_agents[model_name])
    bot_worker = TurkLikeAgent(
        opt,
        model_name=model_name,
        model_agent=bot_agent,
        num_turns=num_turns,
        semaphore=semaphore,
    )
    return bot_worker

def get_dialog_mt(opt: Dict[str, Any]):
    if 'translator' not in opt or opt['translator'].get('activation') == None:
        log.info("translator is either disabled or not configured")
        return None
    args = opt['translator']
    assert args['activation'] in {'pre', 'post', 'pre+post'}
    pre_mt, post_mt = None, None
    if 'pre' in args['activation']:
        pre_mt = get_translator(name=args['preprocess'],
                                args=args['preprocess_args'])
    if 'post' in args['activation']:
        post_mt = get_translator(name=args['postprocess'],
                                args=args['postprocess_args'])
    mt = DialogTranslator(pre_translator=pre_mt, post_translator=post_mt)
    return mt

def make_world(opt, agents):

    # Extract important components from opt
    statistics_condition = opt['statistics_condition']
    context_generator = opt['context_generator']

    # Get context: personas, previous utterances, etc.
    if context_generator is not None:
        context_info = context_generator.get_context(DarmaContextGenerator.idx)
        DarmaContextGenerator.idx += 1
    else:
        context_info = None

    # Decide on a bot to use
    run_statistics = opt['run_statistics']
    with statistics_condition:
        remaining_counts_needed = [
            (m, c - run_statistics[m]) for (m, c) in opt['conversations_needed'].items()
        ]
        remaining_counts_needed.sort(reverse=True, key=lambda x: x[1])
        model_name = remaining_counts_needed[0][0]
        log.info(
            f'Remaining conversation counts needed: {remaining_counts_needed}')
        log.info(f'Choosing the "{model_name}" model for the bot.')
    bot_worker = get_bot_worker(opt=opt, model_name=model_name)
    mt = get_dialog_mt(opt=opt)

    return ModelChatWorld(opt, agent=agents[0], bot=bot_worker, mt=mt,
                          context_info=context_info)


def get_world_params():
    return {"agent_count": 1}

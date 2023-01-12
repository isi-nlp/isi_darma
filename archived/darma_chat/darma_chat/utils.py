#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import base64
import datetime
import json
import os
import random
import threading
import time
import unittest
from io import BytesIO
from typing import Any, Dict, Optional, Tuple

from PIL import Image

from parlai.core.message import Message
from parlai.core.metrics import Metric
from parlai.core.params import ParlaiParser
from parlai.core.loader import load_task_module
from parlai.crowdsourcing.utils.tests import AbstractParlAIChatTest
from parlai.tasks.blended_skill_talk.agents import ContextGenerator


class Compatibility(object):
    """
    Class to address backward compatibility issues with older ParlAI models.
    """

    @staticmethod
    def backward_compatible_force_set(act, key, value):
        if isinstance(act, Message):
            act.force_set(key, value)
        elif isinstance(act, dict):
            act[key] = value
        else:
            raise Exception(f'Unknown type of act: {type(act)}')
        return act

    @staticmethod
    def maybe_fix_act(incompatible_act):
        if 'id' not in incompatible_act:
            new_act = Compatibility.backward_compatible_force_set(
                incompatible_act, 'id', 'NULL_ID'
            )
            return new_act
        return incompatible_act

    @staticmethod
    def serialize_bot_message(bot_message):
        if 'metrics' in bot_message:
            metric_report = bot_message['metrics']
            bot_message['metrics'] = {
                k: v.value() if isinstance(v, Metric) else v
                for k, v in metric_report.items()
            }
        return bot_message


class DarmaContextGenerator: 

    idx = 0 
    def __init__(self, opt): 
        self.opt = opt 
        self._load_data()

    def _load_data(self): 

        with open(self.opt["seed_conversation_source"], "r") as f: 
            self.seed_dialogues = json.load(f)

    def get_context(self, idx_): 
        return self.seed_dialogues[idx_]



class AbstractModelChatTest(AbstractParlAIChatTest, unittest.TestCase):
    """
    Abstract test class for testing model chat code.
    """

    def _remove_non_deterministic_keys(self, actual_state: dict) -> dict:

        # Remove non-deterministic keys from each message
        for message in actual_state['outputs']['messages']:
            for field in ['update_id', 'timestamp']:
                if field in message:
                    del message[field]

        # TODO: in `self._check_output_key()`, there is other logic for ignoring
        #  keys with non-deterministic values. Consolidate all of that logic here!
        custom_data = self._get_custom_data(actual_state)
        # Delete keys that will change depending on when/where the test is run
        for key in ['model_file']:
            del custom_data['task_description'][key]
        for key in ['datapath', 'dict_file', 'model_file', 'parlai_home', 'starttime']:
            if key in custom_data['task_description']['model_opt']:
                del custom_data['task_description']['model_opt'][key]
        for key in ['model_file']:
            if key in custom_data['task_description']['model_opt']['override']:
                del custom_data['task_description']['model_opt']['override'][key]

        return actual_state

    def _filter_agent_state_data(self, agent_state: dict) -> dict:
        """
        Remove agent state messages that do not contain text or final chat data and are thus not useful for testing the crowdsourcing task.
        """
        filtered_messages = [
            m
            for m in agent_state['outputs']['messages']
            if 'text' in m or 'final_chat_data' in m
        ]
        filtered_agent_state = {
            'inputs': agent_state['inputs'],
            'outputs': {**agent_state['outputs'], 'messages': filtered_messages},
        }
        return filtered_agent_state

    def _get_custom_data(self, actual_state: dict) -> dict:
        """
        Return the custom task data (without making a copy).

        The last message contains the custom data saved by the model-chat task code.
        """
        return actual_state['outputs']['messages'][-1]['WORLD_DATA']['custom_data']

    def _check_output_key(self, key: str, actual_value: Any, expected_value: Any):
        """
        Special logic for handling the 'final_chat_data' key.
        """
        if key == 'final_chat_data':
            self._check_final_chat_data(
                actual_value=actual_value, expected_value=expected_value
            )
        else:
            super()._check_output_key(
                key=key, actual_value=actual_value, expected_value=expected_value
            )

    def _check_final_chat_data(
        self, actual_value: Dict[str, Any], expected_value: Dict[str, Any]
    ):
        """
        Check the actual and expected values of the final chat data.

        TODO: this is hard to maintain. It'd be better to just delete the non-deterministic keys from actual_value beforehand, inside self._remove_non_deterministic_keys().
        """
        for key_inner, expected_value_inner in expected_value.items():
            if key_inner == 'dialog':
                assert len(actual_value[key_inner]) == len(expected_value_inner)
                for actual_message, expected_message in zip(
                    actual_value[key_inner], expected_value_inner
                ):
                    clean_actual_message = {
                        k: v for k, v in actual_message.items() if k != 'update_id'
                    }
                    clean_expected_message = {
                        k: v for k, v in expected_message.items() if k != 'update_id'
                    }
                    self.assertDictEqual(
                        clean_actual_message,
                        clean_expected_message,
                        f'The following dictionaries are different: {clean_actual_message} and {clean_expected_message}',
                    )
            elif key_inner == 'task_description':
                for (key_inner2, expected_value_inner2) in expected_value_inner.items():
                    if key_inner2 == 'model_file':
                        pass
                        # The path to the model file depends on the random
                        # tmpdir
                    elif key_inner2 == 'model_opt':
                        keys_to_ignore = [
                            'datapath',
                            'dict_file',
                            'model_file',
                            'override',
                            'parlai_home',
                            'starttime',
                        ]
                        # These paths depend on the random tmpdir and the host
                        # machine
                        for (
                            key_inner3,
                            expected_value_inner3,
                        ) in expected_value_inner2.items():
                            if key_inner3 in keys_to_ignore:
                                pass
                            else:
                                self.assertEqual(
                                    actual_value[key_inner][key_inner2][key_inner3],
                                    expected_value_inner3,
                                    f'Error in key {key_inner3}!',
                                )
                    else:
                        self.assertEqual(
                            actual_value[key_inner][key_inner2],
                            expected_value_inner2,
                            f'Error in key {key_inner2}!',
                        )
            else:
                self.assertEqual(
                    actual_value[key_inner],
                    expected_value_inner,
                    f'Error in key {key_inner}!',
                )


def get_context_generator(
    override_opt: Optional[Dict[str, Any]] = None,
    task: Optional[str] = 'blended_skill_talk',
    **kwargs,
) -> DarmaContextGenerator:
    """
    Return an object to return BlendedSkillTalk-style context info (personas, etc.).
    """
    argparser = ParlaiParser(False, False)
    argparser.add_parlai_data_path()
    if override_opt is not None:
        argparser.set_params(**override_opt)
    opt = argparser.parse_args([])
    task_module = load_task_module(task)
    context_generator_class = getattr(task_module, 'ContextGenerator', None)
    context_generator = context_generator_class(opt, datatype='test', seed=0, **kwargs)
    # We pull from the test set so that the model can't regurgitate
    # memorized conversations
    return context_generator



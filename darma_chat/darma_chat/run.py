#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
from dataclasses import dataclass, field
from typing import Any, List
from pathlib import Path

import hydra
from omegaconf import DictConfig
from mephisto.operations.hydra_config import register_script_config
from parlai.crowdsourcing.utils.mturk import MTurkRunScriptConfig

from darma_chat.impl import run_task

"""
Read parlai/crowdsourcing/README.md to learn how to launch
crowdsourcing tasks with this script.
"""

TASK_DIRECTORY = Path(__file__).parent.resolve()
CWD = Path(".").resolve()

defaults = ["_self_", {"conf": "darma"}]


@dataclass
class ScriptConfig(MTurkRunScriptConfig):
    defaults: List[Any] = field(default_factory=lambda: defaults)
    task_dir: str = TASK_DIRECTORY
    monitoring_log_rate: int = field(
        default=30,
        metadata={
            'help': 'Frequency in seconds of logging the monitoring of the crowdsourcing task'
        },
    )


register_script_config(name='scriptconfig', module=ScriptConfig)


@hydra.main(config_path="hydra_configs", config_name="scriptconfig")
def main(cfg: DictConfig) -> None:
    run_task(cfg=cfg, task_directory=TASK_DIRECTORY)


if __name__ == "__main__":
    main()

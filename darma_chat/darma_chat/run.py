#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


from curses import meta
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

import time
import hydra
from omegaconf import DictConfig, MISSING
from mephisto.operations.hydra_config import RunScriptConfig
from mephisto.operations.hydra_config import register_script_config

from darma_chat.impl import run_task

"""
Read parlai/crowdsourcing/README.md to learn how to launch
crowdsourcing tasks with this script.
"""

TASK_DIRECTORY = Path(__file__).parent.resolve()
CWD = Path(".").resolve()

defaults = ["_self_", {"conf": "darma"}]


@dataclass
class MTurkConfig:
    """
    Add MTurk-specific flags.
    """

    worker_blocklist_paths: Optional[str] = field(
        default=MISSING,
        metadata={
            "help": (
                'Path(s) to a list of IDs of workers to soft-block, separated by newlines. Use commas to indicate multiple lists'
            )
        },
    )

    allowed_locales: List[Dict] = field(
        default=MISSING,
        metadata={
            "help": (
                'List of locales for HITs'
            )
        },
    )



@dataclass
class DarmaRunConfig(RunScriptConfig):

    current_time: int = int(time.time())  # For parametrizing block_qualification
    defaults: List[Any] = field(default_factory=lambda: defaults)
    task_dir: str = TASK_DIRECTORY
    monitoring_log_rate: int = field(
        default=30,
        metadata={
            'help': 'Frequency in seconds of logging the monitoring of the crowdsourcing task'
        },
    )
    mturk: MTurkConfig = MTurkConfig()


register_script_config(name='scriptconfig', module=DarmaRunConfig)


@hydra.main(config_path="hydra_configs", config_name="scriptconfig")
def main(cfg: DictConfig) -> None:
    run_task(cfg=cfg, task_directory=TASK_DIRECTORY)


if __name__ == "__main__":
    main()

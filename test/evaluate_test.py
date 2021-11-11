import os
import sys
sys.path.append(os.path.realpath('.'))

from zerosum_env import make
from zerosum_env.envs.carbon.carbon import random_agent
from zerosum_env.envs.carbon.helpers import *
from utils import *

import unittest


class EvaluateTest(unittest.TestCase):

    """Test on the evaluation process
    """

    # Test case @4.2
    def test_carbon_completes(self):
        env = make("carbon", configuration={"episodeSteps": 100})
        env.run([random_agent, random_agent])
        json = env.toJSON()
        self.assertEqual(json["name"], "Carbon Neutrality")
        self.assertEqual(json["statuses"], ["DONE", "DONE"])

    # Test case @4.3
    def test_carbon_exception_action_has_error_status(self):
        env = make("carbon", configuration={"episodeSteps": 100})

        def error_agent(obs, config):
            raise Exception("An exception occurred!")
        env.run([error_agent, random_agent])
        json = env.toJSON()
        self.assertEqual(json["name"], "Carbon Neutrality")
        self.assertEqual(json["statuses"], ["ERROR", "DONE"])

    # Test case 4.4
    def test_carbon_helpers(self):
        env = make("carbon", configuration={"size": 3})

        @board_agent
        def helper_agent(board):
            for worker in board.current_player.workers:
                worker.next_action = WorkerAction.UP
            for recrtCenter in board.current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR

        env.run([helper_agent, helper_agent])

        json = env.toJSON()
        self.assertEqual(json["name"], "Carbon Neutrality")
        self.assertEqual(json["statuses"], ["DONE", "DONE"])


if __name__ == '__main__':
    unittest.main()
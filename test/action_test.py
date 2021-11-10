import os
import sys
sys.path.append(os.path.realpath('.'))

import unittest
from utils import *


class ActionTest(unittest.TestCase):
    """
    Test on the built-in action function
    """

    # Test case @2.1
    def test_recrtCenter_command_reccollector(self):
        board_size = 15
        recPlantorCost = 30
        recCollectorCost = 30
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 5, "recPlantorCost": recPlantorCost,
                                            "recCollectorCost": recCollectorCost}, debug=True)
        agent_count = 2
        env.reset(agent_count)

        def recrtCenter_reccollector_agent(observation, configuration):
            board = Board(observation, configuration)
            current_player = board.current_player
            for recrtCenter in current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
            return current_player.next_actions

        env.run([recrtCenter_reccollector_agent, "random"])

        # check action
        self.assertEqual(env.steps[1][0]["action"]["player-0-recrtCenter-0"], "RECCOLLECTOR")
        # check position
        self.assertEqual(env.steps[1][0]["observation"]["players"][0][1]["player-0-recrtCenter-0"],
                         env.steps[1][0]["observation"]["players"][0][2]["player-0-worker-0"][0])
        # check role
        self.assertEqual(env.steps[1][0]["observation"]["players"][0][2]["player-0-worker-0"][2], "COLLECTOR")

    # Test case @2.3
    def test_reccollector_command(self):
        board_size = 15
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 10}, debug=True)
        agent_count = 2

        def move_agent(observation, configuration):
            board = Board(observation, configuration)
            current_player = board.current_player
            for recrtCenter in current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
            for worker in current_player.workers:
                worker.next_action = action
            return current_player.next_actions

        for _, action in enumerate(WorkerAction):
            env.reset(agent_count)
            env.run([move_agent, "random"])
            for step in env.steps[2:]:
                self.assertEqual(step[0]["action"]["player-0-worker-0"], str(action))


        def still_agent(observation, configuration):
            board = Board(observation, configuration)
            current_player = board.current_player
            for recrtCenter in current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
            return current_player.next_actions

        board_size = 15
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 10}, debug=True)
        agent_count = 2
        env.reset(agent_count)
        env.run([still_agent, "random"])
        original_position = env.steps[1][0]["observation"]["players"][0][2]["player-0-worker-0"][0]
        for step in env.steps[2:]:
            self.assertEqual(step[0]["observation"]["players"][0][2]["player-0-worker-0"][0], original_position)


if __name__ == '__main__':
    unittest.main()

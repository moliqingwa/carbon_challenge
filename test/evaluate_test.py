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

    # Test case @4.1
    def test_carbon_no_repeated_steps(self):
        step_count = 10
        actual_steps = []

        def step_appender_agent(obs, config):
            actual_steps.append(obs.step)
            return {}

        env = make("carbon", configuration={"episodeSteps": step_count}, debug=True)
        env.run([step_appender_agent])
        self.assertEqual(actual_steps, list(range(step_count - 1)))

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

    # Test case 4.5
    def test_player_command_effect(self):

        board_size = 15
        environment = make("carbon", configuration={"size": board_size, "episodeSteps": 20}, debug=True)

        global obs1, obs1_id, obs2, obs2_id
        obs1, obs2, obs1_id, obs2_id = None, None, None, None

        def move_workers_right_agent(observation, configuration):
            global obs1, obs1_id
            obs1 = observation  # save as global variable in case of garbage collection
            obs1_id = id(observation)
            board = Board(observation, configuration)
            current_player = board.current_player
            if len(current_player.workers) == 0:
                for recrtCenter in board.current_player.recrtCenters:
                    recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
            else:
                for worker in current_player.workers:
                    worker.next_action = WorkerAction.RIGHT
            return current_player.next_actions

        def move_workers_up_agent(observation, configuration):
            global obs2, obs2_id
            obs2 = observation  # save as global variable in case of garbage collection
            obs2_id = id(observation)
            board = Board(observation, configuration)
            worker_action = {}
            current_player = board.current_player
            if len(current_player.workers) == 0:
                for recrtCenter in board.current_player.recrtCenters:
                    recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
                worker_action.update(current_player.next_actions)
            else:
                for worker in current_player.workers:
                    worker.next_action = WorkerAction.UP
                worker_action.update(current_player.next_actions)
                opponent = board.opponents
                for opponent in board.opponents:
                    for worker in opponent.workers:
                        worker.next_action = WorkerAction.UP
                    worker_action.update(opponent.next_actions)
            
            return worker_action

        environment.run([move_workers_right_agent, move_workers_up_agent, "random", "random"])

        self.assertEqual(environment.steps[2][0]["action"]["player-0-worker-0"], "RIGHT")
        self.assertEqual(environment.steps[2][1]["action"]["player-1-worker-0"], "UP")
        self.assertNotEqual(obs1, obs2)
        self.assertNotEqual(obs1_id, obs2_id)

    # Test case 4.6
    def test_recrtCenter_ids_not_reused(self):
        board = create_board(starting_carbon=1000, agent_count=1)
        recrtCenter = first(board.recrtCenters.values())
        recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        worker = board.cells[recrtCenter.position].worker
        self.assertNotEqual(worker.id, recrtCenter.id)

    # Test case 4.7
    def test_seed_parameter(self):
        
        seed = 9

        def aggregate_carbon_for_board(seed):
            board = create_board(starting_carbon=1000, agent_count=1, random_seed=seed)
            return sum(map(lambda c: c.carbon, board.cells.values()))

        def check_player_position(seed):
            board = create_board(starting_carbon=1000, agent_count=1, random_seed=seed)
            for worker in board.workers.values():
                return worker.position

        def get_position_sequence(seed):
            board = create_board(starting_carbon=1000, agent_count=1, random_seed=seed)
            position = []
            for recrtCenter in board.current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
            board = board.next()
            for _ in range(50):
                worker = first(board.workers.values())
                worker.next_action = WorkerAction.RIGHT
                position.append(worker.position)
                board = board.next()
            return position
        
        self.assertEqual(aggregate_carbon_for_board(seed), aggregate_carbon_for_board(seed))
        self.assertEqual(check_player_position(seed), check_player_position(seed))

        for pos1, pos2 in zip(get_position_sequence(seed), get_position_sequence(seed)):
            self.assertEqual(pos1, pos2)


if __name__ == '__main__':
    unittest.main()
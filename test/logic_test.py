import os
import sys

sys.path.append(os.path.realpath('.'))

import unittest
from utils import *


class LogicTest(unittest.TestCase):
    """
    Test on the formulation logic of the simulator
    """

    # Test case @1.1
    def test_cells_regen_carbon(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05)
        cell = first(board.cells.values())
        next_board = board.next()
        next_cell = next_board[cell.position]
        expected_regen = round(cell.carbon * board.configuration.regen_rate, 3)
        # We compare to a floating point value here to handle float rounding errors
        self.assertLess(next_cell.carbon - cell.carbon - expected_regen, .000001)


    # Test case @1.3
    def test_recrtCenter_reccollector_fail(self):
        def recrtCenter_reccollector_agent(observation, configuration):
            board = Board(observation, configuration)
            current_player = board.current_player
            for recrtCenter in current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
            return current_player.next_actions

        # check fail for money
        board_size = 15
        recCollectorCost = 60
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 5,
                                            "recCollectorCost": recCollectorCost}, debug=True)
        agent_count = 2
        env.reset(agent_count)
        env.run([recrtCenter_reccollector_agent, "random"])

        # check action
        self.assertEqual(env.steps[1][0]["action"]["player-0-recrtCenter-0"], "RECCOLLECTOR")
        # check count
        self.assertEqual(len(env.steps[1][0]["observation"]["players"][0][2]), 0)
        print("1 ok")

        # check fail for count
        board_size = 15
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 5, "workerLimit": 1}, debug=True)
        agent_count = 2
        env.reset(agent_count)
        env.run([recrtCenter_reccollector_agent, "random"])

        # check action
        self.assertEqual(env.steps[1][0]["action"]["player-0-recrtCenter-0"], "RECCOLLECTOR")
        # check count
        self.assertEqual(len(env.steps[1][0]["observation"]["players"][0][2]), 1)
        print("2 ok")


    # Test case @1.10
    def test_collector_stay_opponent_recrtCenter(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                opponent_recrtCenter_position = recrtCenter.position
        worker = first(board.workers.values())
        worker._position = opponent_recrtCenter_position
        next_board = board.next()
        self.assertEqual(me.cash - board.configuration.rec_collector_cost, next_board.current_player.cash)
        self.assertEqual(worker.carbon, first(board.workers.values()).carbon)
        print(board)
        print(next_board)


    # Test case @1.31
    def test_termination(self):
        board_size = 21
        collector_cost = 20
        env = make("carbon",
                   configuration={"size": board_size, "recCollectorCost": collector_cost})
        agent_count = 2
        env.reset(agent_count)

        def convert_agent(observation, configuration):
            board = Board(observation, configuration)
            current_player = board.current_player
            for recrtCenter in current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
            return current_player.next_actions

        env.run([convert_agent, "random"])
        self.assertEqual(len(env.steps), 3)



    def test_planter_plant_trees(self):
        size = 7
        rec_cost = 5
        plant_cost = 5
        plant_inflation_rate = 5
        env = make("carbon", configuration={"size": size, "recPlanterCost": rec_cost, "recCollectorCost": rec_cost,
                                            "workerLimit": 5,
                                            "cellAbsorptionRate": 0, "collectorAbsorptionRate": 0,
                                            "plantCost": plant_cost, "plantCostInflationRatio": plant_inflation_rate})
        board = Board(env.reset(2)[0].observation, env.configuration)
        cash = board.current_player.cash
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        cash -= rec_cost
        self.assertEqual(board.current_player.cash, cash)

        first(board.current_player.planters).next_action = WorkerAction.UP
        board = board.next()
        board = board.next()  # 种树
        board = board.next()
        cash -= plant_cost
        self.assertEqual(board.current_player.cash, cash)

        first(board.current_player.planters).next_action = WorkerAction.UP
        board = board.next()
        board = board.next()  # 种树
        cash -= (plant_cost + plant_inflation_rate)
        self.assertEqual(board.current_player.cash, cash)
        for _ in range(50):  # 50轮后重新种树
            board = board.next()
        cash -= plant_cost
        self.assertEqual(board.current_player.cash, cash)

        first(me.planters).next_action = WorkerAction.UP


if __name__ == '__main__':
    unittest.main()

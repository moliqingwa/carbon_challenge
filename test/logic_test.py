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

    # Test case @1.2
    def test_cells_regen_carbon_upper_limit(self):
        board = create_board(starting_carbon=1000, size=2, random_seed=1, regenRate=3, startPosOffset=1)
        cell = first(board.cells.values())
        next_board = board.next()
        next_cell = next_board[cell.position]
        self.assertEqual(next_cell.carbon, 100)

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

    # Test case @1.4
    def test_recrtCenter_recplanter_fail(self):
        def recrtCenter_recplanter_agent(observation, configuration):
            board = Board(observation, configuration)
            current_player = board.current_player
            for recrtCenter in current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER
            return current_player.next_actions

        # check fail for money
        board_size = 15
        recPlanterCost = 60
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 5,
                                            "recPlanterCost": recPlanterCost}, debug=True)
        agent_count = 2
        env.reset(agent_count)
        env.run([recrtCenter_recplanter_agent, "random"])

        # check action
        self.assertEqual(env.steps[1][0]["action"]["player-0-recrtCenter-0"], "RECPLANTER")
        # check count
        self.assertEqual(len(env.steps[1][0]["observation"]["players"][0][2]), 0)
        print("1 ok")

        # check fail for count
        board_size = 15
        recPlanterCost = 25
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 5,
                                            "recPlanterCost": recPlanterCost, "workerLimit": 1}, debug=True)
        agent_count = 2
        env.reset(agent_count)
        env.run([recrtCenter_recplanter_agent, "random"])

        # check action
        self.assertEqual(env.steps[1][0]["action"]["player-0-recrtCenter-0"], "RECPLANTER")
        self.assertEqual(env.steps[2][0]["action"]["player-0-recrtCenter-0"], "RECPLANTER")
        # check count
        self.assertEqual(len(env.steps[2][0]["observation"]["players"][0][2]), 1)
        print("2 ok")

    # Test case @1.5
    def test_collector_no_move_on_carbon_gathers_carbon(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=2, agent_count=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        worker = first(board.workers.values())
        collect_rate = max(board.configuration.initial_collect_rate -
                           len(board.players[worker.player_id].collectors) * board.configuration.collect_decrease_rate,
                           0)
        expected_delta = round(worker.cell.carbon * collect_rate, 2)
        next_board = board.next()
        next_worker = next_board.workers[worker.id]
        worker_delta = next_worker.carbon - worker.carbon
        cell_delta = round(worker.cell.carbon - next_worker.cell.carbon, 2)
        print(board)
        print(next_board)
        print(worker_delta, expected_delta)
        print(cell_delta, expected_delta)
        self.assertEqual(worker_delta, expected_delta)
        self.assertEqual(cell_delta, expected_delta)

    # Test case @1.6
    def test_collector_move_on_carbon_gathers_no_carbon(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.LEFT
        next_board = board.next()
        next_worker = next_board.workers[worker.id]
        worker_delta = next_worker.carbon - worker.carbon
        print(board)
        print(next_board)
        self.assertEqual(worker_delta, 0)

    # Test case @1.7
    def test_planter_no_move_on_plant_tree(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        next_board = board.next()
        me = board.current_player
        next_me = next_board.current_player
        for worker in next_me.planters:
            planter_position = worker.position
        for tree in next_me.trees:
            tree_position = tree.position
        self.assertEqual(planter_position, tree_position)
        self.assertEqual(me.cash - board.configuration.plant_cost, next_me.cash)

    # Test case @1.8
    def test_planter_move_on_plant_no_tree(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=1)

        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.LEFT
        next_board = board.next()
        next_tree = next_board.trees
        self.assertEqual(next_tree, {})
        print(board)
        print(next_board)
        print(next_tree)

    # Test case @1.9
    def test_collector_convert_carbon(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.DOWN
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.DOWN
        next_board = board.next()
        me = board.current_player
        next_me = next_board.current_player
        for worker in me.collectors:
            convert_carbon = worker.carbon
        self.assertEqual(me.cash + convert_carbon, next_me.cash)

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

    # Test case @1.11
    def test_planter_stay_opponent_recrtCenter(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                opponent_recrtCenter_position = recrtCenter.position
        worker = first(board.workers.values())
        worker._position = opponent_recrtCenter_position
        next_board = board.next()
        self.assertEqual(me.cash - board.configuration.rec_planter_cost, next_board.current_player.cash)
        self.assertEqual(me.trees, next_board.current_player.trees)
        print(board)
        print(next_board)

    # Test case @1.12-1
    def test_planter_plant_fail_money(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.LEFT
        board = board.next()
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.LEFT
        board = board.next()
        next_board = board.next()
        self.assertEqual(len(board.current_player.trees), len(next_board.current_player.trees))
        print(board)
        print(next_board)

    # Test case @1.12-2
    def test_planter_plant_fail_recrtCenter(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        next_board = board.next()
        self.assertEqual(board.current_player.trees, next_board.current_player.trees)
        self.assertEqual(len(next_board.current_player.trees), 0)

    # Test case @1.12-3
    def test_planter_plant_fail_position(self):
        env = make("carbon", configuration={
            "size": 5,
            "startingCarbon": 1000,
            "randomSeed": 1,
            "regenRate": 0.05,
            "recPlanterCost": 5,
        })
        board = Board(env.reset(2)[0].observation, env.configuration)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.LEFT
        board = board.next()
        board = board.next()
        next_board = board.next()
        self.assertEqual(len(next_board.current_player.trees), 1)
        print(board.observation)
        print(next_board.observation)

    # Test case @1.13
    def test_collector_stay_tree(self):
        env = make("carbon", configuration={
            "size": 5,
            "startingCarbon": 1000,
            "randomSeed": 1,
            "regenRate": 0.05,
            "recPlanterCost": 5,
            "recCollectorCost": 5,
        })
        board = Board(env.reset(1)[0].observation, env.configuration)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        planter = first(board.planters.values())
        planter.next_action = WorkerAction.LEFT
        board = board.next()
        board = board.next()
        planter = first(board.planters.values())
        planter.next_action = WorkerAction.LEFT
        board = board.next()
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        collector = first(board.collectors.values())
        collector.next_action = WorkerAction.LEFT
        board = board.next()
        next_board = board.next()
        self.assertEqual(first(board.collectors.values()).carbon, first(next_board.collectors.values()).carbon)
        print(board.observation)
        print(next_board.observation)

    # Test case @1.14
    def test_collector_occupy_tree(self):
        env = make("carbon", configuration={
            "size": 5,
            "startingCarbon": 1000,
            "randomSeed": 1,
            "regenRate": 0.05,
            "recPlanterCost": 5,
            "recCollectorCost": 5,
        })
        board = Board(env.reset(2)[0].observation, env.configuration)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        board = board.next()
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        next_board = board.next()
        self.assertEqual(board.current_player.cash - board.configuration.seize_cost, next_board.current_player.cash)
        self.assertEqual(len(board.current_player.trees) + 1, len(next_board.current_player.trees))
        self.assertEqual(len(board.trees), len(next_board.trees))
        self.assertEqual(len(board.workers), len(next_board.workers))

    # Test case @1.15
    def test_collector_occupy_tree_fail_money(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        board = board.next()
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        next_board = board.next()
        self.assertEqual(board.current_player.cash, next_board.current_player.cash)
        self.assertEqual(len(board.current_player.trees), len(next_board.current_player.trees))
        self.assertEqual(len(board.trees), len(next_board.trees))
        self.assertEqual(len(board.workers), len(next_board.workers))

    # Test case @1.16
    def test_planter_occupy_tree(self):
        env = make("carbon", configuration={
            "size": 5,
            "startingCarbon": 1000,
            "randomSeed": 1,
            "regenRate": 0.05,
            "recPlanterCost": 5,
            "recCollectorCost": 5,
        })
        board = Board(env.reset(2)[0].observation, env.configuration)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER

        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        next_board = board.next()
        print(board)
        print(next_board)
        self.assertEqual(board.current_player.cash - board.configuration.seize_cost, next_board.current_player.cash)
        self.assertEqual(len(board.current_player.trees) + 1, len(next_board.current_player.trees))
        self.assertEqual(len(board.trees), len(next_board.trees))
        self.assertEqual(len(board.workers), len(next_board.workers))

    # Test case @1.17
    def test_planter_occupy_tree_fail_money(self):
        board = create_board(starting_carbon=1000, size=5, random_seed=1, regenRate=0.05, agent_count=2)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.RIGHT
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.UP
        next_board = board.next()
        self.assertEqual(board.current_player.cash, next_board.current_player.cash)
        self.assertEqual(len(board.current_player.trees), len(next_board.current_player.trees))
        self.assertEqual(len(board.trees), len(next_board.trees))
        self.assertEqual(len(board.workers), len(next_board.workers))

    # Test case @1.18
    def test_planters_collision_all_destroys(self):
        board = create_board(agent_count=2)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()

        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.UP
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.RIGHT

        board = board.next()
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.UP
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.RIGHT
        next_board = board.next()

        self.assertEqual(len(board.current_player.workers) - 1, len(next_board.current_player.workers))
        self.assertEqual(len(board.workers) - 2, len(next_board.workers))
        self.assertEqual(board.current_player.cash, next_board.current_player.cash)

    # Test case @1.19
    def test_cell_max_carbon(self):
        board = create_board(agent_count=2)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        for collector in board.collectors.values():
            collector._carbon = 2000

        player_worker = first(board.current_player.workers)  # (2, 0)
        player_worker.next_action = WorkerAction.UP  # -> (2, 1)
        opponent_worker = first(first(board.opponents).workers)  # (0, 2)
        opponent_worker.next_action = WorkerAction.RIGHT  # -> (1, 2)
        next_board = board.next()

        board = next_board
        player_worker = first(board.current_player.workers)  # (2, 1)
        player_worker.next_action = WorkerAction.UP  # -> (2, 2)
        opponent_worker = first(first(board.opponents).workers)  # (1, 2)
        opponent_worker.next_action = WorkerAction.RIGHT  # -> (2, 2)
        next_board = board.next()

        self.assertEqual(len(board.current_player.workers) - 1, len(next_board.current_player.workers))
        self.assertEqual(len(board.workers) - 2, len(next_board.workers))
        self.assertEqual(next_board.cells[(2, 2)]._carbon, next_board.configuration.max_cell_carbon)

    # Test case @1.20
    def test_collectors_collision_with_carbon(self):
        board = create_board(agent_count=2)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        for collector in board.collectors.values():
            collector._carbon = 30
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.DOWN
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.LEFT
        next_board = board.next()
        self.assertEqual(len(board.current_player.workers) - 1, len(next_board.current_player.workers))
        self.assertEqual(len(board.workers) - 2, len(next_board.workers))
        sum = 0
        for collector in board.collectors.values():
            sum += collector.carbon
        self.assertEqual(next_board.cells[(2, 2)]._carbon, sum)

    # Test case @1.21
    def test_collectors_collision_on_recrtCenter_with_carbon(self):
        board = create_board(agent_count=2)
        original_cash = board.current_player.cash
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.DOWN
        board = board.next()
        for collector in board.collectors.values():
            collector._carbon = 30
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.RIGHT
        next_board = board.next()
        self.assertEqual(len(board.current_player.workers) - 1, len(next_board.current_player.workers))
        self.assertEqual(len(board.workers) - 2, len(next_board.workers))
        sum = 0
        for collector in board.collectors.values():
            sum += collector.carbon
        self.assertEqual(next_board.current_player.cash -
                         (original_cash - next_board.configuration.rec_collector_cost), sum)

    # Test case @1.22
    def test_collector_planter_collision_on_cell(self):
        board = create_board(agent_count=2)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        for collector in board.collectors.values():
            collector._carbon = 30
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.DOWN
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.LEFT
        next_board = board.next()
        self.assertEqual(len(board.current_player.workers) - 1, len(next_board.current_player.workers))
        self.assertEqual(len(board.workers) - 2, len(next_board.workers))
        self.assertEqual(next_board.cells[(2, 2)]._carbon, 30)

    # Test case @1.23
    def test_collector_planter_collision_on_tree(self):
        board = create_board(agent_count=2)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        player_worker = first(board.current_player.workers)
        player_worker.next_action = WorkerAction.LEFT
        board = board.next()
        board = board.next()
        for collector in board.collectors.values():
            collector._carbon = 30
        opponent_worker = first(first(board.opponents).workers)
        opponent_worker.next_action = WorkerAction.DOWN
        next_board = board.next()
        self.assertEqual(len(board.current_player.workers) - 1, len(next_board.current_player.workers))
        self.assertEqual(len(board.workers) - 2, len(next_board.workers))
        self.assertEqual(len(next_board.trees), 1)
        self.assertEqual(next_board.current_player.cash,
                         board.current_player.cash + first(first(board.opponents).workers).carbon)

    # Test case @1.24
    def test_collectors_collision_on_tree(self):
        board = create_board(agent_count=2)
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        for collector in board.collectors.values():
            collector._carbon = 300
        board = board.next()
        player_collector = first(board.current_player.collectors)
        player_collector.next_action = WorkerAction.LEFT
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        player_collector = first(board.current_player.collectors)
        player_collector.next_action = WorkerAction.LEFT
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.LEFT
        board = board.next()
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.RIGHT
        opponent_collector = first(first(board.opponents).collectors)
        opponent_collector.next_action = WorkerAction.DOWN
        board = board.next()
        for collector in board.collectors.values():
            collector._carbon = 30
        player_collector = first(board.current_player.collectors)
        player_collector.next_action = WorkerAction.RIGHT
        next_board = board.next()
        self.assertEqual(len(board.current_player.workers) - 1, len(next_board.current_player.workers))
        self.assertEqual(len(board.workers) - 2, len(next_board.workers))
        self.assertEqual(len(next_board.trees), 1)
        sum = 0
        for collector in board.collectors.values():
            sum += collector.carbon
        self.assertEqual(next_board.current_player.cash, board.current_player.cash + sum)

    # Test case @1.25
    def test_walk_carbon(self):
        size = 5
        starting_carbon = 1000
        board = create_board(size, starting_carbon, agent_count=2, random_seed=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        next_board = board.next()
        print(next_board.observation)
        print(next_board)

        me = next_board.current_player
        current_planter = first(me.planters)
        opponent_collector = first(first(next_board.opponents).collectors)
        for i in range(6):
            board = next_board
            current_planter.next_action = WorkerAction.RIGHT
            opponent_collector.next_action = WorkerAction.LEFT
            next_board = next_board.next()
            print(board.configuration.regen_rate)
            for cell in board.cells.values():
                print(cell.carbon)
                self.assertEqual(round(cell.carbon * (1 + board.configuration.regen_rate), 3),
                                 next_board.cells[cell.position]._carbon)
            print(next_board.observation)
            print(next_board)
            current_player = next_board.current_player
            current_planter = first(current_player.planters)
            opponent_collector = first(first(next_board.opponents).collectors)

    # Test case @1.26
    def test_after_fifty_tree_disappear_carbon_instead(self):
        size = 5
        starting_carbon = 1000
        board = create_board(size, starting_carbon, agent_count=2, random_seed=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.RIGHT
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.UP
        board = board.next()
        # print(board.observation)
        # 种树
        next_board = board.next()
        # print(next_board.observation)
        me = next_board.current_player
        player_planter = first(me.planters)
        (r1, r2) = player_planter.position
        next_board.configuration['regenRate'] = 0
        next_board.configuration['initialAbsorptionRate'] = 0
        next_board.configuration['absorptionGrowthRate'] = 0
        for i in range(49):
            board = next_board
            me = board.current_player
            player_planter = first(me.planters)
            player_planter.next_action = WorkerAction.UP
            next_board = next_board.next()
            print(board.observation)
            print("round", i)
            print(board.cells[(r1, r2)]._carbon)
            self.assertEqual(board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon,
                             next_board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon)
            self.assertEqual(board.cells[((r1 + 1) % size, r2)]._carbon,
                             next_board.cells[((r1 + 1) % size, r2)]._carbon)
            self.assertEqual(board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon,
                             next_board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon)
            self.assertEqual(board.cells[(r1, (r2 - 1) % size)]._carbon,
                             next_board.cells[(r1, (r2 - 1) % size)]._carbon)
            self.assertEqual(board.cells[(r1, (r2 + 1) % size)]._carbon,
                             next_board.cells[(r1, (r2 + 1) % size)]._carbon)
            self.assertEqual(board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon,
                             next_board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon)
            self.assertEqual(board.cells[((r1 - 1) % size, r2)]._carbon,
                             next_board.cells[((r1 - 1) % size, r2)]._carbon)
            self.assertEqual(board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon,
                             next_board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon)
        board.configuration['regenRate'] = 0.03
        board = next_board
        me = board.current_player
        player_planter = first(me.planters)
        player_planter.next_action = WorkerAction.UP
        next_board = next_board.next()
        self.assertEqual(round(board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon
                               * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon)
        self.assertEqual(round(board.cells[((r1 + 1) % size, r2)]._carbon
                               * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[((r1 + 1) % size, r2)]._carbon)
        self.assertEqual(round(board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon
                               * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon)
        self.assertEqual(round(board.cells[(r1, (r2 - 1) % size)]._carbon * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[(r1, (r2 - 1) % size)]._carbon)
        self.assertEqual(round(board.cells[(r1, (r2 + 1) % size)]._carbon * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[(r1, (r2 + 1) % size)]._carbon)
        self.assertEqual(round(board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon
                               * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon)
        self.assertEqual(round(board.cells[((r1 - 1) % size, r2)]._carbon * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[((r1 - 1) % size, r2)]._carbon)
        self.assertEqual(round(board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon
                               * (1 + board.configuration.regen_rate), 3),
                         next_board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon)
        print(next_board.cells[(r1, r2)]._carbon, next_board.configuration.co2_frm_withered)

    # Test case @1.27
    def test_tree_inhibit_carbon_around_with_cash_growth(self):
        size = 5
        starting_carbon = 1000
        board = create_board(size, starting_carbon, agent_count=2, random_seed=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.RIGHT
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.UP
        board = board.next()
        # 种树
        next_board = board.next()
        # print(next_board.observation)
        me = next_board.current_player
        player_planter = first(me.planters)
        (r1, r2) = player_planter.position
        for i in range(5):
            board = next_board
            me = board.current_player
            player_planter = first(me.planters)
            player_planter.next_action = WorkerAction.UP
            next_board = next_board.next()
            print(board.observation)
            print("round", i)
            # print(board.cells[(r1, r2)]._carbon)
            self.assertEqual(board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon,
                             next_board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon)
            self.assertEqual(board.cells[((r1 + 1) % size, r2)]._carbon,
                             next_board.cells[((r1 + 1) % size, r2)]._carbon)
            self.assertEqual(board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon,
                             next_board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon)
            self.assertEqual(board.cells[(r1, (r2 - 1) % size)]._carbon,
                             next_board.cells[(r1, (r2 - 1) % size)]._carbon)
            self.assertEqual(board.cells[(r1, (r2 + 1) % size)]._carbon,
                             next_board.cells[(r1, (r2 + 1) % size)]._carbon)
            self.assertEqual(board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon,
                             next_board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon)
            self.assertEqual(board.cells[((r1 - 1) % size, r2)]._carbon,
                             next_board.cells[((r1 - 1) % size, r2)]._carbon)
            self.assertEqual(board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon,
                             next_board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon)
            increment = (board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon +
                         board.cells[((r1 + 1) % size, r2)]._carbon +
                         board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon +
                         board.cells[(r1, (r2 - 1) % size)]._carbon +
                         board.cells[(r1, (r2 + 1) % size)]._carbon +
                         board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon +
                         board.cells[((r1 - 1) % size, r2)]._carbon +
                         board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon) * board.configuration.regen_rate
            print(increment)
            self.assertEqual(round(board.current_player.cash + increment, 2), next_board.current_player.cash)

    # Test case @1.28
    def test_collector_around_tree(self):
        size = 5
        starting_carbon = 1000
        board = create_board(size, starting_carbon, agent_count=2, random_seed=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.RIGHT
        opponent_collector = first(first(board.opponents).collectors)
        opponent_collector.next_action = WorkerAction.DOWN
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.UP
        opponent_collector = first(first(board.opponents).collectors)
        opponent_collector.next_action = WorkerAction.DOWN
        board = board.next()
        # 种树
        next_board = board.next()
        # 树的位置CO2消失
        self.assertEqual(next_board.cells[first(next_board.current_player.planters).position]._carbon, 0)
        # 捕碳员捕碳收益
        collect_rate = max(board.configuration.initial_collect_rate -
                           len(first(board.opponents).collectors) * board.configuration.collect_decrease_rate, 0)
        self.assertAlmostEqual(round(board.cells[first(first(board.opponents).collectors).position]._carbon *
                                     collect_rate, 3),
                               first(first(next_board.opponents).collectors)._carbon, 2)
        next_next_board = next_board.next()
        # 树的收益需排除捕碳员所占格子
        me = next_board.current_player
        player_planter = first(me.planters)
        (r1, r2) = player_planter.position
        absorption_rate = next_board.configuration.initial_absorption_rate + first(me.trees).age * next_board.configuration.absorption_growth_rate
        increment = (next_board.cells[((r1 + 1) % size, (r2 - 1) % size)]._carbon +
                     # next_board.cells[((r1 + 1) % size, r2)]._carbon +
                     next_board.cells[((r1 + 1) % size, (r2 + 1) % size)]._carbon +
                     next_board.cells[(r1, (r2 - 1) % size)]._carbon +
                     next_board.cells[(r1, (r2 + 1) % size)]._carbon +
                     next_board.cells[((r1 - 1) % size, (r2 - 1) % size)]._carbon +
                     next_board.cells[((r1 - 1) % size, r2)]._carbon +
                     next_board.cells[((r1 - 1) % size, (r2 + 1) % size)]._carbon) * absorption_rate
        self.assertEqual(round(next_board.current_player.cash + increment, 2), next_next_board.current_player.cash)

    # Test case @1.29
    def test_two_trees_share_cash(self):
        size = 5
        env = make("carbon", configuration={"size": size})
        board = Board(env.reset(2)[0].observation, env.configuration)
        # size = 5
        # starting_carbon = 1000
        # board = create_board(size, starting_carbon, agent_count=2, random_seed=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.RIGHT
        opponent_planter = first(first(board.opponents).planters)
        opponent_planter.next_action = WorkerAction.UP
        board = board.next()
        # 种树
        board = board.next()
        (p1, p2) = first(board.current_player.trees).position
        my_tree_age = first(board.current_player.trees).age
        my_tree_absorption_rate = board.configuration.initial_absorption_rate + my_tree_age * board.configuration.absorption_growth_rate
        (o1, o2) = first(first(board.opponents).trees).position
        opponent_tree_age = first(first(board.opponents).trees).age
        opponent_tree_absorption_rate = board.configuration.initial_absorption_rate + opponent_tree_age * board.configuration.absorption_growth_rate

        next_board = board.next()
        player_increment = (board.cells[((p1 - 1) % size, (p2 + 1) % size)]._carbon +
                            board.cells[(p1 % size, (p2 + 1) % size)]._carbon +
                            board.cells[((p1 + 1) % size, (p2 + 1) % size)]._carbon +
                            board.cells[((p1 - 1) % size, p2 % size)]._carbon +
                            board.cells[((p1 - 1) % size, (p2 - 1) % size)]._carbon +
                            board.cells[(p1 % size, (p2 - 1) % size)]._carbon +
                            board.cells[((p1 + 1) % size, p2 % size)]._carbon) * my_tree_absorption_rate
        self.assertEqual(round(board.current_player.cash + player_increment, 2), next_board.current_player.cash)
        opponent_increment = (board.cells[((o1 + 1) % size, (o2 - 1) % size)]._carbon +
                              board.cells[(o1 % size, (o2 - 1) % size)]._carbon +
                              board.cells[((o1 - 1) % size, (o2 - 1) % size)]._carbon +
                              board.cells[((o1 + 1) % size, o2 % size)]._carbon +
                              board.cells[((o1 + 1) % size, (o2 + 1) % size)]._carbon +
                              board.cells[(o1 % size, (o2 + 1) % size)]._carbon +
                              board.cells[((o1 - 1) % size, o2 % size)]._carbon) * opponent_tree_absorption_rate
        self.assertEqual(round(first(board.opponents).cash + opponent_increment, 2), first(next_board.opponents).cash)

        print(board)
        print(next_board)

    # Test case @1.30
    def test_more_trees_share_cash(self):
        size = 5
        plant_cost = 10
        env = make("carbon", configuration={"size": size, "plantCost": plant_cost, "plantInflationRate": 0})
        board = Board(env.reset(2)[0].observation, env.configuration)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        opponents = board.opponents
        for opponent in opponents:
            for recrtCenter in opponent.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.RIGHT
        opponent_planter = first(first(board.opponents).planters)
        opponent_planter.next_action = WorkerAction.UP
        board = board.next()
        # 种树
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.DOWN
        (p1, p2) = first(board.current_player.trees).position
        (o1, o2) = first(first(board.opponents).trees).position
        board = board.next()
        player_planter = first(board.current_player.planters)
        player_planter.next_action = WorkerAction.DOWN
        board = board.next()
        (p3, p4) = first(board.current_player.planters).position
        board = board.next()
        next_board = board.next()
        player_tree_one = (board.cells[((p1 - 1) % size, (p2 + 1) % size)]._carbon +
                           board.cells[(p1 % size, (p2 + 1) % size)]._carbon +
                           board.cells[((p1 + 1) % size, (p2 + 1) % size)]._carbon +
                           board.cells[((p1 - 1) % size, p2 % size)]._carbon +
                           board.cells[((p1 - 1) % size, (p2 - 1) % size)]._carbon / 2 +
                           board.cells[(p1 % size, (p2 - 1) % size)]._carbon / 3 +
                           board.cells[((p1 + 1) % size, p2 % size)]._carbon / 2) * board.configuration.regen_rate
        player_tree_two = (board.cells[((p3 - 1) % size, (p4 + 1) % size)]._carbon / 2 +
                           board.cells[(p3 % size, (p4 + 1) % size)]._carbon / 3 +
                           board.cells[((p3 + 1) % size, p4 % size)]._carbon / 2 +
                           board.cells[((p3 - 1) % size, p4 % size)]._carbon +
                           board.cells[((p3 - 1) % size, (p4 - 1) % size)]._carbon +
                           board.cells[(p3 % size, (p4 - 1) % size)]._carbon +
                           board.cells[((p3 + 1) % size, (p4 - 1) % size)]._carbon) * board.configuration.regen_rate
        print(round(board.current_player.cash + player_tree_one + player_tree_two, 2),
              next_board.current_player.cash)
        opponent_tree = (board.cells[((o1 + 1) % size, (o2 - 1) % size)]._carbon +
                         board.cells[(o1 % size, (o2 - 1) % size)]._carbon / 2 +
                         board.cells[((o1 + 1) % size, o2 % size)]._carbon +
                         board.cells[((o1 + 1) % size, (o2 + 1) % size)]._carbon +
                         board.cells[(o1 % size, (o2 + 1) % size)]._carbon / 2 +
                         board.cells[((o1 - 1) % size, o2 % size)]._carbon / 3) * board.configuration.regen_rate
        self.assertEqual(round(first(board.opponents).cash + opponent_tree, 2), first(next_board.opponents).cash)
        print(board)
        print(board.observation)
        print(next_board)
        print(next_board.observation)

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

    # Test case @1.32
    def test_act_timeout(self):
        board_size = 21
        env = make("carbon", configuration={"size": board_size, "episodeSteps": 400, "actTimeout": 0})
        agent_count = 2
        env.reset(agent_count)

        import time

        def move_workers_up_agent(observation, configuration):
            board = Board(observation, configuration)
            current_player = board.current_player
            for recrtCenter in current_player.recrtCenters:
                recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
            start = time.time()
            while time.time() - start <= board.configuration.act_timeout:
                time.sleep(1)
            for worker in current_player.workers:
                worker.next_action = WorkerAction.UP
            return current_player.next_actions

        env.run([move_workers_up_agent, "random"])
        self.assertEqual(env.steps[-1][0]["status"], "TIMEOUT")

    # Test case @1.33
    def test_recworker_count_limit(self):
        size = 7
        rec_cost = 5
        env = make("carbon", configuration={"size": size, "recPlanterCost": rec_cost, "recCollectorCost": rec_cost,
                                            "workerLimit": 5})
        board = Board(env.reset(2)[0].observation, env.configuration)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        me = board.current_player
        player_collector = first(me.collectors)
        player_collector.next_action = WorkerAction.UP
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        me = board.current_player
        for worker in me.collectors:
            worker.next_action = WorkerAction.UP
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        me = board.current_player
        for worker in me.collectors:
            worker.next_action = WorkerAction.UP
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        me = board.current_player
        for collector in me.collectors:
            collector.next_action = WorkerAction.UP
        for planter in me.planters:
            planter.next_action = WorkerAction.RIGHT
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        board = board.next()
        me = board.current_player
        for collector in me.collectors:
            collector.next_action = WorkerAction.UP
        for planter in me.planters:
            planter.next_action = WorkerAction.RIGHT
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
        next_board = board.next()
        self.assertEqual(len(board.workers), len(next_board.workers))
        print(board)
        print(next_board)

    def test_planter_plant_trees(self):
        size = 7
        rec_cost = 5
        plant_cost = 5
        plant_inflation_rate = 5
        env = make("carbon", configuration={"size": size, "recPlanterCost": rec_cost, "recCollectorCost": rec_cost,
                                            "workerLimit": 5,
                                            "initialAbsorptionRate": 0, "absorptionGrowthRate": 0,
                                            "plantCost": plant_cost, "plantInflationRate": plant_inflation_rate})
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

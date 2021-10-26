import os
import sys

sys.path.append(os.path.realpath('.'))

import unittest
from utils import *


class BoundaryTest(unittest.TestCase):
    """
    Test on the boundary situation
    """

    # Test case @3.1
    def test_worker_move_cross_boundary(self):
        size = 3
        board = create_board(size=size, agent_count=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        board = board.next()
        worker = first(board.workers.values())
        worker.next_action = WorkerAction.UP
        board = board.next()
        # 穿越上边界
        first(board.workers.values()).next_action = WorkerAction.UP
        next_board = board.next()
        (w1, w2) = first(board.workers.values()).position
        (w3, w4) = first(next_board.workers.values()).position
        self.assertEqual(w1, w3)
        self.assertEqual(w2 + 1 - size, w4)
        # 穿越下边界
        board = next_board
        first(board.workers.values()).next_action = WorkerAction.DOWN
        next_board = board.next()
        (w1, w2) = first(board.workers.values()).position
        (w3, w4) = first(next_board.workers.values()).position
        self.assertEqual(w1, w3)
        self.assertEqual(w2 - 1 + size, w4)
        # 穿越左边界
        board = next_board
        first(board.workers.values()).next_action = WorkerAction.LEFT
        board = board.next()
        first(board.workers.values()).next_action = WorkerAction.LEFT
        next_board = board.next()
        (w1, w2) = first(board.workers.values()).position
        (w3, w4) = first(next_board.workers.values()).position
        self.assertEqual(w2, w4)
        self.assertEqual(w1 - 1 + size, w3)
        # 穿越右边界
        board = next_board
        first(board.workers.values()).next_action = WorkerAction.RIGHT
        next_board = board.next()
        (w1, w2) = first(board.workers.values()).position
        (w3, w4) = first(next_board.workers.values()).position
        self.assertEqual(w2, w4)
        self.assertEqual(w1 + 1 - size, w3)
        print(board)
        print(next_board)

    # Test case @3.2-1
    def test_tree_inhibit_carbon_cross_left_boundary(self):
        size = 5
        board = create_board(starting_carbon=1000, size=size, agent_count=1, random_seed=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
        next_board = board.next()
        (w1, w2) = first(next_board.workers.values()).position
        while w1 > 0:
            board = next_board
            first(board.workers.values()).next_action = WorkerAction.LEFT
            next_board = board.next()
            (w1, w2) = first(next_board.workers.values()).position
        board = next_board
        board = board.next()
        next_board = board.next()
        self.assertEqual(board.cells[w1 - 1 + size, w2]._carbon, next_board.cells[w1 - 1 + size, w2]._carbon)
        print(board)
        print(next_board)

    # Test case @3.2-2
    def test_tree_inhibit_carbon_cross_right_boundary(self):
        size = 5
        board = create_board(starting_carbon=1000, size=size, agent_count=1, random_seed=2)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
        next_board = board.next()
        (w1, w2) = first(next_board.workers.values()).position
        while w1 < size - 1:
            board = next_board
            first(board.workers.values()).next_action = WorkerAction.RIGHT
            next_board = board.next()
            (w1, w2) = first(next_board.workers.values()).position
        board = next_board
        board = board.next()
        next_board = board.next()
        self.assertEqual(board.cells[w1 + 1 - size, w2]._carbon, next_board.cells[w1 + 1 - size, w2]._carbon)
        print(board)
        print(next_board)

    # Test case @3.2-3
    def test_tree_inhibit_carbon_cross_up_boundary(self):
        size = 5
        board = create_board(starting_carbon=1000, size=size, agent_count=1, random_seed=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
        next_board = board.next()
        (w1, w2) = first(next_board.workers.values()).position
        while w2 < size - 1:
            board = next_board
            first(board.workers.values()).next_action = WorkerAction.UP
            next_board = board.next()
            (w1, w2) = first(next_board.workers.values()).position
        board = next_board
        board = board.next()
        next_board = board.next()
        self.assertEqual(board.cells[w1, w2 + 1 - size]._carbon, next_board.cells[w1, w2 + 1 - size]._carbon)
        print(board)
        print(next_board)

    # Test case @3.2-4
    def test_tree_inhibit_carbon_cross_down_boundary(self):
        size = 5
        board = create_board(starting_carbon=1000, size=size, agent_count=1, random_seed=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
        next_board = board.next()
        (w1, w2) = first(next_board.workers.values()).position
        while w2 > 0:
            board = next_board
            first(board.workers.values()).next_action = WorkerAction.DOWN
            next_board = board.next()
            (w1, w2) = first(next_board.workers.values()).position
        board = next_board
        board = board.next()
        next_board = board.next()
        self.assertEqual(board.cells[w1, w2 - 1 + size]._carbon, next_board.cells[w1, w2 - 1 + size]._carbon)
        print(board)
        print(next_board)

    def test_tree_inhibit_carbon_cross_corner_boundary(self):
        size = 5
        board = create_board(starting_carbon=1000, size=size, agent_count=1, random_seed=1)
        me = board.current_player
        for recrtCenter in me.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
        next_board = board.next()
        (w1, w2) = first(next_board.workers.values()).position
        while w2 > 0:
            board = next_board
            first(board.workers.values()).next_action = WorkerAction.DOWN
            next_board = board.next()
            (w1, w2) = first(next_board.workers.values()).position
            while w1 > 0:
                board = next_board
                first(board.workers.values()).next_action = WorkerAction.LEFT
                next_board = board.next()
                (w1, w2) = first(next_board.workers.values()).position
        board = next_board
        board = board.next()
        next_board = board.next()
        self.assertEqual(board.cells[w1 - 1 + size, w2]._carbon, next_board.cells[w1 - 1 + size, w2]._carbon)
        self.assertEqual(board.cells[w1, w2 - 1 + size]._carbon, next_board.cells[w1, w2 - 1 + size]._carbon)
        self.assertEqual(board.cells[w1 - 1 + size, w2 - 1 + size]._carbon,
                         next_board.cells[w1 - 1 + size, w2 - 1 + size]._carbon)
        print(board)
        print(next_board)

if __name__ == '__main__':
    unittest.main()

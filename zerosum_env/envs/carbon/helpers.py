# Copyright 2020 Kaggle Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
from copy import deepcopy
from enum import Enum, auto
from functools import wraps
from zerosum_env.helpers import Point, group_by
from typing import *
import sys
import zerosum_env.helpers

from .idgen import new_worker_id, new_tree_id
from .termtables import to_string


# region Data Model Classes
class Observation(zerosum_env.helpers.Observation):
    """
    Observation primarily used as a helper to construct the Board from the raw observation.
    This provides bindings for the observation type described at https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/carbon/carbon.json
    """

    @property
    def carbon(self) -> List[float]:
        """Serialized list of available carbon per cell on the board."""
        return self["carbon"]

    @property
    def players(self) -> List[List[int]]:
        """List of players and their assets."""
        return self["players"]

    @property
    def trees(self) -> Dict[int, List[int]]:
        """List of players and their assets."""
        return self["trees"]

    @property
    def player(self) -> int:
        """The current agent's player index."""
        return self["player"]


class Configuration(zerosum_env.helpers.Configuration):
    """
    Configuration provides access to tunable parameters in the environment.
    This provides bindings for the configuration type described at https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/carbon/carbon.json
    """

    @property
    def agent_timeout(self) -> float:
        """Maximum runtime (seconds) to initialize an agent."""
        return self["agentTimeout"]

    @property
    def starting_carbon(self) -> int:
        """The starting amount of carbon available on the board."""
        return self["startingCarbon"]

    @property
    def size(self) -> int:
        """The number of cells vertically and horizontally on the board."""
        return self["size"]

    @property
    def move_cost(self) -> float:
        """The percent deducted from worker's current carbon per move."""
        return self["moveCost"]

    @property
    def smelt_cost(self) -> float:
        """The amount of carbon to smelt cargos into carbon ."""
        return self["smeltCost"]

    @property
    def seize_cost(self) -> float:
        """The amount of planter to seize a tree from competitor."""
        return self["seizeCost"]

    @property
    def plant_cost(self) -> float:
        """The amount of planter to plant a tree."""
        return self["plantCost"]

    @property
    def plant_cost_inflation_ratio(self) -> float:
        """The ratio of market amount of planter to plant a tree after a certain number."""
        return self["plantCostInflationRatio"]

    @property
    def plant_cost_inflation_base(self) -> float:
        """The base of market amount of planter to plant a tree after a certain number."""
        return self["plantCostInflationBase"]

    @property
    def player_tree_protective_number(self) -> float:
        """The cost of planter to plant a tree is `plantCost` if not exceeding this number."""
        return self["playerTreeProtectiveNumber"]

    @property
    def initial_collect_rate(self) -> float:
        """The initial rate of carbon collected by a worker from a cell by not moving."""
        return self["initialCollectRate"]

    @property
    def collect_decrease_rate(self) -> float:
        """The decrease rate for collector to collect CO2 according to one player's collectors count."""
        return self["collectDecreaseRate"]

    @property
    def regen_rate(self) -> float:
        """The rate carbon regenerates on the board."""
        return self["regenRate"]

    @property
    def max_cell_carbon(self) -> int:
        """The maximum carbon that can be in any cell."""
        return self["maxCellCarbon"]

    @property
    def starting_cell_carbon(self) -> int:
        """The starting maximum mount of carbon in cell."""
        return self["startingCellCarbon"]

    @property
    def random_seed(self) -> int:
        """The seed to the random number generator (0 means no seed)."""
        return self["randomSeed"]

    @property
    def rec_collector_cost(self) -> int:
        """The amount of recruitment center to recruit a new collector."""
        return self["recCollectorCost"]

    @property
    def rec_collector_increase_cost(self) -> int:
        """The increase amount of recruitment center to recruit a new collector."""
        return self["recCollectorIncreaseCost"]

    @property
    def rec_planter_cost(self) -> int:
        """The amount of recruitment center to recruit a new planter."""
        return self["recPlanterCost"]

    @property
    def rec_planter_increase_cost(self) -> int:
        """The increase amount of recruitment center to recruit a new planter."""
        return self["recPlanterIncreaseCost"]

    @property
    def planter_limit(self) -> int:
        """The limitation of planter."""
        return self["planterLimit"]

    @property
    def collector_limit(self) -> int:
        """The limitation of collector."""
        return self["collectorLimit"]

    @property
    def worker_limit(self):
        """The number of worker"""
        return self["workerLimit"]

    @property
    def co2_frm_withered(self) -> int:
        """The amount of carbon from withered tree."""
        return self["co2FrmWithered"]

    @property
    def tree_lifespan(self) -> int:
        """The maximum age of tree."""
        return self["treeLifespan"]

    @property
    def cell_absorption_rate(self) -> float:
        """The absorption rate of the tree from cell."""
        return self["cellAbsorptionRate"]

    @property
    def collector_absorption_rate(self) -> float:
        """The absorption rate of the tree from collector nearby"""
        return self["collectorAbsorptionRate"]

    @property
    def start_pos_offset(self) -> float:
        """The offset of starting position"""
        return self["startPosOffset"]


class WorkerAction(Enum):
    UP = auto()
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()

    # CONVERT = auto()
    # Use None to collect carbon on a cell

    def to_point(self) -> Optional[Point]:
        """
        This returns the position offset associated with a particular action or None if the action does not change the worker's position.
        UP -> (0, 1)
        RIGHT -> (1, 0)
        DOWN -> (0, -1)
        LEFT -> (-1, 0)
        """
        return (
            Point(0, 1) if self == WorkerAction.UP else
            Point(1, 0) if self == WorkerAction.RIGHT else
            Point(0, -1) if self == WorkerAction.DOWN else
            Point(-1, 0) if self == WorkerAction.LEFT else
            None
        )

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def moves() -> List['WorkerAction']:
        return [
            WorkerAction.UP,
            WorkerAction.RIGHT,
            WorkerAction.DOWN,
            WorkerAction.LEFT,
        ]


class RecrtCenterAction(Enum):
    RECCOLLECTOR = auto()
    RECPLANTER = auto()

    def __str__(self) -> str:
        return self.name


class Occupation(Enum):
    COLLECTOR = auto()
    PLANTER = auto()

    def __str__(self) -> str:
        return self.name


"""树"""
TreeId = NewType('TreeId', str)
WorkerId = NewType('WorkerId', str)
RecrtCenterId = NewType('RecrtCenterId', str)
PlayerId = NewType('PlayerId', int)


class Cell:
    def __init__(self, position: Point, carbon: float, recrtCenter_id: Optional[RecrtCenterId],
                 worker_id: Optional[WorkerId],
                 tree_id: Optional[TreeId], board: 'Board') -> None:
        self._position = position
        self._carbon = carbon
        self._recrtCenter_id = recrtCenter_id
        self._worker_id = worker_id
        self._tree_id = tree_id
        self._board = board

    @property
    def position(self) -> Point:
        return self._position

    @property
    def carbon(self) -> float:
        return self._carbon

    @property
    def recrtCenter_id(self) -> Optional[RecrtCenterId]:
        return self._recrtCenter_id

    @property
    def worker_id(self) -> Optional[WorkerId]:
        return self._worker_id

    @property
    def tree_id(self) -> Optional[TreeId]:
        return self._tree_id

    @property
    def tree(self) -> Optional['Tree']:
        """Returns the tree on this cell if it exists and None otherwise."""
        return self._board.trees.get(self.tree_id)

    @property
    def worker(self) -> Optional['Worker']:
        """Returns the worker on this cell if it exists and None otherwise."""
        return self._board.workers.get(self.worker_id)

    @property
    def planter(self) -> Optional['Planter']:
        """Returns the planter on this cell if it exists and None otherwise."""
        return self._board.planters.get(self.worker_id)

    @property
    def collector(self) -> Optional['Collector']:
        """Returns the collector on this cell if it exists and None otherwise."""
        return self._board.collectors.get(self.worker_id)

    @property
    def recrtCenter(self) -> Optional['RecrtCenter']:
        """Returns the recrtCenter on this cell if it exists and None otherwise."""
        return self._board.recrtCenters.get(self.recrtCenter_id)

    def neighbor(self, offset: Point) -> 'Cell':
        """Returns the cell at self.position + offset."""
        (x, y) = self.position + offset
        return self._board[x, y]

    @property
    def up(self) -> 'Cell':
        """Returns the cell up of this cell."""
        return self.neighbor(WorkerAction.UP.to_point())

    @property
    def down(self) -> 'Cell':
        """Returns the cell down of this cell."""
        return self.neighbor(WorkerAction.DOWN.to_point())

    @property
    def right(self) -> 'Cell':
        """Returns the cell right of this cell."""
        return self.neighbor(WorkerAction.RIGHT.to_point())

    @property
    def left(self) -> 'Cell':
        """Returns the cell left of this cell."""
        return self.neighbor(WorkerAction.LEFT.to_point())


class Tree:
    def __init__(self, tree_id: TreeId, position: Point, age: int, player_id: PlayerId, board: 'Board') -> None:
        self._id = tree_id
        self._age = age
        self._position = position
        self._player_id = player_id
        self._board = board

    @property
    def id(self) -> TreeId:
        return self._id

    @property
    def age(self) -> int:
        return self._age

    @property
    def position(self) -> Point:
        return self._position

    @property
    def player_id(self) -> PlayerId:
        return self._player_id

    @property
    def cell(self) -> Cell:
        """Returns the cell this worker is on."""
        return self._board[self.position]

    @property
    def player(self) -> 'Player':
        """Returns the player that owns this worker."""
        return self._board.players[self.player_id]

    def surround(self) -> List[Point]:
        """
        Returns the directions of octet connected region.
        """
        return [
            Point(-1, 1),  # 左上
            Point(0, 1),  # 上
            Point(1, 1),  # 右上
            Point(1, 0),  # 右
            Point(1, -1),  # 右下
            Point(0, -1),  # 下
            Point(-1, -1),  # 左下
            Point(-1, 0)  # 左
        ]

    def quad_surround(self) -> List[Point]:
        """
        Returns the directions of quad connected region.
        """
        return [
            Point(0, 1),  # 上
            Point(1, 0),  # 右
            Point(0, -1),  # 下
            Point(-1, 0)  # 左
        ]

    @property
    def _observation(self) -> List[int]:
        """Converts a tree back to the normalized observation subset that constructed it."""
        return [self.position.to_index(self._board.configuration.size), self.age]

    def __str__(self):
        return f"{self._id} ({self._age})"


class Worker:
    def __init__(self, worker_id: WorkerId, position: Point, carbon: float, player_id: PlayerId, board: 'Board',
                 next_action: Optional[WorkerAction] = None) -> None:
        self._id = worker_id
        self._occupation = Occupation.COLLECTOR
        self._position = position
        self._carbon = carbon
        self._player_id = player_id
        self._board = board
        self._next_action = next_action

    @property
    def id(self) -> WorkerId:
        return self._id

    @property
    def occupation(self) -> Optional[Occupation]:
        return self._occupation

    @property
    def is_collector(self) -> bool:
        return self._occupation == Occupation.COLLECTOR

    @property
    def is_planter(self) -> bool:
        return self._occupation == Occupation.PLANTER

    @property
    def position(self) -> Point:
        return self._position

    @property
    def carbon(self) -> float:
        return self._carbon

    @property
    def player_id(self) -> PlayerId:
        return self._player_id

    @property
    def cell(self) -> Cell:
        """Returns the cell this worker is on."""
        return self._board[self.position]

    @property
    def player(self) -> 'Player':
        """Returns the player that owns this worker."""
        return self._board.players[self.player_id]

    @property
    def next_action(self) -> Optional[WorkerAction]:
        """Returns the action that will be executed by this worker when Board.next() is called (when the current turn ends)."""
        return self._next_action

    @next_action.setter
    def next_action(self, value: Optional[WorkerAction]) -> None:
        """Sets the action that will be executed by this worker when Board.next() is called (when the current turn ends)."""
        self._next_action = value

    @property
    def _observation(self) -> List[int]:
        """Converts a worker back to the normalized observation subset that constructed it."""
        return [self.position.to_index(self._board.configuration.size), self.carbon, str(self.occupation)]

    def __str__(self):
        return str(self.occupation) + ":" + self.id


# 捕碳人
class Collector(Worker):
    def __init__(self, worker_id: WorkerId, position: Point, carbon: float, player_id: PlayerId, board: 'Board',
                 next_action: Optional[WorkerAction] = None) -> None:
        Worker.__init__(self, worker_id, position, carbon, player_id, board, next_action)
        self._occupation = Occupation.COLLECTOR

    @property
    def occupation(self) -> Optional[Occupation]:
        return self._occupation


# 种树人
class Planter(Worker):
    def __init__(self, worker_id: WorkerId, position: Point, carbon: float, player_id: PlayerId, board: 'Board',
                 next_action: Optional[WorkerAction] = None) -> None:
        Worker.__init__(self, worker_id, position, carbon, player_id, board, next_action)
        self._occupation = Occupation.PLANTER

    @property
    def occupation(self) -> Optional[Occupation]:
        return self._occupation


class RecrtCenter:
    def __init__(self, recrtCenter_id: RecrtCenterId, position: Point, player_id: PlayerId, board: 'Board',
                 next_action: Optional[RecrtCenterAction] = None) -> None:
        self._id = recrtCenter_id
        self._position = position
        self._player_id = player_id
        self._board = board
        self._next_action = next_action

    @property
    def id(self) -> RecrtCenterId:
        return self._id

    @property
    def position(self) -> Point:
        return self._position

    @property
    def player_id(self) -> PlayerId:
        return self._player_id

    @property
    def cell(self) -> Cell:
        """Returns the cell this recrtCenter is on."""
        return self._board[self.position]

    @property
    def player(self) -> 'Player':
        return self._board.players[self.player_id]

    @property
    def next_action(self) -> RecrtCenterAction:
        """Returns the action that will be executed by this recrtCenter when Board.next() is called (when the current turn ends)."""
        return self._next_action

    @next_action.setter
    def next_action(self, value: Optional[RecrtCenterAction]) -> None:
        """Sets the action that will be executed by this recrtCenter when Board.next() is called (when the current turn ends)."""
        self._next_action = value

    @property
    def _observation(self) -> int:
        """Converts a recrtCenter back to the normalized observation subset that constructed it."""
        return self.position.to_index(self._board.configuration.size)


class Player:
    def __init__(self, player_id: PlayerId, cash: float, recrtCenter_ids: List[RecrtCenterId],
                 worker_ids: List[WorkerId],
                 tree_ids: List[TreeId], board: 'Board') -> None:
        self._id = player_id
        self._cash = cash
        self._recrtCenter_ids = recrtCenter_ids
        self._worker_ids = worker_ids
        self._tree_ids = tree_ids
        self._board = board

    @property
    def id(self) -> PlayerId:
        return self._id

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def recrtCenter_ids(self) -> List[RecrtCenterId]:
        return self._recrtCenter_ids

    @property
    def worker_ids(self) -> List[WorkerId]:
        return self._worker_ids

    @property
    def tree_ids(self) -> List[TreeId]:
        return self._tree_ids

    @property
    def recrtCenters(self) -> List[RecrtCenter]:
        """Returns all recrtCenter owned by this player."""
        return [
            self._board.recrtCenters[recrtCenter_id]
            for recrtCenter_id in self.recrtCenter_ids
        ]

    @property
    def workers(self) -> List[Worker]:
        """Returns all workers owned by this player."""
        return [
            self._board.workers[worker_id]
            for worker_id in self.worker_ids
        ]

    @property
    def collectors(self) -> List[Collector]:
        """Returns all collectors owned by this player."""
        res = []
        for worker_id in self.worker_ids:
            worker = self._board.workers[worker_id]
            if worker.occupation == Occupation.COLLECTOR:
                res.append(worker)
        return res

    @property
    def planters(self) -> List[Planter]:
        """Returns all collectors owned by this player."""
        res = []
        for worker_id in self.worker_ids:
            worker = self._board.workers[worker_id]
            if worker.occupation == Occupation.PLANTER:
                res.append(worker)
        return res

    @property
    def trees(self) -> List[Tree]:
        """Returns all workers owned by this player."""
        return [
            self._board.trees[tree_id]
            for tree_id in self.tree_ids
        ]

    @property
    def is_current_player(self) -> bool:
        """Returns whether this player is the current player (generally if this returns True, this player is you)."""
        return self.id == self._board.current_player_id

    @property
    def next_actions(self) -> Dict[str, str]:
        """Returns all queued worker and recrtCenter actions for this player formatted for the carbon interpreter to receive as an agent response."""
        worker_actions = {
            worker.id: worker.next_action.name
            for worker in self.workers
            if worker.next_action is not None
        }
        recrtCenter_actions = {
            recrtCenter.id: recrtCenter.next_action.name
            for recrtCenter in self.recrtCenters
            if recrtCenter.next_action is not None
        }
        return {**worker_actions, **recrtCenter_actions}

    @property
    def _observation(self):
        """Converts a player back to the normalized observation subset that constructed it."""
        recrtCenters = {recrtCenter.id: recrtCenter._observation for recrtCenter in self.recrtCenters}
        workers = {worker.id: worker._observation for worker in self.workers}
        trees = {tree.id: tree._observation for tree in self.trees}
        return [self.cash, recrtCenters, workers, trees]


# endregion


class Board:
    def __init__(
            self,
            raw_observation: Dict[str, Any],
            raw_configuration: Union[Configuration, Dict[str, Any]],
            next_actions: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """
        Creates a board from the provided observation, configuration, and next_actions as specified by
        https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/carbon/carbon.json
        Board tracks players (by id), workers (by id), recrtCenter (by id), and cells (by position).
        Each entity contains both key values (e.g. worker.player_id) as well as entity references (e.g. worker.player).
        References are deep and chainable e.g.
            [worker.carbon for player in board.players for worker in player.workers]
            worker.player.recrtCenter[0].cell.north.east.worker
        Consumers should not set or modify any attributes except Worker.next_action and RecrtCenter.next_action
        """
        observation = Observation(raw_observation)
        # next_actions is effectively a Dict[Union[[WorkerId, WorkerAction], [RecrtCenterId, RecrtCenterAction]]]
        # but that type's not very expressible so we simplify it to Dict[str, str]
        # Later we'll iterate through it once for each worker and recrtCenter to pull all the actions out
        next_actions = next_actions or ([{}] * len(observation.players))

        self._step = observation.step
        self._remaining_overage_time = observation.remaining_overage_time
        self._configuration = Configuration(raw_configuration)
        self._current_player_id = observation.player
        self._players: Dict[PlayerId, Player] = {}
        self._trees: Dict[TreeId, Tree] = {}
        self._trees_dict: Dict[TreeId, Any] = {}
        self._workers: Dict[WorkerId, Worker] = {}
        self._recrtCenters: Dict[RecrtCenterId, RecrtCenter] = {}
        self._cells: Dict[Point, Cell] = {}

        size = self.configuration.size
        # Create a cell for every point in a size x size grid
        for x in range(size):
            for y in range(size):
                position = Point(x, y)
                carbon = observation.carbon[position.to_index(size)]
                # We'll populate the cell's workers and recrtCenter in _add_worker and _add_recrtCenter
                self.cells[position] = Cell(position, carbon, None, None, None, self)

        for (player_id, player_observation) in enumerate(observation.players):
            # We know the len(player_observation) == 3 based on the schema -- this is a hack to have a tuple in json
            [player_cash, player_recrtCenter, player_workers, player_trees] = player_observation
            # We'll populate the player's workers and recrtCenter in _add_worker and _add_recrtCenter
            self.players[player_id] = Player(player_id, player_cash, [], [], [], self)
            player_actions = next_actions[player_id] or {}

            for (tree_id, [tree_index, tree_age]) in player_trees.items():
                tree_position = Point.from_index(tree_index, size)
                new_tree = Tree(tree_id, tree_position, tree_age, player_id, self)
                self._add_tree(new_tree)
                self._add_tree_dict(new_tree, observation.trees[tree_id][0], observation.trees[tree_id][1])

            for (worker_id, [worker_index, worker_carbon, worker_type]) in player_workers.items():
                # In the raw observation, carbon is stored as a 1d list but we convert it to a 2d dict for convenience
                # Accordingly we also need to convert our list indices to dict keys / 2d positions
                worker_position = Point.from_index(worker_index, size)
                raw_action = player_actions.get(worker_id)
                action = (
                    WorkerAction[raw_action]
                    if raw_action in WorkerAction.__members__
                    else None
                )
                if worker_type == str(Occupation.COLLECTOR):
                    self._add_worker(Collector(worker_id, worker_position, worker_carbon, player_id, self, action))
                elif worker_type == str(Occupation.PLANTER):
                    self._add_worker(Planter(worker_id, worker_position, worker_carbon, player_id, self, action))
                else:
                    self._add_worker(Worker(worker_id, worker_position, worker_carbon, player_id, self, action))

            for (recrtCenter_id, recrtCenter_index) in player_recrtCenter.items():
                recrtCenter_position = Point.from_index(recrtCenter_index, size)
                raw_action = player_actions.get(recrtCenter_id)
                action = (
                    RecrtCenterAction[raw_action]
                    if raw_action in RecrtCenterAction.__members__
                    else None
                )
                self._add_recrtCenter(RecrtCenter(recrtCenter_id, recrtCenter_position, player_id, self, action))

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    @property
    def players(self) -> Dict[PlayerId, Player]:
        return self._players

    @property
    def trees(self) -> Dict[TreeId, Tree]:
        """Returns all trees on the current board."""
        return self._trees

    @property
    def workers(self) -> Dict[WorkerId, Worker]:
        """Returns all workers on the current board."""
        return self._workers

    @property
    def collectors(self) -> Dict[WorkerId, Collector]:
        """Returns all collectors on the current board."""
        res = {}
        for work_id in self._workers.keys():
            worker = self._workers[work_id]
            if worker.occupation == Occupation.COLLECTOR:
                res[work_id] = worker
        return res

    @property
    def planters(self) -> Dict[WorkerId, Planter]:
        """Returns all collectors on the current board."""
        res = {}
        for work_id in self._workers.keys():
            worker = self._workers[work_id]
            if worker.occupation == Occupation.PLANTER:
                res[work_id] = worker
        return res

    @property
    def recrtCenters(self) -> Dict[RecrtCenterId, RecrtCenter]:
        """Returns all recrtCenter on the current board."""
        return self._recrtCenters

    @property
    def cells(self) -> Dict[Point, Cell]:
        """Returns all cells on the current board."""
        return self._cells

    @property
    def step(self) -> int:
        return self._step

    @property
    def current_player_id(self) -> PlayerId:
        return self._current_player_id

    @property
    def current_player(self) -> Player:
        """Returns the current player (generally this is you)."""
        return self._players[self.current_player_id]

    @property
    def opponents(self) -> List[Player]:
        """
        Returns all players that aren't the current player.
        You can get all opponent workers with [worker for worker in player.workers for player in board.opponents]
        """
        return [player for player in self.players.values() if not player.is_current_player]

    @property
    def observation(self) -> Dict[str, Any]:
        """Converts a Board back to the normalized observation that constructed it."""
        size = self.configuration.size
        carbon = [self[Point.from_index(index, size)].carbon for index in range(size * size)]
        players = [player._observation for player in self.players.values()]

        return {
            "carbon": carbon,
            "players": players,
            "player": self.current_player_id,
            "step": self.step,
            "trees": self._trees_dict,
            "remainingOverageTime": self._remaining_overage_time,
        }

    def __deepcopy__(self, _) -> 'Board':
        actions = [player.next_actions for player in self.players.values()]
        return Board(self.observation, self.configuration, actions)

    def __getitem__(self, point: Union[Tuple[int, int], Point]) -> Cell:
        """
        This method will wrap the supplied position to fit within the board size and return the cell at that location.
        e.g. on a 3x3 board, board[2, 1] is the same as board[5, 1]
        """
        if not isinstance(point, Point):
            (x, y) = point
            point = Point(x, y)
        return self._cells[point % self.configuration.size]

    def __str__(self) -> str:
        """
        The board is printed in a grid with the following rules:
        B letter is recrtCenter (B represents Base)
        P letter is planter (P represents Planter)
        C letter is collector (C represents Collector)
        Player 1 is number 0
        Player 2 is number 1
        etc.
        """
        player_dict = self.players
        size = self.configuration.size
        # print(f"==== STEP: {observation.step} ====")
        contents = []
        for y in range(size):
            row = []
            for x in range(size):
                cell = self[(x, size - y - 1)]
                s_carbon = f"{cell.carbon:.1f}"

                s_worker_carbon = ""
                if cell.worker is not None:
                    s_worker = f"{str(cell.worker.occupation)[0]}{cell.worker.player_id}" \
                                       f"{cell.worker_id[cell.worker_id.rindex('-'):]}"
                    s_worker_carbon = f'{s_worker} ({cell.worker.carbon})'

                s_base = '' if cell.recrtCenter is None else \
                    f'B{cell.recrtCenter.player_id} ({player_dict[cell.recrtCenter.player_id].cash})'

                s_tree = ""
                if cell.tree is not None:
                    s_tree = f"T{cell.tree.player_id}{cell.tree.id[cell.tree.id.rindex('-'):]}"

                s_base_or_tree = s_base + s_tree
                if s_base_or_tree:
                    row.append(f"{s_base_or_tree} {s_worker_carbon}")
                else:
                    row.append(f"{s_carbon} {s_worker_carbon}")
            contents.append(row)

        return to_string(contents)

    def _add_tree(self: 'Board', tree: Tree) -> None:
        tree.player.tree_ids.append(tree.id)
        tree.cell._tree_id = tree.id
        self._trees[tree.id] = tree

    def _add_tree_dict(self: 'Board', tree: Tree, worker_id: WorkerId, tree_absorption) -> None:
        if tree.id in self._trees_dict:
            del self._trees_dict[tree.id]

        self._trees_dict[tree.id] = [worker_id, tree_absorption]

    def _add_worker(self: 'Board', worker: Worker) -> None:
        worker.player.worker_ids.append(worker.id)
        worker.cell._worker_id = worker.id
        self._workers[worker.id] = worker

    def _add_recrtCenter(self: 'Board', recrtCenter: RecrtCenter) -> None:
        recrtCenter.player.recrtCenter_ids.append(recrtCenter.id)
        recrtCenter.cell._recrtCenter_id = recrtCenter.id
        recrtCenter.cell._carbon = 0
        self._recrtCenters[recrtCenter.id] = recrtCenter

    def _delete_tree(self: 'Board', tree: Tree) -> None:
        tree.player.tree_ids.remove(tree.id)
        if tree.cell.tree_id == tree.id:
            tree.cell._worker_id = None
        del self.trees[tree.id]
        del self._trees_dict[tree.id]

    def _delete_worker(self: 'Board', worker: Worker) -> None:
        worker.player.worker_ids.remove(worker.id)

        if worker.cell.worker_id == worker.id:
            worker.cell._worker_id = None

        for tree_id in self._trees_dict.keys():
            tree_worker_id = self._trees_dict.get(tree_id)[0]
            if tree_worker_id == worker.id:
                self._trees_dict[tree_id][0] = None

        del self._workers[worker.id]

    def _delete_recrtCenter(self: 'Board', recrtCenter: RecrtCenter) -> None:

        recrtCenter.player.recrtCenter_ids.remove(recrtCenter.id)

        if recrtCenter.cell.recrtCenter_id == recrtCenter.id:
            recrtCenter.cell._recrtCenter_id = None
        del self._recrtCenters[recrtCenter.id]

    def next(self) -> 'Board':
        """
        Returns a new board with the current board's next actions applied.
        The current board is unmodified.
        This can form a carbon interpreter, e.g.
            next_observation = Board(current_observation, configuration, actions).next().observation
        """
        # Create a copy of the board to modify so we don't affect the current board
        board = deepcopy(self)
        configuration = board.configuration

        # 计算当前轮招募工人的价格
        rec_collector_cost = configuration.rec_collector_cost + \
                             len(board.collectors) * configuration.rec_collector_increase_cost
        rec_planter_cost = configuration.rec_planter_cost + \
                           len(board.planters) * configuration.rec_planter_increase_cost

        # 计算当前轮树的种植价格
        plant_cost = configuration.plant_cost
        plant_cost_ratio = configuration.plant_cost_inflation_ratio
        plant_cost_base = configuration.plant_cost_inflation_base
        alive_tree_count = sum([tree.age < configuration.tree_lifespan for tree in board.trees.values()])
        plant_market_price = plant_cost + plant_cost_ratio * (plant_cost_base ** alive_tree_count)  # 种树的市场价格

        player_tree_count_threshold = configuration.player_tree_protective_number
        player_plant_cost = {}
        for player in board.players.values():
            if len(player.trees) <= player_tree_count_threshold:  # 种树价格不受市场价格影响
                player_plant_cost[player.id] = plant_cost
            else:
                player_plant_cost[player.id] = plant_market_price

        # 计算玩家指令(转化中心招募指令,种树员+捕碳员移动指令)、更新树龄
        disappeared_tree_flag = {}
        for player in board.players.values():
            # 处理玩家的转化中心发出的指令
            for recrtCenter in player.recrtCenters:
                # 招募捕碳员指令
                if recrtCenter.next_action == RecrtCenterAction.RECCOLLECTOR and \
                        player.cash >= rec_collector_cost and len(player.workers) < configuration.worker_limit:
                    # and len(player.collectors) < configuration.collector_limit  #  暂时不控制捕碳员的数量
                    # Handle RECCOLLECTOR actions
                    player._cash = max(player._cash - rec_collector_cost, 0)
                    board._add_worker(Collector(WorkerId(new_worker_id(player.id)),
                                                recrtCenter.position, 0, player.id, board))
                # 招募种树员指令
                if recrtCenter.next_action == RecrtCenterAction.RECPLANTER and \
                        player.cash >= rec_planter_cost and len(player.workers) < configuration.worker_limit:
                    # and len(player.planters) < configuration.planter_limit  # 暂时不控制种树员的数量
                    # Handle RECPLANTER actions
                    player._cash = max(player._cash - rec_planter_cost, 0)
                    board._add_worker(Planter(WorkerId(new_worker_id(player.id)),
                                              recrtCenter.position, 0, player.id, board))
                # Clear the recrtCenter's action so it doesn't repeat the same action automatically
                recrtCenter.next_action = None

            # 处理玩家的种树人和捕碳人发出的移动指令
            for worker in player.workers:
                if worker.next_action in WorkerAction.moves():
                    worker.cell._worker_id = None
                    worker._position = worker.position.translate(worker.next_action.to_point(), configuration.size)
                    worker._carbon = worker._carbon * (1 - board.configuration.move_cost)

                    # We don't set the new cell's worker_id here as it would be overwritten by another worker in the case of collision.
                    # Later we'll iterate through all workers and re-set the cell._worker_id as appropriate.

            # 处理树龄
            for tree in player.trees:
                if tree.age >= configuration.tree_lifespan:
                    disappeared_tree_flag[tree.position] = True
                    tree.cell._tree_id = None
                    tree.cell._carbon = configuration.co2_frm_withered
                    board._delete_tree(tree)
                else:
                    tree._age += 1  # 树龄 加1

            # Lets just check and make sure.
            assert player.cash >= 0

        # 碰撞检测和更新
        def resolve_collision(workers: List[Worker]) -> Tuple[Optional[Worker], List[Worker]]:
            """
            Accepts the list of workers at a particular position (must not be empty).
            Returns the worker with the least carbon or None in the case of a tie along with all other workers.
            """
            if len(workers) == 1:
                return workers[0], []

            # There was a tie for least carbon, all are deleted
            collectors_by_carbon = group_by(filter(lambda worker: worker.is_collector, workers),
                                            lambda worker: worker.carbon)
            if not collectors_by_carbon:  # 没有捕碳员
                return None, workers
            smallest_carbon = min(collectors_by_carbon.keys())
            smallest_collectors = collectors_by_carbon[smallest_carbon]
            if len(smallest_collectors) == 1:
                winner = smallest_collectors[0]
                return winner, [worker for worker in workers if worker != winner]
            return None, workers

        # Check for worker to worker collisions
        collisions_flag = {}
        worker_collision_groups = group_by(board.workers.values(), lambda worker: worker.position)
        for position, collided_workers in worker_collision_groups.items():
            winner, deleted = resolve_collision(collided_workers)
            collisions_flag[position] = len(deleted) > 0  # 若发生碰撞,标记为True;反之,为False

            is_winner_collector = False
            if winner is not None:
                winner.cell._worker_id = winner.id
                is_winner_collector = winner.is_collector

            for worker in deleted:
                if is_winner_collector:  # 胜者为捕碳员,缴获对方身上的CO2
                    winner._carbon += worker.carbon
                elif worker.cell.tree_id is not None:
                    # 碰撞处存在树，则碰撞方的co2被树全量吸收，即被树的拥有方全量吸收
                    worker.cell.tree.player._cash += worker.carbon
                elif worker.cell.recrtCenter_id is not None:
                    # 碰撞处存在转化中心，则碰撞方的co2被转化中心全量吸收，即被转化中心的拥有方全量吸收
                    worker.cell.recrtCenter.player._cash += worker.carbon
                else:
                    # 碰撞处不存在树，则全掉落在格子处；若格子在树的周围，则树在下一轮才吸收
                    worker.cell._carbon = min(worker.cell._carbon + worker.carbon, configuration.max_cell_carbon)
                # 从地图中删除工人
                board._delete_worker(worker)

        # Check for worker to recrtCenter collisions
        # for recrtCenter in list(board.recrtCenters.values()):
        #     worker = recrtCenter.cell.worker
        #     一组人员进入到对方组转化中心：无影响，仅停留

        # 捕碳员运输CO2到转化中心
        for recrtCenter in list(board.recrtCenters.values()):
            worker = recrtCenter.cell.worker
            if worker is not None:
                if worker.is_collector:  # 捕碳员 回到转化中心
                    if worker.player_id != recrtCenter.player_id and \
                            worker._carbon <= configuration.smelt_cost:  # 对方人员无碳,则直接消失
                        # 从地图中删除工人
                        board._delete_worker(worker)
                    elif worker._carbon >= configuration.smelt_cost:  # 净化CO2
                        recrtCenter.player._cash += worker._carbon - configuration.smelt_cost
                        worker._carbon = 0

        # 计算工人的停留指令(种树员种树/抢树,捕碳员捕碳)
        new_born_tree_ids = set()  # 本轮新种的树
        player_collect_rate = {player_id: max(configuration.initial_collect_rate -
                                              len(player.collectors) * configuration.collect_decrease_rate, 0)
                               for player_id, player in board.players.items()}
        for worker in board.workers.values():
            cell = worker.cell

            if worker.next_action not in WorkerAction.moves():
                if cell.tree_id is None and cell.recrtCenter_id is None:
                    # 此处 无树 且无转化中心
                    delta_carbon = cell.carbon * player_collect_rate.get(worker.player_id, 0)  # 捕碳员的捕碳量

                    if worker.is_planter and worker.player.cash >= player_plant_cost[worker.player_id]:
                        # 此处 当前停留方是种树人 且当前停留方金额超过种树金额 (种树逻辑)
                        worker.player._cash = worker.player._cash - player_plant_cost[worker.player_id]
                        new_tree = Tree(TreeId(new_tree_id(worker.player_id)),
                                        worker.position, 1, worker.player_id, board)
                        board._add_tree(new_tree)
                        board._add_tree_dict(new_tree, worker.id, 0)
                        cell._carbon = 0
                        new_born_tree_ids.add(new_tree.id)
                    elif worker.is_collector and delta_carbon > 0:
                        # 此处 co2数目大于0 且当前停留方是捕碳员 (捕碳逻辑)
                        cell._carbon = max(cell._carbon - delta_carbon, 0)
                        worker._carbon += delta_carbon
                elif cell.tree_id is not None and cell.recrtCenter_id is None:
                    # 此处 有树 且无转化中心 (抢树逻辑)
                    if cell.tree.player_id != worker.player_id and \
                            worker.occupation == Occupation.PLANTER and \
                            worker.player.cash >= configuration.seize_cost:
                        # 此处 当前停留方不是树的归属方,且为种树员,且当前停留方金额超过抢树金额
                        worker.player._cash -= configuration.seize_cost
                        org_tree_id, org_tree_age = cell.tree_id, cell.tree.age
                        board._delete_tree(cell.tree)
                        new_tree = Tree(org_tree_id, cell.position, org_tree_age, worker.player_id, board)
                        board._add_tree(new_tree)
                        board._add_tree_dict(new_tree, worker.id, 0)

        # 树吸收CO2预处理
        quad_surround_tree_flag = {}  # 树的四连通区域标识, key: 坐标, value: 0-表示树不可吸收, >0-表示树可以吸收
        for tree in board.trees.values():
            cell = tree.cell
            for surround_tree in tree.quad_surround():  # 4连通区域
                surround_tree_position = cell.position.translate(surround_tree, configuration.size)

                # 将所有树周围的格子都标记
                if surround_tree_position not in quad_surround_tree_flag:
                    quad_surround_tree_flag[surround_tree_position] = 0

                # 判断树周围是否有人
                surround_tree_cell = board.cells[surround_tree_position]
                if surround_tree_cell.tree_id is None \
                        and (surround_tree_cell.worker_id is None
                             or (surround_tree_cell.worker.occupation == Occupation.PLANTER
                                 or (surround_tree_cell.worker.occupation == Occupation.COLLECTOR
                                     and surround_tree_cell.worker.next_action is not None))):
                    # 周围不存在树 且 (周围不存在人 或 周围存在种树员 或 周围存在捕碳员但不是停留 )
                    quad_surround_tree_flag[surround_tree_position] = quad_surround_tree_flag[surround_tree_position] + 1

        # Collect carbon from cells into trees
        cell_absorption_rate = configuration.cell_absorption_rate  # 树对格子的吸收率(4连通)
        collector_absorption_rate = configuration.collector_absorption_rate  # 树对捕碳员的吸收率(8连通)
        board_carbon_reduction = defaultdict(float)  # 树吸收周边CO2的数量 (仅格子CO2), key: pos, value: co2
        worker_carbon_reduction = defaultdict(float)  # 树吸收周边对手捕碳员携带CO2的数量, key: worker_id, value: co2
        for tree in board.trees.values():
            if tree.id in new_born_tree_ids:  # 本轮种植的树, 不参与计算
                continue

            tree_carbon = 0  # 树吸收CO2总量
            worker_under_tree = board.cells[tree.position].worker
            if worker_under_tree is not None and \
                    worker_under_tree.is_collector and \
                    worker_under_tree.player_id != tree.player_id:  # 树下有对方的捕碳员, 记录树的吸收量
                absorbed_co2 = worker_under_tree.carbon * collector_absorption_rate
                tree_carbon += absorbed_co2  # 记入树
                worker_carbon_reduction[worker_under_tree.id] += absorbed_co2  # 记入捕碳员

            for surround_tree in tree.surround():  # 8连通区域
                surround_tree_position = tree.cell.position.translate(surround_tree, configuration.size)
                surround_tree_cell = board.cells[surround_tree_position]

                if surround_tree_cell.worker is not None and \
                        surround_tree_cell.worker.is_collector and \
                        surround_tree_cell.worker.player_id != tree.player_id:  # 树的周边有对方的捕碳员, 记录树的吸收量
                    absorbed_co2 = surround_tree_cell.worker.carbon * collector_absorption_rate
                    tree_carbon += absorbed_co2  # 记入树
                    worker_carbon_reduction[surround_tree_cell.worker_id] += absorbed_co2  # 记入捕碳员

                if surround_tree_cell.carbon > 0 and \
                        surround_tree_position in quad_surround_tree_flag and \
                        quad_surround_tree_flag[surround_tree_position] > 0:  # 树吸收周边CO2
                    absorbed_co2 = surround_tree_cell.carbon * cell_absorption_rate
                    tree_carbon += absorbed_co2  # 记入树
                    board_carbon_reduction[surround_tree_position] += absorbed_co2  # 记入格子

            tree.player._cash += tree_carbon
            board._add_tree_dict(tree, board._trees_dict[tree.id][0], tree_carbon)

        # 树周围（网格） co2被净化
        for surround_tree_position, absorption_flag in quad_surround_tree_flag.items():
            surround_tree_cell = board.cells[surround_tree_position]
            # 周围单元格的co2大于0，并且，单元格的碳可以被吸收
            if surround_tree_cell.carbon > 0 and absorption_flag > 0:
                current_value = surround_tree_cell.carbon - board_carbon_reduction[surround_tree_position]
                surround_tree_cell._carbon = max(current_value, 0)

        # 树周围（对方捕碳员）在途的CO2被净化
        for worker_id, absorbed_carbon in worker_carbon_reduction.items():
            if absorbed_carbon <= 0:
                continue
            board.workers[worker_id]._carbon = max(board.workers[worker_id].carbon - absorbed_carbon, 0)

        # 地图未受影响的格子CO2增长计算
        for cell in board.cells.values():
            if (cell.worker_id is None or cell.worker.next_action in WorkerAction.moves()) and \
                    cell.position not in collisions_flag and \
                    cell.tree_id is None and \
                    cell.position not in disappeared_tree_flag and \
                    cell.position not in quad_surround_tree_flag:
                # 此处（当前格子中无人 或者 当前格子中有人但不是停留动作）且未发生碰撞 且无树 且树非此轮消失 且非树周围
                next_carbon = cell.carbon * (1 + configuration.regen_rate)
                # TODO: 是否需要随机生成新的碳点 ???
                cell._carbon = min(next_carbon, configuration.max_cell_carbon)
                # Lets just check and make sure.

            assert cell.carbon >= 0

        # Clear the worker's action so it doesn't repeat the same action automatically
        for worker in board.workers.values():
            worker.next_action = None

        # 玩家金额仅保留2位小数
        for player in board.players.values():
            player._cash = round(player._cash, 2)

        # 地图保留3位小数
        for cell in board.cells.values():
            cell._carbon = round(cell._carbon, 3)

        board._step += 1

        return board


def board_agent(agent: Callable[[Board], None]):
    """
    Decorator used to create an agent that modifies a board rather than an observation and a configuration
    Automatically returns the modified board's next actions

    @board_agent
    def my_agent(board: Board) -> None:
        ...
    """

    @wraps(agent)
    def agent_wrapper(obs, config) -> Dict[str, str]:
        board = Board(obs, config)
        agent(board)
        return board.current_player.next_actions

    if agent.__module__ is not None and agent.__module__ in sys.modules:
        setattr(sys.modules[agent.__module__], agent.__name__, agent_wrapper)
    return agent_wrapper

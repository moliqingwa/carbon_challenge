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

import copy
import json
import math
import numpy as np
from os import path
from random import choice, randint, randrange, sample, seed
from numpy.random import MT19937
from numpy.random import RandomState, SeedSequence

from .helpers import board_agent, Board, WorkerAction, RecrtCenterAction, Occupation
from .idgen import new_worker_id, new_recrtCenter_id, new_tree_id, reset as reset_ids
from zerosum_env import utils
from .muagent import mu_agent
from .rain_carbon import *


def get_col_row(size, pos):
    return pos % size, pos // size


def get_to_pos(size, pos, direction):
    col, row = get_col_row(size, pos)
    if direction == "UP":
        return pos - size if pos >= size else size ** 2 - size + col
    elif direction == "DOWN":
        return col if pos + size >= size ** 2 else pos + size
    elif direction == "RIGHT":
        return pos + 1 if col < size - 1 else row * size
    elif direction == "LEFT":
        return pos - 1 if col > 0 else (row + 1) * size - 1


@board_agent
def random_agent(board):
    me = board.current_player
    remaining_carbon = me.cash
    workers = me.workers
    # randomize worker order
    workers = sample(workers, len(workers))
    for worker in workers:
        if worker.cell.carbon > worker.carbon and randint(0, 1) == 0:
            # 50% chance to mine
            continue
        if worker.cell.recrtCenter is None and remaining_carbon > board.configuration.plant_cost:
            # 5% chance to convert at any time
            if randint(0, 19) == 0:
                # remaining_carbon -= board.configuration.plant_cost
                # worker.next_action = WorkerAction.CONVERT
                continue
            # 50% chance to convert if there are no recrtCenters
            if randint(0, 1) == 0 and len(me.recrtCenters) == 0:
                # remaining_carbon -= board.configuration.plant_cost
                # worker.next_action = WorkerAction.CONVERT
                continue
        # None represents the chance to do nothing
        worker.next_action = choice(WorkerAction.moves())
    recrtCenters = me.recrtCenters
    # randomize recrtCenter order
    recrtCenters = sample(recrtCenters, len(recrtCenters))
    worker_count = len(board.next().current_player.workers)
    for recrtCenter in recrtCenters:
        # If there are no workers, always spawn if possible
        if worker_count == 0 and remaining_carbon > board.configuration.rec_collector_cost:
            remaining_carbon -= board.configuration.rec_collector_cost
            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
        # 20% chance to spawn if no workers
        elif randint(0, 4) == 0 and remaining_carbon > board.configuration.rec_plantor_cost:
            remaining_carbon -= board.configuration.rec_plantor_cost
            recrtCenter.next_action = RecrtCenterAction.RECPLANTOR


@board_agent
def my_agent(board):
    me = board.current_player

    # 给自身所有飞船下达往上移动的指令
    for worker in me.workers:
        worker.next_action = WorkerAction.UP

    # 给自身所有飞船下达往下移动的指令
    for worker in me.workers:
        worker.next_action = WorkerAction.DOWN

    # 给自身所有飞船下达往左移动的指令
    for worker in me.workers:
        worker.next_action = WorkerAction.LEFT

    # 给自身所有飞船下达往右移动的指令
    for worker in me.workers:
        worker.next_action = WorkerAction.RIGHT

    # 给自身所有基地下达招募捕碳员的指令
    for recrtCenter in me.recrtCenters:
        recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR

    # 给自身所有基地下达招募种树员的指令
    for recrtCenter in me.recrtCenters:
        recrtCenter.next_action = RecrtCenterAction.RECPLANTOR


@board_agent
def other_agent(board):
    me = board.current_player

    if randint(0, 3) == 1:
        for recrtCenter in me.recrtCenters:
            if me.cash >= 30:
                if randint(0, 2) == 1:
                    recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
                else:
                    recrtCenter.next_action = RecrtCenterAction.RECPLANTOR

    else:
        for worker in me.workers:
            worker.next_action = choice(WorkerAction.moves())


@board_agent
def terminal_agent(board):
    print("current step: ", board.step, ";")
    print("KeyInput: U-UP, D-DOWN, L-LEFT, R-RIGHT, P-RECPLANTOR, C-RECCOLLECTOR, other-None")

    size = board.configuration.size
    result = ''
    for y in range(size):
        for x in range(size):
            cell = board.cells[(x, size - y - 1)]
            result += '| '
            result += str(cell.carbon)
            result += (
                str(cell.worker.occupation)[0] + str(cell.worker.player_id)
                if cell.worker is not None
                else ''
            )
            result += (
                'R' + str(cell.recrtCenter.player_id)
                if cell.recrtCenter is not None
                else ''
            )
            result += (
                'T' + str(cell.tree.player_id)
                if cell.tree is not None
                else ''
            )

        result += ' |\n'

    print(result)

    move_switch = {
        'U': WorkerAction.UP,
        'D': WorkerAction.DOWN,
        'L': WorkerAction.LEFT,
        'R': WorkerAction.RIGHT
    }
    rec_switch = {
        'P': RecrtCenterAction.RECPLANTOR,
        'C': RecrtCenterAction.RECCOLLECTOR,
    }
    me = board.current_player
    for recrtCenter in me.recrtCenters:
        print(recrtCenter.id + " action: ")
        args = input()
        recrtCenter.next_action = rec_switch.get(args.upper())

    for worker in me.workers:
        print(str(worker.occupation) + "-" + worker.id + " action: ")
        args = input()
        worker.next_action = move_switch.get(args.upper())


agents = {"random": random_agent, "my_agent": my_agent,
          "other_agent": other_agent, "my_agent1": Tankagent1, "terminal_agent": terminal_agent,
          "yuhm_agent": Tankagent1, "mu_agent": mu_agent}


def populate_board(state, env):
    obs = state[0].observation
    config = env.configuration
    size = env.configuration.size

    # Set seed for random number generators
    if not hasattr(config, "randomSeed"):
        max_int_32 = (1 << 31) - 1
        config.randomSeed = randrange(max_int_32)

    np_rs = RandomState(MT19937(SeedSequence(config.randomSeed)))
    # np.random.seed(config.randomSeed)
    # seed(config.randomSeed)

    # Distribute Carbon evenly into quartiles.
    half = math.ceil(size / 2)
    grid = [[0] * half for _ in range(half)]

    # Randomly place a few carbon "seeds".
    for i in range(half):
        # random distribution across entire quartile
        grid[randint(0, half - 1)][randint(0, half - 1)] = i ** 2

        # as well as a particular distribution weighted toward the center of the map
        grid[randint(half // 2, half - 1)][randint(half // 2, half - 1)] = i ** 2

    # Spread the seeds radially.
    radius_grid = copy.deepcopy(grid)
    for r in range(half):
        for c in range(half):
            value = grid[r][c]
            if value == 0:
                continue

            # keep initial seed values, but constrain radius of clusters
            radius = min(round((value / half) ** 0.5), 1)
            for r2 in range(r - radius + 1, r + radius):
                for c2 in range(c - radius + 1, c + radius):
                    if 0 <= r2 < half and 0 <= c2 < half:
                        distance = (abs(r2 - r) ** 2 + abs(c2 - c) ** 2) ** 0.5
                        radius_grid[r2][c2] += int(value /
                                                   max(1, distance) ** distance)

    # add some random sprouts of carbon
    radius_grid = np.asarray(radius_grid)
    add_grid = np_rs.gumbel(0, 300.0, size=(half, half)).astype(int)
    sparse_radius_grid = np_rs.binomial(1, 0.5, size=(half, half))
    add_grid = np.clip(add_grid, 0, a_max=None) * sparse_radius_grid
    radius_grid += add_grid

    # add another set of random locations to the center corner
    corner_grid = np_rs.gumbel(
        0, 500.0, size=(half // 4, half // 4)).astype(int)
    corner_grid = np.clip(corner_grid, 0, a_max=None)
    radius_grid[half - (half // 4):, half - (half // 4):] += corner_grid

    # Normalize the available carbon against the defined configuration starting carbon.
    total = sum([sum(row) for row in radius_grid])
    obs.carbon = [0] * (size ** 2)
    for r, row in enumerate(radius_grid):
        for c, val in enumerate(row):
            val = min(int(val * config.startingCarbon / total / 4),
                      config.startingCellCarbon)
            obs.carbon[size * r + c] = val
            obs.carbon[size * r + (size - c - 1)] = val
            obs.carbon[size * (size - 1) - (size * r) + c] = val
            obs.carbon[size * (size - 1) - (size * r) + (size - c - 1)] = val

    # Distribute the starting workers evenly.
    num_agents = len(state)
    starting_positions = [0] * num_agents
    if num_agents == 1:
        starting_positions[0] = size * (size // 2) + size // 2
    elif num_agents == 2:
        # starting_positions[0] = size * (size // 2) + size // 4
        # starting_positions[1] = size * (size // 2) + math.ceil(3 * size / 4) - 1
        starting_positions[0] = size * (size // 4 + config.startPosOffset) + size // 4 + config.startPosOffset
        starting_positions[1] = size * (3 * size // 4 - config.startPosOffset) + 3 * size // 4 - config.startPosOffset
        obs.carbon[starting_positions[0]] = 0
        obs.carbon[starting_positions[1]] = 0
    elif num_agents == 4:
        starting_positions[0] = size * (size // 4) + size // 4
        starting_positions[1] = size * (size // 4) + 3 * size // 4
        starting_positions[2] = size * (3 * size // 4) + size // 4
        starting_positions[3] = size * (3 * size // 4) + 3 * size // 4

    # Initialize the players.
    reset_ids()
    obs.players = []
    for i in range(num_agents):
        # workers = {new_worker_id(i): [starting_positions[i], 0, '']}
        recrtCenter = {new_recrtCenter_id(i): starting_positions[i]}
        # tree = {new_tree_id(i): starting_positions[i]+3}
        obs.players.append([state[0].reward, recrtCenter, {}, {}])

    return state


def interpreter(state, env):
    obs = state[0].observation
    config = env.configuration

    # Initialize the board (place cell carbon and starting workers).
    if env.done:
        return populate_board(state, env)

    # Interpreter invoked here
    actions = [agent.action for agent in state]
    board = Board(obs, config, actions)
    board = board.next()
    state[0].observation = obs = utils.structify(board.observation)

    # Remove players with invalid status or insufficient potential.
    for index, agent in enumerate(state):
        player_cash, recrtCenters, workers, trees = obs.players[index]
        if agent.status == "ACTIVE":
            collector, planter = [], []
            for worker in workers.values():
                _, _, worker_type = worker
                if worker_type == str(Occupation.COLLECTOR):
                    collector.append(worker)
                if worker_type == str(Occupation.PLANTOR):
                    planter.append(worker)
            # 无捕碳员 且无种树员 且无树 且（无转化中心 或（玩家金额不足以 招募捕碳员 或 招募种树员且种一棵树 ））
            if len(workers) == 0 and len(trees) == 0 and (
                    len(recrtCenters) == 0 or player_cash < min(config.recCollectorCost, config.recPlantorCost)):
                # Agent can no longer gather any cash
                agent.status = "DONE"
                agent.reward = board.step - board.configuration.episode_steps - 1

        if agent.status != "ACTIVE" and agent.status != "DONE":
            obs.players[index] = [0, {}, {}, {}]

    # Check if done (< 2 players and num_agents > 1)
    if len(state) > 1 and sum(1 for agent in state if agent.status == "ACTIVE") < 2:
        for agent in state:
            if agent.status == "ACTIVE":
                agent.status = "DONE"

    # Update Rewards.
    for index, agent in enumerate(state):
        if agent.status == "ACTIVE":
            agent.reward = obs.players[index][0]
        elif agent.status != "DONE":
            agent.reward = 0

    return state


def renderer(state, env):
    config = env.configuration
    size = config.size
    obs = state[0].observation

    board = [[h, -1, -1, -1, "", -1, -1] for h in obs.carbon]
    for index, player in enumerate(obs.players):
        _, recrtCenters, workers, trees = player
        for recrtCenter_pos in recrtCenters.values():
            board[recrtCenter_pos][1] = index
        for worker in workers.values():
            worker_pos, worker_carbon, worker_type = worker
            board[worker_pos][2] = index
            board[worker_pos][3] = worker_carbon
            board[worker_pos][4] = worker_type
        for tree_pos, tree_lifecycle in trees.values():
            board[tree_pos][5] = index
            board[tree_pos][6] = tree_lifecycle

    col_divider = "|"
    row_divider = "+" + "+".join(["----"] * size) + "+\n"

    out = row_divider
    for row in range(size):
        for col in range(size):
            _, _, worker, worker_carbon, worker_type, _, _ = board[col + row * size]
            out += col_divider + (
                f"{min(int(worker_carbon), 99)}{worker_type[0]}{worker}" if worker > -1 else ""
            ).ljust(4)
        out += col_divider + "\n"
        for col in range(size):
            carbon, recrtCenter, _, _, _, _, _ = board[col + row * size]
            if recrtCenter > -1:
                out += col_divider + f"R{recrtCenter}".ljust(4)
            else:
                out += col_divider + str(min(int(carbon), 9999)).rjust(4)
        out += col_divider + "\n"
        for col in range(size):
            _, _, _, _, _, tree, tree_lifecycle = board[col + row * size]
            out += col_divider + (
                f"{tree_lifecycle}T{tree}" if tree > -1 else ""
            ).ljust(4)
        out += col_divider + "\n" + row_divider
    print(out)
    return out


dir_path = path.dirname(__file__)
json_path = path.abspath(path.join(dir_path, "carbon.json"))
with open(json_path) as json_file:
    specification = json.load(json_file)


def html_renderer():
    js_path = path.abspath(path.join(dir_path, "carbon.js"))
    with open(js_path, encoding="utf-8") as js_file:
        return js_file.read()

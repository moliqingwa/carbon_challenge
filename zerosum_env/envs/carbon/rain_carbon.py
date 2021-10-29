import copy
import datetime
import heapq
import logging
import numpy as np
from operator import itemgetter, attrgetter
from queue import Queue
import sys
from .helpers import *

MY_DATEFMT = '%M:%S'
file_path = 'my123.txt'


def easy_log(s, loglevel='D'):
    pass
    # with open(file_path, 'a') as file_object:
    #     file_object.write(
    #         f'{datetime.datetime.now().strftime(MY_DATEFMT)}{loglevel.upper()[0]} {s} '+'\n')
    # print(
    #     f'{datetime.datetime.now().strftime(MY_DATEFMT)}{loglevel.upper()[0]} {s}')


easy_log('ini begin')

MAX_TREE_AGE = 50
MAX_HALITE = 500
MAP_SIZE = 15
HALF_MAP_SIZE = MAP_SIZE // 2
ROWS = MAP_SIZE
COLS = MAP_SIZE

MAX_Plater = 4                  # 植树员
MAX_Collector_Tree = 4          # 收树员
MAX_Collector_Carbon = 2        # 攻击
Tree_absorption_rate = 0.02     # 树吸收效率

# 玩家个数
PLAYERS = 2
MOVE = [
    None,
    WorkerAction.UP,
    WorkerAction.RIGHT,
    WorkerAction.DOWN,
    WorkerAction.LEFT,
]
LEN_MOVE = len(MOVE)
I_MINE = 0
I_NORTH = 1
I_EAST = 2
I_SOUTH = 3
I_WEST = 4
I_NORTH_EAST = 5
I_SOUTH_EAST = 6
I_SOUTH_WEST = 7
I_NORTH_WEST = 8
I_CONVERT = 5


def ship_action_to_int(action, convert_aware=False):
    if action is None:
        return I_MINE
    elif isinstance(action, int):
        return action
    elif action == WorkerAction.UP:
        return I_NORTH
    elif action == WorkerAction.RIGHT:
        return I_EAST
    elif action == WorkerAction.DOWN:
        return I_SOUTH
    elif action == WorkerAction.LEFT:
        return I_WEST
    return I_MINE


DY = [0, 1, 0, -1, 0]
DX = [0, 0, 1, 0, -1]

XX = [-1, 0, 1]
YY = [1, 0, -1]

SX = [-2, -1, 0, 1, 2]
SY = [2, 1, 0, -1, -2]


def position_to_ij(p):
    return ROWS - p[1] - 1, p[0]


def ij_to_position(i, j):
    return j, ROWS - i - 1


def mod_map_size_x(x):
    return (x + MAP_SIZE) % MAP_SIZE


def rotated_diff_position_impl(x0, x1):
    """x1 - x0 的値域 控制在 [-20, 20] - [-10, 10] """
    d = x1 - x0
    if d < - HALF_MAP_SIZE:  # [-20, -11]
        return d + MAP_SIZE  # [1, 10]
    elif HALF_MAP_SIZE < d:  # [11, 20]
        return d - MAP_SIZE  # [-10, -1]
    return d


def initialize_rotated_diff_position():
    t = np.zeros((MAP_SIZE, MAP_SIZE), dtype=np.int32)
    for x0 in range(MAP_SIZE):
        for x1 in range(MAP_SIZE):
            t[x0, x1] = rotated_diff_position_impl(x0, x1)
    t.flags.writeable = False
    return t


ROTATED_DIFF_POSITION = initialize_rotated_diff_position()


def rotated_diff_position(x0, x1):
    return ROTATED_DIFF_POSITION[x0, x1]


def distance_impl(x0, x1, y0, y1):
    dx = abs(rotated_diff_position(x0, x1))
    dy = abs(rotated_diff_position(y0, y1))
    return dx + dy


def initialize_distance():
    t = np.zeros((COLS, ROWS, COLS, ROWS), dtype=np.int32)
    for x0 in range(COLS):
        for y0 in range(ROWS):
            for x1 in range(COLS):
                for y1 in range(ROWS):
                    t[x0, y0, x1, y1] = distance_impl(
                        x0=x0, y0=y0, x1=x1, y1=y1)
    t.flags.writeable = False
    return t


DISTANCE = initialize_distance()


def calculate_distance(p0, p1):
    return DISTANCE[p0[0], p0[1], p1[0], p1[1]]


def initialize_neighbor_positions(sup_d):
    """曼哈顿距离增加1时的全范围x, y距离d"""
    ts = []
    us = []
    for d in range(sup_d):
        n_neighbors = 1 + (d * (d + 1) // 2) * 4
        t = np.zeros((n_neighbors, 3), dtype=np.int32)
        k = 0
        for dx in range(-d, d + 1):
            abs_dx = abs(dx)
            for dy in range(-d, d + 1):
                abs_dy = abs(dy)
                if d < abs_dx + abs_dy:
                    continue
                t[k, :] = dx, dy, abs_dx + abs_dy
                k += 1
        assert k == n_neighbors
        u = np.zeros((COLS, ROWS, n_neighbors, 3), dtype=np.int32)
        for x in range(COLS):
            for y in range(ROWS):
                for k, (dx, dy, d) in enumerate(t):
                    x1 = mod_map_size_x(x + dx)
                    y1 = mod_map_size_x(y + dy)
                    u[x, y, k, :] = x1, y1, d
        t.flags.writeable = False
        u.flags.writeable = False
        ts.append(t)
        us.append(u)
    return ts, us


NEIGHBOR_D_POSITIONS, NEIGHBOR_POSITIONS = initialize_neighbor_positions(
    sup_d=5)


def neighbor_d_positions(d):
    return NEIGHBOR_D_POSITIONS[d]


def neighbor_positions(d, p):
    return NEIGHBOR_POSITIONS[d][p[0], p[1]]


DISTANCE_TO_PREFERENCE = [0.62 + 0.02 * i for i in range(HALF_MAP_SIZE)] + [
    1.0] + [1.2 + 0.02 * i for i in range(HALF_MAP_SIZE)]


def distance_to_preference(d):
    return DISTANCE_TO_PREFERENCE[d + HALF_MAP_SIZE]


def preference_move_to_impl_2(x0, x1, dx_action):
    abs_dx0 = abs(rotated_diff_position(x0=x0, x1=x1))
    x_ = mod_map_size_x(x0 + dx_action)
    abs_dx_ = abs(rotated_diff_position(x0=x_, x1=x1))
    preference = 1.0
    dx2 = abs_dx_ - abs_dx0
    if dx2 < 0:  # 缩短了距离远的 abs_dx0
        preference *= distance_to_preference(abs_dx0)
    elif 0 < dx2:  # 远了 abs_dx_
        preference *= distance_to_preference(-abs_dx_)
    return preference


def preference_move_to_impl(x0, y0, x1, y1):
    """x0, y0: 現在位置; x1, y1: 目標位置"""
    preference = np.ones(LEN_MOVE, dtype=np.float32)
    for i_action in range(LEN_MOVE):
        preference[i_action] *= preference_move_to_impl_2(
            x0=x0, x1=x1, dx_action=DX[i_action])
        preference[i_action] *= preference_move_to_impl_2(
            x0=y0, x1=y1, dx_action=DY[i_action])
    if x0 == x1 and y0 == y1:
        preference[0] *= 1.5
    return preference


def initialize_preference_move_to():
    t = np.zeros((COLS, ROWS, LEN_MOVE), dtype=np.float32)
    for x1 in range(COLS):
        for y1 in range(ROWS):
            t[x1, y1, :] = preference_move_to_impl(x0=0, y0=0, x1=x1, y1=y1)
    t.flags.writeable = False
    return t


PREFERENCE_MOVE_TO = initialize_preference_move_to()


def preference_move_to(p0, p1):
    x1 = mod_map_size_x(p1[0] - p0[0])
    y1 = mod_map_size_x(p1[1] - p0[1])
    return PREFERENCE_MOVE_TO[x1, y1]


def calculate_next_position(position, next_action):
    """next_action 移动后查找的坐标"""
    p = position
    if isinstance(int(next_action), int):
        next_action = MOVE[next_action]
    print(isinstance(next_action, int))
    # assert (next_action is None) or isinstance(next_action, WorkerAction)
    if next_action == WorkerAction.UP:
        p = Point(x=p[0], y=(p[1] + 1) % ROWS)
    elif next_action == WorkerAction.RIGHT:
        p = Point(x=(p[0] + 1) % COLS, y=p[1])
    elif next_action == WorkerAction.DOWN:
        p = Point(x=p[0], y=(p[1] + ROWS - 1) % ROWS)
    elif next_action == WorkerAction.LEFT:
        p = Point(x=(p[0] + COLS - 1) % COLS, y=p[1])
    return p


def direction_to_str(next_action):
    if next_action == WorkerAction.UP:
        return '^'
    elif next_action == WorkerAction.RIGHT:
        return '>'
    elif next_action == WorkerAction.DOWN:
        return 'v'
    elif next_action == WorkerAction.LEFT:
        return '<'
    return '.'


I_SCORE_HALITE = 16  # 只是地面 carbon
I_SCORE_HALITE_D4 = 17  # 周围4格的 carbon
I_SCORE_HALITE_D8 = 18  # 周围8格的 carbon
I_SCORE_HALITE_D9 = 19  # 9宫格 carbon
N_SCORE_TYPES = 36


class TankTank():
    def __init__(self, player_id, *args, verbose, **kwargs):
        self.player_id = player_id
        self.verbose = verbose
        self.scores = np.zeros((N_SCORE_TYPES, ROWS, COLS), dtype=np.float32)
        self.collec_tree = [None] * MAX_Collector_Tree
        self.collec_collec = [None] * MAX_Collector_Carbon
        self.planter_list = [None] * MAX_Plater
        self.opponent_player = {}
        self.board = None
        self.log_step = -1
        self.logs = {}

    def log(self, s, step=None, id_=None, indent=0, loglevel='DEBUG'):
        if not self.verbose:
            return
        level = getattr(logging, loglevel.upper())
        if level < logging.DEBUG:
            # return
            pass
        prefix = ''
        if 0 < indent:
            prefix += ' ' * indent
        if step is None:
            step = self.board.step
        prefix += f'step{step} '
        if self.log_step != step:
            self.logs.clear()
            self.log_step = step
        if id_ is not None:
            prefix += f'id{id_} '
            if id_ not in self.logs:
                self.logs[id_] = []
            if (self.verbose & 4) == 4:
                self.logs[id_].append(f'{prefix}{s}')
        # and logging.DEBUG < level
        if ((self.verbose & 4) == 4) or ((self.verbose & 1) == 1):
            easy_log(f'{prefix}{s}', loglevel=loglevel)

    def cup_cell_carbon(self, x, y, position):
        t_count = 1
        for i in range(3):
            for j in range(3):
                pX = (x + XX[i] + 15) % 15
                pY = (y + YY[j] + 15) % 15
                if pX == position[0] and pY == position[1]:
                    continue
                if self.board.cells[pX, pY].tree_id is not None:
                    t_count += 1
        return self.board.cells[x, y].carbon * Tree_absorption_rate / t_count

    def update_score_D89(self, x, y):
        sum8 = 0
        sum9 = 0
        for i in range(3):
            for j in range(3):
                pX = (x + XX[i] + 15) % 15
                pY = (y + YY[j] + 15) % 15
                if(i == 1 and j == 1):
                    sum9 += self.board.cells[pX, pY].carbon
                    continue
                sum8 += self.cup_cell_carbon(pX, pY, [x, y])
                sum9 += self.board.cells[pX, pY].carbon
        return sum8, sum9

    def update_score(self):
        """更新地图资源"""
        self.scores[I_SCORE_HALITE_D8:, ...] = 0.0
        self.scores_D8 = []
        self.scores_D9 = []
        self.scores_D1 = []
        self.Go_back = False
        for x in range(COLS):
            for y in range(ROWS):
                if self.board.cells[x, y].recrtCenter_id is not None:
                    continue
                i, j = position_to_ij((x, y))
                self.scores[I_SCORE_HALITE, i,
                            j] = self.board.cells[x, y].carbon
                d8, d9 = self.update_score_D89(x, y)
                self.scores[I_SCORE_HALITE_D8, i, j] = d8
                self.scores[I_SCORE_HALITE_D9, i, j] = d9
                self.scores_D8.append([self.scores[I_SCORE_HALITE_D8, i,
                                                   j], i, j])
                self.scores_D9.append(
                    [self.scores[I_SCORE_HALITE_D9, i, j], i, j])

                self.scores_D1.append([self.scores[I_SCORE_HALITE, i,
                                                   j], i, j])
        self.scores_D8 = sorted(
            self.scores_D8, key=itemgetter(0), reverse=True)
        self.scores_D9 = sorted(
            self.scores_D9, key=itemgetter(0), reverse=True)
        self.scores_D1 = sorted(
            self.scores_D1, key=itemgetter(0), reverse=True)
        self.log(
            f'地图资源 scores_D8->  = {self.scores_D8}')
        self.world_halite = np.sum(self.scores[I_SCORE_HALITE])
        self.halite_per_ship = self.world_halite / \
            max(1, len(self.board.workers))

        self.log(f'世界地图资源总量：{self.world_halite} 平均捕获量：{self.halite_per_ship} ')

        for d in range(len(self.collec_tree)):
            if(self.collec_tree[d] not in self.board.workers.keys()):
                self.collec_tree[d] = None

        for d in range(len(self.collec_collec)):
            if(self.collec_collec[d] not in self.board.workers.keys()):
                self.collec_collec[d] = None

        for worker in self.board.current_player.collectors:
            if worker.id not in self.collec_tree and None in self.collec_tree:
                i = self.collec_tree.index(None)
                self.collec_tree[i] = worker.id
            elif worker.id not in self.collec_collec and None in self.collec_collec:
                i = self.collec_collec.index(None)
                self.collec_collec[i] = worker.id

        for recrtCenter in self.board.recrtCenters.values():
            if recrtCenter not in self.board.current_player.recrtCenters:
                self.opponent_player['recrtCenter'] = recrtCenter

        for play in self.board.players.values():
            if play.id != self.board.current_player.id:
                self.opponent_player['player'] = play

        for p in range(len(self.planter_list)):
            if self.planter_list[p] not in self.board.workers.keys():
                self.planter_list[p] = None

        for p in self.board.current_player.planters:
            if p.id not in self.planter_list:
                i = self.planter_list.index(None)
                self.planter_list[i] = p.id

        # 初始化可以攻击的捕碳员列表
        self.collectorList = []
        for collectordd in self.board.collectors.values():
            if collectordd not in self.board.current_player.collectors and collectordd.carbon > 100:
                self.collectorList.append(
                    [collectordd.id, collectordd.carbon, collectordd.position])
        self.collectorList = sorted(
            self.collectorList, key=itemgetter(1), reverse=True)
        self.log(
            f'可攻击列表collectorList->  = {self.collectorList}')

    def recrtCenter_strategy(self, recrtCenter):
        """
        有30万金币且转化中心没有自己的工作人员，方可继续。
        """
        p0 = recrtCenter.position
        if self.free_carbon >= 30:
            if self.board.cells[recrtCenter.position].worker_id not in self.board.current_player.worker_ids:
                # if(self.free_carbon >= 50 and (self.len_collectors + self.len_plantors) == 0):
                #     if(self.board.step < 292):
                #         recrtCenter.next_action = RecrtCenterAction.RECPLANTOR
                #     else:
                #         pass
                #     pass
                # else:
                if self.len_collectors < 2:
                    if(self.free_carbon >= 30):
                        recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
                        self.target_position.append(p0)
                        self.danger_position.append(p0)
                        return
                if self.len_planters < MAX_Plater:
                    if(self.free_carbon >= 50 and self.board.step < 292):
                        recrtCenter.next_action = RecrtCenterAction.RECPLANTER
                        self.target_position.append(p0)
                        self.danger_position.append(p0)
                        return
                elif self.len_collectors < MAX_Collector_Tree:
                    if(self.free_carbon >= 30):
                        recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
                        self.target_position.append(p0)
                        self.danger_position.append(p0)
                        return
            else:
                # 有飞船在基地挂机
                pass

    def worker2Position(self, position):
        distance = 99
        for worker in self.opponent_player['player'].workers:
            d = calculate_distance(worker.position, position)
            distance = min(distance, d)
        return distance

    def guss_tree_reverse(self, tree, carban_want=40):
        """判断树否可以转换"""
        i, j = position_to_ij(tree.position)
        getc = self.scores[I_SCORE_HALITE_D8, i, j]
        maxage = min(298 - self.board.step, 50-tree.age,
                     self.worker2Position(tree.position))
        if(getc * maxage > carban_want and self.free_carbon > 100):
            return True
        else:
            return False
        pass

    def now_position_tree(self, position):
        if self.board.cells[position].tree_id is not None and self.board.cells[position].tree_id not in self.board.current_player.tree_ids:
            tree = self.board.trees[self.board.cells[position].tree_id]
            return self.guss_tree_reverse(tree, 40)
        return False

    def distenceP0_P1(self, p0, p1):
        return distance_impl(p0[0], p1[0], p0[1], p1[1])

    def isSound(self, type, x, y, dis):
        for i in range(5):
            for j in range(5):
                sx = (x + SX[i] + 15) % 15
                sy = (y + SY[j] + 15) % 15
                if type == "tree" and self.board.cells[sx, sy].tree_id is not None and self.board.cells[sx, sy].tree_id in self.board.current_player.tree_ids and (50-self.board.cells[sx, sy].tree.age) > dis:
                    return False
                pass
        return True

    def isSound_other_tree(self, position):
        """判断周围是否有对手树木"""
        pass

    def less_tree(self, position):
        for n in self.target_position:
            if distance_impl(position[0], n[0], position[1], n[1]) < 3:
                return False
        return True

    def distenceD_D(self, md, x, y):
        """计算下个目标点"""
        d = 0
        distence = 99999
        self.log(f'self.target_position = {self.target_position}')
        for index in range(len(md)):
            if md[index][1] not in self.target_position and md[index][1] not in self.danger_position:
                xyd = distance_impl(md[index][1][0], x, md[index][1][1], y)
                if(xyd < distence):
                    d = index
                    distence = xyd
        return md[d][1][0], md[d][1][1]

    def putindex(self, worker, x, y, lis):
        id = lis.index(worker.id)
        r1 = self.board.current_player.recrtCenters[0].position
        if(id < 8):
            if(r1[0] < 7):
                if r1[1] < 7:
                    id = (id + 2) % 4
                else:
                    id = (id + 1) % 4
                pass
            else:
                if r1[1] < 7:
                    id = (id + 3) % 4
                else:
                    id = (id + 0) % 4
        if(id == 0):
            if x >= 7 and y >= 7:
                return True
            else:
                return False
        elif id == 1:
            if x <= 7 and y >= 7:
                return True
            else:
                return False
        elif id == 2:
            if x <= 7 and y <= 7:
                return True
            else:
                return False
        elif id == 3:
            if x >= 7 and y <= 7:
                return True
            else:
                return False
        else:
            return True

    def neighbor_cells(self, cell):
        cells = [cell]
        cells.append(cell.up)
        cells.append(cell.right)
        cells.append(cell.down)
        cells.append(cell.left)
        return cells

    def prevent_attach(self, worked, next_move):
        """防止撞击"""
        nextPosition = calculate_next_position(worked.position, next_move)
        if self.Go_back and nextPosition == self.board.current_player.recrtCenters[0].position:
            return True
        self.log(
            f'danger_position = {self.danger_position} nextPosition = {nextPosition}')
        if nextPosition not in self.danger_position:
            cells = self.neighbor_cells(self.board.cells[nextPosition])
            for cell in cells:
                if(cell.position == worked.position):
                    continue
                self.log(f'cell.worker_id = {cell.worker_id}')
                if(cell.worker_id is not None and cell.worker_id not in self.board.current_player.worker_ids):
                    if(self.board.workers[cell.worker_id].carbon > 100):
                        if(cells[0].tree_id is not None):
                            if(cells[0].tree_id in self.board.current_player.tree_ids):
                                self.danger_position.append(nextPosition)
                                return True
                            else:
                                return False
                        else:
                            self.danger_position.append(nextPosition)
                            return True
                    else:
                        return False
            self.danger_position.append(nextPosition)
            return True
        else:
            return False

    def rever_work(self, worker, q):
        """处理worker动作"""
        for action in np.argsort(-q):
            if self.prevent_attach(worker, action):
                worker.next_action = MOVE[action]
                return
        pass

    def random_position(self, worker, lis):
        id = lis.index(worker.id)
        r1 = self.board.current_player.recrtCenters[0].position
        if(id < 8):
            if(r1[0] < 7):
                if r1[1] < 7:
                    id = (id + 2) % 4
                else:
                    id = (id + 1) % 4
                pass
            else:
                if r1[1] < 7:
                    id = (id + 3) % 4
                else:
                    id = (id + 0) % 4
        if(id == 0):
            return 10, 10
        elif id == 1:
            return 4, 10
        elif id == 2:
            return 4, 4
        elif id == 3:
            return 10, 4
        else:
            return 7, 7

    def ranom_next_move(self, worker):
        p0 = worker.position
        p1 = worker.position if p0 != self.board.current_player.recrtCenters[0].position else Point(
            p0.x - 1, p0.y - 1)
        q = preference_move_to(p0, p1)
        self.target_position.append(p1)
        self.rever_work(worker, q)
        self.log(
            f'{worker.id} 当前位置={ p0 }目标位置={ p0 } ')
        print(q)
        pass

    def planter_strategy(self):
        for worker in self.board.current_player.planters:
            """植树策略"""
            p0 = worker.position
            if self.now_position_tree(p0):
                worker.next_action = MOVE[0]
                continue
            md4 = []
            mmm = 5
            for d in self.scores_D8:
                dis = self.distenceP0_P1(p0, [d[1], d[2]])
                if (len(self.board.current_player.trees) == 0):
                    # if disR_8 > 7:
                    #     continue
                    mmm = 5
                else:
                    mmm = 0.7

                # and (d[0] * (1.05) ** dis) < 8
                # elif len(self.board.current_player.trees) > 0:
                #     continue
                x, y = ij_to_position(d[1], d[2])
                # self.board.cells[Point(x, y)].tree_id is None and
                if self.isSound('tree', x, y, dis) and self.less_tree(Point(x, y)):
                    # 当前单元格没有树，且周围也没有自己的树
                    if d[0] > mmm and self.putindex(worker, x, y, self.planter_list):
                        md4.append([0, [x, y]])
                # elif self.board.cells[Point(x, y)].tree_id is not None and self.board.cells[Point(x, y)].tree_id not in self.board.current_player.tree_ids:
                    # 当前单元格有树且不是自己的树
                    pass
            if len(md4) > 0:
                if self.free_carbon < 50 and self.board.cells[p0].tree_id is not None:
                    self.ranom_next_move(worker)
                else:
                    self.log(
                        f'飞船 {worker.id,self.planter_list.index(worker.id),md4} ')
                    mx, my = self.distenceD_D(md4, p0[0], p0[1])
                    p1 = Point(mx, my)
                    self.target_position.append([mx, my])
                    q = preference_move_to(p0, p1)
                    # action = np.argmax(q)
                    # worker.next_action = MOVE[action]
                    self.rever_work(worker, q)
                    self.log(
                        f'{worker.id} 当前位置={ p0 }目标位置={ p1 } ')
            else:
                self.ranom_next_move(worker)

    def statistics_trees(self, worker, position, away=15, carbon=40):
        collect_trees = []
        for tree in self.board.trees.values():
            if tree.player_id != self.board.current_player.id and tree.position not in self.target_position:
                worker_2_Tree = self.distenceP0_P1(position, tree.position)
                age = min(300-self.board.step, 50 - tree.age - worker_2_Tree-1)
                i, j = position_to_ij(tree.position)
                self.log(
                    f'树点--->年龄 {tree.age} 位置 {tree.position, age, self.scores[I_SCORE_HALITE_D8, i, j]} worker_2_Tree {worker_2_Tree}')
                if age * self.scores[I_SCORE_HALITE_D8, i, j] > carbon and worker_2_Tree <= away and self.putindex(worker, tree.position[0], tree.position[1], self.collec_tree):
                    collect_trees.append(
                        [age * self.scores[I_SCORE_HALITE_D8, i, j], tree.position])
        return collect_trees

    def collector_carbon_strategy(self, collector):
        """收集二氧化碳"""
        p0 = collector.position
        p1 = None
        if self.board.cells[collector.position].carbon > 10:
            self.ranom_next_move(collector)
            return

        if len(self.board.current_player.collectors) == 1 and collector.carbon + self.free_carbon > 30 and collector.carbon != 0:
            p1 = self.board.current_player.recrtCenters[0].position
        elif len(self.board.current_player.trees) == 0 and collector.carbon + self.free_carbon > 100 and collector.carbon != 0:
            p1 = self.board.current_player.recrtCenters[0].position
        elif collector.carbon > 100:
            p1 = self.board.current_player.recrtCenters[0].position
        else:
            md = []
            for d in self.scores_D1:
                x, y = ij_to_position(d[1], d[2])
                if d[0] > 5:
                    md.append([0, [x, y]])
            mx, my = self.distenceD_D(md, p0[0], p0[1])
            p1 = Point(mx, my)
        q = preference_move_to(p0, p1)
        # action = np.argmax(q)
        # collertor.next_action = MOVE[action]

        self.target_position.append(p1)
        self.rever_work(collector, q)
        # self.collec_tree.append(collertor.id)
        self.log(
            f'捕碳员={ collector.id }当前位置={ p0 }目标位置={ p1 } next_action = {collector.next_action}')
        pass

    def collector_tree_strategy(self, collertor):
        """收树策略"""
        # if self.board.cells[collertor.position].carbon >= 40:
        #     collertor.next_action = MOVE[0]
        #     return

        if collertor.carbon > self.halite_per_ship:
            self.collector_carbon_strategy(collertor)
            return

        p0 = collertor.position
        collect_trees = sorted(self.statistics_trees(collertor,
                                                     p0), key=itemgetter(0), reverse=True)
        self.log(f'转换树捕碳员={ collect_trees }')
        if len(collect_trees) > 0:
            le = 4 if len(collect_trees) > 4 else len(collect_trees)
            mx, my = self.distenceD_D(collect_trees[0:le], p0[0], p0[1])
            p1 = Point(mx, my)
            q = preference_move_to(p0, p1)
            # action = np.argmax(q)
            # collertor.next_action = MOVE[action]

            self.target_position.append(p1)
            self.rever_work(collertor, q)
            # self.collec_tree.append(collertor.id)
            self.log(
                f'种树人={ collertor.id }当前位置={ p0 }目标位置={ p1 } next_action = {collertor.next_action}')
        else:
            md = []
            for d in self.scores_D1:
                if d[0] > 5:
                    x, y = ij_to_position(d[1], d[2])
                    md.append([0, [x, y]])
            if len(md) > 0:
                mx, my = self.distenceD_D(md, p0[0], p0[1])
                p1 = Point(mx, my)
                q = preference_move_to(p0, p1)
                # action = np.argmax(q)
                # collertor.next_action = MOVE[action]

                self.target_position.append(p1)
                self.rever_work(collertor, q)
                # self.collec_tree.append(collertor.id)
                self.log(
                    f'捕碳员={ collertor.id }当前位置={ p0 }目标位置={ p1 } next_action = {collertor.next_action}')
                return

            if collertor.carbon > self.halite_per_ship:
                self.collector_carbon_strategy(collertor)
            elif self.putindex(collertor, p0[0], p0[1], self.collec_tree):
                self.ranom_next_move(collertor)
            else:
                mx, my = self.random_position(collertor, self.collec_tree)
                p1 = Point(mx, my)
                q = preference_move_to(p0, p1)
                # action = np.argmax(q)
                # collertor.next_action = MOVE[action]

                self.target_position.append(p1)
                self.rever_work(collertor, q)
                # self.collec_tree.append(collertor.id)
                self.log(
                    f'捕碳员={ collertor.id }当前位置={ p0 }目标位置={ p1 } next_action = {collertor.next_action}')
            pass
        pass

    def collector_attach_strategy(self, collector):
        """攻击飞船"""
        pass

    def collec_GoBack(self, collector):
        p0 = collector.position
        p1 = self.board.current_player.recrtCenters[0].position
        q = preference_move_to(p0, p1)
        # action = np.argmax(q)
        # collertor.next_action = MOVE[action]

        self.target_position.append(p1)
        self.rever_work(collector, q)
        # self.collec_tree.append(collertor.id)
        self.log(
            f'捕碳员={ collector.id }当前位置={ p0 }目标位置={ p1 } next_action = {collector.next_action}')
        pass

    def __call__(self, board):
        self.board = board
        assert self.board.current_player.id == self.player_id

        self.current_recrtCenters = self.board.current_player.recrtCenters
        self.len_planters = len(self.board.current_player.planters)
        self.len_collectors = len(self.board.current_player.collectors)
        self.target_position = []  # 目标位置
        self.danger_position = []  # 下一步位置
        self.free_carbon = board.players[self.player_id].cash     # 拥有黄金数量

        # 更新资源
        self.update_score()

        # 处理转化中心
        for recrtCenter in self.current_recrtCenters:
            self.recrtCenter_strategy(recrtCenter)

        # if self.board.step > 25:
            # 处理种树人
        self.planter_strategy()

        # 处理捕CO2员
        for coll in self.board.current_player.collectors:
            if coll.carbon > 0 and self.board.step > 283:
                self.Go_back = True
                self.collec_GoBack(coll)
                continue
            if self.free_carbon < 200:
                self.log(
                    f'飞船={ coll.id } coll-CO2-1-->当前位置={ coll.position }')
                self.collector_carbon_strategy(coll)
                continue
            if coll.id in self.collec_tree:
                self.log(
                    f'飞船={ coll.id } 收集树-->当前位置={ coll.position }')
                self.collector_tree_strategy(coll)
            elif coll.id in self.collec_collec:
                self.log(
                    f'飞船={ coll.id } 攻击目标-->当前位置={ coll.position }')
                self.collector_attach_strategy(coll)
            else:
                self.log(
                    f'飞船={ coll.id } coll-CO2-2-->当前位置={ coll.position }')
                self.collector_carbon_strategy(coll)
        return self.board.current_player.next_actions


class MyAgent(object):
    def __init__(self, player_id, *args, verbose, **kwargs):
        self.player_id = player_id
        self.verbose = verbose
        self.scores = np.zeros((N_SCORE_TYPES, ROWS, COLS), dtype=np.float32)
        self.collec_tree = []
        self.collec_collec = []
        self.opponent_player = {}
        self.board = None
        self.log_step = -1
        self.logs = {}

    def log(self, s, step=None, id_=None, indent=0, loglevel='DEBUG'):
        print(s, "#")
        if not self.verbose:
            return
        level = getattr(logging, loglevel.upper())
        if level < logging.DEBUG:
            # return
            pass
        prefix = ''
        if 0 < indent:
            prefix += ' ' * indent
        if step is None:
            step = self.board.step
        prefix += f'step{step} '
        if self.log_step != step:
            self.logs.clear()
            self.log_step = step
        if id_ is not None:
            prefix += f'id{id_} '
            if id_ not in self.logs:
                self.logs[id_] = []
            if (self.verbose & 4) == 4:
                self.logs[id_].append(f'{prefix}{s}')
        # and logging.DEBUG < level
        if ((self.verbose & 4) == 4) or ((self.verbose & 1) == 1):
            easy_log(f'{prefix}{s}', loglevel=loglevel)

    def cup_cell_carbon(self, x, y, position):
        # if self.board.cells[x, y].worker_id is not None and self.board.cells[x, y].carbon > 40:
        #     return self.board.cells[x, y].carbon * 0.75 * 0.05
        t_count = 1
        for i in range(3):
            for j in range(3):
                pX = (x + XX[i] + 15) % 15
                pY = (y + YY[j] + 15) % 15
                if pX == position[0] and pY == position[1]:
                    continue
                if self.board.cells[pX, pY].tree_id is not None:
                    t_count += 1
        if t_count == 0:
            return self.board.cells[x, y].carbon * 0.05
        else:
            return self.board.cells[x, y].carbon * 0.05 / t_count

    def update_score_D89(self, x, y):
        sum8 = 0
        sum9 = 0
        for i in range(3):
            for j in range(3):
                pX = (x + XX[i] + 15) % 15
                pY = (y + YY[j] + 15) % 15
                if(i == 1 and j == 1):
                    sum9 += self.cup_cell_carbon(pX, pY, [x, y])
                    continue
                sum8 += self.cup_cell_carbon(pX, pY, [x, y])
                sum9 += self.cup_cell_carbon(pX, pY, [x, y])
        return sum8, sum9

    def update_score(self):
        self.scores_initialized = np.zeros(N_SCORE_TYPES, dtype=np.bool)
        self.scores[I_SCORE_HALITE_D8:, ...] = 0.0
        self.scores_D8 = []
        self.scores_D9 = []
        for x in range(COLS):
            for y in range(ROWS):
                flag = False
                for recrtCenter in self.board.recrtCenters.values():
                    if x == recrtCenter.position[0] and y == recrtCenter.position[1]:
                        flag = True
                if flag:
                    continue
                i, j = position_to_ij((x, y))
                self.scores[I_SCORE_HALITE, i,
                            j] = self.board.cells[x, y].carbon
                d8, d9 = self.update_score_D89(x, y)
                self.scores[I_SCORE_HALITE_D8, i, j] = d8
                self.scores[I_SCORE_HALITE_D9, i, j] = d9
                self.scores_D8.append([self.scores[I_SCORE_HALITE_D8, i,
                                                   j], i, j])
        self.scores_initialized[I_SCORE_HALITE] = True
        self.scores_D8 = sorted(self.scores_D8,
                                key=itemgetter(0), reverse=True)
        self.world_halite = np.sum(self.scores[I_SCORE_HALITE])
        self.halite_per_ship = self.world_halite / \
            max(1, len(self.board.workers))
        for d in self.collec_tree:
            if(d not in self.board.workers.keys()):
                self.collec_tree.remove(d)
        for d in self.collec_collec:
            if(d not in self.board.workers.keys()):
                self.collec_collec.remove(d)

        for recrtCenter in self.board.recrtCenters.values():
            if recrtCenter not in self.board.current_player.recrtCenters:
                self.opponent_player['recrtCenter'] = recrtCenter

        for play in self.board.players.values():
            if play.id != self.board.current_player.id:
                self.opponent_player['player'] = play

        # 初始化可以攻击的捕碳员列表
        self.collectorList = []
        for collectordd in self.board.collectors.values():
            if collectordd not in self.board.current_player.collectors and collectordd.carbon > 100:
                self.collectorList.append(
                    [collectordd.id, collectordd.carbon, collectordd.position])
        self.collectorList = sorted(
            self.collectorList, key=itemgetter(1), reverse=True)
        self.log(
            f'可攻击列表 collectorList->  = {self.collectorList}')

    def guss_tree_corban_get(self, carban_want=50):
        """判断是否招募种树人，是否种树"""
        age_tree = min(300 - self.board.step, MAX_TREE_AGE)
        self.scores_D8 = sorted(self.scores_D8,
                                key=itemgetter(0), reverse=True)
        for d in self.scores_D8:
            x, y = ij_to_position(d[1], d[2])
            if self.board.cells[Point(x, y)].tree_id is None and d[0] * age_tree > carban_want:
                return True
        return False

    def guss_tree_reverse(self, tree, carban_want=40):
        """判断树否可以转换"""
        i, j = position_to_ij(tree.position)
        getc = self.scores[I_SCORE_HALITE_D8, i, j]
        if(getc * (50 - tree.age) / 2 > carban_want):
            return True
        else:
            return False
        pass

    def now_position_tree(self, position):
        if self.board.cells[position].tree_id is not None and self.board.cells[position].tree_id not in self.board.current_player.tree_ids:
            tree = self.board.trees[self.board.cells[position].tree_id]
            return self.guss_tree_reverse(tree, 40)
        return False

    def guss_coll_corban_get(self):
        """判断获取预期"""
        pass

    def recrtCenter_strategy(self, recrtCenter):
        """
        有30万金币且转化中心没有自己的工作人员，方可继续。
        """
        if self.free_carbon >= 30:
            if self.board.cells[recrtCenter.position[0], recrtCenter.position[1]].worker_id not in self.board.current_player.worker_ids:
                if((self.len_collectors + self.len_planters) == 0):
                    if(self.guss_tree_corban_get()):
                        recrtCenter.next_action = RecrtCenterAction.RECPLANTER
                    else:
                        pass
                    pass
                else:
                    if self.len_planters < MAX_Plater:
                        if(self.free_carbon >= 50 and self.guss_tree_corban_get()):
                            recrtCenter.next_action = RecrtCenterAction.RECPLANTER
                            return
                        else:
                            pass
                    if self.len_collectors < MAX_Collector:
                        if(self.free_carbon >= 30):
                            recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
                        pass

    def isSound(self, type, x, y):
        for i in range(5):
            for j in range(5):
                sx = (x + SX[i] + 15) % 15
                sy = (y + SY[j] + 15) % 15
                if type == "tree" and self.board.cells[sx, sy].tree_id in self.board.current_player.tree_ids:
                    return False
                pass
        return True

    def distenceD_D(self, md, x, y):
        """计算下个目标点"""
        d = 0
        distence = 99999
        self.log(f'self.target_position = {self.target_position}')
        for index in range(len(md)):
            if md[index][1] not in self.target_position and md[index][1] not in self.danger_position:
                xyd = distance_impl(md[index][1][0], x, md[index][1][1], y)
                if(xyd < distence):
                    d = index
                    distence = xyd
        return md[d][1][0], md[d][1][1]

    def distenceP0_P1(self, p0, p1):
        return distance_impl(p0[0], p1[0], p0[1], p1[1])

    def computer_1234(self, p0, p1):
        """p0表示基地，p1表示收集二氧化碳最多的捕碳源的位置"""
        dx = p0[0] - p1[0]
        dy = p0[1] - p1[1]
        if dx == 0:
            if dy > 0:
                return 3.5
            elif dy < 0:
                return 1.5
            else:
                return 0
        elif dy == 0:
            if dx > 0:
                return 2.5
            elif dx < 0:
                return 4.5
            else:
                return 0
        dD = dy/dx
        if dD > 0:
            if dx > 0 and dy > 0:
                return 3
            elif dx < 0 and dy < 0:
                return 1
            pass
        elif dD <= 0:
            if dx > 0 and dy < 0:
                return 2
            elif dx < 0 and dy > 0:
                return 4
            pass

    def recrtCenter_1234(self, p0, x):
        if x == 1 or x == 1.5:
            return p0[0]+1, p0[1]+1
        elif x == 2 or x == 2.5:
            return p0[0]-1, p0[1]+1
        elif x == 3 or x == 3.5:
            return p0[0]-1, p0[1]-1
        elif x == 4 or x == 4.5:
            return p0[0]+1, p0[1]-1
        pass

    def recrtCenter_12345(self, p0, x):
        """p0: 基地坐标
        """
        if x == 1.5:
            return p0[0], p0[1]+1
        elif x == 2.5:
            return p0[0]-1, p0[1]
        elif x == 3.5:
            return p0[0], p0[1]-1
        elif x == 4.5:
            return p0[0]+1, p0[1]
        else:
            return self.recrtCenter_1234(p0, x)

    def planter_strategy(self):
        for worker in self.board.current_player.planters:
            """植树策略"""
            p0 = worker.position
            if self.now_position_tree(p0):
                worker.next_action = MOVE[0]
                continue
            # guss = self.guss_tree_corban_get(20)
            # if guss:
            self.log(f'scores_D8={self.scores_D8}')
            md4 = []
            od = []
            max_carbon = self.scores_D8[len(
                self.board.current_player.planters)][0]
            for d in self.scores_D8:
                dis = self.distenceP0_P1(p0, [d[1], d[2]])
                disR_8 = self.distenceP0_P1(
                    self.board.current_player.recrtCenters[0].position, [d[1], d[2]])
                if (len(self.board.current_player.trees) == 0 and disR_8 > 7):
                    continue
                elif len(self.board.current_player.trees) > 0 and (d[0] * (1.05) ** dis) < 8:
                    continue
                x, y = ij_to_position(d[1], d[2])
                if self.board.cells[Point(x, y)].tree_id is None and self.isSound('tree', x, y):
                    # 当前单元格没有树，且周围也没有自己的树
                    if d[0] > max_carbon - 1 - 0.01 * self.board.step:
                        self.log(f'next_tree_Point={x,y}')
                        md4.append([0, [x, y]])
                elif self.board.cells[Point(x, y)].tree_id is not None and self.board.cells[Point(x, y)].tree_id not in self.board.current_player.tree_ids:
                    # 当前单元格有树且不是自己的树
                    pass
            if len(md4) > 0:
                mx, my = self.distenceD_D(md4, p0[0], p0[1])
                p1 = Point(mx, my)
                self.target_position.append([mx, my])
                q = preference_move_to(p0, p1)
                action = np.argmax(q)
                worker.next_action = MOVE[action]
                self.log(
                    f'{worker.id} 当前位置={ p0 }目标位置={ p1 } next_action = {MOVE[action]}')
            else:
                pass

    def neighbor_cells(self, cell):
        cells = [cell]
        cells.append(cell.up)
        cells.append(cell.right)
        cells.append(cell.down)
        cells.append(cell.left)
        return cells

    def prevent_attach(self, worked, next_move):
        """防止撞击"""
        nextPosition = calculate_next_position(worked.position, next_move)
        self.log(
            f'determined_ships = {self.determined_ships} nextPosition = {nextPosition}')
        if nextPosition not in self.determined_ships:
            cells = self.neighbor_cells(self.board.cells[nextPosition])
            for cell in cells:
                if(cell.position == worked.position):
                    continue
                self.log(f'cell.worker_id = {cell.worker_id}')
                if(cell.worker_id is not None and cell.worker_id not in self.board.current_player.worker_ids):
                    if(self.board.workers[cell.worker_id].carbon > 100):
                        if(cells[0].tree_id is not None):
                            if(cells[0].tree_id in self.board.current_player.tree_ids):
                                self.determined_ships.append(nextPosition)
                                return True
                            else:
                                return False
                        else:
                            self.determined_ships.append(nextPosition)
                            return True
                    else:
                        return False
            self.determined_ships.append(nextPosition)
            return True
        else:
            return False

    def rever_work(self, worker, q):
        """处理worker动作"""
        for action in np.argsort(-q):
            if self.prevent_attach(worker, action):
                worker.next_action = MOVE[action]
                return
        pass

    def statistics_trees(self, position, away=15, carbon=40):
        collect_trees = []
        for tree in self.board.trees.values():
            if tree.player_id != self.board.current_player.id and tree.position not in self.target_position:
                worker_2_Tree = self.distenceP0_P1(position, tree.position)
                age = min(300-self.board.step, 50 - tree.age - worker_2_Tree-1)
                i, j = position_to_ij(tree.position)
                # self.log(
                #     f'树点--->年龄 {tree.age} 位置 {tree.position, age, self.scores[I_SCORE_HALITE_D8, i, j]}')
                if age * self.scores[I_SCORE_HALITE_D8, i, j] > carbon and worker_2_Tree <= away:
                    collect_trees.append(
                        [age * self.scores[I_SCORE_HALITE_D8, i, j], tree.position])
        return collect_trees

    def collector_tree_strategy(self, collertor):
        """收树策略"""
        # if self.board.cells[collertor.position].carbon >= 40:
        #     collertor.next_action = MOVE[0]
        #     return
        p0 = collertor.position
        collect_trees = sorted(self.statistics_trees(
            p0), key=itemgetter(0), reverse=True)
        self.log(f'转换树捕碳员={ collect_trees }')
        if len(collect_trees) > 0:
            le = 4 if len(collect_trees) > 4 else len(collect_trees)
            mx, my = self.distenceD_D(collect_trees[0:le], p0[0], p0[1])
            p1 = Point(mx, my)
            q = preference_move_to(p0, p1)
            # action = np.argmax(q)
            # collertor.next_action = MOVE[action]

            self.target_position.append(p1)
            self.rever_work(collertor, q)
            self.collec_tree.append(collertor.id)
            self.log(
                f'种树人={ collertor.id }当前位置={ p0 }目标位置={ p1 } next_action = {collertor.next_action}')
        else:
            self.collector_attach_strategy(collertor)
            pass
        pass

    def collector_attach_strategy(self, collector):
        """攻击飞船策略"""
        config = ''
        if len(self.collectorList) == 0:
            """如果没有需要攻击的捕碳员,就去枪树"""
            config += '去抢树'
            p = self.opponent_player['recrtCenter'].position
            # away = max(p[0] % 7, p[1] % 7)
            collect_trees = self.statistics_trees(
                self.opponent_player['recrtCenter'].position, away=8)
            self.log(
                f'攻击捕碳员捕获列表={ collect_trees }')
            collect_trees = sorted(
                collect_trees, key=itemgetter(0), reverse=True)
            if len(collect_trees) > 0:
                le = 4 if len(collect_trees) > 4 else len(collect_trees)
                mx, my = self.distenceD_D(
                    collect_trees[0:le], collector.position[0], collector.position[1])
                p1 = Point(mx, my)
                q = preference_move_to(collector.position, p1)
                # action = np.argmax(q)
                # collector.next_action = MOVE[action]
                self.target_position.append(p1)
                self.rever_work(collector, q)
                self.collec_collec.append(collector.id)
                self.log(
                    f'捕碳员={ collector.id }当前位置={ collector.position }目标位置={ p1 } next_action = {collector.next_action}')
            else:
                config += '无树可枪'
            pass
        else:
            config += '去防守'
            p1 = self.collectorList[0][2]
            xy = self.computer_1234(
                self.opponent_player['recrtCenter'].position, p1)
            disten = self.distenceP0_P1(
                self.opponent_player['recrtCenter'].position, p1)
            distenP0 = self.distenceP0_P1(
                self.opponent_player['recrtCenter'].position, collector.position)
            self.log(
                f'collector攻击飞船->  ={collector.position,self.collectorList[0][1],self.collectorList[0][2]}')
            if disten == 2 and distenP0 == 2:
                p1x, p2x = self.recrtCenter_12345(
                    self.opponent_player['recrtCenter'].position, xy)
                q = preference_move_to(collector.position, Point(p1x, p2x))
                action = np.argmax(q)
                collector.next_action = MOVE[action]
                self.log(
                    f'{collector.id} 当前位置={ collector.position }目标位置={ Point(p1x, p2x) } next_action = {MOVE[action]}')
                pass
            elif disten > 2:
                p1x, p2x = self.recrtCenter_1234(
                    self.opponent_player['recrtCenter'].position, xy)
                q = preference_move_to(collector.position, Point(p1x, p2x))
                action = np.argmax(q)
                collector.next_action = MOVE[action]
                # self.rever_work(collector, q)
                self.log(
                    f'{collector.id} 当前位置={ collector.position }目标位置={ Point(p1x, p2x) } next_action = {MOVE[action]}')
                pass
            self.collec_collec.append(collector.id)
        pass
        self.log(f'策略流程：{config}')

    def collector_carbon_strategy(self, collector):
        """收集二氧化碳"""

        pass

    def __call__(self, board):
        self.board = board
        assert self.board.current_player.id == self.player_id
        self.recrtCenters = self.board.current_player.recrtCenters

        self.len_planters = len(self.board.current_player.planters)
        self.len_collectors = len(self.board.current_player.collectors)
        self.determined_ships = []
        self.target_position = []  # 目标位置
        self.danger_position = []  # 危险位置
        self.free_carbon = board.players[self.player_id].cash     # 拥有黄金数量
        self.configuration = board.configuration
        self.sorted_collectors = sorted(
            self.board.players[self.player_id].collectors,
            key=attrgetter('carbon'),
            reverse=True)   # 对所有飞船按持有黄金进行升序排列
        self.non_empty_collectors = []
        self.empty_collectors = []
        for ship in self.sorted_collectors:
            if ship.carbon == 0:
                self.empty_collectors.append(ship)
            else:
                self.non_empty_collectors.append(ship)

        # 更新资源
        self.update_score()
        self.log(
            f'world_halite={self.world_halite}, halite_per_ship={self.halite_per_ship}, free_halite={self.free_carbon}')

        # 处理转化中心
        for recrtCenter in self.recrtCenters:
            self.recrtCenter_strategy(recrtCenter)

        # 处理种树人
        self.planter_strategy()

        # 处理捕CO2员
        for coll in self.sorted_collectors:

            if self.free_carbon < 20 and len(self.board.current_player.trees) == 0:
                self.log(
                    f'飞船={ coll.id } 收集二氧化碳1-->当前位置={ coll.position }')
                self.collector_carbon_strategy(coll)
                continue
            if (len(self.collec_tree) == 0 and len(self.opponent_player['player'].trees) > 0 and coll.id not in self.collec_collec) or coll.id in self.collec_tree:
                self.log(
                    f'飞船={ coll.id } 收集树-->当前位置={ coll.position }')
                self.collector_tree_strategy(coll)
            elif (len(self.collec_collec) < 2) or coll.id in self.collec_collec:
                self.log(
                    f'飞船={ coll.id } 攻击目标-->当前位置={ coll.position }')
                self.collector_attach_strategy(coll)
            else:
                self.log(
                    f'飞船={ coll.id } 收集二氧化碳2-->当前位置={ coll.position }')
                self.collector_carbon_strategy(coll)
        return self.board.current_player.next_actions


my_agent = [None] * 2
Tankagent = [None] * 2


@ board_agent
def my_agent1(board):
    pid = board.current_player.id
    if (my_agent[pid] is None) or (board.step == 0):
        my_agent[pid] = MyAgent(pid, verbose=4)
    return my_agent[pid](board)


@ board_agent
def Tankagent1(board):
    pid = board.current_player.id
    if (Tankagent[pid] is None) or (board.step == 0):
        Tankagent[pid] = TankTank(pid, verbose=4)
    return Tankagent[pid](board)

from zerosum_env import make
from zerosum_env.envs.carbon.carbon import random_agent
from zerosum_env.envs.carbon.helpers import *


def first(iterable):
    return next(iter(iterable))


def create_board(size=3, starting_carbon=0, agent_count=2, random_seed=0, regenRate=0.03, startPosOffset=2):
    env = make("carbon", configuration={
        "size": size,
        "startingCarbon": starting_carbon,
        "randomSeed": random_seed,
        "regenRate": regenRate,
        "startPosOffset": startPosOffset,
    })
    return Board(env.reset(agent_count)[0].observation, env.configuration)


def move_toward(worker, target: Point):
    (x1, y1) = worker.position
    (x2, y2) = target
    if x2 > x1:
        return WorkerAction.RIGHT
    elif x2 < x1:
        return WorkerAction.LEFT
    elif y2 > y1:
        return WorkerAction.UP
    elif y2 < y1:
        return WorkerAction.DOWN

from zerosum_env import make
from .carbon import random_agent
from .helpers import *


def test_carbon_no_repeated_steps():
    step_count = 10
    actual_steps = []

    def step_appender_agent(obs, config):
        actual_steps.append(obs.step)
        return {}

    env = make("carbon", configuration={"episodeSteps": step_count}, debug=True)
    env.run([step_appender_agent])
    assert actual_steps == list(range(step_count - 1))


def test_carbon_completes():
    env = make("carbon", configuration={"episodeSteps": 100})
    env.run([random_agent, random_agent])
    json = env.toJSON()
    assert json["name"] == "carbon"
    assert json["statuses"] == ["DONE", "DONE"]


def test_carbon_exception_action_has_error_status():
    env = make("carbon")

    def error_agent(obs, config):
        raise Exception("An exception occurred!")
    env.run([error_agent, random_agent])
    json = env.toJSON()
    assert json["name"] == "carbon"
    assert json["statuses"] == ["ERROR", "DONE"]


def test_carbon_helpers():
    env = make("carbon", configuration={"size": 3})

    @board_agent
    def helper_agent(board):
        for worker in board.current_player.workers:
            worker.next_action = WorkerAction.UP
        for recrtCenter in board.current_player.recrtCenters:
            recrtCenter.next_action = RecrtCenterAction.SPAWN

    env.run([helper_agent, helper_agent])

    json = env.toJSON()
    assert json["name"] == "carbon"
    assert json["statuses"] == ["DONE", "DONE"]


def create_board(size=3, starting_carbon=0, agent_count=2, random_seed=0):
    env = make("carbon", configuration={
        "size": size,
        "startingCarbon": starting_carbon,
        "randomSeed": random_seed
    })
    return Board(env.reset(agent_count)[0].observation, env.configuration)


def test_move_moves_worker():
    size = 3
    board = create_board(size, agent_count=1)
    for worker in board.current_player.workers:
        worker.next_action = WorkerAction.DOWN
    next_board = board.next()
    for worker in board.workers.values():
        next_position = worker.position.translate(Point(0, -1), size)
        next_worker = next_board.workers[worker.id]
        assert next_worker.position == next_position


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


def test_equal_worker_collision_destroys_both_workers():
    size = 3
    board = create_board(size, agent_count=2)
    for worker in board.workers.values():
        worker.next_action = move_toward(worker, Point(1, 1))
    next_board = board.next()
    assert len(next_board.workers) == 0


def test_unequal_worker_collision_destroys_weaker_worker():
    board = create_board(agent_count=2)
    for opponent in board.opponents:
        for worker in opponent.workers:
            # Make the opponents' workers have more carbon so they'll be destroyed
            worker._carbon = 1000
    for worker in board.workers.values():
        worker.next_action = move_toward(worker, Point(1, 1))
    next_board = board.next()
    assert len(next_board.current_player.workers) == 1
    assert len(next_board.workers) == 1


def first(iterable):
    return next(iter(iterable))


def test_worker_recrtCenter_collision_destroys_both():
    board = create_board(agent_count=2)
    player_worker = first(board.current_player.workers)
    opponent_worker = first(first(board.opponents).workers)
    opponent_worker.next_action = WorkerAction.CONVERT
    board = board.next()
    assert len(board.workers) == 1
    assert len(board.recrtCenters) == 1
    while player_worker.id in board.workers:
        board.workers[player_worker.id].next_action = move_toward(player_worker, opponent_worker.position)
        board = board.next()
    assert len(board.workers) == 0
    assert len(board.recrtCenters) == 0


def test_cells_regen_carbon():
    board = create_board(starting_carbon=1000, agent_count=1)
    cell = first(board.cells.values())
    next_board = board.next()
    next_cell = next_board[cell.position]
    expected_regen = round(cell.carbon * board.configuration.regen_rate, 3)
    # We compare to a floating point value here to handle float rounding errors
    assert next_cell.carbon - cell.carbon - expected_regen < .000001


def test_no_move_on_carbon_gathers_carbon():
    board = create_board(starting_carbon=1000, agent_count=1)
    worker = first(board.workers.values())
    expected_delta = int(worker.cell.carbon * board.configuration.collect_rate)
    next_board = board.next()
    next_worker = next_board.workers[worker.id]
    worker_delta = next_worker.carbon - worker.carbon
    cell_delta = round(worker.cell.carbon - next_worker.cell.carbon, 3)
    assert worker_delta == expected_delta
    assert cell_delta == expected_delta


def test_move_on_carbon_gathers_no_carbon():
    board = create_board(starting_carbon=1000, agent_count=1)
    worker = first(board.workers.values())
    worker.next_action = WorkerAction.UP
    next_board = board.next()
    next_worker = next_board.workers[worker.id]
    worker_delta = next_worker.carbon - worker.carbon
    assert worker_delta == 0


def test_failed_convert_gathers_carbon():
    board = create_board(starting_carbon=1000, agent_count=1)
    board.current_player._carbon = board.configuration.convert_cost - 1
    worker = first(board.workers.values())
    worker.next_action = WorkerAction.CONVERT
    expected_delta = int(worker.cell.carbon * board.configuration.collect_rate)
    next_board = board.next()
    next_worker = next_board.workers[worker.id]
    worker_delta = next_worker.carbon - worker.carbon
    cell_delta = round(worker.cell.carbon - next_worker.cell.carbon, 3)
    assert worker_delta == expected_delta
    assert cell_delta == expected_delta


def test_recrtCenter_ids_not_reused():
    board = create_board(starting_carbon=1000, agent_count=1)
    worker = first(board.workers.values())
    worker.next_action = WorkerAction.CONVERT
    board = board.next()
    recrtCenter = board.cells[worker.position].recrtCenter
    assert worker.id != recrtCenter.id


def test_seed_parameter():
    seed = 9

    def aggregate_carbon_for_board(seed):
        board = create_board(starting_carbon=1000, agent_count=1, random_seed=seed)
        return sum(map(lambda c: c.carbon, board.cells.values()))

    assert aggregate_carbon_for_board(seed) == aggregate_carbon_for_board(seed)


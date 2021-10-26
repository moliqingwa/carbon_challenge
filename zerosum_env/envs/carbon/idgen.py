
import threading

_rlock = threading.RLock()

_id_dict = {}


def id_gen(player_id, prefix=""):
    """
    Thread-safe ID generator for each player.
    """
    key = f"player-{player_id}-{prefix}"
    global _rlock, _id_dict
    with _rlock:
        _id = _id_dict.get(key, 0)
        _id_dict[key] = _id + 1
    return f"{key}{_id}"


def new_tree_id(player_id):
    """
    Worker ID generator for player.
    """
    return id_gen(player_id, "tree-")


def new_worker_id(player_id):
    """
    Worker ID generator for player.
    """
    return id_gen(player_id, "worker-")


def new_recrtCenter_id(player_id):
    """
    RecrtCenter ID generator for recrtCenter.
    """
    return id_gen(player_id, "recrtCenter-")


def reset():
    global _rlock, _id_dict
    with _rlock:
        _id_dict.clear()

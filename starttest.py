
from zerosum_env.envs.carbon.rain_carbon import *
import numpy as np
q = preference_move_to([7, 14], [6, 0])
print(q)
print(np.argmax(q))
print(np.argmax(q))
print(np.argmax(q))
print(np.argsort(-q))
for action in np.argsort(-q):
    print(MOVE[action])
    # print(calculate_next_position([7, 14], action))
    print(isinstance(int(action), int))

print(min(2, 34, 5))

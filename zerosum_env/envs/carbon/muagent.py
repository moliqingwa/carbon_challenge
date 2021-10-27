from zerosum_env import make
from zerosum_env.envs.carbon.helpers import *
import traceback


def log(info:str):
    a = open("log", "a", encoding="utf-8")
    a.write(info)
    a.close()

def distance(pos1: Point, pos2: Point, size:int) -> int:
    xs = abs(pos1.x - pos2.x)
    ys = abs(pos1.y - pos2.y)
    return min(xs, size - xs) + min(ys, size - ys)

def pointAdd(pos1: Point, pos2: Point, size:int)->Point:
    return pos1.translate(pos2, size)

def printRealMap(size:int, board:Board) -> None:
    size = size
    result = ''
    for y in range(size):
        for x in range(size):
            cell = board[(x, size - y - 1)]
            result += '| '
            result += str(round(cell.carbon,2))

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
    log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
    log(result)

def printCellValue(size:int, cellValue: Dict[int, float]) -> str:
    result = ''
    for y in range(size):
        for x in range(size):
            point = Point(x, size - y - 1)
            result += '| '
            result += str(round(cellValue[point.to_index(size)],2))
        result += ' |\n'

    log("******************************\n")
    log(result)

def intersectionAction(list1:List[WorkerAction], list2:List[WorkerAction])->List[WorkerAction]:
    re:List[WorkerAction] = []
    for action1 in list1:
        for action2 in list2:
            if action1 is None:
                if action2 is None:
                    re.append(action1)
                    break
                else:
                    continue

            if action2 is None:
                continue

            if action1.to_point() == action2.to_point():
                re.append(action1)
                break
    return re

class Agent():
    def __init__(self, board:Board, configuration:Configuration, lastPosition:Dict[str, Point], round:int) -> None:
        self._board = board
        self._playerid = board.current_player_id
        self.configuration = configuration
        self._size = configuration.size
        self._cellValue: Dict[int, float] = {}
        self.exceptPosition:List[Point]=[]
        self.averageC = 0
        self._opponentTreeAround:List[Point] = []
        self._myTreeAround:List[Point] = []
        self.round = round

        self.lastPostion:Dict[str, Point] = {}
        for workerid in self._board.current_player.worker_ids:
            if lastPosition == None:
                self.lastPostion[workerid] = None
            elif lastPosition.get(workerid) is None:
                self.lastPostion[workerid] = None
            else:
                self.lastPostion[workerid] = lastPosition.get(workerid)

        for recrtCenter in board.recrtCenters.values():
            if self._playerid == recrtCenter.player_id:
                self._center = recrtCenter.position
            else:
                self._opponentCenter = recrtCenter.position


    def build(self):
        for key in self._board.trees:
            tree = self._board.trees[key]
            if tree.player_id != self._playerid:
                posList = self.calArroundPoint(tree.position)
                for pos in posList:
                    if pos not in self._opponentTreeAround:
                        self._opponentTreeAround.append(pos)
            else:
                posList = self.calArroundPoint(tree.position)
                for pos in posList:
                    if pos not in self._myTreeAround:
                        self._myTreeAround.append(pos)


        self.calCellValue()
        log("average:{0} round:{1} cash:{2}\n".format(self.averageC, self.round, self._board.current_player.cash))

        log("planter:\n")
        for planter in self._board.planters.values():
            log("{0} {1} {2} {3} \n".format(planter.id, planter.occupation, planter.carbon, planter.position))
        log("collector:\n")
        for collector in self._board.collectors.values():
            log("{0} {1} {2} {3} \n".format(collector.id, collector.occupation, collector.carbon, collector.position))
        self.createExceptPosition()
        self.calAction()

    def pointAdd(self, pos1: Point, pos2: Point) -> Point:
        return pos1.translate(pos2, self._size)

    def createExceptPosition(self):
        self.exceptPosition.append(self._opponentCenter)
        # for tree in self._board.trees.values():
        #     if tree.player_id != self._playerid:
        #         self.exceptPosition.append(tree.position)

    def removeActionForPosition(self, actions, worker, point)->List[WorkerAction]:
        if point == None:
            return actions
        for action in actions:
            if action is None:
                newPosition = worker.position
            else:
                newPosition = self.pointAdd(worker.position, action.to_point())
            if newPosition == point:
                actions.remove(action)
                return actions
        return actions

    def removeActionForException(self, actions, worker)->List[WorkerAction]:
        for exPos in self.exceptPosition:
            actions = self.removeActionForPosition(actions, worker, exPos)
        return actions
    
    def getAction(self, worker)->WorkerAction:
        actions = [WorkerAction.UP, WorkerAction.DOWN, WorkerAction.LEFT, WorkerAction.RIGHT, None]
        return self.removeActionForException(actions, worker)[0]
    
    def setWorkerAction(self, worker:Worker, action:WorkerAction)->None:
        worker.next_action = action
        if action is None:
            self.exceptPosition.append(worker.position)
            return
        self.exceptPosition.append(self.pointAdd(worker.position, action.to_point()))

    def inOwner(self, position:Point)->bool:
        if position == self._board.current_player.recrtCenters[0].position:
            return True

        for tree in self._board.current_player.trees:
            if position == tree.position:
                return True

    def findArroudOwner(self, worker:Worker)->WorkerAction:
        actions = [WorkerAction.UP, WorkerAction.DOWN, WorkerAction.LEFT, WorkerAction.RIGHT]
        for action in actions:
            if self.inOwner(self.pointAdd(worker.position, action.to_point())):
                return action
        return None

    def optimalForCollectorToCenter(self, currPostion:Point, actions:List[WorkerAction])->WorkerAction:
        if len(actions) == 1:
            return actions[0]

        maxValue = 0
        maxAction = None

        for action in actions:
            if action is not None:
                newPos = self.pointAdd(currPostion, action.to_point())
            else:
                newPos = currPostion
            if self._cellValue[newPos.to_index(self._size)] > maxValue:
                maxValue = self._cellValue[newPos.to_index(self._size)]
                maxAction = action
        return maxAction

    def optimalForCollectorFreedom(self, worker:Worker, actions: List[WorkerAction]) -> WorkerAction:
        if len(actions) == 1:
            return actions[0]

        maxValue = -1
        maxAction = actions[0]

        for action in actions:
            if action is not None:
                newPos = self.pointAdd(worker.position, action.to_point())
            else:
                newPos = worker.position

            centerWeight = 0
            if self._board.current_player.cash <= 100 and worker.carbon >= 30:
                centerWeight = worker.carbon/100
            elif self._board.current_player.cash <= 200 and worker.carbon >= 60:
                centerWeight = worker.carbon/200
            elif self._board.current_player.cash <= 500 and worker.carbon >= 200:
                centerWeight = worker.carbon/500
            elif self._board.current_player.cash > 500 and worker.carbon >= min(self._board.current_player.cash*0.4, 500):
                centerWeight = worker.carbon/min(self._board.current_player.cash,2000)

            if self.round > 250:
                centerWeight = max(centerWeight, 0.5)

            value = self.calCellCarbon(newPos, distance=3, centerWeight=centerWeight)
            if value > maxValue:
                maxValue = value
                maxAction = action
        return maxAction

    def optimalForCollector(self, worker:Worker, actions:List[WorkerAction])->WorkerAction:
        if len(actions) == 1:
            return actions[0]

        if len(actions) == 0:
            return None

        if None in actions:
            actions.remove(None)

        if worker.position == self._center:
            self.optimalForCollectorFreedom(worker, actions)

        if len(self._board.current_player.worker_ids) <= 4 and self._board.current_player.cash <= 30:
            curr = worker.position
            cash = self._board.current_player.cash + worker.carbon
            firstFlg = True
            step = 0
            while (cash < 30 and step < 10) or firstFlg == True:
                step += 1
                nactions = self.__distanceAction(curr, self._center, False)
                if len(nactions) == 0:
                    break
                if firstFlg == True:
                    nextActions = intersectionAction(actions, nactions)
                    if len(nextActions) == 0:
                        print(28)
                        break
                    action = self.optimalForCollectorToCenter(curr, nextActions)
                    nextAction = action
                    firstFlg = False
                else:
                    action = self.optimalForCollectorToCenter(curr, nactions)

                if action is None:
                    newPosition = curr
                else:
                    newPosition = self.pointAdd(curr, action.to_point())
                if newPosition == self._center:
                    break
                cash += round(self._board.cells[newPosition].carbon*0.5, 2)
            if cash >= 30 and firstFlg is False:
                print("29")
                return nextAction
        print("30")
        return self.optimalForCollectorFreedom(worker, actions)

    def calOccupyTree(self, worker, actions)->(bool, WorkerAction, Point):
        if self.round > 285:
            return False, None, None

        action = None
        disMin = 4
        cTree = None

        for tree in self._board.trees.values():
            if tree.player_id != self._playerid:
                dist = self.distance(worker.position, tree.position)
                if dist > 3:
                    continue

                roundValue = self.calTreeAroundCarbon(tree.position) * 0.05
                if roundValue * (50 - tree.age -1 - dist) <= 30:
                    continue

                if dist == 0:
                    if None in actions:
                        return True, None, None

                result = intersectionAction(self.__distanceAction(worker.position, tree.position,False), actions)
                if len(result) <= 0:
                    continue
                if dist < disMin:
                    disMin = dist
                    action = result[0]
                    cTree = tree

        if disMin < 4:
            return True, action, cTree.position
        return False, action, None

    def calPlantAction(self, worker, actions):
        notPlantList:list[Point] = []
        notPlantList.extend(self._myTreeAround)
        notPlantList.append(self._center)
        notPlantList.append(self._opponentCenter)

        opponentTreeDic:Dict[Point, Tree] = {}

        for tree in self._board.trees.values():
            if tree.player_id == self._playerid and tree.position not in notPlantList:
                notPlantList.append(tree.position)
            else:
                opponentTreeDic[tree.position] = tree

        minDist = 10000
        maxValue = 0
        action = None
        for cell in self._board.cells.values():

            if cell.position in notPlantList:
                continue

            value = self.calTreeAroundCarbon(worker.position)
            dist = self.distance(cell.position, worker.position) + 1

            if self._board.current_player.cash < 50:
                if value * 0.05 * 3 < 20:
                    continue
            elif self._board.current_player.cash < 100:
                if value * 0.05 * 5 < 20:
                    continue
            else:
                if value * 0.05 * 30 < 20:
                    continue

            opponentTree = opponentTreeDic.get(cell.position)
            if opponentTree != None:
                if ((value * 0.05 * (50 - opponentTree.age - dist)) < 30) or (self._board.current_player.cash < 100):
                    continue

            # plist = self.calArroundPoint(cell.position)
            # for p in plist:
            #     if p in self._myTreeAround:
            #         continue

            if dist > minDist and dist > 3:
                continue

            if dist > minDist and dist <= 3 and value <= maxValue:
                continue

            if worker.position == cell.position and None in actions:
                action = None
            else:
                newActions = intersectionAction(self.__distanceAction(worker.position, cell.position, False), actions)
                if len(newActions) == 0:
                    continue
                action = newActions[0]

            minDist = dist
            if minDist < 4:
                maxValue = value

        if minDist == 10000:
            print("err-1")
            return actions[0]

        return action


    def calAction(self):
        me = self._board.current_player
        print(me.worker_ids)
        for worker in me.workers:
            print(31)
            awayOpponents, ignoreOpponent = self.judgeOpponent(worker)
            if len(awayOpponents) > 0:
                if len(awayOpponents) >= 2:
                    if self.inOwner(worker.position) and worker.position not in self.exceptPosition:
                        self.setWorkerAction(worker, None)
                        continue

                    action = self.findArroudOwner(worker)
                    if action != None:
                        if self.pointAdd(action.to_point(), worker.position) not in self.exceptPosition:
                            self.setWorkerAction(worker, action)
                            continue
                    print(34)

                actions = self.__distanceAction(worker.position, awayOpponents[0], True)
                for i in range(len(awayOpponents) - 1):
                    aactions = self.__distanceAction(worker.position, awayOpponents[i+1], True)
                    actions = intersectionAction(actions, aactions)

                flag = True
                for pos in awayOpponents:
                    if self.distance(worker.position, pos) == 1:
                        flag = False

                if flag == True:
                    actions.append(None)
                print(1)
            else:
                actions = [WorkerAction.UP, WorkerAction.DOWN, WorkerAction.LEFT, WorkerAction.RIGHT, None]
                # if worker.occupation == Occupation.COLLECTOR and self.lastPostion[worker.id] != None and self._board.cells[self.lastPostion[worker.id]].carbon < self.averageC:
                #     actions = self.removeActionForPosition(actions, worker, self.lastPostion[worker.id])
                if self.lastPostion[worker.id] is not None:
                    if worker.occupation == Occupation.PLANTER or (worker.occupation == Occupation.COLLECTOR and self.lastPostion[worker.id] != worker.position):
                        actions = self.removeActionForPosition(actions, worker, self.lastPostion[worker.id])
                        print(27)
                print(2,actions)
            
            actions = self.removeActionForException(actions, worker)

            print(3)

            if ignoreOpponent is True:
                print(4)
                for tree in self._board.trees.values():
                    if tree.player_id != self._playerid:
                        actions = self.removeActionForPosition(actions, worker, tree.position)
                        neighbours = self.calArroundPoint(tree.position)
                        for neighbour in neighbours:
                            actions = self.removeActionForPosition(actions, worker, neighbour)
                print(5)

            print(6)
            if len(actions) == 0:
                self.setWorkerAction(worker, self.getAction(worker))
                print(7)
                continue

            if worker.occupation == Occupation.COLLECTOR:
                print(8, actions)

                re = False
                if ignoreOpponent is False and self._board.current_player.cash >= 100:
                    re, action, treePosition = self.calOccupyTree(worker, actions)
                    if re is True and action is None:
                        self.setWorkerAction(worker, None)
                        continue

                if worker.position not in self._myTreeAround or (worker.position in self._myTreeAround and worker.position in self._opponentTreeAround):
                    if self.lastPostion[worker.id] != None and None in actions:
                        if (worker.position != self.lastPostion[worker.id]) and self._board.cells[worker.position].carbon >= (self.averageC)/4:
                            if re is True:
                                if worker.position in self.calArroundPoint(treePosition):
                                    self.setWorkerAction(worker, action)
                                    continue

                            self.setWorkerAction(worker, None)
                            print(9)
                            continue

                        if worker.position == self.lastPostion[worker.id] and self._board.cells[worker.position].carbon >= self.averageC:
                            if re is True:
                                if worker.position in self.calArroundPoint(treePosition):
                                    self.setWorkerAction(worker, action)
                                    continue

                            self.setWorkerAction(worker, None)
                            print(10)
                            continue
                        print(11)

                if re is True:
                    self.setWorkerAction(worker, action)
                    continue

                print(26, actions)
                maxAction = self.optimalForCollector(worker, actions)
                self.setWorkerAction(worker, maxAction)
                print(12)
                continue

            if worker.occupation == Occupation.PLANTER:
                print(13, actions)
                print(131, worker.position)
                self.setWorkerAction(worker, self.calPlantAction(worker, actions))
                # treePos = self.calC
                # print(14, treePos)
                # if treePos == worker.position and self.inOwner(treePos) == False and None in actions:
                #     self.setWorkerAction(worker, None)
                #     print(15)
                #     continue
                #
                # newActions = self.__distanceAction(worker.position, treePos, False)
                # print(16)
                # newActions = intersectionAction(newActions, actions)
                #
                # if len(newActions) == 0:
                #     print(17)
                #     self.setWorkerAction(worker, actions[0])
                # else:
                #     print(24)
                #     self.setWorkerAction(worker, newActions[0])

        print(18)
        for worker in me.workers:
            if worker.next_action == None and worker.position == self._center:
                me.recrtCenters[0].next_action = None
                print(19)
                return

            if worker.next_action != None and self.pointAdd(worker.position, worker.next_action.to_point()) == self._center:
                me.recrtCenters[0].next_action = None
                print(98)
                return

        if len(me.collectors) < 2 and me.cash >= 30:
            me.recrtCenters[0].next_action = RecrtCenterAction.RECCOLLECTOR
            print(21)
        elif len(me.planters) < 2 and me.cash >= 30:
            me.recrtCenters[0].next_action = RecrtCenterAction.RECPLANTER
            print(22)
        print(99)

    def calArroundPoint(self, point:Point) -> List[Point]:
        return [self.pointAdd(point, Point(0,1)),
                self.pointAdd(point, Point(0,-1)),
                self.pointAdd(point, Point(1,1)),
                self.pointAdd(point, Point(1,-1)),
                self.pointAdd(point, Point(1,0)),
                self.pointAdd(point, Point(-1,1)),
                self.pointAdd(point, Point(-1,-1)),
                self.pointAdd(point, Point(-1,0))]

    def isArround(self, point1:Point, point2:Point):
        sub:Point = point1 - point2
        if abs(sub.x) > 1:
            return False
        if abs(sub.y) > 1:
            return False
        return True

    def calCellCarbon(self, point, distance=3, centerWeight=0):
        value = 0

        for cell in self._board.cells.values():
            if cell.position == point:
                carbon = cell.carbon * 2
                if point in self._opponentTreeAround and point in self._myTreeAround:
                    carbon = carbon
                elif point in self._opponentTreeAround:
                    carbon *= 2
                elif point in self._myTreeAround:
                    carbon = 0
                value += carbon
                continue

            dis = self.distance(point, cell.position)
            if dis > distance:
                value += cell.carbon / (dis*dis)
                continue

            value += cell.carbon/dis

        disToCenter = self.distance(point, self._center)
        value = value/((1-centerWeight) + (centerWeight*disToCenter))
        return value
    
    def calCellValue(self)->None:
        sum = 0
        count = 0

        for cell in self._board.cells.values():
            if cell.carbon > 0:
                sum += cell.carbon
                count += 1

            if cell.position == self._center:
                self._cellValue[cell.position.to_index(self._size)] = 0
                continue

            self._cellValue[cell.position.to_index(self._size)] = self.calCellCarbon(cell.position)

        self.averageC = round(sum/count, 2)
        printCellValue(self._size, self._cellValue)

    def calTreeAroundCarbon(self, position):
        cell = self._board.cells[position]
        value = cell.up.carbon + cell.down.carbon + cell.left.carbon + cell.right.carbon + cell.left.up.carbon + \
                cell.left.down.carbon + cell.right.up.carbon + cell.right.down.carbon
        return value

    # def findBestAction(self, actionList):

    def __distanceAction(self, pos1:Point, pos2:Point, awayFlg:bool) -> List:
        actions = []
        dis = self.distance(pos1, pos2)

        actionList = [WorkerAction.UP, WorkerAction.DOWN, WorkerAction.LEFT, WorkerAction.RIGHT]

        for action in actionList:
            newPosition = self.pointAdd(pos1,action.to_point())
            if distance(newPosition, pos2, self._size) < dis:
                if awayFlg is False:
                    actions.append(action)
            else:
                if awayFlg is True:
                    actions.append(action)

        return actions

    def distance(self, pos1, pos2):
        return distance(pos1, pos2, self._size)

    def judgeOpponent(self, worker:Worker)->(List[Point],bool):
        result:List[Point] = []
        ignoreOpponent:bool = False
        for otherWorker in self._board.workers.values():
            if otherWorker.player_id == self._playerid:
                continue
            if self.distance(worker.position, otherWorker.position) > 2:
                continue

            if otherWorker.occupation == Occupation.COLLECTOR:
                if worker.occupation == Occupation.PLANTER:
                    ignoreOpponent = True
                    continue
                if worker.occupation == Occupation.COLLECTOR and worker.carbon < otherWorker.carbon:
                    if self.distance(worker.position, self._center) < self.distance(worker.position, self._opponentCenter):
                        ignoreOpponent = True
                        continue
            result.append(otherWorker.position)
        return result, ignoreOpponent

    def getNextActions(self)->Dict[str, str]:
        return self._board.current_player.next_actions

    def getPostions(self)->Dict[str,Point]:
        position:Dict[str, Point] = {}
        for worker in self._board.current_player.workers:
            position[worker.id] = worker.position
        return position

class Memory():
    lastPositions:Dict[str,Point] = None
    roundid = 1

@board_agent
def mu_agent(board):
    try:
        Memory.roundid = board.step + 1
        print("start---", Memory.roundid)
        configuration = board.configuration
        printRealMap(configuration.size, board)
        agent = Agent(board, configuration, Memory.lastPositions, Memory.roundid)
        agent.build()
        if Memory.roundid == 1:
            Memory.lastPositions = None
        else:
            Memory.lastPositions = agent.getPostions()
        for player in board.players.values():
            print(player.id, player.cash)
        print(agent.getNextActions())
        return agent.getNextActions()
    except BaseException:
        traceback.print_exc(file=open("error", "w"))


# 构建一个环境
#env = make("carbon", debug=True)


# 选取random agent作为对手
# run 函数将会运行300轮
# env.run([mu_agent, "my_agent1"])
#
# # 渲染对战画面(打开jupyter notebook运行此命令才能看到渲染画面)
# print(env.render(mode="json"))

# 注意的是在提交代码的时候，选手也要将自己的智能体用上述 my_agent 函数的形式封装起来，
# 函数以 observation 和 configuration 作为输入，输出对自身每艘飞船和基地的指令，
# 具体请参考 baseline 中的 submission.py 文件


# from zerosum_env import make
# from zerosum_env.envs.carbon.helpers import *

# 构建环境
# env = make("carbon")

# 构建指定参数的环境
# env = make("carbon", configuration={"episodeSteps":300, "size": 21, "randomSeed": 123456,})

# 查看环境的各项参数
# config = env.configuration

# 确定地图选手数(只能是1,2,4)
# num_agent = 2

# 获取自身初始观测状态并查看
# obs = env.reset(num_agent)[0].observation

# 将obs转换为Board类从而更好获取信息
# board = Board(obs, config)

# 查看当前地图
# print("查看当前地图：首位表示格子中的CO2，R0表示玩家0的基地，C0表示玩家0的捕碳员，P0表示玩家0的种树员，T0表示玩家0的树 ")
# print(board)

# 获取自身对象
# me = board.current_player

# 获取自身初始的金额总数
# print("获取自身初始的金额总数")
# print(me.cash)
#
# # 招募捕碳员
# print("招募捕碳员")
# for recrtCenter in me.recrtCenters:
#     recrtCenter.next_action = RecrtCenterAction.RECCOLLECTOR
#     print(recrtCenter.position)
# board = board.next()
# me = board.current_player
#
# print("player id")
# print(board.current_player_id)
# print(WorkerAction.UP)
# # 查看当前地图
# print("查看招募捕碳员后的地图：首位表示格子中的CO2，R0表示玩家0的基地，C0表示玩家0的捕碳员，P0表示玩家0的种树员，T0表示玩家0的树")
# print(board)
#
# # 获取自身当前的金额总数
# print("获取自身当前的金额总数")
# print(me.cash)
#
# # 获取自身当前的工人id列表
# print("获取自身当前的工人id列表")
# print(me.worker_ids)
#
# # 获取自身当前的转化中心id列表
# print("获取自身当前的转化中心id列表")
# print(me.recrtCenter_ids)
#
# # 获取自身当前的树id列表
# print("获取自身当前的树id列表")
# print(me.tree_ids)
#
# # 获取自身捕碳员信息
# print("获取自身捕碳员信息")
# for worker in me.collectors:
#     print(worker.id, worker.occupation, worker.carbon, worker.position)
#
# # 获取自身种树员信息
# print("获取自身种树员信息")
# for worker in me.planters:
#     print(worker.id, worker.occupation, worker.carbon, worker.position)
#
# # 获取自身转化中心信息
# print("获取自身转化中心信息")
# for recrtCenter in me.recrtCenters:
#     print(recrtCenter.id, recrtCenter.position)
#
# # 获取自身树信息
# print("获取自身树信息")
# for tree in me.trees:
#     print(tree.id, tree.position, tree.age)
#
# # 获取所有种树员信息
# print("获取所有种树员信息")
# for planter in board.planters.values():
#     print(planter.id, planter.occupation, planter.carbon, planter.position)
#
# # 获取所有捕碳员信息
# print("获取所有捕碳员信息")
# for collector in board.collectors.values():
#     print(collector.id, collector.occupation, collector.carbon, collector.position, collector.player_id)
#
# # 获取所有转化中心信息
# print("获取所有转化中心信息")
# for recrtCenter in board.recrtCenters.values():
#     print(recrtCenter.id, recrtCenter.position, recrtCenter.player_id)
#
# # 获取所有树信息
# print("获取所有树信息")
# for tree in board.trees.values():
#     print(tree.id, tree.position, tree.player_id)
#
# # 获取所有co2信息
# print("获取所有co2信息")
# sum = 0
# for cell in board.cells.values():
#     print(cell.position, cell.carbon)
#     sum += cell.carbon
#
# # 获取当前地图的co2总数
# print("获取当前地图的co2总数")
# print(sum)
#
# printRealMap(config.size, board)
# agent = Agent(board, config)


# 需要注意的是，以上通过position属性获取的位置，
# 均以地图左下角为原点, 与np.array的索引不同。


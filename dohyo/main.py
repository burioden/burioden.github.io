#!/usr/bin/env python3
import sys, math, time
from collections import defaultdict
from math import log2, floor, ceil

# ----------------------------
# グローバル変数・クラス定義
# ----------------------------

test = 2  # テスト用フラグ

# 方向：R, D, L, U
dirI = [0, 1, 0, -1]
dirJ = [1, 0, -1, 0]
dirC = ['R', 'D', 'L', 'U']

class Point:
    def __init__(self, i, j):
        self.i = i
        self.j = j
    def __eq__(self, other):
        return self.i == other.i and self.j == other.j
    def __ne__(self, other):
        return not self.__eq__(other)
    def __repr__(self):
        return f"({self.i}, {self.j})"

def isWithin(I, J, h, w):
    return 0 <= I < h and 0 <= J < w

def getMoveCell(n, nowPos, d, step):
    moveI = nowPos.i + dirI[d] * step
    moveJ = nowPos.j + dirJ[d] * step
    if not isWithin(moveI, moveJ, n, n):
        return Point(-1, -1)  # 枠外
    return Point(moveI, moveJ)

# 時間計測用
tStart = time.time()
timeLimit = 1980  # ミリ秒

def checkTime():
    return (time.time() - tStart) * 1000

def outputTime():
    sys.stderr.write(f"time: {checkTime():.2f}\n")

# ----------------------------
# グローバル変数（提出用）
# ----------------------------
N = 0
M = 0
removeStone = 0  # 取り除いた鉱石の数

board = []  # 盤面（list of list of char）
moves = []  # 各操作： (操作種別, 方向) のタプル

# 各鉱石と穴の位置情報
orePositions = defaultdict(list)  # 小文字：各鉱石の位置（複数インスタンス）
# 【修正①】 各鉱石の落下状態を管理する配列（各インスタンスごと）
oreDropped = defaultdict(list)    # 各 ore に対して、各インスタンスが落とされたか（初期は False）
holePositions = dict()            # 大文字：各穴の位置（各種類1つ）

currentPos = None  # 現在のプレイヤー位置（初期は穴 'A' の位置）

# ----------------------------
# 関数定義
# ----------------------------

def readInput():
    global N, M, board, currentPos
    # 入力処理：最初の行に N, M、続いて盤面の N 行
    inp = sys.stdin.read().strip().splitlines()
    if len(inp) < 1:
        sys.exit("入力データが不足しています")
    header = inp[0].split()
    N = int(header[0])
    M = int(header[1])
    board = []
    for i in range(N):
        # 盤面は1行ずつ、文字列をリストに変換
        line = inp[1+i].strip()
        # C++版と同様、'@' を '岩' に置き換える
        line = line.replace('@', '岩')
        board.append(list(line))
    # 盤面から各種オブジェクトの位置情報を抽出
    for i in range(N):
        for j in range(N):
            c = board[i][j]
            if 'a' <= c <= 'z':
                orePositions[c].append(Point(i,j))
                oreDropped[c].append(False)  # 【修正①】未落下状態
            if 'A' <= c <= 'Z':
                holePositions[c] = Point(i,j)
    # 初期位置は穴 'A' の位置
    if 'A' in holePositions:
        currentPos = holePositions['A']
    else:
        currentPos = Point(0,0)

def outputSolution():
    # 各操作を1行ずつ出力
    for act, d in moves:
        print(f"{act} {d}")

def calculateScoreAndReport():
    # 盤面上の鉱石総数 K を計算
    K = sum(len(v) for v in orePositions.values())
    score = 0
    if K == 0:
        score = 0
    elif removeStone == K:
        score = round(1e6 * (1 + math.log2(10000.0 / (len(moves) if moves else 1))))
    else:
        score = round(1e6 * (removeStone / K))
    sys.stderr.write(f"Score: {score}  (N={N}, M={M}, K={K}, A={removeStone}, T={len(moves)})\n")

def isValidMove(actionType, current, direction):
    d = getDirectionIndex(direction)
    if d == -1:
        return False
    newPos = getMoveCell(N, current, d, 1)
    if newPos.i == -1:
        return False
    return True

def getDirectionIndex(d):
    for idx, ch in enumerate(dirC):
        if ch == d:
            return idx
    return -1

def performMove(actionType, direction):
    global currentPos
    d = getDirectionIndex(direction)
    if d == -1:
        return False
    newPos = getMoveCell(N, currentPos, d, 1)
    if newPos.i == -1:
        return False
    currentPos = newPos
    moves.append((1, direction))
    return True

def performThrow(throwDir):
    global board, currentPos, removeStone
    d = getDirectionIndex(throwDir)
    if d == -1:
        return
    obj = board[currentPos.i][currentPos.j]
    if not (obj == '岩' or ('a' <= obj <= 'z')):
        return
    moves.append((3, throwDir))
    board[currentPos.i][currentPos.j] = '.'
    thrownPos = Point(currentPos.i, currentPos.j)
    while True:
        nextPos = getMoveCell(N, thrownPos, d, 1)
        if nextPos.i == -1:
            board[thrownPos.i][thrownPos.j] = obj
            break
        nextCell = board[nextPos.i][nextPos.j]
        if nextCell == '岩' or ('a' <= nextCell <= 'z'):
            board[thrownPos.i][thrownPos.j] = obj
            break
        if 'A' <= nextCell <= 'Z':
            if 'a' <= obj <= 'z':
                removeStone += 1
            break
        thrownPos = nextPos

def performCarry(carryDir):
    global board, currentPos, removeStone
    d = getDirectionIndex(carryDir)
    if d == -1:
        return False
    obj = board[currentPos.i][currentPos.j]
    if not (obj == '岩' or ('a' <= obj <= 'z')):
        return False
    target = getMoveCell(N, currentPos, d, 1)
    if target.i == -1:
        return False
    targetCell = board[target.i][target.j]
    if targetCell == '岩' or ('a' <= targetCell <= 'z'):
        return False
    moves.append((2, carryDir))
    board[currentPos.i][currentPos.j] = '.'
    if 'A' <= targetCell <= 'Z':
        if 'a' <= obj <= 'z':
            removeStone += 1
        currentPos = target
        return True
    if targetCell == '.':
        board[target.i][target.j] = obj
        currentPos = target
        return True
    return False

def returnToPosition(target):
    # 縦方向の移動
    while currentPos.i < target.i:
        if not performMove(1, 'D'):
            break
    while currentPos.i > target.i:
        if not performMove(1, 'U'):
            break
    # 横方向の移動
    while currentPos.j < target.j:
        if not performMove(1, 'R'):
            break
    while currentPos.j > target.j:
        if not performMove(1, 'L'):
            break

def moveToPosition(start, goal):
    # 【補助関数】 簡易的な経路移動（縦→横）
    current = Point(start.i, start.j)
    while current.i != goal.i:
        moveDir = 'D' if current.i < goal.i else 'U'
        # performMove を使って currentPos を更新
        performMove(1, moveDir)
        current = Point(currentPos.i, currentPos.j)
    while current.j != goal.j:
        moveDir = 'R' if current.j < goal.j else 'L'
        performMove(1, moveDir)
        current = Point(currentPos.i, currentPos.j)

def forwardAndThrow(moveDir, throwDir):
    while isValidMove(1, currentPos, moveDir):
        if not performMove(1, moveDir):
            break
        cell = board[currentPos.i][currentPos.j]
        if cell == '岩' or ('a' <= cell <= 'z'):
            performThrow(throwDir)

def solve4dirthrow():
    # C++版のsolve4dirthrow（例として実装）
    for oreType, dropped in oreDropped.items():
        # 各 oreType につき、最低1つでも未落下があれば処理
        if not any(dropped):
            targetHole = holePositions[oreType.upper()]
            if test == 2:
                sys.stderr.write(f"targetOre: {oreType} targetPos: {targetHole}\n")
            for i in range(4):
                returnToPosition(targetHole)
                moveDir = dirC[i]
                throwDir = dirC[(i+2)%4]
                forwardAndThrow(moveDir, throwDir)

# ----------------------------
# 【追加】 全ての鉱石を carry で穴に落とす関数（複数インスタンス対応版）
def moveAllOresToHolesUsingCarry():
    global currentPos, removeStone
    # 各 ore タイプごとに処理
    for oreType, positions in orePositions.items():
        droppedFlags = oreDropped[oreType]  # list of bool
        # 対応する穴の位置（大文字）
        targetHole = holePositions[oreType.upper()]
        # 各 ore インスタンスを順に処理
        for idx in range(len(positions)):
            # 【追加】 既に落とされたならスキップ
            if droppedFlags[idx]:
                continue
            orePos = positions[idx]
            # 盤面上に存在しない場合はスキップ（既に移動済み）
            if not isWithin(orePos.i, orePos.j, N, N):
                continue
            if board[orePos.i][orePos.j] != oreType:
                continue
            # 【追加】 プレイヤーを ore のあるセルに戻す
            returnToPosition(orePos)
            # carry 操作を繰り返し、穴に到達させる
            while currentPos != targetHole:
                if currentPos.i < targetHole.i:
                    moveDir = 'D'
                elif currentPos.i > targetHole.i:
                    moveDir = 'U'
                elif currentPos.j < targetHole.j:
                    moveDir = 'R'
                elif currentPos.j > targetHole.j:
                    moveDir = 'L'
                else:
                    break
                if not performCarry(moveDir):
                    break
            # 【追加】 carry 操作後、もしプレイヤー位置が穴ならオブジェクトは落下済み
            if currentPos == targetHole:
                positions[idx] = Point(-1, -1)  # 位置更新：落とされたので (-1,-1)
                droppedFlags[idx] = True
            else:
                # 落としていなければ、carry 操作で運ばれた先の位置を記録
                positions[idx] = Point(currentPos.i, currentPos.j)

# ----------------------------
# main 関数
# ----------------------------
def main():
    readInput()
    # ここで、必要に応じて solve4dirthrow() も呼び出すことが可能
    # solve4dirthrow()
    # 【追加】 全ての鉱石を carry 操作で穴に落とす
    moveAllOresToHolesUsingCarry()
    outputSolution()
    calculateScoreAndReport()
    outputTime()

if __name__ == '__main__':
    main()
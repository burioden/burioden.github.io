#!/usr/bin/env python3
import sys
import math
import time
from collections import defaultdict

# ----------------------------
# 定数・グローバル変数
# ----------------------------
# 方向：R, D, L, U
dirI = [0, 1, 0, -1]  # C++ の dirI と同様
dirJ = [1, 0, -1, 0]  # C++ の dirJ と同様
dirC = ['R', 'D', 'L', 'U']  # 方向文字

# ----------------------------
# クラス定義
# ----------------------------
class Point:
    def __init__(self, i=0, j=0):
        self.i = i
        self.j = j
    def __eq__(self, other):
        return self.i == other.i and self.j == other.j
    def __ne__(self, other):
        return not self.__eq__(other)
    def __lt__(self, other):
        return (self.i, self.j) < (other.i, other.j)
    def __repr__(self):
        return f"({self.i},{self.j})"

# ----------------------------
# ユーティリティ関数
# ----------------------------
def is_within(I, J, h, w):
    return 0 <= I < h and 0 <= J < w

def get_move_cell(n, now_pos, d, step):
    move_i = now_pos.i + dirI[d] * step
    move_j = now_pos.j + dirJ[d] * step
    if not is_within(move_i, move_j, n, n):
        return Point(-1, -1)  # 枠外
    return Point(move_i, move_j)

# ----------------------------
# グローバル変数（提出用）
# ----------------------------
N = 0
M = 0
removeStone = 0  # 取り除いた鉱石の数

board = []      # 盤面情報（list of str）
moves = []      # 各操作: (操作種別, 方向) のタプル

orePositions = defaultdict(list)  # 小文字: 複数の鉱石の位置
holePositions = {}                # 大文字: 各穴の位置（各種類1つ）
isOredone = {}                    # 各鉱石の処理済みフラグ（未処理なら 0）

currentPos = None  # 現在のプレイヤー位置（初期は穴 'A' の位置）

# ----------------------------
# 関数定義（C++版から Python への変換）
# ----------------------------
def read_input():
    global N, M, board, currentPos
    data = sys.stdin.read().splitlines()
    if not data:
        sys.exit("入力がありません")
    header = data[0].split()
    N = int(header[0])
    M = int(header[1])
    board = []
    for i in range(N):
        line = data[1+i].strip()
        # 【修正】 '@' を '岩' に置換
        line = line.replace('@', '岩')
        board.append(line)
    # 盤面から各種オブジェクトの位置情報を抽出
    for i in range(N):
        for j in range(N):
            c = board[i][j]
            if 'a' <= c <= 'z':
                orePositions[c].append(Point(i, j))
                isOredone[c] = 0  # 未処理
            if 'A' <= c <= 'Z':
                holePositions[c] = Point(i, j)
    # 初期位置は穴 'A' の位置
    if 'A' in holePositions:
        currentPos = holePositions['A']
    else:
        currentPos = Point(0, 0)

def output_solution():
    for act, d in moves:
        print(f"{act} {d}")

def calculate_score_and_report():
    K = 0  # 盤面上の鉱石総数
    for positions in orePositions.values():
        K += len(positions)
    if K == 0:
        score = 0
    elif removeStone == K:
        score = round(1e6 * (1 + math.log2(10000.0 / (len(moves) if moves else 1))))
    else:
        score = round(1e6 * (removeStone / K))
    sys.stderr.write(f"Score: {score}\n")

# ----------------------------
# 移動操作（行動1）：指定方向に移動
def perform_move(action_type, direction):
    global currentPos
    d = get_direction_index(direction)
    if d == -1:
        return False
    new_pos = get_move_cell(N, currentPos, d, 1)
    if new_pos.i == -1:
        return False
    currentPos = new_pos
    moves.append((1, direction))
    return True

# ----------------------------
# 投げる操作（行動3）：指定方向に沿ってオブジェクトを投げる
def perform_throw(throw_dir):
    global board, currentPos, removeStone
    d = get_direction_index(throw_dir)
    if d == -1:
        return
    obj = board[currentPos.i][currentPos.j]
    if not (obj == '岩' or ('a' <= obj <= 'z')):
        return
    moves.append((3, throw_dir))
    # 現在のセルからオブジェクトを取り除く
    board[currentPos.i] = board[currentPos.i][:currentPos.j] + '.' + board[currentPos.i][currentPos.j+1:]
    thrown_pos = Point(currentPos.i, currentPos.j)
    while True:
        next_pos = get_move_cell(N, thrown_pos, d, 1)
        if next_pos.i == -1:
            board[thrown_pos.i] = board[thrown_pos.i][:thrown_pos.j] + obj + board[thrown_pos.i][thrown_pos.j+1:]
            break
        next_cell = board[next_pos.i][next_pos.j]
        if next_cell == '岩' or ('a' <= next_cell <= 'z'):
            board[thrown_pos.i] = board[thrown_pos.i][:thrown_pos.j] + obj + board[thrown_pos.i][thrown_pos.j+1:]
            break
        if 'A' <= next_cell <= 'Z':
            if 'a' <= obj <= 'z':
                removeStone += 1
            break
        thrown_pos = next_pos

# ----------------------------
# 方向文字からインデックスに変換
def get_direction_index(d):
    for idx, ch in enumerate(dirC):
        if ch == d:
            return idx
    return -1

# ----------------------------
# 盤面外に戻る（行動1の移動）【C++ の returnToPosition の動作再現】
def return_to_position(target):
    while currentPos.i < target.i:
        if not perform_move(1, 'D'):
            break
    while currentPos.i > target.i:
        if not perform_move(1, 'U'):
            break
    while currentPos.j < target.j:
        if not perform_move(1, 'R'):
            break
    while currentPos.j > target.j:
        if not perform_move(1, 'L'):
            break

# ----------------------------
# シンプルな四方向投げ解法
def simple_directional_throw_solution(move_dir, throw_dir):
    while is_valid_move(1, currentPos, move_dir):
        if not perform_move(1, move_dir):
            break
        cell = board[currentPos.i][currentPos.j]
        if cell == '岩' or ('a' <= cell <= 'z'):
            perform_throw(throw_dir)

def is_valid_move(action_type, current, direction):
    d = get_direction_index(direction)
    if d == -1:
        return False
    new_pos = get_move_cell(N, current, d, 1)
    return new_pos.i != -1

# ----------------------------
# 解法：各鉱石の穴に投げる（行動3のみ利用）解法
def solve():
    # 第一段階：各 ore タイプについて、未処理なら四方向投げ解法を実行
    for ore, done in isOredone.items():
        if done == 0:
            targetOre = ore
            targetPos = holePositions.get(targetOre.upper(), Point(0, 0))
            for i in range(4):
                return_to_position(targetPos)
                move_dir = dirC[i]
                throw_dir = dirC[(i+2) % 4]
                simple_directional_throw_solution(move_dir, throw_dir)
            isOredone[ore] = 1
    # ★二手目：追加の清掃フェーズ
    second_phase_cleaning()

# ★二手目：追加の清掃フェーズ（実装例）
def second_phase_cleaning():
    global currentPos
    # 基準は穴 'A' の位置
    A = holePositions.get('A', Point(0, 0))
    # 各四象限（対角方向）について処理
    for di, dj in [(1,1), (1,-1), (-1,1), (-1,-1)]:
        # 【★追加】 清掃領域のサイズ：A が端なら 2x2、そうでなければ 3x3
        region_size = 2 if (A.i == 0 or A.i == N-1 or A.j == 0 or A.j == N-1) else 3
        if di == 1:
            row_start = A.i
            row_end = min(N, A.i + region_size)
        else:
            row_start = max(0, A.i - region_size + 1)
            row_end = A.i + 1
        if dj == 1:
            col_start = A.j
            col_end = min(N, A.j + region_size)
        else:
            col_start = max(0, A.j - region_size + 1)
            col_end = A.j + 1

        # 【★追加】 清掃領域内に岩または鉱石が存在する間、以下の処理を繰り返す
        while True:
            found = False
            for i in range(row_start, row_end):
                for j in range(col_start, col_end):
                    if board[i][j] == '岩' or ('a' <= board[i][j] <= 'z'):
                        found = True
                        break
                if found:
                    break
            if not found:
                break  # この象限は清掃完了

            # プレイヤーを A に向かって移動【★追加】
            if currentPos.i != A.i:
                perform_move(1, 'D' if currentPos.i < A.i else 'U')
            if currentPos.j != A.j:
                perform_move(1, 'R' if currentPos.j < A.j else 'L')

            # もし現在位置に岩/鉱石があれば carry（行動2）を実行【★追加】
            cell = board[currentPos.i][currentPos.j]
            if cell == '岩' or ('a' <= cell <= 'z'):
                if currentPos.i != A.i:
                    carry_dir = 'D' if currentPos.i < A.i else 'U'
                elif currentPos.j != A.j:
                    carry_dir = 'R' if currentPos.j < A.j else 'L'
                else:
                    carry_dir = 'R'
                perform_carry(carry_dir)
            # 次に、プレイヤーから A へ向かう方向に投げる【★追加】
            di_move = A.i - currentPos.i
            dj_move = A.j - currentPos.j
            if abs(di_move) >= abs(dj_move):
                throw_dir = 'U' if di_move < 0 else 'D'
            else:
                throw_dir = 'L' if dj_move < 0 else 'R'
            perform_throw(throw_dir)
        # 清掃完了後、プレイヤーを反対側の壁まで移動【★追加】
        # ここでは、可能な限り垂直・水平方向に移動して壁に近づく
        while is_valid_move(1, currentPos, 'U' if di < 0 else 'D') or is_valid_move(1, currentPos, 'L' if dj < 0 else 'R'):
            if is_valid_move(1, currentPos, 'U' if di < 0 else 'D'):
                perform_move(1, 'U' if di < 0 else 'D')
            if is_valid_move(1, currentPos, 'L' if dj < 0 else 'R'):
                perform_move(1, 'L' if dj < 0 else 'R')

# ----------------------------
# performCarry（行動2）の実装（C++版と同様）
def perform_carry(carry_dir):
    global board, currentPos, removeStone
    d = get_direction_index(carry_dir)
    if d == -1:
        return False
    obj = board[currentPos.i][currentPos.j]
    if not (obj == '岩' or ('a' <= obj <= 'z')):
        return False
    target = get_move_cell(N, currentPos, d, 1)
    if target.i == -1:
        return False
    target_cell = board[target.i][target.j]
    if target_cell == '岩' or ('a' <= target_cell <= 'z'):
        return False
    moves.append((2, carry_dir))
    board[currentPos.i] = board[currentPos.i][:currentPos.j] + '.' + board[currentPos.i][currentPos.j+1:]
    if 'A' <= target_cell <= 'Z':
        if 'a' <= obj <= 'z':
            removeStone += 1
        currentPos = target
        return True
    if target_cell == '.':
        board[target.i] = board[target.i][:target.j] + obj + board[target.i][target.j+1:]
        currentPos = target
        return True
    return False

# ----------------------------
# main 関数
def main():
    start_time = time.time()
    read_input()
    solve()
    output_solution()
    calculate_score_and_report()
    elapsed = (time.time() - start_time)*1000
    sys.stderr.write(f"time: {elapsed:.2f}\n")

if __name__ == '__main__':
    main()
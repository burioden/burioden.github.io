#!/usr/bin/env python3
import sys
import math
import time
from collections import defaultdict

# ----------------------------
# 定数・グローバル変数
# ----------------------------
# 方向：R, D, L, U
dirI = [0, 1, 0, -1]  # 【修正】C++ の dirI と同様
dirJ = [1, 0, -1, 0]  # 【修正】C++ の dirJ と同様
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
    # 入力処理：最初の行に N M、続いて盤面の N 行
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
                orePositions[c].append(Point(i,j))
                isOredone[c] = 0  # 未処理
            if 'A' <= c <= 'Z':
                holePositions[c] = Point(i,j)
    # 初期位置は穴 'A' の位置
    if 'A' in holePositions:
        currentPos = holePositions['A']
    else:
        currentPos = Point(0,0)

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
    # 現在位置に岩または鉱石がなければ何もしない
    if not (obj == '岩' or ('a' <= obj <= 'z')):
        return
    moves.append((3, throw_dir))
    # 現在のセルからオブジェクトを取り除く
    board[currentPos.i] = board[currentPos.i][:currentPos.j] + '.' + board[currentPos.i][currentPos.j+1:]
    thrown_pos = Point(currentPos.i, currentPos.j)
    while True:
        next_pos = get_move_cell(N, thrown_pos, d, 1)
        if next_pos.i == -1:
            # 壁にぶつかる → 直前で着地
            board[thrown_pos.i] = board[thrown_pos.i][:thrown_pos.j] + obj + board[thrown_pos.i][thrown_pos.j+1:]
            break
        next_cell = board[next_pos.i][next_pos.j]
        if next_cell == '岩' or ('a' <= next_cell <= 'z'):
            board[thrown_pos.i] = board[thrown_pos.i][:thrown_pos.j] + obj + board[thrown_pos.i][thrown_pos.j+1:]
            break
        if 'A' <= next_cell <= 'Z':
            if 'a' <= obj <= 'z':
                removeStone += 1
            # 投げたオブジェクトは穴に落ちるため、盤面更新不要
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
# 盤面外に戻る（行動1の移動）【そのまま C++ の returnToPosition の動作を再現】
def return_to_position(target):
    # 縦方向の移動
    while currentPos.i < target.i:
        if not perform_move(1, 'D'):
            break
    while currentPos.i > target.i:
        if not perform_move(1, 'U'):
            break
    # 横方向の移動
    while currentPos.j < target.j:
        if not perform_move(1, 'R'):
            break
    while currentPos.j > target.j:
        if not perform_move(1, 'L'):
            break

# ----------------------------
# シンプルな四方向投げ解法
def simple_directional_throw_solution(move_dir, throw_dir):
    # 【修正】 isValidMove 相当のチェック（ここでは盤面外チェックのみ）
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
    # for each ore type (未処理と判定している isOredone で管理)
    for ore, done in isOredone.items():
        if done == 0:
            targetOre = ore
            targetPos = holePositions.get(targetOre.upper(), Point(0,0))
            # 四方向に対して処理
            for i in range(4):
                # 現在位置から目的地まで戻る
                return_to_position(targetPos)
                move_dir = dirC[i]
                throw_dir = dirC[(i+2)%4]
                simple_directional_throw_solution(move_dir, throw_dir)
            # マーク：処理済み
            isOredone[ore] = 1
    # ★二手目：現在壁に隣接するマスにいる。先ほど綺麗にした列・行を軸に、左右1マスずつ、行動1と、岩や鉱石があった場合は行動2を行い、Aがある列・行に岩や鉱石を持ってくる。行動3を行い、周囲の岩や鉱石を穴に落としながら穴に向かって進む。穴に到達したら、反対方向の壁まで行動1で進み、先ほどと同じ行動を繰り返す。を 全方向に対して行う。例えばAの位置が[r, c]だとして、[r + 1, c + 1], [r - 1, c + 1], [r + 1, c - 1], [r - 1, c - 1]の列・行範囲内にある岩と鉱石が全て落とされた状態にする。一手目を終えた時点で例えばセル0,0にいる場合（Aが0行め、または0列目、またはN - 1列目、N - 1行目）にある場合は、3行3列ではなく、2行2列の範囲内にある岩と鉱石が全て落とされた状態にする。

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
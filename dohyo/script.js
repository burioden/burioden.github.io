// グローバル変数
let N = 0; // 盤面サイズ
let M = 0; // 鉱石の種類数
let board = []; // 盤面2次元配列
let playerPos = { r: 0, c: 0 }; // プレイヤー位置

// コマンド管理
let commandIndex = 0; // 現在のコマンド実行位置
let commandLines = [];

// スコア計算用
let initialOreCount = 0; // 盤面にある鉱石総数
let fallenCountByType = {}; // 鉱石が正しい穴に落ちた数 (種類ごと)

// ★ 履歴管理: 1手戻す機能のために、各手の状態を保持するスタック
let historyStack = [];

// ★ 自動再生(Play)用フラグ
let isPlaying = false;

/**
 * 盤面を初期化 (入力データを解析)
 */
function initBoard() {
  // スコア表示リセット
  document.getElementById("scoreboard").textContent =
    "Score: (まだ計算されていません)";

  // inputData から読み込み
  const inputData = document
    .getElementById("inputData")
    .value.split("\n")
    .map((l) => l.trim());

  if (inputData.length < 2) {
    alert("入力データが不足しています (N M, 盤面 が必要)");
    return;
  }

  // 1行目: "N M"
  const [nStr, mStr] = inputData[0].split(/\s+/);
  N = parseInt(nStr, 10);
  M = parseInt(mStr, 10);
  if (isNaN(N) || isNaN(M) || N <= 0) {
    alert("N, M の指定が正しくありません");
    return;
  }

  // 盤面生成の下準備
  board = [];
  for (let r = 0; r < N; r++) {
    let row = [];
    for (let c = 0; c < N; c++) {
      row.push({ hole: null, obj: null });
    }
    board.push(row);
  }

  playerPos = { r: 0, c: 0 };
  initialOreCount = 0;
  fallenCountByType = {};

  // 次の N 行が盤面
  const boardLines = inputData.slice(1, 1 + N);

  // 盤面読み込み
  for (let r = 0; r < N; r++) {
    let line = (boardLines[r] || "").trim();

    // '@' を '岩' に置き換える
    line = line.replace(/@/g, "岩");

    for (let c = 0; c < N; c++) {
      const ch = line[c] || "."; // 足りない分は '.' 扱い
      if (ch === ".") {
        // 何もなし
      } else if (ch === "岩") {
        // 岩
        board[r][c].obj = { type: "rock" };
      } else if (ch >= "a" && ch <= "z") {
        // 鉱石
        board[r][c].obj = { type: "ore", letter: ch };
        initialOreCount++;
        if (!fallenCountByType[ch]) {
          fallenCountByType[ch] = 0;
        }
      } else if (ch >= "A" && ch <= "Z") {
        // 穴
        board[r][c].hole = ch;
        // プレイヤー初期位置を "A" に合わせる
        if (ch === "A") {
          playerPos = { r, c };
        }
      }
    }
  }

  // コマンドリストを再取得
  commandIndex = 0;
  commandLines = document
    .getElementById("commands")
    .value.split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  // grid の大きさを N×N に設定
  const gridDiv = document.getElementById("grid");
  gridDiv.style.gridTemplateColumns = `repeat(${N}, 30px)`;
  gridDiv.style.gridTemplateRows = `repeat(${N}, 30px)`;

  // ★ 履歴をリセットし、現在の状態を最初の履歴として保存
  historyStack = [];
  pushHistory();

  renderBoard();
}

/**
 * 盤面描画
 */
function renderBoard() {
  const gridDiv = document.getElementById("grid");
  gridDiv.innerHTML = "";

  for (let r = 0; r < N; r++) {
    for (let c = 0; c < N; c++) {
      const cell = board[r][c];
      const cellDiv = document.createElement("div");
      cellDiv.className = "cell";

      let content = "";
      // 穴
      if (cell.hole) {
        cellDiv.classList.add("hole");
        content = cell.hole;
      }
      // オブジェクト (岩 or 鉱石)
      if (cell.obj) {
        if (cell.obj.type === "rock") {
          cellDiv.classList.add("rock");
          content = "🪨"; // 絵文字などで表示してみる例
        } else if (cell.obj.type === "ore") {
          cellDiv.classList.add("ore");
          content = cell.obj.letter;
        }
      }
      // プレイヤー位置
      if (r === playerPos.r && c === playerPos.c) {
        cellDiv.classList.add("player");
      }

      cellDiv.textContent = content;
      gridDiv.appendChild(cellDiv);
    }
  }
}

// 方向オフセット
const dirOffsets = {
  U: { dr: -1, dc: 0 },
  D: { dr: 1, dc: 0 },
  L: { dr: 0, dc: -1 },
  R: { dr: 0, dc: 1 },
};

/**
 * 穴に落ちたときの処理
 */
function fallIntoHole(holeChar, movingObj) {
  // 鉱石の場合、対応穴かどうかチェック
  if (movingObj.type === "ore") {
    // 例: 'a' の鉱石が 'A' の穴に落ちたらカウント
    if (holeChar === movingObj.letter.toUpperCase()) {
      fallenCountByType[movingObj.letter]++;
    }
  }
  // 岩の場合は特にカウントしない
}

/**
 * 移動操作（タイプ1）
 */
function move(direction) {
  const offset = dirOffsets[direction];
  if (!offset) return;

  const nr = playerPos.r + offset.dr;
  const nc = playerPos.c + offset.dc;
  if (nr < 0 || nr >= N || nc < 0 || nc >= N) {
    return; // 範囲外
  }

  // プレイヤー移動
  playerPos = { r: nr, c: nc };
}

/**
 * 運ぶ操作（タイプ2）
 */
function carry(direction) {
  const offset = dirOffsets[direction];
  if (!offset) return;

  const cell = board[playerPos.r][playerPos.c];
  if (!cell.obj) {
    // オブジェクトがなければ何もしない
    return;
  }
  const nr = playerPos.r + offset.dr;
  const nc = playerPos.c + offset.dc;
  if (nr < 0 || nr >= N || nc < 0 || nc >= N) return;

  // 運び先に既にオブジェクトがあればキャンセル
  if (board[nr][nc].obj) return;

  const movingObj = cell.obj;
  cell.obj = null;

  // 穴なら落下
  if (board[nr][nc].hole) {
    fallIntoHole(board[nr][nc].hole, movingObj);
  } else {
    board[nr][nc].obj = movingObj;
  }

  // プレイヤーも移動
  playerPos = { r: nr, c: nc };
}

/**
 * 転がす操作（タイプ3）
 * 問題文で示された通り、1マスずつ「穴チェック→障害物チェック」を繰り返す
 * 自分(プレイヤー)は動かず、岩・鉱石のみ動く
 */
function roll(direction) {
  const offset = dirOffsets[direction];
  if (!offset) return;

  const cell = board[playerPos.r][playerPos.c];
  if (!cell.obj) return; // 現在位置にオブジェクトがなければ何もしない

  const movingObj = cell.obj;
  cell.obj = null; // 現在のプレイヤーセルからオブジェクトを取り出す

  // 【修正】 プレイヤー位置からは独立した開始点として、隣接セルを使う
  const firstR = playerPos.r + offset.dr;
  const firstC = playerPos.c + offset.dc;
  if (
    firstR < 0 ||
    firstR >= N ||
    firstC < 0 ||
    firstC >= N ||
    board[firstR][firstC].obj
  ) {
    // 【修正】 隣接セルが使えない場合は、元のプレイヤーセルに戻す（プレイヤーセルはそのまま保持）
    board[playerPos.r][playerPos.c].obj = movingObj;
    return;
  }
  // 【修正】 隣接セルが穴なら、即落下（オブジェクトは消える）
  if (board[firstR][firstC].hole) {
    fallIntoHole(board[firstR][firstC].hole, movingObj);
    return;
  }

  // ここからは、firstR, firstC を開始点として転がす
  let curR = firstR;
  let curC = firstC;
  while (true) {
    const nextR = curR + offset.dr;
    const nextC = curC + offset.dc;

    // 1. 次のセルが範囲外またはオブジェクトがある場合 → ここで停止して、現在のセルに配置
    if (
      nextR < 0 ||
      nextR >= N ||
      nextC < 0 ||
      nextC >= N ||
      board[nextR][nextC].obj
    ) {
      board[curR][curC].obj = movingObj;
      break;
    }
    // 2. 次のセルが穴なら → そこで落下（オブジェクトは消える）
    if (board[nextR][nextC].hole) {
      fallIntoHole(board[nextR][nextC].hole, movingObj);
      break;
    }
    // 3. どちらでもないなら、1マス進む
    curR = nextR;
    curC = nextC;
  }
}
/**
 * コマンド1行分を実行
 */
function processCommand(line) {
  if (!line) return;
  const parts = line.split(/\s+/);
  if (parts.length !== 2) return;

  const type = parts[0];
  const dir = parts[1].toUpperCase();
  if (!dirOffsets[dir]) return;

  if (type === "1") {
    move(dir);
  } else if (type === "2") {
    carry(dir);
  } else if (type === "3") {
    roll(dir);
  }
  console.log("type:" + type + " dir:" + dir);
  renderBoard();
}

/**
 * 1手進む: コマンド1つ実行
 *   - 実行前に現在の状態を履歴に保存し、あとで戻せるようにする
 */
function stepCommand() {
  if (commandIndex < commandLines.length) {
    // ★操作前の状態を保存
    pushHistory();
    processCommand(commandLines[commandIndex]);
    commandIndex++;
  }
}

/**
 * 1手戻す: 直前の状態に復元
 */
function stepBack() {
  // commandIndex が 0 の時は戻れない
  if (commandIndex > 0 && historyStack.length > 1) {
    // 現在の状態を捨て、1つ前の状態を取り出す
    historyStack.pop(); // 今の状態
    const prevState = historyStack[historyStack.length - 1]; // 1つ前
    restoreState(prevState);

    // 1手戻したので、コマンドインデックスも1つ戻す
    commandIndex--;
    renderBoard();
  }
}

/**
 * 自動再生: コマンドを連続実行し、終了後にスコア計算
 */
function playCommands() {
  isPlaying = true; // ★再生フラグを立てる

  function step() {
    if (!isPlaying) {
      // ★一時停止が押された場合、再生を止める
      return;
    }
    if (commandIndex < commandLines.length) {
      pushHistory(); // ★操作前の状態を保存
      processCommand(commandLines[commandIndex]);
      commandIndex++;
      setTimeout(step, 50);
    } else {
      // 全コマンド終了後にスコア計算
      computeAndShowScore();
    }
  }
  step();
}

/**
 * 一時停止ボタン
 */
function stopCommands() {
  isPlaying = false;
}

/**
 * スコア計算
 */
function computeAndShowScore() {
  const T = commandLines.length;
  const K = initialOreCount;

  // 正しく落ちた鉱石数 A
  let A = 0;
  for (const oreLetter in fallenCountByType) {
    A += fallenCountByType[oreLetter];
  }

  let score = 0;
  if (K === 0) {
    // 鉱石がない場合は 0
    score = 0;
  } else if (A === K) {
    // A = K
    // score = round(10^6 * (1 + log2(10000/T)))
    if (T === 0) {
      score = 1000000;
    } else {
      score = Math.round(1e6 * (1 + Math.log2(10000 / T)));
    }
  } else {
    // A < K
    // score = round(10^6 * (A/K))
    score = Math.round(1e6 * (A / K));
  }

  const sb = document.getElementById("scoreboard");
  sb.textContent = `Score: ${score}  (N=${N}, M=${M}, K=${K}, A=${A}, T=${T})`;
}

/* ==============================
   履歴管理 (1手戻す用)
   ============================== */

/**
 * 現在の状態を履歴スタックに push
 *  - board, playerPos, commandIndex, fallenCountByType などをコピー
 */
function pushHistory() {
  const state = {
    board: cloneBoard(board),
    playerPos: { r: playerPos.r, c: playerPos.c },
    commandIndex: commandIndex,
    fallenCountByType: { ...fallenCountByType },
  };
  historyStack.push(state);
}

/**
 * 渡された state をもとに現状を復元
 */
function restoreState(state) {
  board = cloneBoard(state.board);
  playerPos = { r: state.playerPos.r, c: state.playerPos.c };
  commandIndex = state.commandIndex;
  fallenCountByType = { ...state.fallenCountByType };
}

/**
 * board配列をディープコピーする
 */
function cloneBoard(originalBoard) {
  const newBoard = [];
  for (let r = 0; r < originalBoard.length; r++) {
    const row = [];
    for (let c = 0; c < originalBoard[r].length; c++) {
      const cell = originalBoard[r][c];
      // hole と obj を個別にコピー
      // obj がある場合は { type, letter? } のオブジェクト
      let newCell = {
        hole: cell.hole,
        obj: null,
      };
      if (cell.obj) {
        newCell.obj = { ...cell.obj };
      }
      row.push(newCell);
    }
    newBoard.push(row);
  }
  return newBoard;
}

/* ==============================
   イベントリスナー設定
   ============================== */
document.getElementById("resetBtn").addEventListener("click", () => {
  initBoard();
});

document.getElementById("stepBtn").addEventListener("click", () => {
  stepCommand();
});

// ★ 1手戻す
document.getElementById("stepBackBtn").addEventListener("click", () => {
  stepBack();
});

// ★ 自動再生
document.getElementById("playBtn").addEventListener("click", () => {
  playCommands();
});

// ★ 一時停止
document.getElementById("stopBtn").addEventListener("click", () => {
  stopCommands();
});

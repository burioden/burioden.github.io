// グローバル変数
let N = 0; // 盤面サイズ
let M = 0; // 鉱石の種類数
let board = []; // 盤面2次元配列
let playerPos = { r: 0, c: 0 }; // プレイヤー位置

// コマンド管理
let commandIndex = 0;
let commandLines = [];

// スコア計算用
let initialOreCount = 0; // 盤面にある鉱石総数
let fallenCountByType = {}; // 鉱石が正しい穴に落ちた数 (種類ごと)

/**
 * 入力データを解析して盤面を初期化する
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
  // もし入力が足りない場合は空文字列を補完
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
        // プレイヤー初期位置を "A" に合わせる (必要があれば別の大文字でもOK)
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
      // オブジェクト
      if (cell.obj) {
        if (cell.obj.type === "rock") {
          cellDiv.classList.add("rock");
          content = "🪨";
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
  if (nr < 0 || nr >= N || nc < 0 || nc >= N) return; // 範囲外

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
 *   - 壁 or 岩 or 鉱石がある場合は手前で停止
 *   - 穴なら落下
 * ★転がす動作においては、自分自身は移動しないで、岩・鉱石だけが、他の鉱石・岩・壁に当たる手前まで移動する。
 *
 */
function roll(direction) {
  const offset = dirOffsets[direction];
  if (!offset) return;

  const cell = board[playerPos.r][playerPos.c];
  if (!cell.obj) return;

  const movingObj = cell.obj;
  cell.obj = null;

  let curR = playerPos.r;
  let curC = playerPos.c;

  while (true) {
    const nextR = curR + offset.dr;
    const nextC = curC + offset.dc;

    // 範囲外 or 次マスにオブジェクトがある -> 手前で停止
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
    // 次マスが穴なら落下
    if (board[nextR][nextC].hole) {
      fallIntoHole(board[nextR][nextC].hole, movingObj);
      break;
    }
    // さらに進める
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
  renderBoard();
}

/**
 * Stepボタン: 1コマンドだけ実行 (コマンドは消さない)
 */
function stepCommand() {
  if (commandIndex < commandLines.length) {
    processCommand(commandLines[commandIndex]);
    commandIndex++;
  }
}

/**
 * Playボタン: コマンドを自動実行し、終了後にスコア計算
 */
function playCommands() {
  function step() {
    if (commandIndex < commandLines.length) {
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
    // 鉱石がない場合は 0 としておく
    score = 0;
  } else if (A === K) {
    // A = K
    // score = round(10^6 * (1 + log2(10000/T)))
    if (T === 0) {
      // コマンドなしで全鉱石が穴に落ちる状況はほぼ無いが、一応ガード
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

// イベント設定
document.getElementById("resetBtn").addEventListener("click", () => {
  initBoard();
});
document.getElementById("stepBtn").addEventListener("click", () => {
  stepCommand();
});
document.getElementById("playBtn").addEventListener("click", () => {
  playCommands();
});
// ★ 一つ手前に戻るコマンドを追加 html ではすでにボタン追加済み
// ★ 一時停止コマンドを追加 html ではすでにボタン追加済み

// ページ読み込み時、特に処理しない（手動で Reset して利用）

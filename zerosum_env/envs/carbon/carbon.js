// Copyright 2020 Kaggle Inc
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

async function renderer({
  parent,
  // The gamestep we're rendering, starting at 0 and going by default up to 399.
  step,
  // We render several frames within a step for animation, and use float values in [0, 1] range.
  // Rendering while the game is paused gives frame == 1.0.
  frame,
  // Optional list of agents which will render a legend with player names.
  agents,
  // update fn which lets us pass rendering info for `agents` for the legend.
  update,
  environment,
  width = 800,
  height = 600,
}) {
  // Configuration.
  const { size } = environment.configuration;
  const directions = ["UP", "RIGHT", "DOWN", "LEFT"];
  const state = environment.steps[step];
  const { carbon, players } = state[0].observation;

        const colors = {
          bg: "#000B49",
          bgGradient: "#000B2A",
          bgGradientTop: "#1486F8",
          bgGradientBottom: "#C0A9C8",
          players: ["#E2CD13", "#F24E4E", "#34BB1C", "#7B33E2"],
          workers: [
            [
              "#F1E61D",
              "#E2CD13",
              "#C0AE10",
              "#AA990E",
              "#716609",
              "#605708",
              "#161616",
            ],
            [
              "#F97575",
              "#F24E4E",
              "#CE4242",
              "#B63B3B",
              "#792727",
              "#672121",
              "#161616",
            ],
            [
              "#4BCF27",
              "#34BB1C",
              "#299516",
              "#268814",
              "#17560C",
              "#14470A",
              "#161616",
            ],
            [
              "#BA4DF2",
              "#7B33E2",
              "#692BC0",
              "#5C26AB",
              "#3D1971",
              "#341561",
              "#161616",
            ],
          ],
        };

  // Rectangle coordinates on a 20x20 grid, with ';' as separator.
  // Each entry is either a color or a list of [x, y, w, h, special, minFrame, maxFrame]
  // with default values of [0, 0, 1, 1, 0, 0, 1] if missing.  "special" is a bitmask
  // which indicates to swap across axes to help with mirroring common subimages.
  const rects = {
    worker: [
      "9.5,0;9,1;8,3,1,2;7,5,1,2;6,7,1,2;7,10,2;9,9",
      "9,2,2,7;8,5,4,2;7,7,6,2;6,9,1,3;13,9,1,3;10,9;9,10,4,3;7,11,2,2;9,13,2",
      "10,1;11,3,1,2;12,5,1,2;13,7,1,2;8,13;11,13;9,14,2;9.5,15",
      "5,9;4,10;3,11;2,12;1,13",
      "5,10;4,11,2;3,12,3;14,10;14,11,2;14,12,3",
      "2,13,3;14,9;15,10;16,11;17,12;15,13,4",
      "9.5,6;9,7,2;8,8,4;7,9,2;11,9,2;6,12;5,13,3;4,14,5;13,12;12,13,3;11,14,5",
    ],
    flame: [
      "#FF972E;5,15,3,1,4;6,16,1,1,4;4.5,15,4,1,4,0.33;5,16,3,1,4,0.33;6,17,1,1,4,0.33;4,15,5,2,4,0.66;5,17,3,1,4,0.66;6,18,1,1,4,0.66",
      "#FEF545;6,15,1,1,4;5.5,15,2,1,4,0.33;6,16,1,1,4,0.33;5,15,3,1,4,0.66;5.5,16,2,1,4,0.66;6,17,1,1,4,0.66",
      "#FFF5FF;6,15,1,1,4,0.66",
    ],
    recrtCenter: [
      "9,9,2,2;2,2,3,3,15;2,4,5,1,15;3,5,5,1,15;4,6,5,1,15",
      "#FFFFFF33;9,9,2,2,0,0.2;2,2,2,2,14;2,3,3,1,15;3,4,3,1,15;4,5,3,1,15;5,6,3,1,15;",
      "#FFFFFF66;9,9,2,2,0,0.4;6,6,1,1,14,0.6;5,5,1,1,14,0.7;4,4,1,1,14,0.8;3,3,1,1,14,0.9;2,2,1,1,14,1",
    ],
    explosion: [
      "#C84302BB;7,7,1,1,14;6,9,1,2,4;5,5,1,1,14,0.25;9,5,2,10,0,0.25;6,9,8,2,0,0.25;3,3,1,1,14,0.5;7,6,1,1,15,0.5;5,4,1,1,14,0.75;4,5,1,1,14,0.75;8,5,1,1,14,0.75;9,4,2,1,2,0.75;4,8,1,1,14,0.75;7,2,1,1,14,0.75;",
      "#FF972EBB;9,6,2,1,2;8,9,4,2;4,9,1,2,4,0.25,0.74;9,6,2,8,0,0.25;7,7,6,2,2,0.25;2,9,1,2,4,0.5;6,7,8,2,2,0.75;9,5,2,10,0,0.75;8,6,4,8,0,0.5;6,6,1,1,14,0.75;5,5,1,1,14,0.75;5,7,1,1,14,0.75;7,4,1,1,14,0.75;",
      "#FEF545BB;9,8,2,4;9,7,2,6,0,0.25;8,8,4,4,0,0.25;8,7,1,1,14,0.5;8,7,4,6,1,0.75;9,6,2,1,2,0.75;",
      "#FFF5FFBB;9,9,2,2;8,9,4,2,1,0.25;7,9,6,2,0,0.5;9,7,2,6,0,0.75",
    ],
    largeCarbon: [
      "#008DFF;17,6;2,13;9,1,2,18,1;5,7,10,6,1",
      "#00C9FF;9,3,2,14;3,9,14,2",
      "#00FFFF;6,2;13,17;4,9,12,2,1;7,7,6,6",
      "#FFFFFF;13,2;17,13;2,6;6,17;6,9,8,2,1",
    ],
    mediumCarbon: [
      "#008DFF;6,4;16,7;16,12;6,15;4,9,12,2,1;6,8,8,4,1",
      "#00C9FF;9,5,2,10,1;",
      "#00FFFF;13,4;3,7;3,12;13,15;9,6,2,8,1;8,8,4,4",
      "#FFFFFF;9,7,2,6,1",
    ],
    smallCarbon: [
      "#008DFF;13.5,6.5;13.5,12.5;9.5,5.5,1,9,1;8.5,6.5,3,7,1",
      "#00C9FF;9.5,6.5,1,7,1",
      "#00FFFF;5.5,6.5;5.5,12.5;9.5,7.5,1,5,1;8.5,8.5,3,3",
      "#FFFFFF;9.5,8.5,1,3,1",
    ],
  };

  // Helper Functions.
  const createElement = (type, id) => {
    const el = document.createElement(type);
    el.id = id;
    parent.appendChild(el);
    return el;
  };

  const getImagePath = () => {
    let dir = 'https://ai-studio-match-dist.cdn.bcebos.com/spdb/zerosum_env/static/src/';
        // 如果路径包含srcdoc，则认为是ipython，否则是html

        return dir;
  }

const createImage = (id) => {
let img = document.querySelector(`#${id}`);
if(!img){
  img = new Image();
  const dir = getImagePath();
      // console.log(dir)
      img.id = id;
      img.src = dir + id + '.svg';
      img.style.cssText = `display: none;`;
      parent.appendChild(img);
    }
  }

  const getCanvas = (id, options = { clear: false, alpha: false }) => {
    let canvas = document.querySelector(`#${id}`);
    if (!canvas) {
      canvas = createElement("canvas", id);
      canvas.width = options.width || width;
      canvas.height = options.height || height;
      canvas.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%; 
      `;
      const image = getImagePath() + 'bg.png';
      canvas.style.cssText =
          id === 'foreground'?
              canvas.style.cssText +
              `background: url(${image}); 
        background-repeat:no-repeat;
        background-position:50% 100%;`
          :
          canvas.style.cssText
    }
    const ctx = canvas.getContext("2d", { alpha: options.alpha });
    if (options.clear) ctx.clearRect(0, 0, canvas.width, canvas.height);
    return [canvas, ctx];
  };

  const data = function(selector, key, value) {
    const el =
      typeof selector === "string"
        ? document.querySelector(selector)
        : selector;
    if (arguments.length === 3) {
      el.setAttribute(`data-${key}`, JSON.stringify(value));
      return value;
    }
    if (el.hasAttribute(`data-${key}`)) {
      return JSON.parse(el.getAttribute(`data-${key}`));
    }
    return null;
  };

  const move = (ctx, options = {}, fn) => {
    const { x, y, width, height, angle, scale } = {
      x: 0,
      y: 0,
      width: 100,
      height: 100,
      angle: 0,
      ...options,
    };
    ctx.save();
    ctx.translate(x, y);
    if (scale) ctx.scale(scale, scale);
    if (angle) {
      ctx.translate(width / 2, height / 2);
      ctx.rotate((Math.PI * angle) / 180);
      ctx.translate(-width / 2, -height / 2);
    }
    fn();
    ctx.restore();
  };

  const drawRects = (
    ctx,
    rects,
    color,
    scale = 1,
    gridSize = 20,
    drawFrame = -1
  ) => {
    if (drawFrame == -1) drawFrame = frame;
    // rects="x,y,w,h,specials,minFrame,maxFrame;..."
    ctx.save();
    if (color) ctx.fillStyle = color;
    ctx.beginPath();
    const drawSpecials = (x, y, w, h, special) => {
      const size = gridSize * scale;
      if ((special & 1) === 1) ctx.rect(y, x, h, w); // swap x/y and w/h
      if ((special & 2) === 2) ctx.rect(x, size - y - h, w, h); // Mirror over X Axis
      if ((special & 4) === 4) ctx.rect(size - x - w, y, w, h); // Mirror over Y Axis
      if ((special & 8) === 8) ctx.rect(size - x - w, size - y - h, w, h); // Mirror over X & Y Axis
      // Repeat mirroring if a swap occurred.
      if ((special & 1) === 1) drawSpecials(y, x, h, w, special - 1);
    };
    rects
      .replace(/\s/g, "")
      .split(";")
      .filter(r => !!r)
      .forEach(coords => {
        // Apply a fill style.
        if (coords[0] == "#" || coords[0] == "r") {
          ctx.fillStyle = coords;
          return;
        }
        const defaultCoords = ["0", "0", "1", "1", "0", "0", "1"];
        coords = coords.split(",");
        let [x, y, w, h, special, minFrame, maxFrame] = defaultCoords.map(
          (v, i) =>
            parseFloat(coords.length > i ? coords[i] : v) * (i < 4 ? scale : 1)
        );
        if (minFrame > drawFrame || maxFrame < drawFrame) return;
        ctx.rect(x, y, w, h);
        drawSpecials(x, y, w, h, special);
      });
    ctx.fill();
    ctx.closePath();
    ctx.restore();
  };

  const getColRow = pos => [pos % size, Math.floor(pos / size)];

  const getMovePos = (pos, direction) => {
    const [col, row] = getColRow(pos);
    switch (direction) {
      case "UP":
        return pos >= size ? pos - size : Math.pow(size, 2) - size + col;
      case "DOWN":
        return pos + size >= Math.pow(size, 2) ? col : pos + size;
      case "RIGHT":
        return col < size - 1 ? pos + 1 : row * size;
      case "LEFT":
        return col > 0 ? pos - 1 : (row + 1) * size - 1;
      default:
        throw new Error(`"${direction}" is not a valid move action.`);
    }
  };

  const getCoords = pos => {
    const [col, row] = getColRow(pos);
    return {
      col,
      row,
      scale: cellScale * cellInset,
      dx: xOffset + cellSize * col + (cellSize - cellSize * cellInset) / 2,
      dy: yOffset + cellSize * row + (cellSize - cellSize * cellInset) / 2,
      ds: cellScale * cellInset * fixedCellSize,
      ss: fixedCellSize,
    };
  };

  const getWorkerDir = (playerIndex, uid) => {
    for (let s = step; s >= 0; s--) {
      const action = environment.steps[s][playerIndex].action || {};
      if (uid in action) return Math.max(directions.indexOf(action[uid]), 0);
    }
    for (let s = step + 1; s < environment.steps.length; s++) {
      const action = environment.steps[s][playerIndex].action || {};
      if (uid in action) return Math.max(directions.indexOf(action[uid]), 0);
    }
    return 0;
  };

  // First time setup.
  for (const imgName of [
      'chessboard', 'carbon',
      'blue_tree', 'blue_center', 'blue_collector', 'blue_defense', 'blue_planter', 'blue_collector_tree',
      'red_tree', 'red_center', 'red_collector', 'red_defense', 'red_planter', 'red_collector_tree',
      'left_info',  'left_avatar', 'left_name',
      'right_info', 'right_avatar', 'right_name',
      'smile', 'sad'
    ]) {
      createImage(imgName);
    }

  if (!parent.querySelector("#background")) {
    // console.time('pre-rerender')
    const [bgCanvas, ctx] = getCanvas("background", {
      alpha: true,
      clear: false,
    });

          // Setup common fields.
          const cellInset = 0.8;
          const fixedCellSize = 100;
          const minOffset = Math.min(height, width) > 400 ? 30 : 4;
          const cellSize = Math.min(
            (width - minOffset * 7) / size,
            (height - minOffset *7) / size
          );

    data(bgCanvas, "storage", {
      cellInset,
      cellScale: cellSize / fixedCellSize,
      cellSize,
      fixedCellSize,
      xOffset: Math.max(0, (width - cellSize * size) / 2),
      yOffset: (height - cellSize * size) / 2 > 1.2*cellSize + 50 ? (height - cellSize * size) / 2 : 1.2*cellSize + 5 // 边距>42时取平均边距， 否则顶部身为最小

    });
  }
        // Restore Canvases.
        const [bgCanvas, bgCtx] = getCanvas("background", {
          alpha: true,
          clear: false,
        });
        const [, fgCtx] = getCanvas("foreground", {
          alpha: true,
          clear: true,
        });

  // Expand storage.
  const {
    cellInset,
    cellScale,
    cellSize,
    fixedCellSize,
    xOffset,
    yOffset,
  } = data(bgCanvas, "storage");

  const topLeftCell = getCoords(0);
  const botRightCell = getCoords(size * size - 1);

  // 绘制二氧化碳
  const renderCarbon = (ctx, pos, carbon, maxCarbon, scaleFactor, rotate) => {
    // console.log("card",carbon);
    if (carbon <= 0) return;

    let { dx, dy, ds, ss } = getCoords(pos);
    let sx = 0;
    let sy = 0;

    const pct = Math.min(1, carbon / maxCarbon);
    let scale = 1;

    // Scale by the carbon size.
    // if (pct > 0.7) {
    //   scale = pct;
    // } else
      if (pct > 0.3) {
      sy = 100;
      scale = pct;
    } else {
      sy = 200;
      scale = 0.3;
    }

    // Apply the scale.
    scale = Math.max(0.3, scaleFactor * scale);
    dx += (ds - ds * scale) / 2;
    dy += (ds - ds * scale) / 2;
    ds *= scale;

    let img = document.getElementById("carbon");
    ctx.drawImage(img, dx, dy, ds, ds);
    // TODO:测试代码，交付时需删除
    ctx.fillText(carbon,dx, dy,)
    // Rotate the carbon to get a bit of randomness, if desired.
    // move(
    //   ctx,
    //   { x: dx, y: dy, width: ds, height: ds, angle: rotate ? carbonRotations[pos] : 0 },
    //   // () => ctx.drawImage(bufferCanvas, sx, sy, ss, ss, 0, 0, ds, ds)
    //   ()=>{

    //   }
    // );
  }

  // Render Background once per step (Gradient + Carbon)
  const boxPadding = height * 0.007;
  if ((step==0) || data(bgCanvas, "step") !== step) { // 会造成首帧棋盘不展示
    // console.time('render bg')
    data(bgCanvas, "step", step);
    // bgCtx.fillStyle = colors.bg;
    // bgCtx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);

          // const r = Math.min(height, width) / 2;
          // const bgStyle = bgCtx.createRadialGradient(r, r, 0, r, r, r); // 环形渐变
          // 绘制背景线性渐变
          const bgStyle = bgCtx.createLinearGradient(0, 0, 0, height);  // 线性渐变

          bgStyle.addColorStop(0, colors.bgGradientTop);
          bgStyle.addColorStop(1, colors.bgGradientBottom);

          bgCtx.fillStyle = bgStyle;
          bgCtx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);

          // 通过SVG绘制棋盘格
          let ChessboardX = topLeftCell.dx - boxPadding  // 左上角起始横坐标
          let ChessboardY = topLeftCell.dy - boxPadding  // 左上角起始纵坐标
          let ChessboardWidth = (botRightCell.dx + botRightCell.ds - topLeftCell.dx + 2 * boxPadding) / size // 棋盘格子宽度
          let ChessboardHeight = (botRightCell.dy + botRightCell.ds - topLeftCell.dy + 2 * boxPadding) / size // 棋盘格子高度


          let img = document.getElementById("chessboard");
          bgCtx.drawImage(img, ChessboardX - ChessboardWidth * 1.2, ChessboardY - ChessboardHeight * 1.2, ChessboardWidth * (size + 2.4), ChessboardHeight * (size + 2.4));

          // canvas绘制方法
          // bgCtx.strokeStyle = "red";   //"#628ed7"
          // bgCtx.lineWidth = 0.02
          //  ChessboardX = topLeftCell.dx - boxPadding  // 左上角起始横坐标
          //  ChessboardY = topLeftCell.dy - boxPadding  // 左上角起始纵坐标
          // // let ChessboardWidth = boxPadding+topLeftCell.ds+0.5 // 棋盘宽度
          // // let ChessboardHeight = boxPadding+topLeftCell.ds+0.5 // 棋盘高度
          //  ChessboardWidth = (botRightCell.dx + botRightCell.ds - topLeftCell.dx + 2 * boxPadding) / size
          //  ChessboardHeight = (botRightCell.dy + botRightCell.ds - topLeftCell.dy + 2 * boxPadding) / size

          // // 绘制纵向棋盘格
          // for (let i = 1; i < size; i++) {
          //   bgCtx.moveTo(ChessboardX + i * ChessboardWidth, ChessboardY)
          //   bgCtx.lineTo(ChessboardX + i * ChessboardWidth, ChessboardY + size * ChessboardHeight)
          //   bgCtx.stroke();
          // }
          // // 绘制横向棋盘格
          // for (let i = 1; i < size; i++) {
          //   bgCtx.moveTo(ChessboardX, ChessboardY + i * ChessboardWidth)
          //   bgCtx.lineTo(ChessboardX + size * ChessboardWidth, ChessboardY + i * ChessboardHeight)
          //   bgCtx.stroke();
          // }

          // // Render bounding box.
          // bgCtx.strokeStyle = "white";
          // bgCtx.lineWidth = 0.5;
          // bgCtx.strokeRect(
          //   topLeftCell.dx - boxPadding,
          //   topLeftCell.dy - boxPadding,
          //   botRightCell.dx + botRightCell.ds - topLeftCell.dx + 2 * boxPadding,
          //   botRightCell.dy + botRightCell.ds - topLeftCell.dy + 2 * boxPadding);

          // Render the carbon 绘制二氧化碳
          carbon.forEach((cellCarbon, pos) => renderCarbon(bgCtx, pos, cellCarbon, 100, 1, true));
          // console.timeEnd('render bg')
        }

  // Render Foreground (every frame).

  // Draw RecrtCenters.
  // players.forEach((player, playerIndex) => {
  //   Object.values(player[1]).forEach(pos => {
  //     const workerx = 500 + 100 * playerIndex;
  //     const ss = fixedCellSize;
  //     const { dx, dy, ds } = getCoords(pos);
  //     fgCtx.drawImage(bufferCanvas, workerx, 400, ss, ss, dx, dy, ds, ds);
  //   });
  // });

  // Draw Workers and a smaller Carbon icon according to their current cargo.
  let tree_img = [document.getElementById("blue_tree"), document.getElementById("red_tree")]
  let collector_img = [document.getElementById("blue_collector"), document.getElementById("red_collector")]
  let planter_img = [document.getElementById("blue_planter"), document.getElementById("red_planter")]
  let recrtCenter_img = [document.getElementById("blue_center"), document.getElementById("red_center")]
  let defense_img = [document.getElementById("blue_defense"), document.getElementById("red_defense")]
  let collector_tree_img = [document.getElementById("blue_collector_tree"), document.getElementById("red_collector_tree")]

  // 绘制转化中心、树、捕碳员、种树员、人树合一
  const renderFigure = (players)=>{
    let flag = {};
    let rectCenter = [],
      workers = [],
      trees = [],
      defenses = [];

    // 数据处理
    players.forEach((player, playerIndex) => {
      for (const rectCenter_id in player[1]) {
        rectCenter.push({playerIndex, pos: player[1][rectCenter_id]})
      }

      // 以下标为key，标记各树和人的位置
      for (const worker_id in player[2]) {
        const worker_pos = player[2][worker_id][0];
        if (worker_pos in flag) {
          flag[worker_pos]["worker"] = {playerIndex, pos: worker_pos, role: player[2][worker_id][2]};
        } else {
          flag[worker_pos] = {
            worker: {playerIndex, pos: worker_pos, role: player[2][worker_id][2]},
          };
        }
      }
      for (const tree_id in player[3]) {
        const tree_pos = player[3][tree_id][0];
        if (tree_pos in flag) {
          flag[tree_pos]["tree"] = { playerIndex, pos: tree_pos };
        } else {
          flag[tree_pos] = { tree: { playerIndex, pos: tree_pos } };
        }
      }
    });
    // 从标记数组中获取人、树、人树
    for (const flagKey in flag){
      let flag_worker = flag[flagKey]["worker"], flag_tree = flag[flagKey]["tree"];
      if (flag_worker && flag_tree ) {
        if ( flag_worker["playerIndex"] == flag_tree["playerIndex"]){ // 同一玩家的树和人，单个守卫图标
          defenses.push(flag_worker);
        } else { // 不同玩家的树和人，树图标和人图标叠加
          workers.push(flag_worker);
          trees.push(flag_tree);
        }
      } else if (flag_worker) {
        workers.push(flag_worker);
      } else if (flag_tree) {
        trees.push(flag_tree);
      }
    }
    // 绘制转化中心
    rectCenter.forEach(({ playerIndex, pos }) => {
      const { dx, dy, ds } = getCoords(pos);
      fgCtx.drawImage(recrtCenter_img[playerIndex], dx, dy, ds, ds); // 根据playerIndex绘制蓝/红队树木元素
    })
    // 绘制人树合一
    defenses.forEach(({ playerIndex, pos, role }) => {
      const { dx, dy, ds } = getCoords(pos);
      if (role == "COLLECTOR") {
        // 绘制 捕碳员和树 元素
        fgCtx.drawImage(collector_tree_img[playerIndex], dx, dy, ds, ds);
      } else {
        // 绘制 种树员和树 元素
        fgCtx.drawImage(defense_img[playerIndex], dx, dy, ds, ds); // 根据playerIndex绘制蓝/红队守卫元素
      }
    });

    // 绘制树
    trees.forEach(({ playerIndex, pos }) => {
      const { dx, dy, ds } = getCoords(pos);
      fgCtx.drawImage(tree_img[playerIndex], dx, dy, ds, ds); // 根据playerIndex绘制蓝/红队树木元素
    });
    // 绘制人
    workers.forEach(({ playerIndex, pos, role }) => {
      const { dx, dy, ds } = getCoords(pos);
      if (role == "COLLECTOR") {
        // 绘制捕碳员
        fgCtx.drawImage(collector_img[playerIndex], dx, dy, ds, ds);
      } else {
        // 绘制种树员
        fgCtx.drawImage(planter_img[playerIndex], dx, dy, ds, ds);
      }
    });
  }

  renderFigure(players);

        // Draw collisions.
  //       if (step > 0) {
  //         const board = Array(size * size)
  //           .fill(0)
  //           .map(() => ({ recrtCenter: -1, worker: null, collision: false }));
  //         players.forEach((player, playerIndex) => {
  //           const [, recrtCenters, workers] = player;
  //           Object.values(recrtCenters).forEach(
  //             pos => (board[pos].recrtCenter = playerIndex)
  //           );
  //           Object.entries(workers).forEach(([uid, [pos]]) => (board[pos].worker = uid));
  //         });
  //         environment.steps[step - 1][0].observation.players.forEach(
  //           (player, playerIndex) => {
  //             const status = state[playerIndex].status;
  //             const [, recrtCenters, workers] = player;
  //             const action = environment.steps[step][playerIndex].action || {};
  //             // Stationary workers collecting Carbon.
  //             Object.entries(workers).forEach(([uid, [pos]]) => {
  //               if (uid in action) return;
  //               if (board[pos].worker !== uid) board[pos].collision = true;
  //             });
  //             // Convert to recrtCenter, Spawn worker, or Move worker.
  //             Object.entries(action).forEach(([uid, value]) => {
  //               if (value !== "RECPLANTER" && value !== "RECCOLLECTOR") {
  //                 const toPos = getMovePos(workers[uid][0], value);
  //                 if (board[toPos].worker !== uid) board[toPos].collision = true;
  //               }
  //             });
  //           }
  //         );
  //
  //   board.forEach(({ collision }, pos) => {
  //     if (!collision) return;
  //     const { dx, dy, ds, ss } = getCoords(pos);
  //     const sx = 100;
  //     const sy = 100 * Math.round(4 * (1 - frame));
  //     fgCtx.drawImage(bufferCanvas, sx, sy, ss, ss, dx, dy, ds, ds);
  //   });
  // }

  const scoreboardFontSizePx = Math.round(height / 36);
  const scoreboardPaddingPx = Math.max(1, scoreboardFontSizePx / 4);
  const scoreboardLineYDiffPx = scoreboardFontSizePx + scoreboardPaddingPx;

  const getFortune = player => player[0];
  const getCargo = player => Object.entries(player[2]).map(([, v]) => v[1]).reduce((a, b) => a + b, 0);
  const getNumWorkers = player => Object.entries(player[2]).length;
  const getNumRecrtCenters = player => Object.entries(player[1]).length;
  /**
   * histogram rendering according to parameters
   * 
   * @param {*} ctx canvas 
   * @param {*} x   index_x
   * @param {*} y   index_y
   * @param {*} w   the width of histogram
   * @param {*} h   the height of histogram
   * @param {*} status the status of icon (smile/sad)
   * @param {*} color the color of histogram (blue/orange)
   * @param {*} coef the coefficient of log function
   * @param {*} trans the transparency of border (0 to 1)
   */
   const drawHistogram = (ctx, x, y, w, h, status, color, coef, trans) => {
    // storage of money
    let money = h.toFixed(2)
    // padding top
    let limitHeight = bgCanvas.height - 50
    
    let linearNum = 10000

    // coz 0 has no logarithm
    if (h >= linearNum) {
      h = h - linearNum + 1
      // Use logarithmic curve to draw histogram
      h = limitHeight / 3 + (Math.log10(h) / Math.log10(coef)) ** 3 * 5
    } else if(h > 0 && h < linearNum){
      h = h * ((limitHeight / 3) / linearNum)
    } else {
      h = 0
    }
    // parrtern height 
    h += w
    // limit height
    if(h > limitHeight){
      h = limitHeight
    }
    // number
    ctx.fillStyle = "#FFFFFF";
    let moyLen = money.toString().length > 2 ? money.toString().length - 2 : 0
    ctx.font = w * 0.4 - moyLen * 1.5 + "px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(money + "万", x + w / 2, y - h - w * 0.6 + moyLen * 1.5)

    // histogram
    ctx.beginPath();
    ctx.lineWidth = 0;
    ctx.moveTo(x, y);
    ctx.lineTo(x, y - h);
    ctx.lineTo(x + w * 0.1, y - h - w * 0.1)
    ctx.lineTo(x + w * 0.9, y - h - w * 0.1)
    ctx.lineTo(x + w, y - h);
    ctx.lineTo(x + w, y);
    ctx.lineTo(x, y)
    
    // set gradient
    var grd=ctx.createLinearGradient(x,y,x,y-h);

    if(color === "blue"){
      grd.addColorStop(0,"#6172FF");
      grd.addColorStop(1,"#53D6FF");
    }

    if(color === "orange"){
      grd.addColorStop(0,"#FF6161");
      grd.addColorStop(1,"#FFAB53");
    }

    ctx.fillStyle = grd;
    ctx.fill();
    ctx.globalAlpha = trans;
    ctx.stroke();
    ctx.closePath();
    ctx.globalAlpha = 1;

    // set status ( smile or sad)
    if(status === "smile"){
      const smile = document.getElementById('smile');
      ctx.drawImage(smile, x + w * 0.2, y - w * 0.8, w * 0.66, w * 0.66)
    }

    if(status === "sad"){
      const sad = document.getElementById('sad');
      ctx.drawImage(sad, x + w * 0.2, y - w * 0.8, w * 0.66, w * 0.66)
    }

    // back up color
    ctx.fillStyle = "#FFFFFF";

  }

  const scoreboardWorkerSizePx = scoreboardFontSizePx * 1.7;
  // const drawWorker = (ctx, playerIndex, x, y, iconSize = scoreboardWorkerSizePx) => ctx.drawImage(
  //   bufferCanvas, 500 + 100 * playerIndex, 0, fixedCellSize, fixedCellSize,
  //   x, y, iconSize, iconSize);
  // const drawWorkerYard = (ctx, playerIndex, x, y, iconSize = scoreboardWorkerSizePx) => ctx.drawImage(
  //   bufferCanvas, 500 + 100 * playerIndex, 400, fixedCellSize, fixedCellSize,
  //   x, y, iconSize, iconSize);

  const scoreboardWorkerXPaddingPx = scoreboardWorkerSizePx + scoreboardPaddingPx;
  // const drawWorkerAndYardCounts = (ctx, player, playerIndex, x, y, iconSize = scoreboardWorkerSizePx) => {
  //   drawWorker(ctx, playerIndex, x, y);
  //   ctx.fillText(`x ${getNumWorkers(player)}`, x + scoreboardWorkerXPaddingPx, y + 0.28 * iconSize);
  //   drawWorkerYard(ctx, playerIndex, x, y + iconSize);
  //   ctx.fillText(`x ${getNumRecrtCenters(player)}`, x + scoreboardWorkerXPaddingPx, y + 1.38 * iconSize);
  // }

  // 绘制信息栏
  const drawContent = (ctx, x, y, w, h, flag, info) => {
    const coefficient = 1.2; // 补偿系数
    const textSpacing = h * 0.1629; // 文字间距
    const upFontPadding = h * 0.1561; // 文字的上边距
    const leftFontPadding = w * 0.0786; // 文字的左边距
    const fontSize = w * 0.0693 * coefficient; // 字体大小

    ctx.font = `normal ${fontSize}px sans-serif`;
    if (flag === 'left') {
      const img = document.getElementById("left_info");
      ctx.drawImage(img, x, y, w, h);
      ctx.fillText(`资金：${info.fund.toFixed(2)}万`, x + leftFontPadding, y + upFontPadding);
      ctx.fillText(`树：${info.tree}棵`, x + leftFontPadding, y + upFontPadding + textSpacing);
      ctx.fillText(`种树员：${info.treePlanter}人`, x + leftFontPadding, y + upFontPadding + 2 * textSpacing);
      ctx.fillText(`捕碳员：${info.carbonCatcher}人`, x + leftFontPadding, y + upFontPadding + 3 * textSpacing);
      ctx.fillText(`在途CO2数量：${info.CO2num.toFixed(2)}万吨`, x + leftFontPadding, y + upFontPadding + 4 * textSpacing);
    } else if (flag === 'right') {
      ctx.save();
      const img = document.getElementById("right_info");
      ctx.drawImage(img, x, y, w, h);
      ctx.textAlign = 'right';
      ctx.fillText(`资金：${info.fund.toFixed(2)}万`, x + w - leftFontPadding, y + upFontPadding);
      ctx.fillText(`树：${info.tree}棵`, x + w - leftFontPadding, y + upFontPadding + textSpacing);
      ctx.fillText(`种树员：${info.treePlanter}人`, x + w - leftFontPadding, y + upFontPadding + 2 * textSpacing);
      ctx.fillText(`捕碳员：${info.carbonCatcher}人`, x + w - leftFontPadding, y + upFontPadding + 3 * textSpacing);
      ctx.fillText(`在途CO2数量：${info.CO2num.toFixed(2)}万吨`, x + w - leftFontPadding, y + upFontPadding + 4 * textSpacing);
      ctx.restore();
    }
  }

  // 绘制头像框
  const drawLogo = (ctx, x, y, w, flag) => {
    let img;
    if (flag === 'left') {
      img = document.getElementById("left_avatar");
    } else if (flag === 'right') {
      img = document.getElementById("right_avatar");
    }
    ctx.drawImage(img, x, y, w, w);
  }

  // 绘制名称栏
  const drawTeam = (ctx, x, y, w, h, flag, name) => {
    const coefficient = 1.2; // 补偿系数
    const fontSize = w * 0.1625 * coefficient; // 字体大小

    ctx.font = `normal ${fontSize}px sans-serif`;
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    if (flag === 'left') {
      const img = document.getElementById("left_name");
      ctx.drawImage(img, x, y, w, h);
      ctx.fillText(`${name}`, x + w / 2, y + h / 2);
    } else if (flag === 'right') {
      const img = document.getElementById("right_name");
      ctx.drawImage(img, x, y, w, h);
      ctx.fillText(`${name}`, x + w / 2, y + h / 2);
    }
    ctx.restore();
  }

  const getPlayerInfo = (player) => {
    const planterStr = "PLANTER"; 
    const collectorStr = "COLLECTOR";
    let treePlanter = 0;
    let carbonCatcher = 0;
    let CO2num = 0;
    const fund = player[0];
    const tree = Object.entries(player[3]).length;
    Object.entries(player[2]).map(([, v]) => {
      if (v[2] === planterStr) {
        treePlanter++;
        CO2num += v[1];
      } else if (v[2] === collectorStr) {
        carbonCatcher++;
        CO2num += v[1];
      }
    });
    return {
      fund,
      tree,
      treePlanter,
      carbonCatcher,
      CO2num
    }
  }

  // 绘制选手信息
  const drawPlayerInfo = () => {
    const cellSize = botRightCell.ds; // 单元格宽度
    const cWidth = botRightCell.dx + botRightCell.ds - topLeftCell.dx + 2 * boxPadding; // 棋盘宽度
    const coefficient = 1.2; // 补偿系数
    const threshold = cellSize; // 阈值

    const tx = topLeftCell.dx - boxPadding - cWidth * 0.6768; // 左侧队伍名称框起始位置横坐标
    const ty = topLeftCell.dy + cWidth * 0.583; // 队伍名称框起始位置纵坐标
    const th = cWidth * 0.0809 * coefficient; // 队伍名称框高度
    const tw = th * (160 / 63); // 队伍名称框宽度
    const txr = botRightCell.dx + boxPadding + cellSize + cWidth * 0.6768 - tw; // 右侧队伍名称框起始位置横坐标

    const cx = tx + cWidth * 0.0202; // 左侧内容框起始位置横坐标
    const cy = ty + cWidth * 0.0613 * coefficient; // 内容框起始位置纵坐标
    const ch = cWidth * 0.188 * coefficient; // 内容框高度
    const cw = ch * (202 / 143); // 内容框宽度
    const cxr = txr + tw - cWidth * 0.0202 - cw; // 右侧内容框起始位置横坐标

    const lx = tx + cWidth * 0.03; // 左侧头像框起始位置横坐标
    const ly = ty - cWidth * 0.1253 * coefficient; // 头像框起始位置纵坐标
    const lw = cWidth * 0.1044 * coefficient; // 头像框宽度
    const lxr = txr + tw - cWidth * 0.03 - lw; // 右侧头像框起始位置横坐标

    if (tx > threshold) {
      fgCtx.fillStyle = "#FFFFFF";
      fgCtx.lineWidth = 2;
      fgCtx.textBaseline = "top";
      fgCtx.textAlign = "left";

      players.forEach((player, playerIndex) => {
        const info = getPlayerInfo(player);
        if (playerIndex === 0) {
          drawContent(fgCtx, cx, cy, cw, ch, 'left', info);
          drawLogo(fgCtx, lx, ly, lw, 'left');
          drawTeam(fgCtx, tx, ty, tw, th, 'left', '队伍A');
        } else if (playerIndex === 1) {
          drawContent(fgCtx, cxr, cy, cw, ch, 'right', info);
          drawLogo(fgCtx, lxr, ly, lw, 'right');
          drawTeam(fgCtx, txr, ty, tw, th, 'right', '队伍B');
        }
      });
    }
  }

  // Render Scoreboard for each player, if we have enough room on the sides of the window.
  if (width / height >= 1.3) {
    fgCtx.fillStyle = "#FFFFFF";
    const boardw = botRightCell.dx + botRightCell.ds - topLeftCell.dx + 2 * boxPadding; // the width of board
    const hmxl = topLeftCell.dx - boxPadding - boardw * 0.25; // index_x of left histogram 
    const hmy = bgCanvas.height; // index_y of histogram
    const hmw = boardw * 0.1; // histogram width
    const hmxr = topLeftCell.dx - boxPadding + boardw + boardw * 0.15; // index_x of right histogram 
    const coefhm = 10; // coefficient of histogram
    const leftColor = "blue"; // color of left histogram
    const rightColor = "orange"; // color of right histogram
    const trans = 0 // transparency

    // let lftFn = -1; // left histogram fortune
    // let rgtFn = -1;  // right histogram fortune 

    // players.forEach((player, playerIndex) => {
    //   fgCtx.font = `normal ${scoreboardFontSizePx}px sans-serif`;
      // record fortune for each player
      // if(playerIndex % 2 === 1){
      //   rgtFn = getFortune(player)
      // } else {
      //   lftFn = getFortune(player)
      // }
    // });

    let lftFn = state[0].reward; // left histogram fortune
    let rgtFn = state[1].reward; // right histogram fortune 

    // draw right histogram
    rgtFn >= lftFn ? drawHistogram(fgCtx, hmxr, hmy, hmw, rgtFn, "smile", rightColor, coefhm, trans) : drawHistogram(fgCtx, hmxr, hmy, hmw, rgtFn, "sad", rightColor, coefhm, trans)
    // draw left histogram
    lftFn >= rgtFn ? drawHistogram(fgCtx, hmxl, hmy, hmw, lftFn, "smile", leftColor, coefhm, trans) : drawHistogram(fgCtx, hmxl, hmy, hmw, lftFn, "sad", leftColor, coefhm, trans)

    drawPlayerInfo();
  }
}

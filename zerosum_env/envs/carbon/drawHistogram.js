/**
 * histogram rendering according to parameters
 * 
 * @param {*} ctx   Canvas
 * @param {*} x     index_x
 * @param {*} y     index_y
 * @param {*} w     width
 * @param {*} h     height
 * @param {*} gc    growth coefficient
 */
const drawHistogram = (ctx, x, y, w, h, gc = 15) => {
  // storage of money
  let money = h
  // coz 0 has no logarithm
  if (h > 0) {
    // Use logarithmic curve to draw histogram
    h = Math.log(h) * gc
  }
  // parrtern height 
  h += w
  // number
  ctx.fillStyle = "#FFFFFF";
  ctx.font = w / 2.5 + "px sans-serif";
  ctx.fillText(money + "万", x + w / 10, y - h - w * 0.6)

  // histogram
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x, y - h);
  ctx.lineTo(x + w / 10, y - h - w / 10)
  ctx.lineTo(x + w * 0.9, y - h - w / 10)
  ctx.lineTo(x + w, y - h);
  ctx.lineTo(x + w, y);
  ctx.strokeStyle = "72716c";
  ctx.stroke();
  ctx.fillStyle = "#a6a69c99";
  ctx.fill();
  ctx.stroke();
  ctx.closePath();

  // circle
  ctx.beginPath();
  ctx.arc(x + w / 2, y - w / 2, w * 0.3, 0, Math.PI * 2, true);
  ctx.strokeStyle = "000000";
  ctx.stroke();
  ctx.closePath();

  // internal circle
  ctx.beginPath();
  ctx.arc(x + w / 2, y - w / 2, w / 4, 0, Math.PI * 2, true);
  ctx.strokeStyle = "000000";
  ctx.stroke();
  ctx.closePath();

  // outside part of circle
  ctx.beginPath();
  ctx.arc(x + w / 2, y - w / 2.5, w * 0.3, Math.PI * 0.1, Math.PI * 0.875, false);
  ctx.strokeStyle = "000000";
  ctx.stroke();
  ctx.closePath();

  // internal line
  ctx.beginPath();
  ctx.moveTo(x + w / 3, y - w / 2);
  ctx.lineTo(x + w / 1.5, y - w / 2);
  ctx.stroke();
  ctx.closePath();

  // internel quarter circle
  ctx.beginPath();
  ctx.arc(x + w / 2, y - w / 2, w * 0.175, 0, Math.PI / 2, false);
  ctx.stroke();
  ctx.closePath();

  // vertical line 
  ctx.beginPath();
  ctx.moveTo(x + w / 3, y - w * 0.65);
  ctx.lineTo(x + w / 3 + w / 9, y - w * 0.6);
  ctx.lineTo(x + w / 3, y - w * 0.55);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 3 * 2, y - w * 0.65);
  ctx.lineTo(x + w / 3 * 2 - w / 9, y - w * 0.6);
  ctx.lineTo(x + w / 3 * 2, y - w * 0.55);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 2 - w / 25 * 7, y - w * 0.4);
  ctx.lineTo(x + w / 2 - w / 25 * 7, y - w * 0.29);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 3 * 2 + w / 25 * 3, y - w * 0.4);
  ctx.lineTo(x + w / 3 * 2 + w / 25 * 3, y - w * 0.29);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 2 - w / 5, y - w * 0.28);
  ctx.lineTo(x + w / 2 - w / 5, y - w * 0.19);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 3 * 2 + w / 25, y - w * 0.28);
  ctx.lineTo(x + w / 3 * 2 + w / 25, y - w * 0.19);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 2 - w * 0.12, y - w * 0.23);
  ctx.lineTo(x + w / 2 - w * 0.12, y - w * 0.13);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 3 * 2 - w / 25, y - w * 0.23);
  ctx.lineTo(x + w / 3 * 2 - w / 25, y - w * 0.13);
  ctx.stroke();
  ctx.closePath();

  ctx.beginPath();
  ctx.moveTo(x + w / 2, y - w / 5);
  ctx.lineTo(x + w / 2, y - w * 0.09);
  ctx.stroke();
  ctx.closePath();

}
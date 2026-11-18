// Draws the tug of war on a canvas. It only displays what the server reports.
const W = 960, H = 320, GROUND = 260, ROPE_Y = 205;
const SHIFT = 115;                       // how far the rope can move from the center, in pixels
const COLORS = { A: "#D6452D", B: "#2F6FD1" };
const CHALK = "#F2F5F0", TURF = "#27583F", ROPE = "#B98B4A";

export class Arena {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    canvas.width = W;
    canvas.height = H;
    this.me = null;
    this.reset([]);
    requestAnimationFrame((time) => this.frame(time));
  }

  reset(players, me = this.me) {
    this.players = players;
    this.me = me;
    this.target = 0;       // rope position from the server (-1 .. 1)
    this.shown = 0;        // smoothed position that is actually drawn
    this.wordsDone = {};
    this.pulse = {};       // 1 right after a player types a word, fades to 0
  }

  update(snapshot) {
    this.target = snapshot.rope;
    for (const [id, count] of Object.entries(snapshot.words_done)) {
      if (count > (this.wordsDone[id] ?? 0)) this.pulse[id] = 1;
      this.wordsDone[id] = count;
    }
  }

  frame(time) {
    if (this.canvas.offsetParent !== null) {   // skip drawing while the arena is hidden
      this.shown += (this.target - this.shown) * 0.12;
      for (const id in this.pulse) this.pulse[id] *= 0.9;
      this.draw(time / 1000);
    }
    requestAnimationFrame((next) => this.frame(next));
  }

  draw(seconds) {
    const ctx = this.ctx;
    ctx.fillStyle = TURF;
    ctx.fillRect(0, 0, W, H);
    this.drawField();

    const offset = -this.shown * SHIFT;       // rope toward A (+1) moves everything left
    const figures = [];
    for (const team of ["A", "B"]) {
      const side = team === "A" ? -1 : 1;
      this.players.filter((p) => p.team === team).forEach((player, i) => {
        const x = W / 2 + offset + side * (90 + i * 56);
        const lead = team === "A" ? this.shown : -this.shown;
        const lean = 0.35 + 0.25 * lead + 0.2 * (this.pulse[player.id] ?? 0);
        figures.push({ x, player, lean: lean + Math.sin(seconds * 12 + i) * 0.02, away: side, color: COLORS[team] });
      });
    }

    if (figures.length) {
      const xs = figures.map((f) => f.x);
      this.drawRope(Math.min(...xs), Math.max(...xs));
    }
    figures.forEach((f) => this.drawFigure(f));
    this.drawFlag(W / 2 + offset);
  }

  drawField() {
    const ctx = this.ctx;
    ctx.strokeStyle = CHALK;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, GROUND);
    ctx.lineTo(W, GROUND);
    ctx.stroke();
    ctx.setLineDash([8, 8]);                   // win lines
    for (const x of [W / 2 - SHIFT, W / 2 + SHIFT]) {
      ctx.beginPath();
      ctx.moveTo(x, 30);
      ctx.lineTo(x, GROUND);
      ctx.stroke();
    }
    ctx.setLineDash([]);
    ctx.fillStyle = CHALK;
    ctx.font = "600 13px 'Bricolage Grotesque', sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Red wins", W / 2 - SHIFT, 22);
    ctx.fillText("Blue wins", W / 2 + SHIFT, 22);
  }

  drawRope(left, right) {
    const ctx = this.ctx;
    ctx.strokeStyle = ROPE;
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(left, ROPE_Y);
    ctx.quadraticCurveTo((left + right) / 2, ROPE_Y + 8, right, ROPE_Y);
    ctx.stroke();
  }

  drawFlag(x) {
    const ctx = this.ctx;
    ctx.fillStyle = CHALK;
    ctx.fillRect(x - 1.5, ROPE_Y - 50, 3, 50);
    ctx.beginPath();
    ctx.moveTo(x + 1.5, ROPE_Y - 50);
    ctx.lineTo(x + 26, ROPE_Y - 42);
    ctx.lineTo(x + 1.5, ROPE_Y - 34);
    ctx.fill();
  }

  drawFigure({ x, player, lean, away, color }) {
    const ctx = this.ctx;
    const pulse = this.pulse[player.id] ?? 0;
    const hip = { x, y: GROUND - 34 };
    const shoulder = { x: x + away * lean * 44, y: hip.y - 46 };
    const line = (from, to) => { ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(to.x, to.y); ctx.stroke(); };

    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 6;
    ctx.lineCap = "round";
    line(hip, { x: x + away * 16, y: GROUND });               // back leg
    line(hip, { x: x - away * 14, y: GROUND });               // front leg
    line(hip, shoulder);                                      // body
    line(shoulder, { x: x - away * 20, y: ROPE_Y });          // arm to the rope
    ctx.beginPath();
    ctx.arc(shoulder.x + away * 6, shoulder.y - 14 - pulse * 3, 10, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = CHALK;
    ctx.font = `${player.id === this.me ? 700 : 500} 12px 'Bricolage Grotesque', sans-serif`;
    ctx.textAlign = "center";
    const name = player.name.length > 8 ? player.name.slice(0, 7) + "…" : player.name;
    ctx.fillText(name, shoulder.x, shoulder.y - 34);
  }
}

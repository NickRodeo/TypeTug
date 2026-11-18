// Thin wrapper around the browser WebSocket: JSON in, JSON out.
export class Socket {
  constructor(name, onMessage, onClose) {
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    this.ws = new WebSocket(`${scheme}://${location.host}/ws?name=${encodeURIComponent(name)}`);
    this.ws.onmessage = (event) => onMessage(JSON.parse(event.data));
    this.ws.onclose = onClose;
  }

  send(type, data = {}) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    }
  }
}

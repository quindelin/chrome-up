const WS_URL = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;

export class Net {
  constructor() {
    this.handlers = [];
    this.statusHandlers = [];
    this.connected = false;
    this.ws = null;
  }

  on(fn) { this.handlers.push(fn); }
  onStatus(fn) { this.statusHandlers.push(fn); }

  connect() {
    try {
      this.ws = new WebSocket(WS_URL);
    } catch (err) {
      this._status(false);
      setTimeout(() => this.connect(), 1500);
      return;
    }
    this.ws.onopen = () => this._status(true);
    this.ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        for (const fn of this.handlers) fn(data);
      } catch (err) { /* ignore malformed frame */ }
    };
    this.ws.onclose = () => {
      this._status(false);
      setTimeout(() => this.connect(), 1500);
    };
    this.ws.onerror = () => this._status(false);
  }

  _status(ok) {
    this.connected = ok;
    for (const fn of this.statusHandlers) fn(ok);
  }
}

export async function fetchConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error(res.status);
    return await res.json();
  } catch (err) {
    return { markers: [], tick_hz: 20, bars: 12, skills: {} };
  }
}

/** Shortest signed angular delta from a to b, in degrees. */
export function delta(a, b) {
  return ((b - a + 180) % 360 + 360) % 360 - 180;
}

export function lerp(a, b, t) { return a + (b - a) * t; }

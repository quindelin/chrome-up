"""Speech-to-text: what did the learner actually *say*?

Repetition can be graded against a known line. Free response cannot - we have
to listen first, then grade the pronunciation of whatever came out. So this
module exists purely to serve the `answer` steps.

Providers, in the order `auto` tries them:

  client  - the phone already ran Web Speech API (zh-CN) and posted the text.
            Free, instant, no keys: this is the default on the phone UI.
  iflytek - 语音听写 (IAT). Same appid/apikey as the ISE scoring engine.
  azure   - Azure Speech STT REST (same key/region as scoring).
  mock    - offline. Returns None; free response then falls back to drilling
            the sample answer instead of grading your own words.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from typing import Any, Dict, List, Optional

from .config import azure_ready, iflytek_ready
from .pronunciation import _resample_linear  # 16-bit mono resampler


def wav_bytes(pcm: bytes, sample_rate: int) -> bytes:
    """Wrap 16-bit mono PCM in a WAV container (Azure STT wants a container)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sample_rate))
        w.writeframes(pcm)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# iflytek dictation (IAT)
# ---------------------------------------------------------------------------


def _iflytek_transcribe(pcm: bytes, sample_rate: int, cfg: Dict) -> Optional[str]:
    ise = cfg["pronunciation"].get("iflytek") or {}
    appid, apikey = ise.get("appid"), ise.get("apikey")
    if not (appid and apikey):
        return None
    if sample_rate != 16000:
        pcm = _resample_linear(pcm, sample_rate, 16000)

    param = {"engine_type": "sms16k", "aue": "raw"}
    param_b64 = base64.b64encode(json.dumps(param).encode("utf-8")).decode()
    cur_time = str(int(time.time()))
    checksum = hashlib.md5(f"{apikey}{cur_time}{param_b64}".encode("utf-8")).hexdigest()

    body = urllib.parse.urlencode({"audio": base64.b64encode(pcm).decode()}).encode()
    req = urllib.request.Request(
        ise.get("iat_endpoint") or "https://iat-api.xfyun.cn/v2/iat",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-Appid": appid,
            "X-CurTime": cur_time,
            "X-Param": param_b64,
            "X-CheckSum": checksum,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=float(ise.get("timeout", 20))) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None
    if str(payload.get("code")) != "0":
        return None
    return _collect_words(payload.get("data"))


def _collect_words(node: Any, out: Optional[List[str]] = None) -> Optional[str]:
    """IAT nests words as data.result.ws[].cw[].w - grab them in order."""
    if out is None:
        out = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "w" and isinstance(value, str):
                out.append(value)
            elif isinstance(value, (dict, list)):
                _collect_words(value, out)
    elif isinstance(node, list):
        for value in node:
            _collect_words(value, out)
    return "".join(out) if out else None


# ---------------------------------------------------------------------------
# azure STT (REST, no SDK needed)
# ---------------------------------------------------------------------------


def _azure_token(region: str, key: str, timeout: float) -> Optional[str]:
    req = urllib.request.Request(
        f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
        data=b"",
        headers={"Ocp-Apim-Subscription-Key": key, "Content-Length": "0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None


def _azure_transcribe(pcm: bytes, sample_rate: int, cfg: Dict) -> Optional[str]:
    pron = cfg["pronunciation"]
    key, region = pron.get("key"), pron.get("region")
    if not (key and region):
        return None
    timeout = float(pron.get("iflytek", {}).get("timeout", 20))
    token = _azure_token(region, key, timeout)
    if not token:
        return None
    url = (
        f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/"
        f"cognitiveservices/v1?language={pron.get('language', 'zh-CN')}&format=detailed"
    )
    req = urllib.request.Request(
        url,
        data=wav_bytes(pcm, sample_rate),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"audio/wav; codecs=audio/pcm; samplerate={int(sample_rate)}",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None
    if payload.get("RecognitionStatus") != "Success":
        return None
    text = payload.get("DisplayText")
    if not text:
        best = payload.get("NBest") or []
        if best:
            text = best[0].get("Display") or best[0].get("Lexical")
    return text or None


PROVIDERS = {
    "iflytek": _iflytek_transcribe,
    "azure": _azure_transcribe,
    "mock": lambda *a, **k: None,
}


def resolve(cfg: Dict) -> str:
    """Which ASR engine `auto` should use, given the keys that exist.

    Japanese course prefers Azure (ja-JP dictation is solid there); the
    Mandarin course prefers iFlytek, which is already configured for scoring.
    """
    want = (cfg.get("free", {}).get("asr") or "auto").lower()
    if want != "auto":
        if want == "iflytek" and not iflytek_ready(cfg):
            return "mock"
        if want == "azure" and not azure_ready(cfg):
            return "mock"
        return want
    order = ["iflytek", "azure"] if cfg.get("language") == "zh" else ["azure", "iflytek"]
    for name in order:
        if name == "iflytek" and iflytek_ready(cfg):
            return "iflytek"
        if name == "azure" and azure_ready(cfg):
            return "azure"
    return "mock"


def transcribe(
    pcm: bytes,
    sample_rate: int,
    cfg: Dict,
    provider: Optional[str] = None,
    client_text: str = "",
) -> tuple:
    """Return (text, provider_name). text is "" when nothing could be heard."""
    client_text = (client_text or "").strip()
    if client_text:
        return client_text, "client"
    name = provider or resolve(cfg)
    if name == "client":
        name = resolve(cfg)
    fn = PROVIDERS.get(name, PROVIDERS["mock"])
    try:
        text = fn(pcm, sample_rate, cfg)
    except Exception:  # never let ASR kill the lesson
        text = None
    return (text or "").strip(), name

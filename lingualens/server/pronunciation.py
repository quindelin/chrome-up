"""Pronunciation scoring + the gate that decides whether you move on.

Works for either course language - the only thing that changes is the locale
tag handed to the engine (`pronunciation.language`: zh-CN or ja-JP).

Provider interface:
    score(pcm: bytes, sample_rate: int, reference: str, cfg) -> Score

`iflytek` iFlytek ISE. For zh_cn with extra_ability=multi_dimension it returns
         tone_score (调型) + phone_score (声韵) + per-syllable nodes. This is
         the one you want for Mandarin. ja_jp works too if your account has the
         Japanese evaluation service - it returns the standard dimensions.
`azure`   Azure AI Speech pronunciation assessment. Accuracy / fluency /
         completeness / pron score and word-level error types
         (Mispronunciation, Omission, Insertion). No tone or pitch accent.
`mock`    Offline scorer for development: uses duration + loudness only, so the
         app is runnable with no keys.

To swap in another engine (Chivox, SpeechSuper, iFlytek SDK) add a function
here and register it in PROVIDERS - the rest of the app only depends on the
`Score` object.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import random
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import wave
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .config import iflytek_ready, resolve_provider
from .models import Score

# ---------------------------------------------------------------------------
# audio helpers
# ---------------------------------------------------------------------------

_PUNCT = re.compile(
    r"[\s，。！？、；：,.!?;:\"'“”‘’（）()…—\-–・·「」『』]+"
)


def read_wav(data: bytes) -> Tuple[int, bytes]:
    """Return (sample_rate, 16-bit mono PCM bytes) for a WAV blob."""
    with wave.open(io.BytesIO(data)) as w:
        sr = w.getframerate()
        channels = w.getnchannels()
        width = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        raise ValueError("only 16-bit PCM WAV is supported")
    if channels == 1:
        return sr, raw
    arr = np.frombuffer(raw, dtype="<i2").astype(np.float32)
    arr = arr.reshape(-1, channels).mean(axis=1)
    return sr, arr.astype("<i2").tobytes()


def normalize_text(text: str) -> str:
    """Strip punctuation/space so we can compare spoken vs target text."""
    text = unicodedata.normalize("NFKC", text or "")
    return _PUNCT.sub("", text)


_LATIN_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def _fold(text: str) -> str:
    """casefold + drop accents, keeping ñ (año and ano are different words)."""
    text = unicodedata.normalize("NFD", (text or "").casefold().replace("ñ", "\x00"))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", text).replace("\x00", "ñ")


def _spaced(text: str) -> bool:
    """A line written with spaces between Latin-script words (Spanish)."""
    letters = [ch for ch in text if ch.isalpha()]
    return bool(letters) and " " in text.strip() and all(ord(ch) < 0x0370 for ch in letters)


def coverage_of(reference: str, recognized: str) -> float:
    """Fraction of reference characters that actually made it into the audio.

    For a space-delimited line the unit is the word: any two Spanish
    sentences share most of their letters, so letter coverage passes almost
    anything. Accents are folded (ñ is kept): dictation that writes "si" for
    "sí" is the transcriber's spelling, not the learner's pronunciation.
    """
    if _spaced(reference or ""):
        ref_w = _LATIN_WORD.findall(_fold(reference))
        rec_w = _LATIN_WORD.findall(_fold(recognized or ""))
        if not ref_w:
            return 1.0
        pool = list(rec_w)
        hits = 0
        for w in ref_w:
            if w in pool:
                pool.remove(w)
                hits += 1
        return hits / len(ref_w)
    ref = normalize_text(reference)
    rec = normalize_text(recognized)
    if not ref:
        return 1.0
    remaining = list(rec)
    hits = 0
    for ch in ref:
        if ch in remaining:
            remaining.remove(ch)
            hits += 1
    return hits / len(ref)


def pcm_stats(pcm: bytes, sample_rate: int) -> Tuple[float, float]:
    """Return (seconds, rms 0..1)."""
    if not pcm:
        return 0.0, 0.0
    arr = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    return len(arr) / float(sample_rate or 16000), float(np.sqrt(np.mean(arr ** 2)))


# ---------------------------------------------------------------------------
# mock provider (no keys, no network)
# ---------------------------------------------------------------------------


def _mock_score(pcm: bytes, sample_rate: int, reference: str, cfg: Dict) -> Score:
    audio = cfg["audio"]
    duration, rms = pcm_stats(pcm, sample_rate)
    score = Score(provider="mock", duration=duration)

    if duration < float(audio.get("min_seconds", 0.4)):
        score.reasons.append("No speech detected - hold the button and say the whole line.")
        return score
    if rms < float(audio.get("noise_gate_rms", 0.005)):
        score.reasons.append("Too quiet - speak up, the mic barely heard you.")
        return score

    ref = normalize_text(reference)
    # a Japanese mora is roughly half the length of a Chinese syllable
    per_char = float(audio.get("seconds_per_char", 0.32) or 0.32)
    expected = max(1.0, len(ref) * per_char)
    ratio = duration / expected
    rng = random.Random(hash(pcm[:512]) & 0xFFFF)
    # short / rushed utterances score badly, full-length ones pass
    base = 40.0 + 60.0 * ratio if ratio < 0.7 else min(95.0, 62.0 + 32.0 * min(1.15, ratio))
    jitter = rng.uniform(-6.0, 6.0)
    accuracy = max(0.0, min(100.0, base + jitter))
    score.accuracy = accuracy
    score.fluency = max(0.0, min(100.0, accuracy + rng.uniform(-8.0, 8.0)))
    score.completeness = max(0.0, min(100.0, 100.0 * min(1.0, ratio) + rng.uniform(-5.0, 5.0)))
    score.pron = 0.6 * min(accuracy, score.fluency, 100.0) + 0.4 * accuracy
    score.recognized = ref if ratio >= 0.7 else ref[: max(1, int(len(ref) * ratio))]
    if ratio < 0.55:
        score.reasons.append("Too rushed - say the whole line, every syllable.")
    return score


# ---------------------------------------------------------------------------
# azure provider
# ---------------------------------------------------------------------------


def _granularity(name: str):
    """PronunciationAssessmentGranularity, defaulting safely."""
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:  # pragma: no cover - optional dependency
        return None
    g = speechsdk.PronunciationAssessmentGranularity
    return g.Word if str(name).lower().startswith("word") else g.Phoneme


def _azure_score(pcm: bytes, sample_rate: int, reference: str, cfg: Dict) -> Score:
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:  # pragma: no cover - optional dependency
        score = Score(provider="mock", duration=pcm_stats(pcm, sample_rate)[0])
        score.error = "azure-cognitiveservices-speech not installed; fell back to mock"
        return _mock_score(pcm, sample_rate, reference, cfg)

    pron_cfg = cfg["pronunciation"]
    duration, _ = pcm_stats(pcm, sample_rate)
    score = Score(provider="azure", duration=duration)
    locale = pron_cfg.get("language", "zh-CN")

    speech_config = speechsdk.SpeechConfig(
        subscription=pron_cfg["key"], region=pron_cfg["region"]
    )
    speech_config.speech_recognition_language = locale

    stream_format = speechsdk.audio.AudioStreamFormat(
        samples_per_second=int(sample_rate), bits_per_sample=16, channels=1
    )
    push_stream = speechsdk.audio.PushAudioInputStream(stream_format)
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        language=locale,
        audio_config=audio_config,
    )
    assessment = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=_granularity(pron_cfg.get("granularity", "phoneme")),
        enable_miscue=bool(pron_cfg.get("enable_miscue", True)),
    )
    nbest = int(pron_cfg.get("phoneme_nbest", 0) or 0)
    if nbest > 0:
        assessment.nbest_phoneme_count = nbest
    assessment.apply_to(recognizer)

    push_stream.write(pcm)
    push_stream.close()
    try:
        result = recognizer.recognize_once()
    finally:
        recognizer = None  # help the SDK release the stream

    if result.reason == speechsdk.ResultReason.Canceled:  # type: ignore[union-attr]
        details = getattr(result, "cancellation_details", None)
        score.error = getattr(details, "error_details", "recognition cancelled") or "recognition cancelled"
        score.reasons.append("Speech service error - check AZURE_SPEECH_KEY / region.")
        return score

    raw = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
    try:
        payload = json.loads(raw) if raw else {}
    except ValueError:
        payload = {}

    nbest_list = payload.get("NBest") or []
    top = nbest_list[0] if nbest_list else {}
    pron = top.get("PronunciationAssessment") or {}
    score.recognized = top.get("DisplayText") or top.get("Lexical") or ""
    score.accuracy = float(pron.get("AccuracyScore", 0.0) or 0.0)
    score.fluency = float(pron.get("FluencyScore", 0.0) or 0.0)
    score.completeness = float(pron.get("CompletenessScore", 0.0) or 0.0)
    score.pron = float(pron.get("PronScore", 0.0) or 0.0)

    words: list = []
    for w in top.get("Words") or []:
        info = w.get("PronunciationAssessment") or {}
        words.append(
            {
                "word": w.get("Word", ""),
                "accuracy": float(info.get("AccuracyScore", 0.0) or 0.0),
                "error": info.get("ErrorType", "None"),
            }
        )
    score.words = words

    if not score.recognized:
        score.reasons.append("Nothing recognised - say the line again.")
    return score


# ---------------------------------------------------------------------------
# iflytek provider - returns tone (调型 / アクセント) + phone scores when the
# engine supports multi_dimension for the locale
# ---------------------------------------------------------------------------

_SCORE_KEYS = (
    "total_score",
    "accuracy_score",
    "fluency_score",
    "integrity_score",
    "phone_score",
    "tone_score",
    "syll_score",
)


def _walk(node: Any, found: Dict[str, float], syllables: list, reference: str = "") -> None:
    """Collect scores + per-unit nodes wherever they sit in the ISE tree.

    First occurrence wins, so the sentence-level score beats the per-word one.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _SCORE_KEYS and key not in found:
                try:
                    found[key] = float(value)
                except (TypeError, ValueError):
                    pass
        content = str(node.get("content", ""))
        if content and content != reference and ("tone_score" in node or "accuracy_score" in node):
            syllables.append(
                {
                    "word": content,
                    "symbol": str(node.get("symbol", "")),
                    "tone": float(node.get("tone_score", -1) or -1),
                    "accuracy": float(node.get("accuracy_score", -1) or -1),
                }
            )
        for value in node.values():
            _walk(value, found, syllables, reference)
    elif isinstance(node, list):
        for value in node:
            _walk(value, found, syllables, reference)


def _ise_category(reference: str, setting: str, lang: str = "zh") -> str:
    if setting and setting != "auto":
        return setting
    n = len(normalize_text(reference))
    # Japanese lines are longer for the same amount of speech, so the cut-offs
    # move up a little.
    if lang == "ja":
        if n <= 2:
            return "read_syllable"
        if n <= 8:
            return "read_word"
        return "read_sentence"
    if n <= 1:
        return "read_syllable"
    if n <= 6:
        return "read_word"
    return "read_sentence"


def _iflytek_score(pcm: bytes, sample_rate: int, reference: str, cfg: Dict) -> Score:
    """iFlytek ISE WebAPI.

    POST <endpoint>
      headers: X-Appid, X-CurTime, X-Param (base64 json), X-CheckSum
               X-CheckSum = MD5(APIKey + X-CurTime + X-Param)
      body   : audio=<base64 pcm>&text=<utf-8 reference>   (urlencoded)

    With extra_ability=multi_dimension a zh_cn sentence returns total_score,
    integrity_score, fluency_score, phone_score (声韵) and tone_score (调型),
    plus per-syllable nodes when result_level=entirety.
    """
    ise = cfg["pronunciation"].get("iflytek") or {}
    appid, apikey = ise.get("appid"), ise.get("apikey")
    duration, _ = pcm_stats(pcm, sample_rate)
    score = Score(provider="iflytek", duration=duration)

    if not (appid and apikey):
        score.error = "iFlytek keys missing (IFLYTEK_APPID / IFLYTEK_API_KEY)"
        return score

    # ISE wants 16k / 16-bit / mono raw PCM
    if sample_rate != 16000:
        pcm = _resample_linear(pcm, sample_rate, 16000)
        sample_rate = 16000

    lang = cfg.get("language", "zh")
    param = {
        "aue": "raw",
        "result_level": ise.get("result_level", "entirety"),
        "language": ise.get("language", "zh_cn"),
        "category": _ise_category(reference, ise.get("category", "auto"), lang),
        "extra_ability": ise.get("extra_ability", "multi_dimension"),
    }
    param_b64 = base64.b64encode(json.dumps(param, ensure_ascii=False).encode("utf-8")).decode()
    cur_time = str(int(time.time()))
    checksum = hashlib.md5(f"{apikey}{cur_time}{param_b64}".encode("utf-8")).hexdigest()

    body = urllib.parse.urlencode(
        {"audio": base64.b64encode(pcm).decode(), "text": reference}
    ).encode("utf-8")
    req = urllib.request.Request(
        ise.get("endpoint") or "https://ise-api.xfyun.cn/v2/ise",
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
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        score.error = f"iflytek ISE call failed: {exc}"
        score.reasons.append("Scoring service unreachable - try again.")
        return score

    if str(payload.get("code")) != "0":
        score.error = f"{payload.get('code')}: {payload.get('desc')}"
        score.reasons.append("Scoring service rejected the request.")
        return score

    found: Dict[str, float] = {}
    syllables: list = []
    _walk(payload.get("data"), found, syllables, normalize_text(reference))

    total = found.get("total_score", -1.0)
    score.pron = total if total >= 0 else 0.0
    score.accuracy = found.get("phone_score", found.get("accuracy_score", total))
    score.fluency = found.get("fluency_score", -1.0)
    score.completeness = found.get("integrity_score", 100.0)
    score.tone = found.get("tone_score", -1.0)
    score.phone = found.get("phone_score", -1.0)
    score.syllables = syllables
    score.recognized = reference if score.pron > 0 else ""

    # surface the three worst units so the learner knows what to fix
    bad = [s for s in syllables if 0 <= s["tone"] < 70]
    if bad:
        worst = sorted(bad, key=lambda s: s["tone"])[:3]
        score.reasons.append(
            "Tone/accent: " + ", ".join(f"{s['word']} ({s['tone']:.0f})" for s in worst)
        )
    if score.recognized == "":
        score.reasons.append("Nothing recognised - say the line again.")
    return score


def _resample_linear(pcm: bytes, src_rate: int, dst_rate: int) -> bytes:
    """Cheap linear resample of 16-bit mono PCM (ISE requires 16 kHz)."""
    if src_rate == dst_rate or not pcm:
        return pcm
    arr = np.frombuffer(pcm, dtype="<i2").astype(np.float32)
    ratio = dst_rate / float(src_rate)
    out_len = max(1, int(len(arr) * ratio))
    idx = np.arange(out_len) / ratio
    i0 = np.floor(idx).astype(np.int64)
    i1 = np.minimum(i0 + 1, len(arr) - 1)
    frac = idx - i0
    out = arr[i0] * (1 - frac) + arr[i1] * frac
    return out.astype("<i2").tobytes()


PROVIDERS = {"iflytek": _iflytek_score, "azure": _azure_score, "mock": _mock_score}


def score_attempt(
    pcm: bytes, sample_rate: int, reference: str, cfg: Dict, provider: Optional[str] = None
) -> Score:
    name = provider or resolve_provider(cfg)
    fn = PROVIDERS.get(name, _mock_score)
    score = fn(pcm, sample_rate, reference, cfg)
    score.coverage = coverage_of(reference, score.recognized)
    return score


def simulated_score(reference: str, quality: str = "good") -> Score:
    """Dev shortcut: grade an attempt without any audio."""
    q = (quality or "good").lower()
    if q in ("bad", "fail", "wrong"):
        text = normalize_text(reference)
        score = Score(
            provider="sim",
            pron=52.0,
            accuracy=47.0,
            fluency=58.0,
            completeness=68.0,
            tone=44.0,
            phone=49.0,
            recognized=text[:-1] if len(text) > 2 else "",
        )
        score.syllables = [{"word": text[:1], "symbol": "", "tone": 41.0, "accuracy": 46.0}] if text else []
        score.words = [{"word": text[:2], "accuracy": 44.0, "error": "Mispronunciation"}]
        score.reasons.append("Simulated weak attempt.")
    else:
        score = Score(
            provider="sim",
            pron=91.0,
            accuracy=93.0,
            fluency=88.0,
            completeness=100.0,
            tone=89.0,
            phone=92.0,
            recognized=reference,
        )
    score.coverage = coverage_of(reference, score.recognized)
    return score


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# fluency
# ---------------------------------------------------------------------------
# Every gate key above is segmental: did you pronounce the line. By HSK 5 the
# tones are usually fine and the answer still sounds foreign, because of the
# pauses and the 那个s rather than the segments. Two numbers, both derived
# from timing the score already carries:
#
#   rate    characters of the reference per second of audio. Reading off the
#           glasses, word by word, is slow and is exactly what this catches.
#   filler  那个 / 嗯 / 就是 / 然后 as a share of what was actually said.
#
# Neither is graded at the low bands, where slow-and-careful is right.

_FILLERS = {
    "zh": ("那个", "这个", "就是", "然后", "嗯", "呃", "啊", "就是说"),
    "ja": ("えっと", "ええと", "あの", "あのー", "まあ", "その", "うーん"),
}


def fluency_reasons(
    score: Score, reference: str, cfg: Dict, lang: str = "zh", band: int = 0
) -> List[str]:
    """Reasons the answer wasn't fluent, or [] when fluency isn't being graded."""
    f = cfg.get("fluency") or {}
    if not f.get("enabled", False):
        return []
    if int(band or 0) < int(f.get("min_band", 5) or 5):
        return []
    if score.error or not (score.recognized or "").strip():
        return []

    out: List[str] = []
    duration = float(score.duration or 0.0)
    ref = normalize_text(reference or "")
    min_rate = float(f.get("min_chars_per_second", 0.0) or 0.0)
    if min_rate > 0 and duration >= 0.5 and ref:
        rate = len(ref) / duration
        if rate < min_rate:
            out.append(
                f"Too halting ({rate:.1f} characters a second, want {min_rate:.1f}) "
                "- say it in one go"
            )

    max_filler = float(f.get("max_filler_ratio", 0.0) or 0.0)
    if max_filler > 0:
        said = normalize_text(score.recognized or "")
        if said:
            junk = sum(said.count(word) * len(word) for word in _FILLERS.get(lang, ()))
            if junk / len(said) > max_filler:
                out.append("Too much filler - drop the 那个s and just say it")
    return out


def evaluate(score: Score, gate: Dict) -> Tuple[bool, list]:
    """Decide pass/fail. Returns (passed, reasons)."""
    reasons: list = list(score.reasons)
    passed = True

    if score.error:
        return False, reasons or ["Speech service error."]

    if score.recognized == "" and score.pron == 0.0:
        return False, ["No speech detected - say the line out loud."]

    if score.pron < float(gate.get("min_pron_score", 70.0)):
        passed = False
        reasons.append(f"Pronunciation {score.pron:.0f} < {gate['min_pron_score']:.0f}")
    if score.accuracy < float(gate.get("min_accuracy", 70.0)):
        passed = False
        reasons.append(f"Accuracy {score.accuracy:.0f} < {gate['min_accuracy']:.0f}")
    if score.completeness and score.completeness < float(gate.get("min_completeness", 80.0)):
        passed = False
        reasons.append(f"You skipped part of the line ({score.completeness:.0f}% complete)")
    if gate.get("require_recognized_match", True):
        if score.coverage < float(gate.get("min_reference_coverage", 0.75)):
            passed = False
            reasons.append("Not all of the words came through - say every syllable")

    # suprasegmental gates - only applied when the provider reports a score
    min_tone = float(gate.get("min_tone_score", 0.0) or 0.0)
    if score.tone >= 0 and min_tone > 0 and score.tone < min_tone:
        passed = False
        worst = score.worst_syllable()
        if worst and worst.get("tone", 100) < min_tone:
            reasons.append(f"Tone/accent on “{worst['word']}” is off ({worst['tone']:.0f})")
        else:
            reasons.append(f"Tones {score.tone:.0f} < {min_tone:.0f}")

    min_phone = float(gate.get("min_phone_score", 0.0) or 0.0)
    if score.phone >= 0 and min_phone > 0 and score.phone < min_phone:
        passed = False
        reasons.append(f"Initials/finals {score.phone:.0f} < {min_phone:.0f}")

    for w in score.words:
        if w.get("error") in ("Mispronunciation", "Omission"):
            passed = False
            reasons.append(f"“{w['word']}” came out wrong")
            break

    if passed and not reasons:
        reasons.append("Clear enough. Moving on.")
    return passed, reasons

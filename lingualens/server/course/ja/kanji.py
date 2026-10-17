# -*- coding: utf-8 -*-
"""Kanji, taught as things in their own right rather than as parts of words.

A word bank teaches 読む. It does not teach that 読 is ショウ + ヨム and that
the same character is the どく in 朗読 and the とう in 句読点. Without that,
every unfamiliar kanji is a wall, and the learner stays dependent on having
the kana printed above the line - which is exactly the crutch the reading
mode is trying to wean them off.

The contract
------------
    (char, english gloss, on-yomi, kun-yomi, stage)

* `stage` 1-6 is a teaching order, roughly "how soon you need it". It is
  NOT the MEXT grade: it is ordered by when the character actually turns up
  in this course, which is what a learner here cares about. Do not relabel
  it as the official school grade.
* on-yomi are katakana (the Chinese reading); kun-yomi are hiragana (the
  Japanese reading). A kanji may legitimately have several of either, or
  none at all - 円 has no kun, 畑 has no on.
* Kun-yomi use a dot where the okurigana starts: た.べる is the reading of
  食べる. A leading or trailing hyphen marks a bound form: -び (as in 日
  読み), おお- (as in 大雨). This is the standard dictionary convention and
  it is what lets the UI show "taberu" without showing 食べ as たべ.
* The gloss is a flashcard-sized English hook, not a definition. One line,
  no etymology: "eat", not "to consume food; also refers to making a living".

Which kanji a lesson teaches is derived from the vocabulary the lesson
already contains (see `for_lesson`), so a kanji never appears before a word
that uses it. `CORE` only supplies the readings and the gloss.
"""

if not __package__:  # run directly as a script: no package context
    import os as _os
    import sys as _sys

    _sys.path.insert(0, _os.path.abspath(
        _os.path.join(_os.path.dirname(__file__), "..", "..", "..")))
    from server.course.ja import _parts
else:
    from . import _parts

# (char, en, on-yomi, kun-yomi, stage)
CORE: list = [
    # --- 1. numbers, money, time -------------------------------------------
    ("一", "one", ("イチ", "イツ"), ("ひと", "ひと.つ"), 1),
    ("二", "two", ("ニ",), ("ふた", "ふた.つ"), 1),
    ("三", "three", ("サン",), ("み", "みっ.つ"), 1),
    ("四", "four", ("シ",), ("よ", "よっ.つ", "よん"), 1),
    ("五", "five", ("ゴ",), ("いつ", "いつ.つ"), 1),
    ("六", "six", ("ロク",), ("む", "むっ.つ"), 1),
    ("七", "seven", ("シチ",), ("なな", "なな.つ"), 1),
    ("八", "eight", ("ハチ",), ("や", "やっ.つ"), 1),
    ("九", "nine", ("キュウ", "ク"), ("ここの", "ここの.つ"), 1),
    ("十", "ten", ("ジュウ",), ("とお",), 1),
    ("百", "hundred", ("ヒャク",), ("もも",), 1),
    ("千", "thousand", ("セン",), ("ち",), 1),
    ("万", "ten thousand", ("マン", "バン"), ("よろず",), 1),
    ("円", "yen; circle", ("エン",), ("まる",), 1),
    ("半", "half", ("ハン",), ("なか.ば",), 1),
    ("時", "time; hour", ("ジ",), ("とき", "-どき"), 1),
    ("分", "minute; part", ("ブン", "フン", "ブ"), ("わ.ける", "わ.かれる"), 1),
    ("年", "year", ("ネン",), ("とし",), 1),
    ("月", "month; moon", ("ゲツ", "ガツ"), ("つき",), 1),
    ("日", "day; sun", ("ニチ", "ジツ"), ("ひ", "-び", "-か"), 1),
    ("今", "now", ("コン", "キン"), ("いま",), 1),
    ("毎", "every", ("マイ",), ("ごと",), 1),
    ("先", "ahead; previous", ("セン",), ("さき", "ま.ず"), 1),
    ("朝", "morning", ("チョウ",), ("あさ",), 1),
    ("昼", "noon; daytime", ("チュウ",), ("ひる",), 1),
    ("夜", "night", ("ヤ",), ("よる", "よ"), 1),
    ("晩", "evening", ("バン",), (), 1),
    ("早", "early", ("ソウ", "サッ"), ("はや.い", "はや-"), 1),
    # --- 2. the world ------------------------------------------------------
    ("天", "sky; heaven", ("テン",), ("あま",), 2),
    ("空", "sky; empty", ("クウ",), ("そら", "あ.く", "から"), 2),
    ("雨", "rain", ("ウ",), ("あめ", "あま-"), 2),
    ("雪", "snow", ("セツ",), ("ゆき",), 2),
    ("風", "wind", ("フウ", "フ"), ("かぜ", "かざ-"), 2),
    ("火", "fire", ("カ",), ("ひ", "-び", "ほ-"), 2),
    ("水", "water", ("スイ",), ("みず",), 2),
    ("木", "tree; wood", ("モク", "ボク"), ("き", "こ-"), 2),
    ("金", "gold; money", ("キン", "コン", "カネ"), ("かね", "かな-"), 2),
    ("土", "earth; soil", ("ド", "ト"), ("つち",), 2),
    ("山", "mountain", ("サン",), ("やま",), 2),
    ("川", "river", ("セン",), ("かわ",), 2),
    ("田", "rice field", ("デン",), ("た",), 2),
    ("花", "flower", ("カ",), ("はな",), 2),
    ("草", "grass", ("ソウ",), ("くさ",), 2),
    ("森", "forest", ("シン",), ("もり",), 2),
    ("林", "grove", ("リン",), ("はやし",), 2),
    # --- 3. people ---------------------------------------------------------
    ("人", "person", ("ジン", "ニン"), ("ひと", "-と"), 1),
    ("大", "big", ("ダイ", "タイ"), ("おお.きい", "おお-"), 1),
    ("小", "small", ("ショウ",), ("ちい.さい", "こ-", "お-"), 1),
    ("中", "middle; inside", ("チュウ",), ("なか", "うち"), 1),
    ("上", "up; above", ("ジョウ", "ショウ"), ("うえ", "あ.げる", "あ.がる"), 1),
    ("下", "down; below", ("カ", "ゲ"), ("した", "さ.げる", "くだ.る"), 1),
    ("前", "before; front", ("ゼン",), ("まえ",), 1),
    ("後", "after; behind", ("ゴ", "コウ"), ("あと", "うし.ろ", "のち"), 1),
    ("左", "left", ("サ", "シャ"), ("ひだり",), 1),
    ("右", "right", ("ウ", "ユウ"), ("みぎ",), 1),
    ("東", "east", ("トウ",), ("ひがし",), 2),
    ("西", "west", ("セイ", "サイ"), ("にし",), 2),
    ("南", "south", ("ナン",), ("みなみ",), 2),
    ("北", "north", ("ホク",), ("きた",), 2),
    ("子", "child", ("シ", "ス"), ("こ", "-こ"), 1),
    ("女", "woman", ("ジョ", "ニョ", "ニョウ"), ("おんな", "め"), 1),
    ("男", "man", ("ダン", "ナン"), ("おとこ",), 1),
    ("名", "name", ("メイ", "ミョウ"), ("な",), 1),
    ("友", "friend", ("ユウ",), ("とも",), 1),
    ("家", "house; family", ("カ", "ケ"), ("いえ", "や", "うち"), 1),
    ("母", "mother", ("ボ",), ("はは", "かあ"), 2),
    ("父", "father", ("フ",), ("ちち", "とう"), 2),
    ("社", "company; shrine", ("シャ",), ("やしろ",), 2),
    ("会", "meet; meeting", ("カイ", "エ"), ("あ.う",), 2),
    # --- 4. the body -------------------------------------------------------
    ("口", "mouth", ("コウ", "ク"), ("くち",), 1),
    ("目", "eye", ("モク", "ボク"), ("め", "ま-"), 1),
    ("耳", "ear", ("ジ",), ("みみ",), 1),
    ("手", "hand", ("シュ",), ("て", "た-"), 1),
    ("足", "foot; enough", ("ソク",), ("あし", "た.りる"), 1),
    ("力", "power; strength", ("リョク", "リキ"), ("ちから",), 1),
    ("気", "spirit; air", ("キ", "ケ"), ("いき",), 1),
    ("心", "heart; mind", ("シン",), ("こころ",), 2),
    ("体", "body", ("タイ", "テイ"), ("からだ",), 2),
    ("元", "origin; former", ("ゲン", "ガン"), ("もと",), 2),
    # --- 5. words and learning ---------------------------------------------
    ("言", "say; word", ("ゲン", "ゴン"), ("い.う", "こと"), 1),
    ("話", "talk; story", ("ワ",), ("はな.す", "はなし"), 1),
    ("語", "word; language", ("ゴ",), ("かた.る", "かた.らう"), 1),
    ("読", "read", ("ドク", "トク", "トウ"), ("よ.む",), 1),
    ("書", "write", ("ショ",), ("か.く",), 1),
    ("見", "see", ("ケン",), ("み.る", "み.える", "み.せる"), 1),
    ("聞", "hear; ask", ("ブン", "モン"), ("き.く", "き.こえる"), 1),
    ("文", "writing; sentence", ("ブン", "モン"), ("ふみ",), 1),
    ("字", "character; letter", ("ジ",), ("あざ",), 1),
    ("本", "book; origin", ("ホン",), ("もと",), 1),
    ("紙", "paper", ("シ",), ("かみ",), 2),
    ("新", "new", ("シン",), ("あたら.しい", "あら.た"), 2),
    ("学", "learn", ("ガク",), ("まな.ぶ",), 1),
    ("校", "school", ("コウ",), (), 1),
    ("生", "life; birth; raw", ("セイ", "ショウ"), ("い.きる", "う.まれる", "なま"), 1),
    # --- 6. moving around --------------------------------------------------
    ("行", "go; carry out", ("コウ", "ギョウ", "アン"), ("い.く", "ゆ.く", "おこな.う"), 1),
    ("来", "come", ("ライ", "タイ"), ("く.る", "きた.る"), 1),
    ("帰", "return home", ("キ",), ("かえ.る", "かえ.す"), 1),
    ("出", "go out; put out", ("シュツ", "スイ"), ("で.る", "だ.す"), 1),
    ("入", "enter; put in", ("ニュウ",), ("はい.る", "い.れる"), 1),
    ("立", "stand", ("リツ", "リュウ"), ("た.つ", "た.てる"), 2),
    ("休", "rest", ("キュウ",), ("やす.む", "やす.める"), 2),
    ("住", "live; reside", ("ジュウ", "チュウ"), ("す.む", "す.まう"), 2),
    ("道", "road; way", ("ドウ", "トウ"), ("みち",), 2),
    ("車", "car; wheel", ("シャ",), ("くるま",), 1),
    ("駅", "station", ("エキ",), (), 1),
    ("電", "electricity", ("デン",), (), 1),
    # --- 7. eating, buying -------------------------------------------------
    ("食", "eat", ("ショク", "ジキ"), ("た.べる", "く.う"), 1),
    ("飲", "drink", ("イン",), ("の.む",), 1),
    ("米", "rice", ("ベイ", "マイ"), ("こめ",), 2),
    ("茶", "tea", ("チャ", "サ"), (), 2),
    ("肉", "meat", ("ニク",), (), 2),
    ("魚", "fish", ("ギョ",), ("さかな", "うお"), 2),
    ("店", "shop", ("テン",), ("みせ",), 1),
    ("買", "buy", ("バイ",), ("か.う",), 2),
    ("売", "sell", ("バイ",), ("う.る", "う.れる"), 2),
    ("安", "cheap; safe", ("アン",), ("やす.い",), 2),
    ("高", "tall; expensive", ("コウ",), ("たか.い", "たか.さ"), 2),
    # --- 8. doing ----------------------------------------------------------
    ("事", "thing; matter", ("ジ", "ズ"), ("こと",), 1),
    ("仕", "serve", ("シ", "ジ"), ("つか.える",), 2),
    ("働", "work", ("ドウ",), ("はたら.く",), 2),
    ("作", "make", ("サク", "サ"), ("つく.る",), 2),
    ("使", "use", ("シ",), ("つか.う",), 2),
    ("持", "hold; have", ("ジ",), ("も.つ",), 2),
    ("合", "join; fit", ("ゴウ", "ガッ", "カッ"), ("あ.う", "あわ.せる"), 2),
    ("会", "meet; meeting", ("カイ", "エ"), ("あ.う",), 2),
    # --- 9. judging --------------------------------------------------------
    ("良", "good", ("リョウ",), ("よ.い",), 2),
    ("悪", "bad", ("アク", "オ"), ("わる.い",), 2),
    ("古", "old", ("コ",), ("ふる.い",), 2),
    ("多", "many", ("タ",), ("おお.い",), 2),
    ("少", "few; little", ("ショウ",), ("すく.ない", "すこ.し"), 2),
    ("好", "like; fond of", ("コウ",), ("この.む", "す.く"), 2),
    ("間", "interval; between", ("カン", "ケン"), ("あいだ", "ま"), 2),
    ("場", "place (of an event)", ("ジョウ",), ("ば",), 2),
    ("所", "place", ("ショ",), ("ところ",), 2),
    # --- 10. colour --------------------------------------------------------
    ("白", "white", ("ハク", "ビャク"), ("しろ", "しろ.い"), 2),
    ("黒", "black", ("コク",), ("くろ", "くろ.い"), 2),
    ("赤", "red", ("セキ", "シャク"), ("あか", "あか.い"), 2),
    ("青", "blue; green", ("セイ", "ショウ"), ("あお", "あお.い"), 2),
    # 餃 has no kun reading and effectively occurs only in 餃子. It is here
    # because the course writes 餃子 in its own vocabulary, so without an
    # entry that word would be the only one in the course to get no kanji
    # step. It is not a JLPT character; it earns its place on usage.
    ("餃", "dumpling (as in 餃子)", ("キョウ",), (), 2),
]

# CORE is the worked first tranche. The rest of the table is authored in
# parts so it can be written in parallel; each part is a CORE-shaped list.
# A character already in CORE is left alone - CORE is the reference for
# what a correct entry looks like.
_EXTRA_1, _EXTRA_2 = _parts.load_parts(("kanji_extra1", "kanji_extra2"), "EXTRA")

# First occurrence wins, and CORE goes first, so CORE is what a learner
# sees for any character it covers. Dedupe against everything seen so far,
# not just CORE: two people writing parts at once will overlap, and a set
# comprehension reading `CORE` here would see the pre-assignment value and
# let every duplicate through.
_SEEN: set = set()
_MERGED: list = []
for _row in list(CORE) + list(_EXTRA_1 or []) + list(_EXTRA_2 or []):
    if not _row or not _row[0]:
        continue
    if _row[0] in _SEEN:
        continue
    _SEEN.add(_row[0])
    _MERGED.append(_row)

CORE = _MERGED
_BY_CHAR: dict = {row[0]: row for row in CORE}


def lookup(char: str) -> dict:
    """One kanji as a dict, or {} if the table does not have it yet."""
    row = _BY_CHAR.get(char)
    if not row:
        return {}
    return {
        "char": row[0],
        "en": row[1],
        "on": list(row[2]),
        "kun": list(row[3]),
        "stage": row[4],
    }


def kanji_in(text: str) -> list:
    """Every character in `text` that is a CJK ideograph.

    Deliberately broad - it takes chars this table may not know yet, so a
    missing entry shows up as a gap to fill rather than as silence.
    """
    out, seen = [], set()
    for ch in text:
        if "一" <= ch <= "鿿" and ch not in seen:
            seen.add(ch)
            out.append(ch)
    return out


def for_lesson(words: list, per_lesson: int = 3, known: set = None) -> list:
    """Pick the kanji a lesson should teach, from the words it already uses.

    `words` is the lesson's vocabulary as (text, reading, en) tuples. A
    kanji is only offered once a word containing it has been taught, so
    this never asks a learner to read a character before meeting it in
    context. Already-taught characters in `known` are skipped, and the
    earliest stage wins - 人 before 働.
    """
    known = known or set()
    found = {}
    for entry in words:
        text = entry[0] if isinstance(entry, (tuple, list)) else getattr(entry, "text", "")
        for ch in kanji_in(text):
            row = _BY_CHAR.get(ch)
            if not row or ch in known:
                continue
            if ch not in found or row[4] < found[ch][4]:
                found[ch] = row
    ordered = sorted(found.values(), key=lambda r: (r[4], r[0]))
    return [lookup(r[0]) for r in ordered[:per_lesson]]


def stats() -> dict:
    return {
        "total": len(CORE),
        "by_stage": {
            s: sum(1 for r in CORE if r[4] == s) for s in sorted({r[4] for r in CORE})
        },
    }


def check() -> list:
    """Structural problems in the merged table.

    A duplicate used to be possible here because the parts were merged
    without being deduped against each other, so it is checked explicitly
    rather than assumed. So is the script of each reading: an on-yomi in
    hiragana or a kun-yomi in katakana is a sign the two were transposed.
    """
    import re

    problems = []
    seen, dupes = set(), set()
    for row in CORE:
        if row[0] in seen:
            dupes.add(row[0])
        seen.add(row[0])
    if dupes:
        problems.append("duplicate characters: " + "".join(sorted(dupes)))
    if [r for r in CORE if not re.fullmatch(r"[一-鿿]", r[0])]:
        problems.append("there are non-kanji entries in CORE")
    mixed = [
        r[0] for r in CORE
        if any(re.search(r"[ぁ-ん]", x) for x in r[2])
        or any(re.search(r"[ァ-ヴ]", x) for x in r[3])
    ]
    if mixed:
        problems.append("on/kun script mixup: " + "".join(mixed))
    if [r for r in CORE if len(r) != 5]:
        problems.append("there are rows that are not 5-tuples")
    if [r for r in CORE if not r[2] and not r[3]]:
        problems.append(
            "entries with no reading at all: "
            + "".join(r[0] for r in CORE if not r[2] and not r[3])
        )
    return problems


if __name__ == "__main__":
    # A part that exists on disk but contributed nothing means the module
    # failed to import, and several hundred characters would vanish while
    # every other check still reported clean.
    print(stats())
    print("parts:", _parts.LOADED)
    found = check()
    found += [f"part {n} exists but loaded nothing" for n in
              _parts.dead_parts(("kanji_extra1", "kanji_extra2"))]
    print(f"{len(found)} problem(s)")
    for p in found:
        print("  " + p)

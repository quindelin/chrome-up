# -*- coding: utf-8 -*-
"""The two syllabaries, as something you are taught rather than assumed.

Everything else in this course assumes you can already read. For Japanese
that assumption does not hold: the writing system is three scripts deep
(kanji carried on a kana spine), and a learner who has never been shown
あ cannot read the dialogue they are being asked to speak.

This module is deliberately not a reference chart. It is the teaching
order, in the order that works:

  seion       the 46 basic kana - the spine
  dakuten     濁点: the same mouth shape, voiced (か→が)
  handakuten  半濁点: the は row only, and only ぱぴぷぺぽ
  yoon        拗音: the small ゃゅょ that fuse two kana into one beat

Katakana is taught immediately beside hiragana rather than after it. The
usual reason for deferring it is that learners confuse the two; the reason
for not deferring it is that loanwords are everywhere from lesson one
(コーヒー, タクシー, ホテル) and a learner who meets カタカナ in week six
has spent six weeks unable to read the menu.

Every entry is (hiragana, katakana, romaji). The romaji is a pronunciation
key for an English speaker, not a transliteration standard: し is "shi"
not "si", ふ is "fu" not "hu", because that is what stops a beginner
saying "si" and "hu" out loud.
"""

# (hiragana, katakana, romaji) - grouped in the order they are taught.
KANA: list = [
    # --- seion: the 46 basic kana ----------------------------------------
    ("あ", "ア", "a"),
    ("い", "イ", "i"),
    ("う", "ウ", "u"),
    ("え", "エ", "e"),
    ("お", "オ", "o"),
    ("か", "カ", "ka"),
    ("き", "キ", "ki"),
    ("く", "ク", "ku"),
    ("け", "ケ", "ke"),
    ("こ", "コ", "ko"),
    ("さ", "サ", "sa"),
    ("し", "シ", "shi"),
    ("す", "ス", "su"),
    ("せ", "セ", "se"),
    ("そ", "ソ", "so"),
    ("た", "タ", "ta"),
    ("ち", "チ", "chi"),
    ("つ", "ツ", "tsu"),
    ("て", "テ", "te"),
    ("と", "ト", "to"),
    ("な", "ナ", "na"),
    ("に", "ニ", "ni"),
    ("ぬ", "ヌ", "nu"),
    ("ね", "ネ", "ne"),
    ("の", "ノ", "no"),
    ("は", "ハ", "ha"),
    ("ひ", "ヒ", "hi"),
    ("ふ", "フ", "fu"),
    ("へ", "ヘ", "he"),
    ("ほ", "ホ", "ho"),
    ("ま", "マ", "ma"),
    ("み", "ミ", "mi"),
    ("む", "ム", "mu"),
    ("め", "メ", "me"),
    ("も", "モ", "mo"),
    ("や", "ヤ", "ya"),
    ("ゆ", "ユ", "yu"),
    ("よ", "ヨ", "yo"),
    ("ら", "ラ", "ra"),
    ("り", "リ", "ri"),
    ("る", "ル", "ru"),
    ("れ", "レ", "re"),
    ("ろ", "ロ", "ro"),
    ("わ", "ワ", "wa"),
    ("を", "ヲ", "wo"),
    ("ん", "ン", "n"),
    # --- dakuten: the same kana, voiced ----------------------------------
    ("が", "ガ", "ga"),
    ("ぎ", "ギ", "gi"),
    ("ぐ", "グ", "gu"),
    ("げ", "ゲ", "ge"),
    ("ご", "ゴ", "go"),
    ("ざ", "ザ", "za"),
    ("じ", "ジ", "ji"),
    ("ず", "ズ", "zu"),
    ("ぜ", "ゼ", "ze"),
    ("ぞ", "ゾ", "zo"),
    ("だ", "ダ", "da"),
    ("ぢ", "ヂ", "ji"),
    ("づ", "ヅ", "zu"),
    ("で", "デ", "de"),
    ("ど", "ド", "do"),
    ("ば", "バ", "ba"),
    ("び", "ビ", "bi"),
    ("ぶ", "ブ", "bu"),
    ("べ", "ベ", "be"),
    ("ぼ", "ボ", "bo"),
    # --- handakuten: only the は row -------------------------------------
    ("ぱ", "パ", "pa"),
    ("ぴ", "ピ", "pi"),
    ("ぷ", "プ", "pu"),
    ("ぺ", "ペ", "pe"),
    ("ぽ", "ポ", "po"),
    # --- yoon: a small ゃゅょ fuses two kana into one beat ---------------
    ("きゃ", "キャ", "kya"),
    ("きゅ", "キュ", "kyu"),
    ("きょ", "キョ", "kyo"),
    ("しゃ", "シャ", "sha"),
    ("しゅ", "シュ", "shu"),
    ("しょ", "ショ", "sho"),
    ("ちゃ", "チャ", "cha"),
    ("ちゅ", "チュ", "chu"),
    ("ちょ", "チョ", "cho"),
    ("にゃ", "ニャ", "nya"),
    ("にゅ", "ニュ", "nyu"),
    ("にょ", "ニョ", "nyo"),
    ("ひゃ", "ヒャ", "hya"),
    ("ひゅ", "ヒュ", "hyu"),
    ("ひょ", "ヒョ", "hyo"),
    ("みゃ", "ミャ", "mya"),
    ("みゅ", "ミュ", "myu"),
    ("みょ", "ミョ", "myo"),
    ("りゃ", "リャ", "rya"),
    ("りゅ", "リュ", "ryu"),
    ("りょ", "リョ", "ryo"),
    ("ぎゃ", "ギャ", "gya"),
    ("ぎゅ", "ギュ", "gyu"),
    ("ぎょ", "ギョ", "gyo"),
    ("じゃ", "ジャ", "ja"),
    ("じゅ", "ジュ", "ju"),
    ("じょ", "ジョ", "jo"),
    ("びゃ", "ビャ", "bya"),
    ("びゅ", "ビュ", "byu"),
    ("びょ", "ビョ", "byo"),
    ("ぴゃ", "ピャ", "pya"),
    ("ぴゅ", "ピュ", "pyu"),
    ("ぴょ", "ピョ", "pyo"),
]

# Where each group starts and ends, so a lesson can take one mouthful.
GROUPS: list = [
    ("seion-vowels", "the five vowels", 0, 5),
    ("seion-k", "the k row", 5, 10),
    ("seion-s", "the s row - し is 'shi'", 10, 15),
    ("seion-t", "the t row - ち is 'chi', つ is 'tsu'", 15, 20),
    ("seion-n", "the n row", 20, 25),
    ("seion-h", "the h row - ふ is 'fu'", 25, 30),
    ("seion-m", "the m row", 30, 35),
    ("seion-y", "the y row - only three", 35, 38),
    ("seion-r", "the r row", 38, 43),
    ("seion-w", "わ, を and the ん that ends a syllable", 43, 46),
    ("dakuten-g", "濁点: k becomes g", 46, 51),
    ("dakuten-z", "濁点: s becomes z", 51, 56),
    ("dakuten-d", "濁点: t becomes d", 56, 61),
    ("dakuten-b", "濁点: h becomes b", 61, 66),
    ("handakuten", "半濁点: h becomes p", 66, 71),
    ("yoon-k", "拗音: き + ゃ = きゃ", 71, 74),
    ("yoon-s", "拗音: し + ゃ = しゃ", 74, 77),
    ("yoon-ch", "拗音: ち + ゃ = ちゃ", 77, 80),
    ("yoon-nhm", "拗音: に, ひ, み", 80, 89),
    ("yoon-r", "拗音: り + ゃ = りゃ", 89, 92),
    ("yoon-gjbp", "拗音: ぎ, じ, び, ぴ", 92, 104),
]

# Katakana has a few habits of its own that are worth saying out loud once.
KATAKANA_NOTES: list = [
    "A long vowel in katakana is written with ー, not with a second kana: "
    "コーヒー (koohii), not コオヒイ.",
    "A small ッ doubles the consonant that follows it: マッチ (matchi) is "
    "'match', with a pause where the t is held.",
    "Loanwords are spelled by sound, so フォーク is 'fork' - フ + ォ - and "
    "the small vowel is doing the work of an f that Japanese does not have "
    "before o.",
    "カタカナ is also the italics of Japanese: it marks foreign words, "
    "company names, onomatopoeia, and anything a writer wants to stand out.",
]


def entries(group: str = "") -> list:
    """Kana rows, optionally narrowed to one group id."""
    if not group:
        return list(KANA)
    for gid, _label, start, end in GROUPS:
        if gid == group:
            return KANA[start:end]
    return []


def kana_for_lesson(lesson_id: int, per_lesson: int = 5, through_lesson: int = 8) -> list:
    """The slice of the syllabary that belongs with one early lesson.

    Five a lesson is roughly a week of looking at them before the next
    five arrive. After `through_lesson` the syllabary has been covered and
    the lessons go back to being about the language.
    """
    if lesson_id > through_lesson:
        return []
    start = (lesson_id - 1) * per_lesson
    return KANA[start : start + per_lesson]


def group_of(hiragana: str) -> str:
    for gid, _label, start, end in GROUPS:
        for row in KANA[start:end]:
            if row[0] == hiragana:
                return gid
    return ""

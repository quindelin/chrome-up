# -*- coding: utf-8 -*-
"""汉字, taught as things in their own right rather than as parts of words.

The course used to skip this entirely, on the reasoning that literacy was a
Japanese problem: Japanese has two syllabaries that have to be taught outright,
and Mandarin has pinyin. That reasoning is backwards. Pinyin is a one-way
bridge from sound to meaning; it never builds meaning -> character, or
character -> sound. So the moment `ui.reading_mode` fades the pinyin out at
HSK 5, the learner is standing on nothing - and HSK 5-6 is mostly a reading
exam in which 阅读 is 50 of the questions.

A word bank teaches 喜欢. It does not teach that 欢 is 又 + 欠, or that the 青
in 请 is the same 青 as in 清 and 情, and that those three are pronounced
qīng / qǐng / qíng because the radical is carrying the meaning and the other
half is carrying a sound you can guess. Without that, every unfamiliar
character is a drawing to memorise, 2,600 of them, one at a time.

The contract
------------
    (char, pinyin, gloss, radical, components, stage)

* `stage` 1-6 is a teaching order, roughly "how soon you need it". It is NOT
  the HSK level of the character and NOT a frequency list: it is ordered by
  when the character actually turns up in this course, which is what a
  learner here cares about.
* `radical` is the 部首, the dictionary head under which you would look the
  character up. It is usually the half that carries the meaning: 妈 sits under
  女, 请 sits under 讠.
* `components` is the rest, written the way a teacher would say it out loud:
  "女 + 马". Where the other half is doing phonetic duty as well, that is the
  whole point of the entry and the note says so.
* Either may be empty. A partial table is safe: `for_lesson` skips characters
  it has no row for, so a missing entry costs one step rather than crashing.
* `pinyin` carries tone marks and is checked by `pinyin_check.py` like every
  other reading in the course.

Which characters a lesson teaches is derived from the vocabulary that lesson
already contains (see `for_lesson`), so a character never turns up before a
word that uses it. CORE only supplies the readings, the gloss and the parts.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

# (char, pinyin, gloss, radical, components, stage)
CORE: List[Tuple[str, str, str, str, str, int]] = [
    # --- 1. the grammatical skeleton: pronouns, particles, the copula -------
    ("我", "wǒ", "I; me", "戈", "手 + 戈", 1),
    ("你", "nǐ", "you", "亻", "亻 + 尔", 1),
    ("他", "tā", "he; him", "亻", "亻 + 也", 1),
    ("她", "tā", "she; her", "女", "女 + 也", 1),
    ("们", "men", "plural suffix for people", "亻", "亻 + 门", 1),
    ("是", "shì", "to be", "日", "日 + 正", 1),
    ("不", "bù", "not", "一", "一 + 卜", 1),
    ("了", "le", "aspect: change of state", "子", "子", 1),
    ("吗", "ma", "yes-no question particle", "口", "口 + 马", 1),
    ("呢", "ne", "question particle; and you?", "口", "口 + 尼", 1),
    ("吧", "ba", "softener: let's…", "口", "口 + 巴", 1),
    ("的", "de", "possessive / attributive", "白", "白 + 勺", 1),
    ("得", "de", "manner complement marker", "彳", "彳 + 㝵", 1),
    ("地", "de", "adverb marker", "土", "土 + 也", 1),
    ("在", "zài", "at; in the middle of", "土", "土 + 才", 1),
    ("有", "yǒu", "to have; there is", "月", "𠂇 + 月", 1),
    ("没", "méi", "have not", "氵", "氵 + 殳", 1),
    ("也", "yě", "also", "乙", "乙", 1),
    ("都", "dōu", "all; both", "阝", "者 + 阝", 1),
    ("就", "jiù", "then; right away", "尢", "京 + 尤", 1),
    ("还", "hái", "still; in addition", "辶", "不 + 辶", 1),
    ("又", "yòu", "again", "又", "又", 1),
    ("再", "zài", "again (future)", "冂", "冂 + 土", 1),
    ("很", "hěn", "very", "彳", "彳 + 艮", 1),
    ("太", "tài", "too; excessively", "大", "大 + 丶", 1),
    ("最", "zuì", "most", "日", "日 + 取", 1),
    ("更", "gèng", "even more", "曰", "曰 + 攵", 1),

    # --- 2. the verbs you cannot avoid --------------------------------------
    ("来", "lái", "to come", "木", "木", 1),
    ("去", "qù", "to go", "厶", "土 + 厶", 1),
    ("说", "shuō", "to speak", "讠", "讠 + 兑", 1),
    ("看", "kàn", "to look; to read", "目", "𠂤 + 目", 1),
    ("听", "tīng", "to listen", "口", "口 + 斤", 1),
    ("问", "wèn", "to ask", "门", "门 + 口", 1),
    ("吃", "chī", "to eat", "口", "口 + 乞", 1),
    ("喝", "hē", "to drink", "口", "口 + 曷", 1),
    ("做", "zuò", "to do; to make", "亻", "亻 + 故", 1),
    ("买", "mǎi", "to buy", "乙", "乛 + 头", 1),
    ("卖", "mài", "to sell", "十", "十 + 买", 1),
    ("走", "zǒu", "to walk; to leave", "走", "走", 1),
    ("坐", "zuò", "to sit", "土", "从 + 土", 1),
    ("站", "zhàn", "to stand; a stop", "立", "立 + 占", 1),
    ("打", "dǎ", "to hit; to make (a call)", "扌", "扌 + 丁", 1),
    ("开", "kāi", "to open", "廾", "廾", 1),
    ("关", "guān", "to close", "八", "丷 + 天", 1),
    ("给", "gěi", "to give; for", "纟", "纟 + 合", 1),
    ("找", "zhǎo", "to look for", "扌", "扌 + 戈", 1),
    ("用", "yòng", "to use", "用", "用", 1),
    ("要", "yào", "to want; must", "西", "西 + 女", 1),
    ("想", "xiǎng", "to think; would like to", "心", "相 + 心", 1),
    ("知", "zhī", "to know (a fact)", "矢", "矢 + 口", 1),
    ("道", "dào", "way; (知道) to know", "辶", "首 + 辶", 1),
    ("觉", "jué", "to feel (觉得)", "见", "⺍ + 见", 1),
    ("会", "huì", "can (learned); will", "人", "人 + 云", 1),
    ("能", "néng", "can; be able to", "月", "厶 + 月 + 匕", 1),
    ("可", "kě", "may; can (可以)", "口", "丁 + 口", 1),
    ("应", "yīng", "should (应该)", "广", "广 + ⺍", 1),
    ("该", "gāi", "ought to", "讠", "讠 + 亥", 1),
    ("住", "zhù", "to live (somewhere)", "亻", "亻 + 主", 1),
    ("等", "děng", "to wait; etc.", "竹", "竹 + 寺", 1),
    ("起", "qǐ", "to rise; (想起) recall", "走", "走 + 己", 1),
    ("回", "huí", "to return", "囗", "囗 + 囗", 1),
    ("出", "chū", "to go out", "凵", "山 + 山", 1),
    ("进", "jìn", "to enter", "辶", "井 + 辶", 1),
    ("到", "dào", "to arrive", "刂", "至 + 刂", 1),
    ("过", "guò", "to pass; (aspect) ever", "辶", "寸 + 辶", 1),
    ("完", "wán", "to finish", "宀", "宀 + 元", 1),
    ("懂", "dǒng", "to understand", "忄", "忄 + 董", 1),

    # --- 3. courtesy, the first thirty seconds ------------------------------
    ("请", "qǐng", "please; to invite", "讠", "讠 + 青", 1),
    ("谢", "xiè", "to thank", "讠", "讠 + 射", 1),
    ("对", "duì", "correct; (对不起) sorry", "寸", "又 + 寸", 1),
    ("客", "kè", "guest (客气)", "宀", "宀 + 各", 1),
    ("见", "jiàn", "to see; to meet", "见", "见", 1),
    ("欢", "huān", "joyful (欢迎)", "欠", "又 + 欠", 1),
    ("迎", "yíng", "to welcome", "辶", "卬 + 辶", 1),
    ("慢", "màn", "slow", "忄", "忄 + 曼", 1),
    ("点", "diǎn", "a little; o'clock", "灬", "占 + 灬", 1),

    # --- 4. questions and placeholders --------------------------------------
    ("什", "shén", "what (什么)", "亻", "亻 + 十", 1),
    ("么", "me", "interrogative suffix", "丿", "丿 + 厶", 1),
    ("哪", "nǎ", "which; where", "口", "口 + 那", 1),
    ("里", "lǐ", "inside; (哪里) where", "里", "田 + 土", 1),
    ("怎", "zěn", "how (怎么)", "心", "乍 + 心", 1),
    ("样", "yàng", "way; kind (怎么样)", "木", "木 + 羊", 1),
    ("谁", "shéi", "who", "讠", "讠 + 隹", 1),
    ("几", "jǐ", "how many (small number)", "几", "几", 1),
    ("多", "duō", "how many; many", "夕", "夕 + 夕", 1),
    ("少", "shǎo", "few; (多少) how much", "小", "小 + 丿", 1),
    ("钱", "qián", "money", "钅", "钅 + 戋", 1),
    ("块", "kuài", "yuan (spoken); lump", "土", "土 + 夬", 1),
    ("个", "gè", "the general measure word", "人", "人 + 丨", 1),
    ("时", "shí", "time (时候)", "日", "日 + 寸", 1),
    ("候", "hòu", "to wait (时候)", "亻", "亻 + 侯", 1),
    ("现", "xiàn", "now (现在)", "王", "王 + 见", 1),

    # --- 5. size, quality, comparison ---------------------------------------
    ("大", "dà", "big", "大", "大", 1),
    ("小", "xiǎo", "small", "小", "小", 1),
    ("好", "hǎo", "good; well", "女", "女 + 子", 1),
    ("坏", "huài", "bad; broken", "土", "土 + 不", 1),
    ("新", "xīn", "new", "斤", "亲 + 斤", 2),
    ("旧", "jiù", "old (of things)", "日", "丨 + 日", 2),
    ("长", "cháng", "long", "长", "长", 2),
    ("短", "duǎn", "short", "矢", "矢 + 豆", 2),
    ("高", "gāo", "tall; expensive", "高", "高", 2),
    ("低", "dī", "low", "亻", "亻 + 氐", 2),
    ("贵", "guì", "expensive", "贝", "中 + 一 + 贝", 2),
    ("便", "pián", "cheap (便宜)", "亻", "亻 + 更", 2),
    ("宜", "yí", "suitable (便宜)", "宀", "宀 + 且", 2),
    ("快", "kuài", "fast", "忄", "忄 + 夬", 2),
    ("远", "yuǎn", "far", "辶", "元 + 辶", 2),
    ("近", "jìn", "near", "辶", "斤 + 辶", 2),
    ("重", "zhòng", "heavy; serious", "里", "千 + 里", 2),
    ("轻", "qīng", "light (in weight)", "车", "车 + 𡿨", 2),
    ("难", "nán", "difficult", "隹", "又 + 隹", 2),
    ("易", "yì", "easy", "日", "日 + 勿", 2),

    # --- 6. the body and its states -----------------------------------------
    ("身", "shēn", "body", "身", "身", 2),
    ("体", "tǐ", "body; health (身体)", "亻", "亻 + 本", 2),
    ("头", "tóu", "head", "头", "头", 2),
    ("目", "mù", "eye", "目", "目", 2),
    ("眼", "yǎn", "eye", "目", "目 + 艮", 2),
    ("口", "kǒu", "mouth; opening", "口", "口", 2),
    ("手", "shǒu", "hand", "手", "手", 2),
    ("心", "xīn", "heart; mind", "心", "心", 2),
    ("病", "bìng", "illness; to be ill", "疒", "疒 + 丙", 2),
    ("疼", "téng", "to ache", "疒", "疒 + 冬", 2),
    ("累", "lèi", "tired", "糸", "田 + 糸", 2),
    ("饿", "è", "hungry", "饣", "饣 + 我", 2),
    ("渴", "kě", "thirsty", "氵", "氵 + 曷", 2),
    ("冷", "lěng", "cold", "冫", "冫 + 令", 2),
    ("热", "rè", "hot", "灬", "执 + 灬", 2),
    ("睡", "shuì", "to sleep", "目", "目 + 垂", 2),
    ("休", "xiū", "to rest", "亻", "亻 + 木", 2),
    ("息", "xī", "rest (休息)", "心", "自 + 心", 2),

    # --- 7. feeling and wanting ---------------------------------------------
    ("喜", "xǐ", "to like (喜欢)", "口", "壴 + 口", 2),
    ("爱", "ài", "to love", "心", "爫 + 冖 + 心", 2),
    ("怕", "pà", "to fear", "忄", "忄 + 白", 2),
    ("急", "jí", "anxious; urgent", "心", "刍 + 心", 3),
    ("忙", "máng", "busy", "忄", "忄 + 亡", 2),
    ("兴", "xìng", "interest (兴趣)", "八", "八 + 一", 3),
    ("趣", "qù", "interest (兴趣)", "走", "走 + 取", 3),
    ("思", "sī", "to think (意思)", "心", "田 + 心", 3),
    ("意", "yì", "meaning; idea", "心", "立 + 曰 + 心", 3),
    ("感", "gǎn", "to feel", "心", "咸 + 心", 3),
    ("情", "qíng", "feeling; situation", "忄", "忄 + 青", 3),
    ("况", "kuàng", "situation (情况)", "冫", "冫 + 兄", 3),

    # --- 8. time ------------------------------------------------------------
    ("今", "jīn", "today (今天)", "人", "人 + 卩", 1),
    ("天", "tiān", "day; sky", "大", "一 + 大", 1),
    ("明", "míng", "bright; tomorrow", "日", "日 + 月", 1),
    ("昨", "zuó", "yesterday", "日", "日 + 乍", 1),
    ("年", "nián", "year", "干", "𠂉 + 干", 2),
    ("月", "yuè", "month; moon", "月", "月", 2),
    ("日", "rì", "day; sun", "日", "日", 2),
    ("星", "xīng", "star; (星期) week", "日", "日 + 生", 2),
    ("期", "qī", "period (星期)", "月", "其 + 月", 2),
    ("周", "zhōu", "week; (周末) weekend", "口", "冂 + 土 + 口", 2),
    ("末", "mò", "end (周末)", "木", "木 + 一", 2),
    ("早", "zǎo", "early; morning", "日", "日 + 十", 2),
    ("晚", "wǎn", "late; evening", "日", "日 + 免", 2),
    ("午", "wǔ", "noon (中午)", "十", "𠂉 + 十", 2),
    ("分", "fēn", "minute; to divide", "刀", "八 + 刀", 2),
    ("钟", "zhōng", "clock; o'clock", "钅", "钅 + 中", 2),
    ("半", "bàn", "half", "十", "丶 + 丷 + 十", 2),
    ("久", "jiǔ", "a long time", "丿", "丿 + 丶", 3),
    ("已", "yǐ", "already", "己", "己", 3),

    # --- 9. place, direction, the city --------------------------------------
    ("上", "shàng", "up; on", "一", "一 + 卜", 1),
    ("下", "xià", "down; under", "一", "一 + 卜", 1),
    ("中", "zhōng", "middle; in", "丨", "口 + 丨", 1),
    ("外", "wài", "outside", "夕", "夕 + 卜", 2),
    ("前", "qián", "front; before", "刂", "䒑 + 月 + 刂", 2),
    ("后", "hòu", "behind; after", "口", "𠂆 + 一 + 口", 2),
    ("左", "zuǒ", "left", "工", "𠂇 + 工", 2),
    ("右", "yòu", "right", "口", "𠂇 + 口", 2),
    ("东", "dōng", "east", "一", "一 + 小", 2),
    ("西", "xī", "west", "西", "西", 2),
    ("南", "nán", "south", "十", "十 + 冂", 2),
    ("北", "běi", "north", "匕", "北", 2),
    ("边", "biān", "side", "辶", "力 + 辶", 2),
    ("面", "miàn", "face; side", "面", "面", 2),
    ("方", "fāng", "direction; place", "方", "方", 2),
    ("路", "lù", "road", "足", "足 + 各", 2),
    ("街", "jiē", "street", "行", "行 + 圭", 3),
    ("城", "chéng", "city", "土", "土 + 成", 3),
    ("市", "shì", "city; market", "巾", "亠 + 巾", 3),
    ("区", "qū", "district; area", "匚", "匚 + 乂", 3),
    ("附", "fù", "nearby (附近)", "阝", "阝 + 付", 3),
    ("场", "chǎng", "place; (市场) market", "土", "土 + 昜", 3),
    ("园", "yuán", "park (公园)", "囗", "囗 + 元", 3),
    ("公", "gōng", "public", "八", "八 + 厶", 2),

    # --- 10. getting around -------------------------------------------------
    ("车", "chē", "vehicle", "车", "车", 2),
    ("铁", "tiě", "iron; (地铁) subway", "钅", "钅 + 失", 2),
    ("机", "jī", "machine; (飞机) plane", "木", "木 + 几", 2),
    ("票", "piào", "ticket", "示", "西 + 示", 2),
    ("船", "chuán", "boat; ship", "舟", "舟 + 㕣", 3),
    ("飞", "fēi", "to fly", "飞", "飞", 3),
    ("旅", "lǚ", "to travel", "方", "方 + 𭤨", 3),
    ("行", "xíng", "to go; (旅行) travel", "行", "行", 3),
    ("迷", "mí", "lost (迷路)", "辶", "米 + 辶", 3),

    # --- 11. food -----------------------------------------------------------
    ("饭", "fàn", "meal; cooked rice", "饣", "饣 + 反", 2),
    ("菜", "cài", "dish; vegetable", "艹", "艹 + 采", 2),
    ("茶", "chá", "tea", "艹", "艹 + 余", 2),
    ("酒", "jiǔ", "alcohol", "酉", "氵 + 酉", 2),
    ("肉", "ròu", "meat", "肉", "冂 + 人", 2),
    ("牛", "niú", "cow; beef", "牛", "牛", 2),
    ("鱼", "yú", "fish", "鱼", "鱼", 3),
    ("蛋", "dàn", "egg", "虫", "疋 + 虫", 3),
    ("汤", "tāng", "soup", "氵", "氵 + 昜", 3),
    ("糖", "táng", "sugar", "米", "米 + 唐", 3),
    ("盐", "yán", "salt (咸)", "皿", "土 + 卜 + 皿", 3),
    ("辣", "là", "spicy", "辛", "辛 + 束", 2),
    ("甜", "tián", "sweet", "甘", "舌 + 甘", 3),
    ("饱", "bǎo", "full (after eating)", "饣", "饣 + 包", 3),
    ("杯", "bēi", "cup", "木", "木 + 不", 2),
    ("碗", "wǎn", "bowl", "石", "石 + 宛", 3),
    ("馆", "guǎn", "shop (餐馆)", "饣", "饣 + 官", 2),
    ("单", "dān", "bill (买单)", "丷", "丷 + 田 + 十", 2),

    # --- 12. shopping and numbers -------------------------------------------
    ("一", "yī", "one", "一", "一", 1),
    ("二", "èr", "two", "二", "二", 1),
    ("三", "sān", "three", "一", "一 + 一 + 一", 1),
    ("四", "sì", "four", "囗", "囗 + 儿", 1),
    ("五", "wǔ", "five", "二", "二 + 乛", 1),
    ("六", "liù", "six", "八", "亠 + 八", 1),
    ("七", "qī", "seven", "一", "一 + 乚", 1),
    ("八", "bā", "eight", "八", "八", 1),
    ("九", "jiǔ", "nine", "乙", "乙 + 丿", 1),
    ("十", "shí", "ten", "十", "十", 1),
    ("百", "bǎi", "hundred", "白", "一 + 白", 1),
    ("千", "qiān", "thousand", "十", "丿 + 十", 2),
    ("零", "líng", "zero", "雨", "雨 + 令", 2),
    ("两", "liǎng", "two (before a measure)", "一", "一 + 从", 2),
    ("斤", "jīn", "jin, 500 g", "斤", "斤", 2),
    ("号", "hào", "number; size", "口", "口 + 丂", 2),
    ("色", "sè", "colour", "色", "色", 2),
    ("红", "hóng", "red", "纟", "纟 + 工", 2),
    ("黑", "hēi", "black", "黑", "黑", 2),
    ("白", "bái", "white", "白", "白", 2),
    ("件", "jiàn", "item (clothing)", "亻", "亻 + 牛", 2),
    ("条", "tiáo", "long thin thing", "木", "夂 + 木", 3),
    ("双", "shuāng", "pair", "又", "又 + 又", 3),
    ("试", "shì", "to try", "讠", "讠 + 式", 2),
    ("换", "huàn", "to change; exchange", "扌", "扌 + 奂", 3),

    # --- 13. work, study, the office ----------------------------------------
    ("工", "gōng", "work", "工", "工", 2),
    ("作", "zuò", "work (工作)", "亻", "亻 + 乍", 2),
    ("学", "xué", "to study", "子", "⺍ + 冖 + 子", 1),
    ("习", "xí", "to practise (学习)", "乙", "乙 + 冫", 1),
    ("教", "jiāo", "to teach", "攵", "孝 + 攵", 3),
    ("书", "shū", "book", "乙", "乙 + 丶", 2),
    ("字", "zì", "character; word", "子", "宀 + 子", 2),
    ("文", "wén", "writing; language", "文", "文", 1),
    ("课", "kè", "class; lesson", "讠", "讠 + 果", 3),
    ("班", "bān", "shift; class", "王", "王 + 王 + 刂", 2),
    ("经", "jīng", "to manage (经理)", "纟", "纟 + 𡿨", 3),
    ("理", "lǐ", "to manage; reason", "王", "王 + 里", 3),
    ("司", "sī", "company (公司)", "口", "𠃌 + 一 + 口", 3),
    ("员", "yuán", "staff (人员)", "口", "口 + 贝", 3),
    ("医", "yī", "medicine", "匚", "匚 + 矢", 2),
    ("院", "yuàn", "hospital; institute", "阝", "阝 + 完", 2),
    ("假", "jià", "leave (请假)", "亻", "亻 + 叚", 3),
    ("安", "ān", "peaceful; to arrange", "宀", "宀 + 女", 3),
    ("排", "pái", "to arrange; to queue", "扌", "扌 + 非", 3),

    # --- 14. home, family ---------------------------------------------------
    ("家", "jiā", "home; family", "宀", "宀 + 豕", 2),
    ("房", "fáng", "room; house", "户", "户 + 方", 2),
    ("间", "jiān", "room (房间)", "门", "门 + 日", 2),
    ("妈", "mā", "mother", "女", "女 + 马", 1),
    ("爸", "bà", "father", "父", "父 + 巴", 1),
    ("哥", "gē", "older brother", "口", "可 + 口", 2),
    ("姐", "jiě", "older sister", "女", "女 + 且", 2),
    ("弟", "dì", "younger brother", "丷", "丷 + 弓", 2),
    ("孩", "hái", "child", "子", "子 + 亥", 3),
    ("朋", "péng", "friend", "月", "月 + 月", 2),
    ("友", "yǒu", "friend", "又", "𠂇 + 又", 2),

    # --- 15. connectives: how an argument is joined --------------------------
    ("和", "hé", "and; with", "禾", "禾 + 口", 1),
    ("与", "yǔ", "and; with (formal)", "一", "一 + 与", 4),
    ("但", "dàn", "but", "亻", "亻 + 旦", 1),
    ("而", "ér", "and yet; -ly", "而", "而", 4),
    ("且", "qiě", "moreover (而且)", "一", "一 + 目", 4),
    ("因", "yīn", "because (因为)", "囗", "囗 + 大", 1),
    ("为", "wèi", "for; (为什么) why", "丶", "丶 + 力", 1),
    ("所", "suǒ", "place; (所以) therefore", "户", "户 + 斤", 2),
    ("以", "yǐ", "by means of (所以)", "人", "人 + 丶", 2),
    ("如", "rú", "if; like (如果)", "女", "女 + 口", 3),
    ("果", "guǒ", "result; fruit", "木", "日 + 木", 3),
    ("虽", "suī", "although (虽然)", "虫", "口 + 虫", 4),
    ("然", "rán", "so; -ly (虽然)", "灬", "肰 + 灬", 4),
    ("即", "jí", "namely; (即使) even if", "卩", "卩 + 皀", 4),
    ("使", "shǐ", "to cause; to use", "亻", "亻 + 吏", 4),
    ("管", "guǎn", "to mind; (不管) whatever", "竹", "竹 + 官", 4),
    ("既", "jì", "since (既然)", "无", "皀 + 无", 4),
    ("越", "yuè", "more and more (越来越)", "走", "走 + 戉", 4),
    ("其", "qí", "its; (与其) rather than", "八", "八 + 其", 5),
    ("否", "fǒu", "not; whether or not", "口", "不 + 口", 5),

    # --- 16. grammar words that carry a whole structure ----------------------
    ("把", "bǎ", "object marker; handle", "扌", "扌 + 巴", 4),
    ("被", "bèi", "passive marker; quilt", "衤", "衤 + 皮", 4),
    ("从", "cóng", "from; to follow", "人", "人 + 人", 2),
    ("向", "xiàng", "towards", "口", "宀 + 口", 4),
    ("于", "yú", "at; to (formal)", "二", "一 + 二", 5),
    ("通", "tōng", "through (通过)", "辶", "甬 + 辶", 4),
    ("并", "bìng", "and also; (并不) not at all", "八", "丷 + 开", 5),
    ("反", "fǎn", "contrary (反而)", "又", "厂 + 又", 5),
    ("另", "lìng", "other (另一方面)", "口", "口 + 力", 5),
    ("仅", "jǐn", "only (不仅)", "亻", "亻 + 又", 5),

    # --- 17. abstract nouns: the HSK 5-6 diet -------------------------------
    ("事", "shì", "matter; affair", "亅", "一 + 口 + 彐", 3),
    ("物", "wù", "thing; matter", "牛", "牛 + 勿", 4),
    ("题", "tí", "topic (问题)", "页", "是 + 页", 4),
    ("原", "yuán", "cause; original", "厂", "厂 + 白 + 小", 4),
    ("结", "jié", "result; to tie", "纟", "纟 + 吉", 4),
    ("度", "dù", "degree; extent", "广", "广 + 廿 + 又", 4),
    ("程", "chéng", "degree (程度)", "禾", "禾 + 呈", 4),
    ("性", "xìng", "nature; -ity", "忄", "忄 + 生", 5),
    ("质", "zhì", "quality (质量)", "贝", "斤 + 斤 + 贝", 5),
    ("量", "liàng", "quantity", "里", "日 + 里", 5),
    ("影", "yǐng", "shadow; influence", "彡", "景 + 彡", 5),
    ("响", "xiǎng", "to sound; influence", "口", "口 + 向", 5),
    ("系", "xì", "system; relation", "糸", "丿 + 糸", 5),
    ("态", "tài", "attitude; state", "心", "太 + 心", 5),
    ("观", "guān", "view; outlook", "见", "又 + 见", 5),
    ("念", "niàn", "idea; to miss", "心", "今 + 心", 5),
    ("论", "lùn", "to discuss; -ism", "讠", "讠 + 仑", 5),
    ("议", "yì", "opinion (意见)", "讠", "讠 + 义", 5),
    ("标", "biāo", "mark; standard", "木", "木 + 示", 5),
    ("准", "zhǔn", "standard; accurate", "冫", "冫 + 隹", 5),
    ("规", "guī", "rule (规则)", "见", "夫 + 见", 5),
    ("则", "zé", "rule (规则)", "刂", "贝 + 刂", 5),
    ("制", "zhì", "system (制度)", "刂", "制", 5),
    ("值", "zhí", "value (值得)", "亻", "亻 + 直", 5),
    ("义", "yì", "justice; meaning", "丶", "丶 + 乂", 6),
    ("底", "dǐ", "bottom line (底线)", "广", "广 + 氐", 6),
    ("线", "xiàn", "line (底线)", "纟", "纟 + 戋", 6),

    # --- 18. society: the HSK 6 argument ------------------------------------
    ("社", "shè", "society", "礻", "礻 + 土", 5),
    ("化", "huà", "-ise; culture (文化)", "亻", "亻 + 匕", 5),
    ("济", "jì", "economy (经济)", "氵", "氵 + 齐", 5),
    ("政", "zhèng", "government; politics", "攵", "正 + 攵", 6),
    ("治", "zhì", "to govern (政治)", "氵", "氵 + 台", 6),
    ("法", "fǎ", "law", "氵", "氵 + 去", 5),
    ("律", "lǜ", "law (法律)", "彳", "彳 + 聿", 6),
    ("环", "huán", "ring; (环境) environment", "王", "王 + 不", 5),
    ("境", "jìng", "environment (环境)", "土", "土 + 竟", 5),
    ("保", "bǎo", "to protect", "亻", "亻 + 呆", 5),
    ("护", "hù", "to protect (保护)", "扌", "扌 + 户", 5),
    ("发", "fā", "to develop; emit", "又", "丿 + 又", 4),
    ("展", "zhǎn", "to develop (发展)", "尸", "尸 + 廿 + 衣", 4),
    ("变", "biàn", "to change", "又", "亦 + 又", 4),
    ("改", "gǎi", "to change; reform", "攵", "己 + 攵", 5),
    ("革", "gé", "reform (改革)", "革", "革", 6),
    ("提", "tí", "to raise", "扌", "扌 + 是", 5),
    ("效", "xiào", "effect (效果)", "攵", "交 + 攵", 5),
    ("率", "lǜ", "rate (效率)", "玄", "玄 + 十", 6),
    ("增", "zēng", "to increase", "土", "土 + 曾", 6),
    ("减", "jiǎn", "to decrease", "冫", "冫 + 咸", 6),
    ("压", "yā", "pressure", "厂", "厂 + 土 + 丶", 6),
    ("源", "yuán", "source (资源)", "氵", "氵 + 原", 6),
    ("资", "zī", "resource (资源)", "贝", "次 + 贝", 6),
    ("消", "xiāo", "to consume", "氵", "氵 + 肖", 5),
    ("费", "fèi", "to spend (消费)", "贝", "弓 + 贝", 5),
    ("技", "jì", "skill (技术)", "扌", "扌 + 支", 5),
    ("术", "shù", "art; technology", "木", "木 + 丶", 5),
    ("网", "wǎng", "net; the internet", "冂", "冂 + 乂", 4),
    ("信", "xìn", "letter; information", "亻", "亻 + 言", 4),
    ("媒", "méi", "media", "女", "女 + 某", 6),
    ("舆", "yú", "public (舆论)", "车", "𦥑 + 车", 6),

    # --- 19. the formal register --------------------------------------------
    ("鉴", "jiàn", "to examine (鉴于)", "金", "监 + 金", 6),
    ("旨", "zhǐ", "aim (旨在)", "日", "匕 + 日", 6),
    ("予", "yǔ", "to grant (予以)", "亅", "亅 + 卩", 6),
    ("相", "xiāng", "mutual; relevant", "目", "木 + 目", 5),
    ("特", "tè", "special (特此)", "牛", "牛 + 寺", 6),
    ("此", "cǐ", "this (特此)", "止", "止 + 匕", 6),
    ("随", "suí", "to follow (随着)", "阝", "阝 + 隋", 6),
    ("着", "zhe", "aspect: continuing", "目", "⺶ + 目", 5),
    ("综", "zōng", "to synthesise (综合)", "纟", "纟 + 宗", 6),
    ("合", "hé", "to combine (综合)", "口", "人 + 一 + 口", 5),
    ("述", "shù", "to state (上述)", "辶", "术 + 辶", 6),
    ("言", "yán", "words (换言之)", "言", "言", 6),
    ("之", "zhī", "of; it (formal)", "丶", "丶 + 乀", 6),
    ("尽", "jǐn", "as far as (尽管)", "尸", "尸 + 尺", 6),
    ("诚", "chéng", "sincere; admittedly", "讠", "讠 + 成", 6),
    ("厚", "hòu", "thick; to praise", "厂", "厂 + 日 + 子", 6),
    ("非", "fēi", "wrong; to blame", "非", "非", 6),
    ("趋", "qū", "trend (趋势)", "走", "走 + 刍", 6),
    ("势", "shì", "trend; force", "力", "执 + 力", 6),
    ("促", "cù", "to promote", "亻", "亻 + 足", 6),
    ("异", "yì", "difference (差异)", "廾", "巳 + 廾", 6),
    ("差", "chā", "difference", "工", "羊 + 工", 5),

    # --- 20. people in the abstract -----------------------------------------
    ("人", "rén", "person", "人", "人", 1),
    ("民", "mín", "the people", "氏", "尸 + 氏", 5),
    ("众", "zhòng", "crowd; the public", "人", "人 + 人 + 人", 6),
    ("者", "zhě", "the one who", "老", "老 + 日", 5),
    ("专", "zhuān", "specialist; expert", "一", "一 + 丨", 5),
    ("业", "yè", "profession; industry", "业", "业", 5),
    ("职", "zhí", "job; position", "耳", "耳 + 只", 5),
    ("力", "lì", "strength; ability", "力", "力", 4),
    ("精", "jīng", "spirit; essence", "米", "米 + 青", 6),
    ("神", "shén", "spirit; mind", "礻", "礻 + 申", 6),
    ("努", "nǔ", "to exert (努力)", "力", "奴 + 力", 4),
    ("持", "chí", "to hold; persist", "扌", "扌 + 寺", 5),
    ("坚", "jiān", "firm; to persist", "土", "𠬤 + 土", 5),
    ("决", "jué", "to decide", "冫", "冫 + 夬", 5),
    ("定", "dìng", "to decide; fixed", "宀", "宀 + 廴", 4),
    ("选", "xuǎn", "to choose", "辶", "先 + 辶", 5),
    ("择", "zé", "to choose (选择)", "扌", "扌 + 睪", 5),
    ("计", "jì", "to plan; to count", "讠", "讠 + 十", 5),
    ("划", "huà", "to plan (计划)", "刂", "戈 + 刂", 5),
    ("备", "bèi", "to prepare", "夂", "夂 + 田", 5),
    ("突", "tū", "sudden", "穴", "穴 + 犬", 6),
    ("显", "xiǎn", "obvious", "日", "日 + 业", 6),
    ("深", "shēn", "deep", "氵", "氵 + 罙", 5),
    ("淡", "dàn", "light; faint", "氵", "氵 + 炎", 6),
    ("楚", "chǔ", "clear (清楚)", "木", "林 + 疋", 5),
    ("清", "qīng", "clear (清楚)", "氵", "氵 + 青", 5),
]

# The rest of the table, in a part of its own: characters the course actually
# uses that were missing from CORE. Without it the HSK 6 lessons find nothing
# to teach - their vocabulary is made almost entirely of characters CORE has
# never seen - so the band where reading matters most gets no character steps.
# Only ImportError is swallowed. `except Exception` also caught SyntaxError,
# so one bad row anywhere in the part made all of it disappear while the
# checker still reported clean.
try:
    from .hanzi_b import CORE_B as _CORE_B
except ImportError:
    if __package__:
        _CORE_B = []
    else:  # run as a script: no package context, so bootstrap the repo root
        import os as _os
        import sys as _sys

        _sys.path.insert(0, _os.path.abspath(_os.path.join(
            _os.path.dirname(__file__), "..", "..", "..")))
        try:
            from server.course.zh.hanzi_b import CORE_B as _CORE_B
        except ImportError:
            _CORE_B = []
# entries above win, so a disagreement is never a surprise
_in_core = {row[0] for row in CORE}
CORE.extend(row for row in _CORE_B if row[0] not in _in_core)

_HANZI_RE = re.compile(r"[一-鿿]")

_BY_CHAR: Dict[str, Tuple[str, str, str, str, int]] = {}
for _char, _pinyin, _en, _radical, _components, _stage in CORE:
    # first entry wins: the early stages carry the everyday reading
    _BY_CHAR.setdefault(_char, (_pinyin, _en, _radical, _components, _stage))


def hanzi_in(text: str) -> List[str]:
    """Every character in a line, in order, no duplicates."""
    out: List[str] = []
    for ch in _HANZI_RE.findall(text or ""):
        if ch not in out:
            out.append(ch)
    return out


def lookup(char: str) -> Optional[dict]:
    row = _BY_CHAR.get(char)
    if not row:
        return None
    pinyin, en, radical, components, stage = row
    return {
        "char": char,
        "pinyin": pinyin,
        "en": en,
        "radical": radical,
        "components": components,
        "stage": stage,
    }


def for_lesson(words: List[Tuple[str, str, str]], count: int, known: Optional[Set[str]] = None) -> List[dict]:
    """The characters this lesson should teach, derived from its vocabulary.

    Derived rather than scheduled for the same reason as the Japanese table:
    a character never turns up before a word that uses it, so the learner
    always has somewhere to hang it - and a gap in CORE costs a step rather
    than breaking the lesson.

    Characters already introduced by an earlier lesson are skipped, and the
    ones that appear in the most words of the lesson come first, because a
    character you are about to meet three times is worth more than one you
    will meet once.
    """
    known = known or set()
    seen: Dict[str, int] = {}
    for text, _reading, _en in words or []:
        for ch in hanzi_in(text):
            seen[ch] = seen.get(ch, 0) + 1
    candidates = [
        (freq, ch) for ch, freq in seen.items()
        if ch not in known and ch in _BY_CHAR
    ]
    # most-used first; the character order inside CORE breaks ties, so the
    # derivation is stable and a lesson always teaches the same characters
    candidates.sort(key=lambda pair: (-pair[0], CORE_INDEX.get(pair[1], 999)))
    out: List[dict] = []
    for _freq, ch in candidates[: max(0, count)]:
        row = lookup(ch)
        if row:
            out.append(row)
    return out


CORE_INDEX: Dict[str, int] = {char: i for i, (char, *_rest) in enumerate(CORE)}


def check() -> List[str]:
    """The mechanical rules above, so the table cannot quietly rot.

    Run it the way you run pinyin_check.py. Also checked there: every pinyin
    in this table is a legal Mandarin syllable, because a wrong tone printed
    on the glasses is a wrong word taught.
    """
    problems: List[str] = []
    seen: Dict[str, str] = {}
    for char, pinyin, en, _radical, _components, stage in CORE:
        where = f"{char} ({pinyin})"
        if len(char) != 1 or not _HANZI_RE.match(char):
            problems.append(f"{where}: not a single hanzi")
        if not pinyin or not en:
            problems.append(f"{where}: missing pinyin or gloss")
        if not 1 <= int(stage) <= 6:
            problems.append(f"{where}: stage {stage} outside 1-6")
        if char in seen and seen[char] != pinyin:
            problems.append(f"{where}: duplicate entry, also read {seen[char]}")
        seen.setdefault(char, pinyin)
    try:
        from .pinyin_check import check_pairs
    except Exception:  # pragma: no cover - the validator is part of the course
        return problems
    problems += check_pairs(((c, p, e) for c, p, e, _r, _co, _s in CORE), "hanzi")
    return problems


def stats() -> dict:
    by_stage: Dict[int, int] = {}
    for _char, _p, _e, _r, _co, stage in CORE:
        by_stage[stage] = by_stage.get(stage, 0) + 1
    return {"characters": len(_BY_CHAR), "rows": len(CORE), "by_stage": dict(sorted(by_stage.items()))}


if __name__ == "__main__":
    print(stats())
    found = check()
    print(f"{len(found)} problem(s)")
    for p in found:
        print("  " + p)

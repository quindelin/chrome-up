"""“Think in <language>”: English thought -> a line you must then say.

Two backends:
  llm         OpenAI-compatible chat model (set OPENAI_API_KEY). Best quality,
              returns the line + its reading + a literal gloss.
  phrasebook  Offline pattern matcher + lexicon. Always available, and it is
              what you get when there is no API key.

Both are per-language: `server/think.py` holds a Mandarin and a Japanese
phrasebook and prompt, picked by `cfg["language"]`.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .course import LANG_NAMES, normalize


@dataclass
class Target:
    text: str       # the line as it is written
    reading: str    # pinyin / kana
    en: str
    source: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "reading": self.reading,
            "en": self.en,
            "source": self.source,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# offline phrasebook - Mandarin
# ---------------------------------------------------------------------------

ZH_LEXICON: Dict[str, Tuple[str, str]] = {
    # places
    "bathroom": ("厕所", "cèsuǒ"),
    "restroom": ("厕所", "cèsuǒ"),
    "toilet": ("厕所", "cèsuǒ"),
    "subway": ("地铁", "dìtiě"),
    "subway station": ("地铁站", "dìtiě zhàn"),
    "metro": ("地铁", "dìtiě"),
    "airport": ("机场", "jīchǎng"),
    "train station": ("火车站", "huǒchē zhàn"),
    "station": ("车站", "chēzhàn"),
    "hotel": ("酒店", "jiǔdiàn"),
    "bank": ("银行", "yínháng"),
    "hospital": ("医院", "yīyuàn"),
    "restaurant": ("餐馆", "cānguǎn"),
    "shop": ("商店", "shāngdiàn"),
    "store": ("商店", "shāngdiàn"),
    "market": ("市场", "shìchǎng"),
    "park": ("公园", "gōngyuán"),
    "museum": ("博物馆", "bówùguǎn"),
    "pharmacy": ("药店", "yàodiàn"),
    "taxi": ("出租车", "chūzū chē"),
    "bus": ("公共汽车", "gōnggòng qìchē"),
    "bus stop": ("公交站", "gōngjiāo zhàn"),
    # food & drink
    "coffee": ("咖啡", "kāfēi"),
    "tea": ("茶", "chá"),
    "water": ("水", "shuǐ"),
    "beer": ("啤酒", "píjiǔ"),
    "wine": ("红酒", "hóngjiǔ"),
    "rice": ("米饭", "mǐfàn"),
    "noodles": ("面条", "miàntiáo"),
    "beef noodles": ("牛肉面", "niúròu miàn"),
    "dumplings": ("饺子", "jiǎozi"),
    "beef": ("牛肉", "niúròu"),
    "chicken": ("鸡肉", "jīròu"),
    "pork": ("猪肉", "zhūròu"),
    "fish": ("鱼", "yú"),
    "vegetables": ("蔬菜", "shūcài"),
    "egg": ("鸡蛋", "jīdàn"),
    "soup": ("汤", "tāng"),
    "bread": ("面包", "miànbāo"),
    "apple": ("苹果", "píngguǒ"),
    "breakfast": ("早饭", "zǎofàn"),
    "lunch": ("午饭", "wǔfàn"),
    "dinner": ("晚饭", "wǎnfàn"),
    "menu": ("菜单", "càidān"),
    "bill": ("账单", "zhàngdān"),
    # things
    "phone": ("手机", "shǒujī"),
    "power bank": ("充电宝", "chōngdiàn bǎo"),
    "charger": ("充电器", "chōngdiàn qì"),
    "map": ("地图", "dìtú"),
    "ticket": ("票", "piào"),
    "room": ("房间", "fángjiān"),
    "bag": ("包", "bāo"),
    "shirt": ("衬衫", "chènshān"),
    "shoes": ("鞋", "xié"),
    # qualities
    "spicy": ("辣", "là"),
    "spicy food": ("辣的", "là de"),
    "hot water": ("热水", "rè shuǐ"),
    "ice": ("冰", "bīng"),
    "credit card": ("信用卡", "xìnyòng kǎ"),
    "hot": ("热", "rè"),
    "cold": ("冷", "lěng"),
    "big": ("大", "dà"),
    "small": ("小", "xiǎo"),
    "cheap": ("便宜", "piányi"),
    "expensive": ("贵", "guì"),
    "good": ("好", "hǎo"),
    "delicious": ("好吃", "hǎochī"),
    "fast": ("快", "kuài"),
    "slow": ("慢", "màn"),
    "near": ("近", "jìn"),
    "far": ("远", "yuǎn"),
    # nationalities
    "american": ("美国人", "Měiguórén"),
    "chinese": ("中国人", "Zhōngguórén"),
    "british": ("英国人", "Yīngguórén"),
    "english": ("英国人", "Yīngguórén"),
    "canadian": ("加拿大人", "Jiānádà rén"),
    "australian": ("澳大利亚人", "Àodàlìyà rén"),
    "french": ("法国人", "Fǎguó rén"),
    "german": ("德国人", "Déguó rén"),
    "japanese": ("日本人", "Rìběn rén"),
    "korean": ("韩国人", "Hánguó rén"),
    # abstract
    "chinese language": ("中文", "Zhōngwén"),
    "chinese food": ("中国菜", "Zhōngguó cài"),
    "english language": ("英语", "Yīngyǔ"),
    "japanese language": ("日语", "Rìyǔ"),
}

ZH_PHRASES: Dict[str, Tuple[str, str]] = {
    "hello": ("你好", "nǐ hǎo"),
    "hi": ("你好", "nǐ hǎo"),
    "good morning": ("早上好", "zǎoshang hǎo"),
    "good evening": ("晚上好", "wǎnshang hǎo"),
    "goodbye": ("再见", "zàijiàn"),
    "bye": ("再见", "zàijiàn"),
    "see you tomorrow": ("明天见", "míngtiān jiàn"),
    "thank you": ("谢谢", "xièxie"),
    "thanks": ("谢谢", "xièxie"),
    "thank you very much": ("非常感谢", "fēicháng gǎnxiè"),
    "you are welcome": ("不客气", "bú kèqi"),
    "excuse me": ("请问", "qǐng wèn"),
    "sorry": ("对不起", "duìbuqǐ"),
    "i am sorry": ("对不起", "duìbuqǐ"),
    "never mind": ("没关系", "méi guānxi"),
    "please": ("请", "qǐng"),
    "i do not understand": ("我不懂", "wǒ bù dǒng"),
    "i don't understand": ("我不懂", "wǒ bù dǒng"),
    "please say it again": ("请再说一遍", "qǐng zài shuō yí biàn"),
    "say it again please": ("请再说一遍", "qǐng zài shuō yí biàn"),
    "please speak slower": ("请慢一点", "qǐng màn yìdiǎn"),
    "speak slower please": ("请慢一点", "qǐng màn yìdiǎn"),
    "do you speak english": ("你会说英语吗？", "nǐ huì shuō Yīngyǔ ma?"),
    "i cannot speak chinese": ("我不会说中文", "wǒ bú huì shuō Zhōngwén"),
    "i speak a little chinese": ("我会说一点点中文", "wǒ huì shuō yìdiǎndiǎn Zhōngwén"),
    "i am hungry": ("我饿了", "wǒ è le"),
    "i am thirsty": ("我渴了", "wǒ kě le"),
    "i am tired": ("我累了", "wǒ lèi le"),
    "i am sick": ("我生病了", "wǒ shēngbìng le"),
    "i am cold": ("我很冷", "wǒ hěn lěng"),
    "i am hot": ("我很热", "wǒ hěn rè"),
    "i am lost": ("我迷路了", "wǒ mí lù le"),
    "i am late": ("我迟到了", "wǒ chídào le"),
    "i am in a hurry": ("我很急", "wǒ hěn jí"),
    "help me": ("帮帮我", "bāngbang wǒ"),
    "what time is it": ("现在几点？", "xiànzài jǐ diǎn?"),
    "how are you": ("你好吗？", "nǐ hǎo ma?"),
    "i am fine": ("我很好", "wǒ hěn hǎo"),
    "nice to meet you": ("很高兴认识你", "hěn gāoxìng rènshi nǐ"),
    "what is your name": ("你叫什么名字？", "nǐ jiào shénme míngzi?"),
    "my name is john": ("我叫约翰", "wǒ jiào Yuēhàn"),
    "where are you from": ("你从哪里来？", "nǐ cóng nǎlǐ lái?"),
    "i am american": ("我是美国人", "wǒ shì Měiguórén"),
    "wait a moment": ("等一下", "děng yíxià"),
    "hurry up": ("快一点", "kuài yìdiǎn"),
    "it is delicious": ("很好吃", "hěn hǎochī"),
    "it is too expensive": ("太贵了", "tài guì le"),
    "a little cheaper please": ("便宜一点", "piányi yìdiǎn"),
    "the bill please": ("买单", "mǎidān"),
    "i will take it": ("我要了", "wǒ yào le"),
    "i am just looking": ("我看看", "wǒ kànkàn"),
    "can i pay by card": ("可以刷卡吗？", "kěyǐ shuā kǎ ma?"),
    "do you have wechat pay": ("可以用微信吗？", "kěyǐ yòng Wēixìn ma?"),
    "i like it": ("我喜欢", "wǒ xǐhuan"),
    "i don't like it": ("我不喜欢", "wǒ bù xǐhuan"),
    "really": ("真的吗？", "zhēn de ma?"),
    "why": ("为什么？", "wèishénme?"),
    "ok": ("好", "hǎo"),
    "no problem": ("没关系", "méi guānxi"),
}

ZH_PATTERNS = [
    (r"^(?:i )?(?:want|would like) to go to (?:the )?(?P<x>.+)$",
     "我要去{x}", "wǒ yào qù {x}", "I want to go to {x}"),
    (r"^how (?:do i get|can i get) to (?:the )?(?P<x>.+)$",
     "去{x}怎么走？", "qù {x} zěnme zǒu?", "How do I get to {x}?"),
    (r"^where (?:is|are) (?:the )?(?P<x>.+)$",
     "{x}在哪里？", "{x} zài nǎlǐ?", "Where is the {x}?"),
    (r"^how much (?:is|are|for) (?:the )?(?P<x>.+)$",
     "{x}多少钱？", "{x} duōshao qián?", "How much is the {x}?"),
    (r"^(?:do you have|is there|are there) (?:any )?(?P<x>.+)$",
     "有没有{x}？", "yǒu méiyǒu {x}?", "Do you have {x}?"),
    (r"^(?:i )?(?:want|would like) (?:to (?:buy|order|have) )?(?:a |an |some |the )?(?P<x>.+)$",
     "我要{x}", "wǒ yào {x}", "I want {x}"),
    (r"^(?:i )?need (?:a |an |some |the )?(?P<x>.+)$",
     "我需要{x}", "wǒ xūyào {x}", "I need {x}"),
    (r"^(?:can i have|could i have|give me) (?:a |an |some |the )?(?P<x>.+)$",
     "请给我{x}", "qǐng gěi wǒ {x}", "Please give me {x}"),
    (r"^(?:i )?like (?:the )?(?P<x>.+)$",
     "我喜欢{x}", "wǒ xǐhuan {x}", "I like {x}"),
    (r"^(?:i )?(?:don't|do not) like (?:the )?(?P<x>.+)$",
     "我不喜欢{x}", "wǒ bù xǐhuan {x}", "I don't like {x}"),
    (r"^(?:i am|i'm) (?:a |an )?(?P<x>.+)$",
     "我是{x}", "wǒ shì {x}", "I am {x}"),
    (r"^my name is (?P<x>.+)$",
     "我叫{x}", "wǒ jiào {x}", "My name is {x}"),
    (r"^(?:i )?(?:am )?looking for (?:a |an |the )?(?P<x>.+)$",
     "我找{x}", "wǒ zhǎo {x}", "I'm looking for {x}"),
    (r"^how (?:far|long) (?:is|to) (?:the )?(?P<x>.+)$",
     "到{x}要多长时间？", "dào {x} yào duō cháng shíjiān?", "How long to {x}?"),
]

# ---------------------------------------------------------------------------
# offline phrasebook - Japanese
# ---------------------------------------------------------------------------

JA_LEXICON: Dict[str, Tuple[str, str]] = {
    # places
    "bathroom": ("トイレ", "トイレ"),
    "restroom": ("トイレ", "トイレ"),
    "toilet": ("トイレ", "トイレ"),
    "subway": ("地下鉄", "ちかてつ"),
    "subway station": ("地下鉄の駅", "ちかてつのえき"),
    "metro": ("地下鉄", "ちかてつ"),
    "airport": ("空港", "くうこう"),
    "train station": ("駅", "えき"),
    "station": ("駅", "えき"),
    "hotel": ("ホテル", "ホテル"),
    "bank": ("銀行", "ぎんこう"),
    "hospital": ("病院", "びょういん"),
    "restaurant": ("レストラン", "レストラン"),
    "shop": ("店", "みせ"),
    "store": ("店", "みせ"),
    "market": ("市場", "いちば"),
    "park": ("公園", "こうえん"),
    "museum": ("美術館", "びじゅつかん"),
    "pharmacy": ("薬局", "やっきょく"),
    "taxi": ("タクシー", "タクシー"),
    "bus": ("バス", "バス"),
    "bus stop": ("バス停", "バスてい"),
    "convenience store": ("コンビニ", "コンビニ"),
    # food & drink
    "coffee": ("コーヒー", "コーヒー"),
    "tea": ("お茶", "おちゃ"),
    "water": ("水", "みず"),
    "beer": ("ビール", "ビール"),
    "wine": ("ワイン", "ワイン"),
    "rice": ("ごはん", "ごはん"),
    "noodles": ("麺", "めん"),
    "ramen": ("ラーメン", "ラーメン"),
    "sushi": ("寿司", "すし"),
    "dumplings": ("餃子", "ぎょうざ"),
    "beef": ("牛肉", "ぎゅうにく"),
    "chicken": ("鶏肉", "とりにく"),
    "pork": ("豚肉", "ぶたにく"),
    "fish": ("魚", "さかな"),
    "vegetables": ("野菜", "やさい"),
    "egg": ("卵", "たまご"),
    "soup": ("スープ", "スープ"),
    "bread": ("パン", "パン"),
    "apple": ("りんご", "りんご"),
    "breakfast": ("朝ごはん", "あさごはん"),
    "lunch": ("昼ごはん", "ひるごはん"),
    "dinner": ("晩ごはん", "ばんごはん"),
    "menu": ("メニュー", "メニュー"),
    "bill": ("お会計", "おかいけい"),
    # things
    "phone": ("スマホ", "スマホ"),
    "power bank": ("モバイルバッテリー", "モバイルバッテリー"),
    "charger": ("充電器", "じゅうでんき"),
    "map": ("地図", "ちず"),
    "ticket": ("切符", "きっぷ"),
    "room": ("部屋", "へや"),
    "bag": ("かばん", "かばん"),
    "shirt": ("シャツ", "シャツ"),
    "shoes": ("靴", "くつ"),
    # qualities
    "spicy": ("辛い", "からい"),
    "spicy food": ("辛い料理", "からいりょうり"),
    "hot water": ("お湯", "おゆ"),
    "ice": ("氷", "こおり"),
    "credit card": ("カード", "カード"),
    "hot": ("暑い", "あつい"),
    "cold": ("寒い", "さむい"),
    "big": ("大きい", "おおきい"),
    "small": ("小さい", "ちいさい"),
    "cheap": ("安い", "やすい"),
    "expensive": ("高い", "たかい"),
    "good": ("いい", "いい"),
    "delicious": ("おいしい", "おいしい"),
    "fast": ("速い", "はやい"),
    "slow": ("遅い", "おそい"),
    "near": ("近い", "ちかい"),
    "far": ("遠い", "とおい"),
    # nationalities
    "american": ("アメリカ人", "あめりかじん"),
    "japanese": ("日本人", "にほんじん"),
    "british": ("イギリス人", "いぎりすじん"),
    "english": ("イギリス人", "いぎりすじん"),
    "canadian": ("カナダ人", "かなだじん"),
    "australian": ("オーストラリア人", "おーすとらりあじん"),
    "french": ("フランス人", "ふらんすじん"),
    "german": ("ドイツ人", "どいつじん"),
    "chinese": ("中国人", "ちゅうごくじん"),
    "korean": ("韓国人", "かんこくじん"),
    # abstract
    "japanese language": ("日本語", "にほんご"),
    "english language": ("英語", "えいご"),
    "chinese language": ("中国語", "ちゅうごくご"),
}

JA_PHRASES: Dict[str, Tuple[str, str]] = {
    "hello": ("こんにちは", "こんにちは"),
    "hi": ("こんにちは", "こんにちは"),
    "good morning": ("おはようございます", "おはようございます"),
    "good evening": ("こんばんは", "こんばんは"),
    "goodbye": ("さようなら", "さようなら"),
    "bye": ("さようなら", "さようなら"),
    "see you tomorrow": ("またあした", "またあした"),
    "thank you": ("ありがとう", "ありがとう"),
    "thanks": ("ありがとう", "ありがとう"),
    "thank you very much": ("ありがとうございます", "ありがとうございます"),
    "you are welcome": ("どういたしまして", "どういたしまして"),
    "excuse me": ("すみません", "すみません"),
    "sorry": ("ごめんなさい", "ごめんなさい"),
    "i am sorry": ("ごめんなさい", "ごめんなさい"),
    "never mind": ("大丈夫です", "だいじょうぶです"),
    "no problem": ("大丈夫です", "だいじょうぶです"),
    "please": ("お願いします", "おねがいします"),
    "i do not understand": ("わかりません", "わかりません"),
    "i don't understand": ("わかりません", "わかりません"),
    "please say it again": ("もう一度お願いします", "もういちどおねがいします"),
    "say it again please": ("もう一度お願いします", "もういちどおねがいします"),
    "please speak slower": ("ゆっくりお願いします", "ゆっくりおねがいします"),
    "speak slower please": ("ゆっくりお願いします", "ゆっくりおねがいします"),
    "do you speak english": ("英語を話せますか", "えいごをはなせますか"),
    "i cannot speak japanese": ("日本語が話せません", "にほんごがはなせません"),
    "i speak a little japanese": ("日本語が少し話せます", "にほんごがすこしはなせます"),
    "i am hungry": ("おなかがすきました", "おなかがすきました"),
    "i am thirsty": ("のどがかわきました", "のどがかわきました"),
    "i am tired": ("疲れました", "つかれました"),
    "i am sick": ("気分が悪いです", "きぶんがわるいです"),
    "i am cold": ("寒いです", "さむいです"),
    "i am hot": ("暑いです", "あついです"),
    "i am lost": ("道に迷いました", "みちにまよいました"),
    "i am late": ("遅れました", "おくれました"),
    "i am in a hurry": ("急いでいます", "いそいでいます"),
    "help me": ("助けて", "たすけて"),
    "what time is it": ("今何時ですか", "いまなんじですか"),
    "how are you": ("お元気ですか", "おげんきですか"),
    "i am fine": ("元気です", "げんきです"),
    "nice to meet you": ("初めまして", "はじめまして"),
    "what is your name": ("お名前は", "おなまえは"),
    "my name is john": ("ジョンです", "じょんです"),
    "where are you from": ("出身はどこですか", "しゅっしんはどこですか"),
    "i am american": ("アメリカ人です", "あめりかじんです"),
    "wait a moment": ("ちょっと待ってください", "ちょっとまってください"),
    "hurry up": ("急いでください", "いそいでください"),
    "it is delicious": ("おいしいです", "おいしいです"),
    "it is too expensive": ("高すぎます", "たかすぎます"),
    "a little cheaper please": ("もう少し安くしてください", "もうすこしやすくしてください"),
    "the bill please": ("お会計をお願いします", "おかいけいをおねがいします"),
    "i will take it": ("これをください", "これをください"),
    "i am just looking": ("見ているだけです", "みているだけです"),
    "can i pay by card": ("カードで払えますか", "カードではらえますか"),
    "i like it": ("好きです", "すきです"),
    "i don't like it": ("好きじゃありません", "すきじゃありません"),
    "really": ("本当ですか", "ほんとうですか"),
    "why": ("どうしてですか", "どうしてですか"),
    "ok": ("はい", "はい"),
}

JA_PATTERNS = [
    (r"^(?:i )?(?:want|would like) to go to (?:the )?(?P<x>.+)$",
     "{x}に行きたいです", "{x}にいきたいです", "I want to go to {x}"),
    (r"^how (?:do i get|can i get) to (?:the )?(?P<x>.+)$",
     "{x}へはどうやって行きますか", "{x}へはどうやっていきますか", "How do I get to {x}?"),
    (r"^where (?:is|are) (?:the )?(?P<x>.+)$",
     "{x}はどこですか", "{x}はどこですか", "Where is the {x}?"),
    (r"^how much (?:is|are|for) (?:the )?(?P<x>.+)$",
     "{x}はいくらですか", "{x}はいくらですか", "How much is the {x}?"),
    (r"^(?:do you have|is there|are there) (?:any )?(?P<x>.+)$",
     "{x}はありますか", "{x}はありますか", "Do you have {x}?"),
    (r"^(?:i )?(?:want|would like) (?:to (?:buy|order|have) )?(?:a |an |some |the )?(?P<x>.+)$",
     "{x}をお願いします", "{x}をおねがいします", "{x}, please"),
    (r"^(?:i )?need (?:a |an |some |the )?(?P<x>.+)$",
     "{x}が必要です", "{x}がひつようです", "I need {x}"),
    (r"^(?:can i have|could i have|give me) (?:a |an |some |the )?(?P<x>.+)$",
     "{x}をください", "{x}をください", "{x}, please"),
    (r"^(?:i )?like (?:the )?(?P<x>.+)$",
     "{x}が好きです", "{x}がすきです", "I like {x}"),
    (r"^(?:i )?(?:don't|do not) like (?:the )?(?P<x>.+)$",
     "{x}は好きじゃありません", "{x}はすきじゃありません", "I don't like {x}"),
    (r"^(?:i am|i'm) (?:a |an )?(?P<x>.+)$",
     "{x}です", "{x}です", "I am {x}"),
    (r"^my name is (?P<x>.+)$",
     "{x}です", "{x}です", "My name is {x}"),
    (r"^(?:i )?(?:am )?looking for (?:a |an |the )?(?P<x>.+)$",
     "{x}を探しています", "{x}をさがしています", "I'm looking for {x}"),
    (r"^how (?:far|long) (?:is|to) (?:the )?(?P<x>.+)$",
     "{x}までどのくらいかかりますか", "{x}までどのくらいかかりますか", "How long to {x}?"),
]

# Spanish: a small offline phrasebook. The reading slot is empty - Spanish
# is spelled the way it sounds, so there is nothing to put above the line.
ES_LEXICON: Dict[str, Tuple[str, str]] = {
    "coffee": ("un café", ""), "tea": ("un té", ""), "water": ("agua", ""),
    "beer": ("una cerveza", ""), "wine": ("vino", ""), "bread": ("pan", ""),
    "bathroom": ("el baño", ""), "restroom": ("el baño", ""), "toilet": ("el baño", ""),
    "station": ("la estación", ""), "train station": ("la estación de tren", ""),
    "bus stop": ("la parada de autobús", ""), "airport": ("el aeropuerto", ""),
    "hotel": ("el hotel", ""), "bank": ("el banco", ""), "pharmacy": ("la farmacia", ""),
    "hospital": ("el hospital", ""), "market": ("el mercado", ""), "beach": ("la playa", ""),
    "museum": ("el museo", ""), "restaurant": ("el restaurante", ""),
    "ticket": ("el billete", ""), "menu": ("la carta", ""), "bill": ("la cuenta", ""),
    "check": ("la cuenta", ""), "help": ("ayuda", ""), "taxi": ("un taxi", ""),
    "this": ("esto", ""), "that": ("eso", ""),
}
ES_PHRASES: Dict[str, Tuple[str, str]] = {
    "hello": ("Hola.", ""), "good morning": ("Buenos días.", ""),
    "good afternoon": ("Buenas tardes.", ""), "good evening": ("Buenas noches.", ""),
    "good night": ("Buenas noches.", ""), "goodbye": ("Adiós.", ""),
    "see you later": ("Hasta luego.", ""), "see you tomorrow": ("Hasta mañana.", ""),
    "thank you": ("Gracias.", ""), "thanks": ("Gracias.", ""),
    "thank you very much": ("Muchas gracias.", ""), "you are welcome": ("De nada.", ""),
    "please": ("Por favor.", ""), "excuse me": ("Perdón.", ""), "sorry": ("Lo siento.", ""),
    "yes": ("Sí.", ""), "no": ("No.", ""), "ok": ("Vale.", ""), "okay": ("Vale.", ""),
    "i do not understand": ("No entiendo.", ""), "i do not know": ("No sé.", ""),
    "slowly please": ("Más despacio, por favor.", ""),
    "more slowly please": ("Más despacio, por favor.", ""),
    "again please": ("Otra vez, por favor.", ""), "one more time": ("Otra vez, por favor.", ""),
    "do you speak english": ("¿Habla inglés?", ""),
    "how are you": ("¿Qué tal?", ""), "i am fine": ("Estoy bien, gracias.", ""),
    "what is your name": ("¿Cómo te llamas?", ""), "nice to meet you": ("Mucho gusto.", ""),
    "how much is it": ("¿Cuánto cuesta?", ""), "the check please": ("La cuenta, por favor.", ""),
    "the bill please": ("La cuenta, por favor.", ""), "cheers": ("¡Salud!", ""),
    "i am hungry": ("Tengo hambre.", ""), "i am thirsty": ("Tengo sed.", ""),
    "i am tired": ("Estoy cansado.", ""), "really": ("¿En serio?", ""),
    "what time is it": ("¿Qué hora es?", ""),
}
ES_PATTERNS: List[Tuple[str, str, str, str]] = [
    (r"^i (?:would like|want) (?:a |an |some )?(?P<x>.+)$",
     "Quiero {x}, por favor.", "", "I'd like {x}, please."),
    (r"^where is (?:the )?(?P<x>.+)$",
     "¿Dónde está {x}?", "", "Where is {x}?"),
    (r"^how much is (?:the )?(?P<x>.+)$",
     "¿Cuánto cuesta {x}?", "", "How much is {x}?"),
    (r"^i am looking for (?:the |a |an )?(?P<x>.+)$",
     "Busco {x}.", "", "I'm looking for {x}."),
    (r"^is there (?:a |an )?(?P<x>.+?)(?: near here| nearby)?$",
     "¿Hay {x} por aquí?", "", "Is there {x} around here?"),
]

LEXICON = {"zh": ZH_LEXICON, "ja": JA_LEXICON, "es": ES_LEXICON}
PHRASES = {"zh": ZH_PHRASES, "ja": JA_PHRASES, "es": ES_PHRASES}
PATTERNS = {"zh": ZH_PATTERNS, "ja": JA_PATTERNS, "es": ES_PATTERNS}

_FILLER = re.compile(r"^(?:the|a|an|some|my|your|please)\s+")

SYSTEM_PROMPT = {
    "zh": (
        "You are a Mandarin coach inside a hands-free glasses app. Turn the user's English "
        "thought into natural SPOKEN Mandarin a beginner can repeat out loud.\n"
        "Rules: HSK1-HSK2 vocabulary only; max 14 Chinese characters; no rare or literary "
        "words; prefer 你/我/我们; use 吗 for yes-no questions; keep the English word order "
        "out of it - produce what a Beijing taxi driver would actually say.\n"
        "Reply with JSON only: {\"text\": str, \"reading\": pinyin with tone marks, "
        "\"literal\": short English gloss, \"tips\": one short pronunciation tip}."
    ),
    "ja": (
        "You are a Japanese coach inside a hands-free glasses app. Turn the user's English "
        "thought into natural SPOKEN Japanese a beginner can repeat out loud.\n"
        "Rules: JLPT N5-N4 vocabulary only; keep it short; end polite sentences with "
        "です/ます; no literary or archaic forms; drop pronouns that Japanese would drop; "
        "never translate word-for-word - produce what a Tokyo shop assistant would say.\n"
        "Reply with JSON only: {\"text\": str in normal Japanese script, \"reading\": the "
        "same line in kana, \"literal\": short English gloss, \"tips\": one short "
        "pronunciation tip}."
    ),
    "es": (
        "You are a Spanish coach inside a hands-free glasses app. Turn the user's English "
        "thought into natural SPOKEN Spanish a beginner can repeat out loud.\n"
        "Rules: CEFR A1-A2 vocabulary only; keep it short; drop subject pronouns the way "
        "Spanish does; use tú unless the thought is clearly to a stranger or official, then "
        "usted; get gender and number agreement right; Peninsular (Spain) usage to match "
        "the course - billete, zumo, móvil - unless the user writes Latin American forms; "
        "produce what a waiter in Madrid would say.\n"
        "Reply with JSON only: {\"text\": str, \"reading\": \"\" (Spanish needs no "
        "reading line), \"literal\": short English gloss, \"tips\": one short "
        "pronunciation tip - stress, r/rr, the soft d, linking}."
    ),
}


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[.!?。！？,，]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b(i'm|im)\b", "i am", text)
    text = re.sub(r"\b(don't|dont)\b", "do not", text)
    text = re.sub(r"\b(can't|cant)\b", "can not", text)
    text = re.sub(r"\b(i'd|id)\b", "i would", text)
    text = re.sub(r"\b(it's|its)\b", "it is", text)
    return text.strip()


def _lookup(word: str, lang: str) -> Optional[Tuple[str, str]]:
    lex = LEXICON.get(lang, ZH_LEXICON)
    w = _FILLER.sub("", word.strip().lower())
    w = re.sub(r"\b(?:the|a|an|some|my)\b\s*", "", w).strip()
    if w in lex:
        return lex[w]
    # try dropping a trailing plural s
    if w.endswith("s") and w[:-1] in lex:
        return lex[w[:-1]]
    return None


def phrasebook(text: str, lang: str = "zh") -> Target:
    """Deterministic English -> target language, no network."""
    lang = normalize(lang)
    norm = _norm(text)
    phrases = PHRASES.get(lang, ZH_PHRASES)
    patterns = PATTERNS.get(lang, ZH_PATTERNS)

    if norm in phrases:
        value, reading = phrases[norm]
        return Target(value, reading, text, "phrasebook")

    for pattern, text_tpl, reading_tpl, en_tpl in patterns:
        m = re.match(pattern, norm)
        if not m:
            continue
        groups = {k: v for k, v in m.groupdict().items() if v}
        filled_t, filled_r, filled_en = {}, {}, {}
        missing = []
        for key, value in groups.items():
            entry = _lookup(value, lang)
            if entry:
                filled_t[key] = entry[0]
                filled_r[key] = entry[1]
                filled_en[key] = value
            else:
                filled_t[key] = value
                filled_r[key] = ""
                filled_en[key] = value
                missing.append(value)
        try:
            out_text = text_tpl.format(**filled_t)
            reading = reading_tpl.format(**filled_r)
            en = en_tpl.format(**filled_en)
        except (KeyError, IndexError):
            continue
        note = ""
        if filled_r.get("x", "") == "":
            reading = ""
            note = f"No dictionary entry for “{groups.get('x', '')}” - swap in your own word."
        return Target(out_text, reading, en or text, "phrasebook", note)

    # last resort: single known word?
    entry = _lookup(norm, lang)
    if entry:
        return Target(entry[0], entry[1], text, "phrasebook")

    name = LANG_NAMES.get(lang, lang)
    return Target(
        text,
        "",
        text,
        "phrasebook",
        f"No offline translation - set OPENAI_API_KEY for full “think in {name}”.",
    )


# ---------------------------------------------------------------------------
# llm backend (OpenAI compatible)
# ---------------------------------------------------------------------------


def _llm(text: str, cfg: Dict, lang: str) -> Optional[Target]:
    key_env = cfg["think"].get("api_key_env") or "OPENAI_API_KEY"
    key = os.getenv(key_env) if key_env else None
    if not key:
        return None

    base = (cfg["think"].get("base_url") or "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": cfg["think"].get("model", "gpt-4o-mini"),
        "temperature": 0.3,
        "max_tokens": 220,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.get(lang, SYSTEM_PROMPT["zh"])},
            {"role": "user", "content": f"English thought: {text}\nLevel: beginner (A1-A2)."},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=float(cfg["think"].get("timeout", 12))) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None

    try:
        content = body["choices"][0]["message"]["content"]
        data = json.loads(content)
        value = (data.get("text") or "").strip()
        if not value:
            return None
        tips = (data.get("tips") or "").strip()
        return Target(
            text=value,
            reading=(data.get("reading") or "").strip(),
            en=(data.get("literal") or text).strip(),
            source="llm",
            note=tips,
        )
    except (KeyError, IndexError, ValueError):
        return None


def translate(text: str, cfg: Dict) -> Target:
    """English -> target line, LLM first, phrasebook as fallback."""
    lang = normalize(cfg.get("language") or "zh")
    provider = (cfg["think"].get("provider") or "auto").lower()
    if provider in ("auto", "llm"):
        target = _llm(text, cfg, lang)
        if target:
            return target
        if provider == "llm":
            fallback = phrasebook(text, lang)
            fallback.note = "LLM unavailable - offline phrasebook used. " + fallback.note
            return fallback
    return phrasebook(text, lang)

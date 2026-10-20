# -*- coding: utf-8 -*-
"""Band 1 (shown as N3) — formal & abstract.

Pimsleur-style, but the register now moves with the situation: keigo to a
client, です/ます to a colleague, plain form to a friend or in an aside.  That
movement IS the N1 skill, so a lesson shifts register line by line.  Each
lesson's vocabulary is re-used in the dialogue so the learner meets the words
twice in one sitting.

  text    the line as Japanese write it (kanji + kana, normal script)
  reading the same line written entirely in kana — the furigana slot
          printed above the line, including okurigana
  en      natural English

Pattern slots use the same three keys: text / reading / en, each carrying a
"{x}" placeholder that the value fills in.

A pattern may also carry "kind", naming what {x} accepts so the app can drop
a word learned elsewhere into this frame:

    object | place | person | clock | day | food | weather-noun | weather-adj

Most N1 frames are left untagged on purpose.  The slots here take clauses and
abstract nouns, and an old concrete noun dropped into "根拠として{x}を挙げます"
reads like nonsense.  Only the slots that genuinely take a plain thing carry a
tag, and they are tagged "object" to match N3's request frames.
"""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Unit 12 - Formal & Business Japanese.  Humble forms, requests, refusals,
    # and the telephone.
    # -----------------------------------------------------------------------
    {
        "id": 12,
        "title": "Formal & Business Japanese",
        "focus": "Introduce yourself, request, decline and take calls in keigo without sounding either cold or servile.",
        "gate": {"min_pron_score": 80.0, "min_accuracy": 80.0, "min_completeness": 88.0},
        "lessons": [
            {
                "id": 50,
                "title": "Business self-introduction",
                "goal": "Introduce yourself and your role with humble forms (〜と申します / 〜ております).",
                "vocab": [
                    ("自己紹介", "じこしょうかい", "self-introduction"),
                    ("営業部", "えいぎょうぶ", "the sales department"),
                    ("申します", "もうします", "to be called (humble)"),
                    ("担当", "たんとう", "in charge of"),
                    ("前職", "ぜんしょく", "one's previous position"),
                    ("契約", "けいやく", "contract"),
                    ("お客様", "おきゃくさま", "customer / client (polite)"),
                ],
                "dialogue": [
                    ("them", "初めまして。自己紹介をお願いいたします。",
                     "はじめまして。じこしょうかいをおねがいいたします。",
                     "How do you do. Please introduce yourself."),
                    ("you", "営業部の鈴木と申します。どうぞよろしくお願いいたします。",
                     "えいぎょうぶのすずきともうします。どうぞよろしくおねがいいたします。",
                     "I'm Suzuki, from Sales. Pleased to meet you."),
                    ("them", "鈴木さんの担当を教えていただけますか。",
                     "すずきさんのたんとうをおしえていただけますか。",
                     "Could you tell me what you are in charge of?"),
                    ("you", "海外のお客様との契約を担当しております。",
                     "かいがいのおきゃくさまとのけいやくをたんとうしております。",
                     "I handle contracts with our overseas clients."),
                    ("them", "前職では、どのようなお仕事をしていましたか。",
                     "ぜんしょくでは、どのようなおしごとをしていましたか。",
                     "And what sort of work did you do before?"),
                    ("you", "同じく契約の仕事をしておりました。三年ほどです。",
                     "おなじくけいやくのしごとをしておりました。さんねんほどです。",
                     "Much the same contract work. For about three years."),
                    ("them", "そうですか。では、部の皆さんに紹介いたします。",
                     "そうですか。では、ぶのみなさんにしょうかいいたします。",
                     "I see. Then let me introduce you to the department."),
                ],
                "patterns": [
                    {
                        "text": "{x}と申します",
                        "reading": "{x}ともうします",
                        "en": "My name is {x}",
                        "values": [
                            ("鈴木", "すずき", "Suzuki"),
                            ("田中", "たなか", "Tanaka"),
                            ("山田", "やまだ", "Yamada"),
                        ],
                    },
                    {
                        "text": "{x}を担当しております",
                        "reading": "{x}をたんとうしております",
                        "en": "I am in charge of {x}",
                        "kind": "object",
                        "values": [
                            ("海外のお客様", "かいがいのおきゃくさま", "our overseas clients"),
                            ("新規案件", "しんきあんけん", "new projects"),
                            ("契約の管理", "けいやくのかんり", "contract administration"),
                        ],
                    },
                    {
                        "text": "前職では{x}をしておりました",
                        "reading": "ぜんしょくでは{x}をしておりました",
                        "en": "In my previous post I did {x}",
                        "values": [
                            ("同じ仕事", "おなじしごと", "much the same work"),
                            ("営業", "えいぎょう", "sales"),
                            ("品質の管理", "ひんしつのかんり", "quality control"),
                        ],
                    },
                ],
                "notes": [
                    "〜と申します is the humble form of 〜と言います: use it whenever you give your own name at work.",
                    "〜ております is the humble form of 〜ています: 担当しております = 'I am in charge of'.",
                ],
            },
            {
                "id": 51,
                "title": "Polite requests",
                "goal": "Make and accept a business request: 〜いただけますでしょうか / 承知いたしました.",
                "vocab": [
                    ("至急", "しきゅう", "urgently / as a matter of urgency"),
                    ("確認", "かくにん", "checking / confirmation"),
                    ("資料", "しりょう", "materials / documents"),
                    ("送付", "そうふ", "sending (documents)"),
                    ("承知", "しょうち", "noted / I understand"),
                    ("対応", "たいおう", "handling / dealing with it"),
                    ("次第", "しだい", "as soon as (Vます-stem + 次第)"),
                    ("かしこまりました", "かしこまりました", "certainly (humble)"),
                ],
                "dialogue": [
                    ("them", "恐れ入りますが、至急ご確認いただけますでしょうか。",
                     "おそれいりますが、しきゅうごかくにんいただけますでしょうか。",
                     "Sorry to press you, but could you check this urgently?"),
                    ("you", "承知いたしました。直ちに確認いたします。",
                     "しょうちいたしました。ただちにかくにんいたします。",
                     "Understood. I'll look into it immediately."),
                    ("them", "終わりましたら、ご連絡をお願いいたします。",
                     "おわりましたら、ごれんらくをおねがいいたします。",
                     "And let me know when you are done."),
                    ("you", "かしこまりました。終わり次第、連絡いたします。",
                     "かしこまりました。おわりしだい、れんらくいたします。",
                     "Certainly. I'll be in touch the moment it is finished."),
                    ("them", "では、資料の送付もお願いしたいのですが。",
                     "では、しりょうのそうふもおねがいしたいのですが。",
                     "And I'd like to ask for the materials to be sent as well."),
                    ("you", "承知しました。本日中にお送りいたします。",
                     "しょうちしました。ほんじつちゅうにおおくりいたします。",
                     "Of course. I'll have them with you within today."),
                    ("them", "助かります。対応のほど、よろしくお願いいたします。",
                     "たすかります。たいおうのほど、よろしくおねがいいたします。",
                     "That is a great help. I leave it in your hands."),
                ],
                "patterns": [
                    {
                        "text": "{x}を至急お願いいたします",
                        "reading": "{x}をしきゅうおねがいいたします",
                        "en": "I urgently ask for {x}",
                        "kind": "object",
                        "values": [
                            ("ご確認", "ごかくにん", "your check"),
                            ("資料の送付", "しりょうのそうふ", "the materials to be sent"),
                            ("ご連絡", "ごれんらく", "a reply"),
                        ],
                    },
                    {
                        "text": "承知いたしました。{x}いたします",
                        "reading": "しょうちいたしました。{x}いたします",
                        "en": "Certainly. I will {x}",
                        "values": [
                            ("確認", "かくにん", "check it"),
                            ("すぐ連絡", "すぐれんらく", "be in touch at once"),
                            ("本日中に送付", "ほんじつちゅうにそうふ", "send it within today"),
                        ],
                    },
                    {
                        "text": "恐れ入りますが、{x}でしょうか",
                        "reading": "おそれいりますが、{x}でしょうか",
                        "en": "I'm sorry to trouble you, but {x}?",
                        "values": [
                            ("ご確認いただけます", "ごかくにんいただけます", "might I ask you to check"),
                            ("明日までお待ちいただけます", "あしたまでおまちいただけます", "could you wait until tomorrow"),
                            ("ご変更いただけます", "ごへんこういただけます", "could it be changed"),
                        ],
                    },
                ],
                "notes": [
                    "〜いただけますでしょうか is the standard polite request; softer than 〜てください and the safe choice with a client.",
                    "承知いたしました and かしこまりました both mean 'certainly': the first is neutral, the second customer-facing.",
                ],
            },
            {
                "id": 52,
                "title": "Declining politely",
                "goal": "Refuse an invitation or a date without closing the door: あいにく / 〜させていただければと存じます.",
                "vocab": [
                    ("都合", "つごう", "one's schedule / convenience"),
                    ("先約", "せんやく", "a prior engagement"),
                    ("誘い", "さそい", "invitation"),
                    ("見送る", "みおくる", "to pass on (an offer)"),
                    ("今回", "こんかい", "this time"),
                    ("改めて", "あらためて", "again / at another time"),
                    ("存じます", "ぞんじます", "to think / know (humble)"),
                    ("せっかく", "せっかく", "kindly / despite the trouble taken"),
                    ("あいにく", "あいにく", "unfortunately"),
                ],
                "dialogue": [
                    ("them", "今週の金曜日、ご都合はいかがですか。",
                     "こんしゅうのきんようび、ごつごうはいかがですか。",
                     "How does Friday this week look for you?"),
                    ("you", "せっかくですが、あいにく先約がありまして。",
                     "せっかくですが、あいにくせんやくがありまして。",
                     "That is kind of you, but sadly I have a prior engagement."),
                    ("them", "そうですか。今回の誘いは難しいですか。",
                     "そうですか。こんかいのさそいはむずかしいですか。",
                     "I see. So this invitation is not going to work?"),
                    ("you", "ええ、今回だけは見送らせていただければと存じます。",
                     "ええ、こんかいだけはみおくらせていただければとぞんじます。",
                     "This once, I would be grateful to be allowed to pass."),
                    ("them", "承知しました。では、改めて来週はいかがでしょうか。",
                     "しょうちしました。では、あらためてらいしゅうはいかがでしょうか。",
                     "Of course. Then might I suggest next week instead?"),
                    ("you", "来週でしたら、木曜の午後なら伺えます。",
                     "らいしゅうでしたら、もくようのごごならうかがえます。",
                     "Next week I could call on you on Thursday afternoon."),
                    ("them", "では、木曜の午後二時にお願いいたします。",
                     "では、もくようのごごにじにおねがいいたします。",
                     "Then two o'clock on Thursday afternoon, please."),
                ],
                "patterns": [
                    {
                        "text": "あいにく{x}がありまして",
                        "reading": "あいにく{x}がありまして",
                        "en": "Sadly I already have {x}",
                        "kind": "object",
                        "values": [
                            ("先約", "せんやく", "a prior engagement"),
                            ("別の予定", "べつのよてい", "another appointment"),
                            ("出張", "しゅっちょう", "a business trip"),
                        ],
                    },
                    {
                        # 見送る is godan: its causative is 見送らせて, not 見送りさせて.
                        # The 〜させて lives on the value so the frame cannot force a
                        # wrong conjugation onto a verb of either class.
                        "text": "今回は{x}いただければと存じます",
                        "reading": "こんかいは{x}いただければとぞんじます",
                        "en": "This time I would be grateful to be allowed to {x}",
                        "values": [
                            ("見送らせて", "みおくらせて", "pass on it"),
                            ("辞退させて", "じたいさせて", "decline"),
                            ("延期させて", "えんきさせて", "postpone it"),
                        ],
                    },
                    {
                        "text": "改めて{x}はいかがでしょうか",
                        "reading": "あらためて{x}はいかがでしょうか",
                        "en": "Might I suggest {x} instead?",
                        "kind": "day",
                        "values": [
                            ("来週の木曜日", "らいしゅうのもくようび", "Thursday next week"),
                            ("来月の初め", "らいげつのはじめ", "early next month"),
                            ("別の日", "べつのひ", "another day"),
                        ],
                    },
                ],
                "notes": [
                    "あいにく plus a reason is the standard softening before a refusal: 'unfortunately…'.",
                    "〜（さ）せていただければと存じます hands the decision back: 'let me pass this time, if I may'.",
                ],
            },
            {
                "id": 53,
                "title": "Business calls & email",
                "goal": "Handle a phone call and follow it up in writing: 恐れ入ります / 折り返し.",
                "vocab": [
                    ("恐れ入ります", "おそれいります", "I'm sorry to trouble you"),
                    ("担当者", "たんとうしゃ", "the person in charge"),
                    ("席を外す", "せきをはずす", "to be away from one's desk"),
                    ("折り返し", "おりかえし", "calling back"),
                    ("要件", "ようけん", "the matter at hand"),
                    ("確認の電話", "かくにんのでんわ", "a call to confirm"),
                ],
                "dialogue": [
                    ("them", "お電話ありがとうございます。山川商事でございます。",
                     "おでんわありがとうございます。やまかわしょうじでございます。",
                     "Thank you for calling. Yamakawa Trading."),
                    ("you", "恐れ入りますが、担当者をお願いできますか。",
                     "おそれいりますが、たんとうしゃをおねがいできますか。",
                     "Sorry to trouble you, but could I speak to the person in charge?"),
                    ("them", "佐藤は、ただ今席を外しております。",
                     "さとうは、ただいませきをはずしております。",
                     "Sato is away from his desk at the moment."),
                    ("you", "そうですか。では、折り返しお願いできますでしょうか。",
                     "そうですか。では、おりかえしおねがいできますでしょうか。",
                     "I see. Then might I ask him to call me back?"),
                    ("them", "かしこまりました。ご要件を伺ってもよろしいでしょうか。",
                     "かしこまりました。ごようけんをうかがってもよろしいでしょうか。",
                     "Certainly. May I ask what it concerns?"),
                    ("you", "はい、資料の件です。確認の電話をいただけますか。",
                     "はい、しりょうのけんです。かくにんのでんわをいただけますか。",
                     "Yes, the materials. Could he ring just to confirm?"),
                    ("them", "承知いたしました。佐藤から折り返し連絡いたします。",
                     "しょうちいたしました。さとうからおりかえしれんらくいたします。",
                     "Understood. Sato will be back in touch with you."),
                ],
                "patterns": [
                    {
                        "text": "恐れ入りますが、{x}をお願いできますか",
                        "reading": "おそれいりますが、{x}をおねがいできますか",
                        "en": "Sorry to trouble you, but could I have {x}?",
                        "kind": "object",
                        "values": [
                            ("担当者", "たんとうしゃ", "the person in charge"),
                            ("折り返し", "おりかえし", "a callback"),
                            ("お名前", "おなまえ", "your name"),
                        ],
                    },
                    {
                        # て-forms cannot share a slot: 外して / 外出して take て but
                        # 取る takes って, so 休みを取りしております would be wrong. The
                        # value carries its own て-form; the frame supplies おります.
                        "text": "ただ今{x}おります",
                        "reading": "ただいま{x}おります",
                        "en": "He is {x} at the moment",
                        "values": [
                            ("席を外して", "せきをはずして", "away from his desk"),
                            ("外出して", "がいしゅつして", "stepping out"),
                            ("休みを取って", "やすみをとって", "taking the day off"),
                        ],
                    },
                    {
                        "text": "{x}から折り返し連絡いたします",
                        "reading": "{x}からおりかえしれんらくいたします",
                        "en": "{x} will call you back",
                        "values": [
                            ("佐藤", "さとう", "Sato"),
                            ("担当者", "たんとうしゃ", "the colleague in charge"),
                            ("私", "わたし", "I"),
                        ],
                    },
                ],
                "notes": [
                    "ただ今 is 'right now' on the phone, a step above 今: ただ今席を外しております.",
                    "折り返し is the callback itself: 折り返しお願いできますか covers 'ring me back' politely.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 13 - Abstract Thought & Argument.  Define, ground, cause, judge.
    # -----------------------------------------------------------------------
    {
        "id": 13,
        "title": "Abstract Thought & Argument",
        "focus": "Define abstract ideas, support a claim with grounds, trace a cause, and judge between competing values.",
        "gate": {"min_pron_score": 82.0, "min_accuracy": 82.0, "min_completeness": 88.0},
        "lessons": [
            {
                "id": 54,
                "title": "Abstract ideas",
                "goal": "Define and discuss abstract ideas: 〜とは〜ということだ.",
                "vocab": [
                    ("自由", "じゆう", "freedom"),
                    ("効率", "こうりつ", "efficiency"),
                    ("範囲", "はんい", "range / scope"),
                    ("余白", "よはく", "room to breathe / slack"),
                    ("価値観", "かちかん", "values / what one holds dear"),
                    ("求める", "もとめる", "to seek / to look for"),
                    ("深い", "ふかい", "deep"),
                ],
                "dialogue": [
                    ("them", "自由とは何だとお考えですか。",
                     "じゆうとはなんだとおかんがえですか。",
                     "What do you take freedom to be?"),
                    ("you", "選べる範囲がどこまで広いかということだと思います。",
                     "えらべるはんいがどこまでひろいかということだとおもいます。",
                     "I think it is a question of how wide the real choices are."),
                    ("them", "では、効率だけを追うと、どうなりますか。",
                     "では、こうりつだけをおうと、どうなりますか。",
                     "And what happens if you chase efficiency alone?"),
                    ("you", "範囲は狭くなります。余白も失われるでしょう。",
                     "はんいはせまくなります。よはくもうしなわれるでしょう。",
                     "The range narrows. And the slack disappears with it."),
                    ("them", "余白とは、何のことでしょうか。",
                     "よはくとは、なんのことでしょうか。",
                     "What do you mean by slack?"),
                    ("you", "急がずに考えたり、人と深く関わったりする時間です。",
                     "いそがずにかんがえたり、ひととふかくかかわったりするじかんです。",
                     "Time to think unhurried, and to be deeply involved with people."),
                    ("them", "価値観の違いもありますね。では、何を求めるべきでしょうか。",
                     "かちかんのちがいもありますね。では、なにをもとめるべきでしょうか。",
                     "Values differ here too. So what should we look for?"),
                ],
                "patterns": [
                    {
                        "text": "{x}とは何だと思いますか",
                        "reading": "{x}とはなんだとおもいますか",
                        "en": "What do you take {x} to be?",
                        "values": [
                            ("自由", "じゆう", "freedom"),
                            ("効率", "こうりつ", "efficiency"),
                            ("公正", "こうせい", "fairness"),
                        ],
                    },
                    {
                        "text": "{x}ということだと思います",
                        "reading": "{x}ということだとおもいます",
                        "en": "I think it means {x}",
                        "values": [
                            ("選べる範囲が広い", "えらべるはんいがひろい", "the range of real choices widens"),
                            ("余白が減る", "よはくがへる", "there is less room to breathe"),
                            ("一人ずつの負担が増える", "ひとりずつのふたんがふえる", "each person carries more"),
                        ],
                    },
                    {
                        "text": "{x}だけを追うと",
                        "reading": "{x}だけをおうと",
                        "en": "If you chase {x} alone",
                        "values": [
                            ("効率", "こうりつ", "efficiency"),
                            ("利益", "りえき", "profit"),
                            ("数字", "すうじ", "the numbers"),
                        ],
                    },
                ],
                "notes": [
                    "〜とは marks the word being defined; 〜ということだ delivers the definition itself.",
                    "範囲 and 価値観 carry most of the weight in abstract talk: learn them as nouns of measure.",
                ],
            },
            {
                "id": 55,
                "title": "Building an argument",
                "goal": "Support a claim with grounds and answer an objection: 〜に基づいて / 〜を分けて考える.",
                "vocab": [
                    ("主張", "しゅちょう", "claim / contention"),
                    ("根拠", "こんきょ", "grounds / evidence"),
                    ("挙げる", "あげる", "to cite / to give (examples)"),
                    ("短期", "たんき", "the short term"),
                    ("長期", "ちょうき", "the long term"),
                    ("満足度", "まんぞくど", "degree of satisfaction"),
                    ("顧客", "こきゃく", "client / customer"),
                    ("添える", "そえる", "to attach / add"),
                    ("結論", "けつろん", "conclusion"),
                    ("そして", "そして", "and / and then"),
                ],
                "dialogue": [
                    ("you", "今回の主張の根拠は三つございます。",
                     "こんかいのしゅちょうのこんきょはみっつございます。",
                     "There are three grounds for what I am arguing."),
                    ("them", "順に挙げていただけますか。",
                     "じゅんにあげていただけますか。",
                     "Could you give them in order?"),
                    ("you", "費用、時間、そして顧客の満足度です。",
                     "ひよう、じかん、そしてこきゃくのまんぞくどです。",
                     "Cost, time, and customer satisfaction."),
                    ("them", "費用の根拠は少し弱いように見えます。",
                     "ひようのこんきょはすこしよわいようにみえます。",
                     "The cost argument looks a little thin."),
                    ("you", "では、数字を添えて、改めて説明いたします。",
                     "では、すうじをそえて、あらためてせつめいいたします。",
                     "Then let me put figures to it and explain again."),
                    ("them", "短期と長期の効果は混ぜないほうがいいですね。",
                     "たんきとちょうきのこうかはまぜないほうがいいですね。",
                     "You would do better not to mix the short and the long term."),
                    ("you", "ええ。分けて考えれば、結論が変わる場合もあります。",
                     "ええ。わけてかんがえれば、けつろんがかわるばあいもあります。",
                     "Quite. Taken apart, the conclusion sometimes changes."),
                ],
                "patterns": [
                    {
                        "text": "根拠として{x}を挙げます",
                        "reading": "こんきょとして{x}をあげます",
                        "en": "As grounds I would cite {x}",
                        "values": [
                            ("費用の削減", "ひようのさくげん", "the cut in costs"),
                            ("顧客の満足度", "こきゃくのまんぞくど", "customer satisfaction"),
                            ("作業時間の短縮", "さぎょうじかんのたんしゅく", "the shorter working time"),
                        ],
                    },
                    {
                        "text": "{x}に基づいて判断します",
                        "reading": "{x}にもとづいてはんだんします",
                        "en": "I judge on the basis of {x}",
                        "values": [
                            ("過去の実績", "かこのじっせき", "past results"),
                            ("現場の声", "げんばのこえ", "what people on the ground say"),
                            ("今回の数字", "こんかいのすうじ", "this set of figures"),
                        ],
                    },
                    {
                        "text": "{x}と長期の効果を分けて考えます",
                        "reading": "{x}とちょうきのこうかをわけてかんがえます",
                        "en": "I separate {x} from the long-term effects",
                        "values": [
                            ("短期の効果", "たんきのこうか", "the short-term effects"),
                            ("目先の利益", "めさきのりえき", "immediate returns"),
                            ("初期費用", "しょきひよう", "the initial outlay"),
                        ],
                    },
                ],
                "notes": [
                    "〜を挙げる here is 'to cite': three 根拠 make a claim defensible even before they are strong.",
                    "〜に基づいて binds your conclusion to something checkable: 実績に基づいて判断する.",
                ],
            },
            {
                "id": 56,
                "title": "Cause & effect",
                "goal": "Trace what lies behind a problem and what follows from it: 背景にある / 影響を及ぼす.",
                "vocab": [
                    ("背景", "はいけい", "what lies behind something"),
                    ("要因", "よういん", "contributing factor"),
                    ("偏り", "かたより", "imbalance / skew"),
                    ("負担", "ふたん", "burden / load"),
                    ("及ぼす", "およぼす", "to exert (an influence)"),
                    ("仕組み", "しくみ", "structure / mechanism"),
                    ("伸びる", "のびる", "to grow / rise"),
                    ("将来", "しょうらい", "the future"),
                    ("不安", "ふあん", "anxiety / unease"),
                    ("支え合う", "ささえあう", "to support each other"),
                ],
                "dialogue": [
                    ("them", "この問題の背景には何があるとお考えですか。",
                     "このもんだいのはいけいにはなにがあるとおかんがえですか。",
                     "What do you think lies behind this problem?"),
                    ("you", "世代間の負担の偏りがあると思います。",
                     "せだいかんのふたんのかたよりがあるとおもいます。",
                     "An uneven share of the burden between generations."),
                    ("them", "その偏りはどこから生まれるのでしょうか。",
                     "そのかたよりはどこからうまれるのでしょうか。",
                     "And where does that imbalance come from?"),
                    ("you", "人口の構成と、賃金が伸びないことが要因です。",
                     "じんこうのこうせいと、ちんぎんがのびないことがよういんです。",
                     "The shape of the population, and wages that no longer rise."),
                    ("them", "社会にはどんな影響を及ぼしますか。",
                     "しゃかいにはどんなえいきょうをおよぼしますか。",
                     "What effect does that exert on society?"),
                    ("you", "将来への不安が強まります。支え合う仕組みが要ります。",
                     "しょうらいへのふあんがつよまります。ささえあうしくみがいります。",
                     "Anxiety about the future deepens. We need structures of mutual support."),
                ],
                "patterns": [
                    {
                        "text": "{x}が背景にあると考えます",
                        "reading": "{x}がはいけいにあるとかんがえます",
                        "en": "I think {x} lies behind it",
                        "values": [
                            ("負担の偏り", "ふたんのかたより", "the uneven burden"),
                            ("賃金の停滞", "ちんぎんのていたい", "stagnant wages"),
                            ("人口の減少", "じんこうのげんしょう", "the falling population"),
                        ],
                    },
                    {
                        "text": "{x}に影響が及んでいます",
                        "reading": "{x}にえいきょうがおよんでいます",
                        "en": "The effects reach {x}",
                        "values": [
                            ("地方", "ちほう", "the regions"),
                            ("家計", "かけい", "household budgets"),
                            ("次の世代", "つぎのせだい", "the next generation"),
                        ],
                    },
                    {
                        "text": "{x}をもたらします",
                        "reading": "{x}をもたらします",
                        "en": "It brings {x}",
                        "values": [
                            ("新しい負担", "あたらしいふたん", "a new burden"),
                            ("小さな変化", "ちいさなへんか", "small changes"),
                            ("予期せぬ結果", "よきせぬけっか", "results nobody foresaw"),
                        ],
                    },
                ],
                "notes": [
                    "背景 sets the scene; 要因 is the part you can actually act on. Keep them apart.",
                    "影響を及ぼす = 'exert an influence'; whatever is affected takes に.",
                ],
            },
            {
                "id": 57,
                "title": "Values & judgement",
                "goal": "Weigh competing values and say what should take priority: 〜べきだ / 〜を優先する.",
                "vocab": [
                    ("優先", "ゆうせん", "priority"),
                    ("安全", "あんぜん", "safety"),
                    ("便利", "べんり", "convenience"),
                    ("妥協", "だきょう", "compromise"),
                    ("不利", "ふり", "disadvantage"),
                    ("判断", "はんだん", "judgement / decision"),
                    ("形", "かたち", "form / shape"),
                    ("高齢", "こうれい", "advanced age / elderly"),
                ],
                "dialogue": [
                    ("them", "便利さと安全、どちらを優先すべきでしょうか。",
                     "べんりさとあんぜん、どちらをゆうせんすべきでしょうか。",
                     "Convenience or safety — which should take priority?"),
                    ("you", "安全を優先すべきだと考えます。",
                     "あんぜんをゆうせんすべきだとかんがえます。",
                     "I believe safety has to come first."),
                    ("them", "便利さを求める人は納得しません。",
                     "べんりさをもとめるひとはなっとくしません。",
                     "Those who want convenience will not accept that."),
                    ("you", "では、範囲を決めて妥協する形にします。",
                     "では、はんいをきめてだきょうするかたちにします。",
                     "Then we set its scope and compromise within it."),
                    ("them", "その判断で誰が不利になりますか。",
                     "そのはんだんでだれがふりになりますか。",
                     "Who loses out under that decision?"),
                    ("you", "高齢の方と収入の少ない方です。そこを全体で支えます。",
                     "こうれいのかたとしゅうにゅうのすくないかたです。そこをぜんたいでささえます。",
                     "Elderly people and those on low incomes. We carry that between us."),
                ],
                "patterns": [
                    {
                        "text": "{x}を優先すべきです",
                        "reading": "{x}をゆうせんすべきです",
                        "en": "We should give priority to {x}",
                        "values": [
                            ("安全", "あんぜん", "safety"),
                            ("信頼", "しんらい", "trust"),
                            ("長期的な利益", "ちょうきてきなりえき", "the long-term gain"),
                        ],
                    },
                    {
                        "text": "{x}には妥協できないと考えています",
                        "reading": "{x}にはだきょうできないとかんがえています",
                        "en": "I do not think I can compromise on {x}",
                        "values": [
                            ("安全性", "あんぜんせい", "safety"),
                            ("品質", "ひんしつ", "quality"),
                            ("納期", "のうき", "the delivery date"),
                        ],
                    },
                    {
                        "text": "その判断で{x}が不利になります",
                        "reading": "そのはんだんで{x}がふりになります",
                        "en": "Under that decision, {x} lose out",
                        "values": [
                            ("高齢の方", "こうれいのかた", "elderly people"),
                            ("収入の少ない方", "しゅうにゅうのすくないかた", "people on low incomes"),
                            ("地方の利用者", "ちほうのりようしゃ", "users in rural areas"),
                        ],
                    },
                ],
                "notes": [
                    "〜べきだ = 'it ought to be'. 優先すべきだ is a judgement; 優先したほうがいい is advice.",
                    "不利 is a noun: 不利になる = 'to end up worse off'.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 14 - Nuance & Expression.  Hedging, emphasis, how things properly
    # are, and disagreement that never says no.
    # -----------------------------------------------------------------------
    {
        "id": 14,
        "title": "Nuance & Expression",
        "focus": "Keep a claim open, point at one thing, say how things properly are, and disagree without saying no.",
        "gate": {"min_pron_score": 84.0, "min_accuracy": 84.0, "min_completeness": 90.0},
        "lessons": [
            {
                "id": 58,
                "title": "Keeping a claim open",
                "goal": "Report something without standing behind it: 〜と思われる / 断定を避ける.",
                "vocab": [
                    ("思われる", "おもわれる", "it appears / it is thought"),
                    ("傾向", "けいこう", "tendency / trend"),
                    ("解釈", "かいしゃく", "interpretation / reading"),
                    ("確実", "かくじつ", "certainty"),
                    ("一時的", "いちじてき", "temporary"),
                    ("見通し", "みとおし", "outlook / forecast"),
                    ("含める", "ふくめる", "to include"),
                    ("幅", "はば", "range / width"),
                    ("しばらく", "しばらく", "for a while"),
                ],
                "dialogue": [
                    ("them", "今後、この状況は続くと思われますか。",
                     "こんご、このじょうきょうはつづくとおもわれますか。",
                     "Do you expect this situation to continue?"),
                    ("you", "しばらくは続くと思われますが、確実ではありません。",
                     "しばらくはつづくとおもわれますが、かくじつではありません。",
                     "It seems likely to run on for a while, but nothing is certain."),
                    ("them", "数字には一時的な要因もありますね。",
                     "すうじにはいちじてきなよういんもありますね。",
                     "Temporary factors are in those figures as well."),
                    ("you", "ええ。解釈には、その幅を含めるべきでしょう。",
                     "ええ。かいしゃくには、そのはばをふくめるべきでしょう。",
                     "Yes. Any reading of them should allow for that spread."),
                    ("them", "半年先の見通しはいかがですか。",
                     "はんとしさきのみとおしはいかがですか。",
                     "And six months out?"),
                    ("you", "まだ傾向が読めないため、断定は避けたいです。",
                     "まだけいこうがよめないため、だんていはさけたいです。",
                     "The trend is still unreadable, so I would rather not commit."),
                ],
                "patterns": [
                    {
                        "text": "{x}と思われますが、確実ではありません",
                        "reading": "{x}とおもわれますが、かくじつではありません",
                        "en": "It appears that {x}, but nothing is certain",
                        "values": [
                            ("この傾向が続く", "このけいこうがつづく", "the trend continues"),
                            ("需要が伸びる", "じゅようがのびる", "demand grows"),
                            ("影響が残る", "えいきょうがのこる", "the effects linger"),
                        ],
                    },
                    {
                        "text": "{x}として見るべきでしょう",
                        "reading": "{x}としてみるべきでしょう",
                        "en": "We should read it as {x}",
                        "values": [
                            ("一時的な動き", "いちじてきなうごき", "a temporary movement"),
                            ("長い傾向の一部", "ながいけいこうのいちぶ", "part of a long trend"),
                            ("例外的な数字", "れいがいてきなすうじ", "an exceptional figure"),
                        ],
                    },
                    {
                        "text": "{x}については断定を避けたいです",
                        "reading": "{x}についてはだんていをさけたいです",
                        "en": "On {x} I would rather not commit myself",
                        "values": [
                            ("半年先の見通し", "はんとしさきのみとおし", "the six-month outlook"),
                            ("その解釈", "そのかいしゃく", "that reading of it"),
                            ("来期の数字", "らいきのすうじ", "next quarter's figures"),
                        ],
                    },
                ],
                "notes": [
                    "〜と思われる is the impersonal 'it appears'; unlike 〜と思う it belongs to nobody in particular.",
                    "〜幅を含める keeps a number honest: it admits the margin instead of hiding it.",
                ],
            },
            {
                "id": 59,
                "title": "Pointing at one thing",
                "goal": "Single out the one thing that matters: 〜こそ / 〜だけは.",
                "vocab": [
                    ("意思決定", "いしけってい", "decision-making"),
                    ("速さ", "はやさ", "speed"),
                    ("最低限", "さいていげん", "the bare minimum"),
                    ("守る", "まもる", "to protect / to keep"),
                    ("信頼", "しんらい", "trust"),
                    ("変える", "かえる", "to change"),
                    ("課題", "かだい", "issue / challenge"),
                ],
                "dialogue": [
                    ("them", "今回こそ変えるべき点はどこでしょうか。",
                     "こんかいこそかえるべきてんはどこでしょうか。",
                     "What is it, this time, that we must change?"),
                    ("you", "意思決定の速さこそが課題だと考えます。",
                     "いしけっていのはやさこそがかだいだとかんがえます。",
                     "The speed of decision-making is precisely the problem."),
                    ("them", "最低限、何だけは守るべきでしょうか。",
                     "さいていげん、なにだけはまもるべきでしょうか。",
                     "At the very least, what has to be protected?"),
                    ("you", "お客様との信頼だけは守るべきです。",
                     "おきゃくさまとのしんらいだけはまもるべきです。",
                     "Trust with our customers, come what may."),
                    ("them", "では、具体的にどうされますか。",
                     "では、ぐたいてきにどうされますか。",
                     "So what will you do, concretely?"),
                    ("you", "回答の期限を決め、必ず守る仕組みにします。",
                     "かいとうのきげんをきめ、かならずまもるしくみにします。",
                     "We set a deadline for replies, and build a structure that keeps it."),
                ],
                "patterns": [
                    {
                        "text": "{x}こそ課題だと考えます",
                        "reading": "{x}こそかだいだとかんがえます",
                        "en": "It is {x} itself that is the problem",
                        "values": [
                            ("意思決定の速さ", "いしけっていのはやさ", "the speed of decision-making"),
                            ("現場との距離", "げんばとのきょり", "the distance from the front line"),
                            ("情報の共有", "じょうほうのきょうゆう", "the sharing of information"),
                        ],
                    },
                    {
                        "text": "{x}だけは守るべきです",
                        "reading": "{x}だけはまもるべきです",
                        "en": "{x} above all must be protected",
                        "values": [
                            ("お客様との信頼", "おきゃくさまとのしんらい", "trust with our customers"),
                            ("回答の期限", "かいとうのきげん", "the deadline for replying"),
                            ("品質", "ひんしつ", "quality"),
                        ],
                    },
                    {
                        "text": "{x}ように心がけています",
                        "reading": "{x}ようにこころがけています",
                        "en": "I make a point of {x}",
                        "values": [
                            ("期限を守る", "きげんをまもる", "meeting the deadline"),
                            ("先に結論を言う", "さきにけつろんをいう", "giving the conclusion first"),
                            ("数字を添える", "すうじをそえる", "attaching the figures"),
                        ],
                    },
                ],
                "notes": [
                    "〜こそ singles out one thing as the real one: 今回こそ, 速さこそ.",
                    "〜だけは = 'this one thing at least': it marks the minimum you refuse to give up.",
                ],
            },
            {
                "id": 60,
                "title": "How things properly are",
                "goal": "State custom and nature with 〜ものだ / 〜ものではない.",
                "vocab": [
                    ("約束", "やくそく", "promise"),
                    ("教わる", "おそわる", "to be taught"),
                    ("失敗", "しっぱい", "failure"),
                    ("恐れる", "おそれる", "to fear"),
                    ("伝える", "つたえる", "to pass on / to tell"),
                    ("経験", "けいけん", "experience"),
                ],
                "dialogue": [
                    ("them", "仕事で大切にしていることは何ですか。",
                     "しごとでたいせつにしていることはなんですか。",
                     "What do you value most in your work?"),
                    ("you", "約束は守るものだと教わってきました。",
                     "やくそくはまもるものだとおそわってきました。",
                     "I was brought up to believe promises are there to be kept."),
                    ("them", "若い人には、失敗をどう伝えますか。",
                     "わかいひとには、しっぱいをどうつたえますか。",
                     "And what do you pass on to younger people about failure?"),
                    ("you", "失敗は恐れるものではないと伝えたいです。",
                     "しっぱいはおそれるものではないとつたえたいです。",
                     "That failure is nothing to be afraid of."),
                    ("them", "経験の少ない人には何と言いますか。",
                     "けいけんのすくないひとにはなんといいますか。",
                     "What do you say to people with little experience?"),
                    ("you", "まず形を覚えれば、後で意味が分かるものです。",
                     "まずかたちをおぼえれば、あとでいみがわかるものです。",
                     "Learn the shape first; the meaning comes afterwards."),
                ],
                "patterns": [
                    {
                        "text": "{x}ものだと教わりました",
                        "reading": "{x}ものだとおそわりました",
                        "en": "I was taught that one {x}",
                        "values": [
                            ("約束を守る", "やくそくをまもる", "keeps promises"),
                            ("感謝を忘れない", "かんしゃをわすれない", "does not forget gratitude"),
                            ("謙虚でいる", "けんきょでいる", "stays modest"),
                        ],
                    },
                    {
                        "text": "{x}ものではありません",
                        "reading": "{x}ものではありません",
                        "en": "It is not something to {x}",
                        "values": [
                            ("急ぐ", "いそぐ", "be rushed"),
                            ("恐れる", "おそれる", "be afraid of"),
                            ("一人で抱える", "ひとりでかかえる", "carry alone"),
                        ],
                    },
                    {
                        "text": "{x}ものだと思います",
                        "reading": "{x}ものだとおもいます",
                        "en": "It is only natural that {x}",
                        "values": [
                            ("最初は上手くいかない", "さいしょはうまくいかない", "things do not go well at first"),
                            ("時間がかかる", "じかんがかかる", "it takes time"),
                            ("人は迷う", "ひとはまよう", "people hesitate"),
                        ],
                    },
                ],
                "notes": [
                    "〜ものだ states how things are by nature or by custom; 〜ものではない says they should not be treated so.",
                ],
            },
            {
                "id": 61,
                "title": "Saying it indirectly",
                "goal": "Disagree without ever saying no: 持ち帰る / 検討させていただく.",
                "vocab": [
                    ("検討", "けんとう", "consideration / examining"),
                    ("持ち帰る", "もちかえる", "to take back (for consideration)"),
                    ("角度", "かくど", "angle / point of view"),
                    ("遠回し", "とおまわし", "indirect (speech)"),
                    ("顔をつぶす", "かおをつぶす", "to make someone lose face"),
                    ("断る", "ことわる", "to decline"),
                    ("申し訳ありません", "もうしわけありません", "I am truly sorry"),
                ],
                "dialogue": [
                    ("you", "この提案、一度持ち帰らせていただけますか。",
                     "このていあん、いちどもちかえらせていただけますか。",
                     "Might I take this proposal back with me once?"),
                    ("them", "つまり、賛成できないということですか。",
                     "つまり、さんせいできないということですか。",
                     "In other words, you cannot agree to it."),
                    ("you", "いいえ、別の角度からも見たいということです。",
                     "いいえ、べつのかくどからもみたいということです。",
                     "No — only that I would like to see it from another angle."),
                    ("them", "遠回しに断られている気がします。",
                     "とおまわしにことわられているきがします。",
                     "This feels like a refusal at one remove."),
                    ("you", "申し訳ありません。顔をつぶすつもりはありません。",
                     "もうしわけありません。かおをつぶすつもりはありません。",
                     "My apologies. I have no wish to make anyone lose face."),
                    ("them", "では、いつ頃いただけますか。",
                     "では、いつごろいただけますか。",
                     "Then when might we hear from you?"),
                    ("you", "検討した上で、今週中に書面でお答えいたします。",
                     "けんとうしたうえで、こんしゅうちゅうにしょめんでおこたえいたします。",
                     "Once we have examined it, in writing, within this week."),
                ],
                "patterns": [
                    {
                        # Same 〜させて trap as L52: 持ち帰る is godan, so the value
                        # carries 持ち帰らせて rather than the frame forcing 持ち帰りさせて.
                        "text": "一度{x}いただければと存じます",
                        "reading": "いちど{x}いただければとぞんじます",
                        "en": "If I might be allowed to {x} once",
                        "values": [
                            ("持ち帰らせて", "もちかえらせて", "take it away with me"),
                            ("検討させて", "けんとうさせて", "examine it"),
                            ("相談させて", "そうだんさせて", "talk it over"),
                        ],
                    },
                    {
                        "text": "別の角度から{x}たいのです",
                        "reading": "べつのかくどから{x}たいのです",
                        "en": "I would like to {x} from another angle",
                        "values": [
                            ("見", "み", "look at it"),
                            ("検討し", "けんとうし", "examine it"),
                            ("考え", "かんがえ", "think about it"),
                        ],
                    },
                    {
                        "text": "{x}という形にさせていただきます",
                        "reading": "{x}というかたちにさせていただきます",
                        "en": "I would like to settle it as {x}",
                        "values": [
                            ("書面で回答", "しょめんでかいとう", "a reply in writing"),
                            ("後日回答", "ごじつかいとう", "an answer at a later date"),
                            ("段階的な実施", "だんかいてきなじっし", "a staged rollout"),
                        ],
                    },
                ],
                "notes": [
                    "持ち帰る = take a proposal back to your own people; it lets you say 'not yet' without saying 'no'.",
                    "〜ということですが repairs a reading someone has just put on you: that is not quite what I meant.",
                ],
            },
        ],
    },
]


LEVEL = {
    "band": 1,
    "id": 5,
    # Business keigo set phrases plus N3 grammar (〜べきだ, 〜こそ, 〜ものだ,
    # 〜と思われる) with a few N2 points (〜に基づいて, 〜た上で). Not N1:
    # docs/COURSE_AUDIT.md, finding 1.
    "code": "N3",
    "title": "JLPT N3 · Keigo & argument",
    "focus": "Business keigo (〜と申します, 〜いたします, 〜いただけますでしょうか), declining and calling politely, and N3 tools for argument: 〜べきだ, 〜こそ, 〜ものだ, 〜と思われる, with a first look at N2's 〜に基づいて and 〜た上で.",
    "gate": {"min_pron_score": 80.0, "min_accuracy": 80.0, "min_completeness": 88.0},
    "units": UNITS,
}

# -*- coding: utf-8 -*-
"""Band 2 (shown as N4–N3) — opinions and reasons.

Pimsleur-style.  Polite base (です/ます) with a fair share of plain form,
which is correct here: news, opinions and conditions are the point of this
band, not errands.  Each lesson's vocabulary is re-used in the dialogue so
the learner meets the words twice in one sitting.

  text    the line as Japanese write it (kanji + kana, normal script)
  reading the same line written entirely in kana — the furigana slot
          printed above the line, including okurigana
  en      natural English

Pattern slots use the same three keys: text / reading / en, each carrying a
"{x}" placeholder that the value fills in.

A pattern may also carry "kind", naming what {x} accepts so the app can drop
a word learned elsewhere into this frame:

    object | place | person | clock | day | food | weather-noun | weather-adj

The last two are one concept in two word forms.  A slot that takes 雨/雪/大雨
("rain"/"snow"/"heavy rain") is weather-noun; one that takes 晴れ/雨/曇り
("sunny"/"rainy"/"cloudy") is weather-adj, and the two must never share a
tag.  Likewise every value gloss is written to compose inside its own frame:
"the population" for "{x} keeps falling", never "sales" for a singular verb.
Slots that take verbs or full clauses are deliberately left untagged —
学校を食べます is worse than no slot at all, and the course works fine with
none.
"""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Unit 9 - Work & Society.  What you heard, why it happened, who did it
    # to you, and who you had do it.
    # -----------------------------------------------------------------------
    {
        "id": 9,
        "title": "Work & Society",
        "focus": "Pass on what you hear at work, give a reason, and talk about what was done to you or made someone do.",
        "gate": {"min_pron_score": 76.0, "min_accuracy": 76.0, "min_completeness": 86.0},
        "lessons": [
            {
                "id": 38,
                "title": "I heard that…",
                "goal": "Pass on what you heard at work: 〜そうです / 〜によると.",
                "vocab": [
                    ("部長", "ぶちょう", "department manager"),
                    ("同僚", "どうりょう", "colleague"),
                    ("転勤", "てんきん", "job transfer"),
                    ("今月", "こんげつ", "this month"),
                    ("噂", "うわさ", "rumour"),
                    ("本当", "ほんとう", "true / really"),
                    ("知る", "しる", "to know"),
                    ("びっくりする", "びっくりする", "to be surprised"),
                    ("いっぱい", "いっぱい", "until the end of (今月いっぱい)"),
                ],
                "dialogue": [
                    ("them", "部長が来月から転勤するそうです。", "ぶちょうがらいげつからてんきんするそうです。",
                     "I hear the manager is being transferred from next month."),
                    ("you", "え、本当ですか。誰に聞きましたか。", "え、ほんとうですか。だれにききましたか。",
                     "Really? Who told you?"),
                    ("them", "同僚の佐藤さんです。噂じゃないですよ。", "どうりょうのさとうさんです。うわさじゃないですよ。",
                     "My colleague Sato. It's not a rumour."),
                    ("you", "そうですか。今月いっぱいで、いなくなるんですね。", "そうですか。こんげついっぱいで、いなくなるんですね。",
                     "I see. So he'll be gone by the end of this month."),
                    ("them", "ええ。次の部長は東京から来るそうです。", "ええ。つぎのぶちょうはとうきょうからくるそうです。",
                     "Yes. And the next manager comes from Tokyo, they say."),
                    ("you", "それは知りませんでした。びっくりしました。", "それはしりませんでした。びっくりしました。",
                     "I didn't know that. That's a surprise."),
                ],
                "patterns": [
                    {
                        "text": "{x}そうです",
                        "reading": "{x}そうです",
                        "en": "I hear that {x}",
                        "values": [
                            ("部長が転勤する", "ぶちょうがてんきんする", "the manager is being transferred"),
                            ("新しい人が来る", "あたらしいひとがくる", "a new person is coming"),
                            ("給料が上がる", "きゅうりょうがあがる", "salaries are going up"),
                        ],
                    },
                    {
                        "text": "{x}の話では、来月転勤するそうです",
                        "reading": "{x}のはなしでは、らいげつてんきんするそうです",
                        "en": "According to {x}, he transfers next month",
                        "kind": "person",
                        "values": [
                            ("佐藤さん", "さとうさん", "Sato"),
                            ("部長", "ぶちょう", "the manager"),
                            ("田中さん", "たなかさん", "Tanaka"),
                        ],
                    },
                    {
                        "text": "{x}に転勤するそうです",
                        "reading": "{x}にてんきんするそうです",
                        "en": "I hear he is being transferred to {x}",
                        "kind": "place",
                        "values": [
                            ("東京", "とうきょう", "Tokyo"),
                            ("大阪", "おおさか", "Osaka"),
                            ("札幌", "さっぽろ", "Sapporo"),
                        ],
                    },
                ],
                "notes": [
                    "〜そうです after a plain clause = 'I heard that …': 転勤するそうです. It is not the そうです that means 'it looks like rain'.",
                    "〜によると / 〜の話では mark the source: 天気予報によると.",
                ],
            },
            {
                "id": 39,
                "title": "Giving a reason",
                "goal": "Explain why at work with 〜ので and 〜ため（に）.",
                "vocab": [
                    ("遅刻", "ちこく", "being late"),
                    ("理由", "りゆう", "reason"),
                    ("電車", "でんしゃ", "train"),
                    ("事故", "じこ", "accident"),
                    ("影響", "えいきょう", "effect / impact"),
                    ("報告", "ほうこく", "report"),
                    ("早く", "はやく", "early / sooner"),
                    ("安心", "あんしん", "relief / peace of mind"),
                    ("もっと", "もっと", "more"),
                ],
                "dialogue": [
                    ("them", "今朝は遅刻でしたね。理由を聞かせてください。", "けさはちこくでしたね。りゆうをきかせてください。",
                     "You were late this morning. Let me hear your reason."),
                    ("you", "電車の事故の影響で、遅れてしまいました。", "でんしゃのじこのえいきょうで、おくれてしまいました。",
                     "There was a train accident and I got held up."),
                    ("them", "そうですか。それは大変でしたね。", "そうですか。それはたいへんでしたね。",
                     "I see. That must have been rough."),
                    ("you", "すみません。もっと早く報告すればよかったです。", "すみません。もっとはやくほうこくすればよかったです。",
                     "Sorry. I should have reported it sooner."),
                    ("them", "事故のために、ほかの人も遅れましたよ。", "じこのために、ほかのひともおくれましたよ。",
                     "Others were late too because of the accident."),
                    ("you", "安心しました。明日は気をつけます。", "あんしんしました。あしたはきをつけます。",
                     "That's a relief. I'll be careful tomorrow."),
                ],
                "patterns": [
                    {
                        "text": "{x}のために遅れました",
                        "reading": "{x}のためにおくれました",
                        "en": "I was late because of {x}",
                        "values": [
                            ("事故", "じこ", "the accident"),
                            ("雨", "あめ", "the rain"),
                            ("工事", "こうじ", "the roadworks"),
                        ],
                    },
                    {
                        "text": "{x}ので、会議に出られません",
                        "reading": "{x}ので、かいぎにでられません",
                        "en": "Since {x}, I can't attend the meeting",
                        "values": [
                            ("電車が遅れている", "でんしゃがおくれている", "the train is delayed"),
                            ("別の予定がある", "べつのよていがある", "I have another appointment"),
                            ("体調が悪い", "たいちょうがわるい", "I'm not well"),
                        ],
                    },
                ],
                "notes": [
                    "〜ので = 'since'; it presents a reason rather than pushing one, so it is softer than から.",
                    "〜ため（に） is the formal twin, common in writing and at work: 事故のために遅れた.",
                ],
            },
            {
                "id": 40,
                "title": "Things done to you",
                "goal": "Say what was done to you, and by whom: 〜れる / 〜られる.",
                "vocab": [
                    ("注意する", "ちゅういする", "to warn / caution"),
                    ("呼ぶ", "よぶ", "to call / summon"),
                    ("褒める", "ほめる", "to praise"),
                    ("上司", "じょうし", "boss / superior"),
                    ("会議", "かいぎ", "meeting"),
                    ("意見", "いけん", "opinion"),
                    ("困る", "こまる", "to be in trouble / at a loss"),
                    ("認める", "みとめる", "to recognise / acknowledge"),
                ],
                "dialogue": [
                    ("them", "今朝、部長に呼ばれました。", "けさ、ぶちょうによばれました。",
                     "The manager called me in this morning."),
                    ("you", "え、何かありましたか。", "え、なにかありましたか。",
                     "Oh? What about?"),
                    ("them", "遅刻のことで注意されました。", "ちこくのことでちゅういされました。",
                     "I was warned about my lateness."),
                    ("you", "それは困りましたね。", "それはこまりましたね。",
                     "That's awkward."),
                    ("them", "会議で意見を言ったら、今度は褒められました。", "かいぎでいけんをいったら、こんどはほめられました。",
                     "When I gave my opinion at the meeting, I got praised for once."),
                    ("you", "よかったですね。上司に認められたということです。", "よかったですね。じょうしにみとめられたということです。",
                     "Good for you. It means your boss rates you."),
                ],
                "patterns": [
                    {
                        "text": "{x}に注意されました",
                        "reading": "{x}にちゅういされました",
                        "en": "I was cautioned by {x}",
                        "kind": "person",
                        "values": [
                            ("部長", "ぶちょう", "the manager"),
                            ("上司", "じょうし", "my boss"),
                            ("先生", "せんせい", "the teacher"),
                        ],
                    },
                    {
                        "text": "{x}で褒められました",
                        "reading": "{x}でほめられました",
                        "en": "I was praised for {x}",
                        "values": [
                            ("会議での意見", "かいぎでのいけん", "my opinion at the meeting"),
                            ("昨日の仕事", "きのうのしごと", "yesterday's work"),
                            ("この企画書", "このきかくしょ", "this proposal"),
                        ],
                    },
                ],
                "notes": [
                    "Passive: 呼ぶ → 呼ばれる, 注意する → 注意される. Whoever did it takes に: 部長に呼ばれた.",
                    "When the cause is a thing or an occasion, に becomes で: 会議で褒められた.",
                ],
            },
            {
                "id": 41,
                "title": "Having someone do it",
                "goal": "Say you had someone do something, or were made to: 〜せる / 〜させる.",
                "vocab": [
                    ("手伝う", "てつだう", "to help"),
                    ("後輩", "こうはい", "junior colleague"),
                    ("用意する", "よういする", "to prepare"),
                    ("資料", "しりょう", "materials / handout"),
                    ("担当", "たんとう", "person in charge"),
                    ("待つ", "まつ", "to wait"),
                    ("避ける", "さける", "to avoid"),
                ],
                "dialogue": [
                    ("them", "新しい企画は誰が担当しますか。", "あたらしいきかくはだれがたんとうしますか。",
                     "Who is in charge of the new project?"),
                    ("you", "私です。後輩にも手伝わせるつもりです。", "わたしです。こうはいにもてつだわせるつもりです。",
                     "Me. I'll have my junior help too."),
                    ("them", "一人では大変でしょう。", "ひとりではたいへんでしょう。",
                     "It would be tough alone."),
                    ("you", "ええ。資料は後輩に用意させました。", "ええ。しりょうはこうはいによういさせました。",
                     "True. I had my junior prepare the materials."),
                    ("them", "それはいいですね。時間は足りますか。", "それはいいですね。じかんはたりますか。",
                     "Good. Do you have enough time?"),
                    ("you", "足りますが、お客さんを待たせるのは避けたいです。", "たりますが、おきゃくさんをまたせるのはさけたいです。",
                     "Yes, but I'd rather not keep customers waiting."),
                    ("them", "わかりました。私も手伝いますよ。", "わかりました。わたしもてつだいますよ。",
                     "Understood. I'll help as well."),
                ],
                "patterns": [
                    {
                        "text": "{x}に手伝わせます",
                        "reading": "{x}にてつだわせます",
                        "en": "I'll have {x} help",
                        "kind": "person",
                        "values": [
                            ("後輩", "こうはい", "my junior colleague"),
                            ("同僚", "どうりょう", "a colleague"),
                            ("息子", "むすこ", "my son"),
                        ],
                    },
                    {
                        "text": "後輩に{x}させました",
                        "reading": "こうはいに{x}させました",
                        "en": "I had my junior {x}",
                        "values": [
                            ("資料を用意", "しりょうをようい", "prepare the materials"),
                            ("部屋を掃除", "へやをそうじ", "clean the room"),
                            ("書類をコピー", "しょるいをコピー", "copy the documents"),
                        ],
                    },
                ],
                "notes": [
                    "Causative: 手伝う → 手伝わせる, 待つ → 待たせる. The person who has to do it takes に.",
                    "〜（さ）せられる turns it back on you: 待たされる = 'I was kept waiting'.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 10 - News, Opinions & Reasons.  Report, judge, deny, explain why.
    # -----------------------------------------------------------------------
    {
        "id": 10,
        "title": "News, Opinions & Reasons",
        "focus": "Report the news, say what you think, deny the obvious conclusion, and give the cause.",
        "gate": {"min_pron_score": 78.0, "min_accuracy": 78.0, "min_completeness": 86.0},
        "lessons": [
            {
                "id": 42,
                "title": "According to the news",
                "goal": "Report what the news said: 〜によると〜そうです.",
                "vocab": [
                    ("ニュース", "ニュース", "news"),
                    ("経済", "けいざい", "the economy"),
                    ("人口", "じんこう", "population"),
                    ("減る", "へる", "to decrease"),
                    ("増える", "ふえる", "to increase"),
                    ("来月", "らいげつ", "next month"),
                    ("選挙", "せんきょ", "election"),
                    ("なるほど", "なるほど", "I see"),
                ],
                "dialogue": [
                    ("them", "今朝のニュースを見ましたか。", "けさのニュースをみましたか。",
                     "Did you see the news this morning?"),
                    ("you", "いいえ、何かありましたか。", "いいえ、なにかありましたか。",
                     "No, what happened?"),
                    ("them", "ニュースによると、経済が少し良くなるそうです。", "ニュースによると、けいざいがすこしよくなるそうです。",
                     "According to the news, the economy is set to improve a little."),
                    ("you", "本当ですか。人口は減る一方だと思っていました。", "ほんとうですか。じんこうはへるいっぽうだとおもっていました。",
                     "Really? I thought the population only ever fell."),
                    ("them", "ええ、地方は減っています。でも都市は増えています。", "ええ、ちほうはへっています。でもとしはふえています。",
                     "Yes, rural areas are shrinking. But the cities are growing."),
                    ("you", "なるほど。来月の選挙にも影響しますね。", "なるほど。らいげつのせんきょにもえいきょうしますね。",
                     "I see. That will affect next month's election too."),
                    ("them", "そういうことですね。", "そういうことですね。",
                     "That's the gist of it."),
                ],
                "patterns": [
                    {
                        "text": "ニュースによると、{x}そうです",
                        "reading": "ニュースによると、{x}そうです",
                        "en": "According to the news, {x}",
                        "values": [
                            ("経済が良くなる", "けいざいがよくなる", "the economy is improving"),
                            ("人口が減っている", "じんこうがへっている", "the population is falling"),
                            ("新しい駅ができる", "あたらしいえきができる", "a new station is being built"),
                        ],
                    },
                    {
                        "text": "{x}は減る一方です",
                        "reading": "{x}はへるいっぽうです",
                        "en": "{x} keeps falling",
                        "values": [
                            ("人口", "じんこう", "the population"),
                            ("客の数", "きゃくのかず", "the number of customers"),
                            ("利用者の数", "りようしゃのかず", "the number of users"),
                        ],
                    },
                ],
                "notes": [
                    "〜によると marks where the information came from; the 〜そうです after it means 'they say'.",
                    "〜一方だ = keeps moving one way only: 減る一方だ (does nothing but fall).",
                ],
            },
            {
                "id": 43,
                "title": "It must be…",
                "goal": "Say you are sure, and say what should follow: 〜に違いない / 〜はずです.",
                "vocab": [
                    ("犯人", "はんにん", "the culprit"),
                    ("証拠", "しょうこ", "evidence"),
                    ("鍵", "かぎ", "key"),
                    ("顔", "かお", "face"),
                    ("現場", "げんば", "the scene / the site"),
                    ("逃げる", "にげる", "to run away"),
                    ("社内", "しゃない", "inside the company"),
                    ("違いない", "ちがいない", "there is no doubt / must be"),
                    ("記録", "きろく", "record"),
                    ("はず", "はず", "should (expectation)"),
                ],
                "dialogue": [
                    ("them", "財布がなくなったそうですね。犯人は分かりましたか。", "さいふがなくなったそうですね。はんにんはわかりましたか。",
                     "I hear your wallet went missing. Do you know who took it?"),
                    ("you", "分かりません。でも、社内にいた人に違いないです。", "わかりません。でも、しゃないにいたひとにちがいないです。",
                     "No. But it must be someone who was in the office."),
                    ("them", "証拠はありますか。", "しょうこはありますか。",
                     "Is there any evidence?"),
                    ("you", "鍵の記録があります。それを見れば分かるはずです。", "かぎのきろくがあります。それをみればわかるはずです。",
                     "There's a key-card log. Looking at it should tell us."),
                    ("them", "現場にいた人の顔は覚えていますか。", "げんばにいたひとのかおはおぼえていますか。",
                     "Do you remember the faces of the people there?"),
                    ("you", "少しだけ。逃げる人はいなかったと思います。", "すこしだけ。にげるひとはいなかったとおもいます。",
                     "Only a little. I don't think anyone ran off."),
                ],
                "patterns": [
                    {
                        "text": "{x}に違いない",
                        "reading": "{x}にちがいない",
                        "en": "It must be {x}",
                        "kind": "person",
                        "values": [
                            ("社内にいた人", "しゃないにいたひと", "someone who was in the office"),
                            ("彼", "かれ", "him"),
                            ("昨日来た客", "きのうきたきゃく", "the visitor who came yesterday"),
                        ],
                    },
                    {
                        "text": "{x}はずです",
                        "reading": "{x}はずです",
                        "en": "It should {x}",
                        "values": [
                            ("すぐ分かる", "すぐわかる", "be clear straight away"),
                            ("間に合う", "まにあう", "be in time"),
                            ("もう着いている", "もうついている", "have arrived already"),
                        ],
                    },
                ],
                "notes": [
                    "〜に違いない = 'I am certain'; 〜はずだ = 'it should be, given what I know'.",
                    "Both follow the plain form: 分かるはずです, いたに違いない.",
                ],
            },
            {
                "id": 44,
                "title": "It's not that…",
                "goal": "Deny the obvious conclusion: 〜わけではない / 〜というほどではない.",
                "vocab": [
                    ("反対", "はんたい", "opposition / against"),
                    ("賛成", "さんせい", "agreement / in favour"),
                    ("難しい", "むずかしい", "difficult"),
                    ("簡単", "かんたん", "simple / easy"),
                    ("全部", "ぜんぶ", "everything"),
                    ("説明", "せつめい", "explanation"),
                ],
                "dialogue": [
                    ("them", "田中さんの案に反対なんですか。", "たなかさんのあんにはんたいなんですか。",
                     "So you are against Tanaka's proposal?"),
                    ("you", "いいえ、反対しているわけではないんです。", "いいえ、はんたいしているわけではないんです。",
                     "No, it's not that I'm against it."),
                    ("them", "じゃあ、賛成なんですね。", "じゃあ、さんせいなんですね。",
                     "Then you're for it."),
                    ("you", "それも簡単には言えません。難しいところもあります。", "それもかんたんにはいえません。むずかしいところもあります。",
                     "I can't put it that simply either. There are difficult parts."),
                    ("them", "全部直したほうがいいですか。", "ぜんぶなおしたほうがいいですか。",
                     "Should we revise all of it?"),
                    ("you", "全部ではなく、一部でいいと思います。", "ぜんぶではなく、いちぶでいいとおもいます。",
                     "Not all of it — I think a part would do."),
                    ("them", "分かりました。説明してくれてありがとう。", "わかりました。せつめいしてくれてありがとう。",
                     "I see. Thanks for explaining."),
                ],
                "patterns": [
                    {
                        "text": "{x}わけではありません",
                        "reading": "{x}わけではありません",
                        "en": "It's not that I {x}",
                        "values": [
                            ("反対している", "はんたいしている", "am against it"),
                            ("嫌いな", "きらいな", "dislike it"),
                            ("忙しい", "いそがしい", "am busy"),
                        ],
                    },
                    {
                        "text": "{x}というほどではありません",
                        "reading": "{x}というほどではありません",
                        "en": "It's not all that {x}",
                        "values": [
                            ("難しい", "むずかしい", "difficult"),
                            ("高い", "たかい", "expensive"),
                            ("遠い", "とおい", "far"),
                        ],
                    },
                ],
                "notes": [
                    "〜わけではない denies the conclusion the other person just drew: 反対しているわけではない.",
                    "〜というほどではない = 'not to that extent': 難しいというほどではない.",
                ],
            },
            {
                "id": 45,
                "title": "Because of it",
                "goal": "Say what caused a good or a bad result: 〜おかげで / 〜せいで.",
                "vocab": [
                    ("体調", "たいちょう", "physical condition"),
                    ("睡眠", "すいみん", "sleep"),
                    ("失敗", "しっぱい", "failure / mistake"),
                    ("成功", "せいこう", "success"),
                    ("準備", "じゅんび", "preparation"),
                    ("油断", "ゆだん", "carelessness"),
                    ("声", "こえ", "voice"),
                ],
                "dialogue": [
                    ("them", "昨日の発表、うまくいきましたか。", "きのうのはっぴょう、うまくいきましたか。",
                     "Did yesterday's presentation go well?"),
                    ("you", "ええ、準備をしたおかげで、失敗しませんでした。", "ええ、じゅんびをしたおかげで、しっぱいしませんでした。",
                     "Yes — thanks to preparing, I didn't mess it up."),
                    ("them", "それはよかった。緊張しましたか。", "それはよかった。きんちょうしましたか。",
                     "Good for you. Were you nervous?"),
                    ("you", "少し。睡眠が足りなかったせいか、声が小さかったです。", "すこし。すいみんがたりなかったせいか、こえがちいさかったです。",
                     "A bit. Maybe because I hadn't slept enough, my voice was quiet."),
                    ("them", "体調は大丈夫ですか。", "たいちょうはだいじょうぶですか。",
                     "Are you feeling all right?"),
                    ("you", "ええ。油断しないで、もう一度準備します。", "ええ。ゆだんしないで、もういちどじゅんびします。",
                     "Yes. I won't get careless, and I'll prepare again."),
                    ("them", "その調子なら、次の発表も成功しますよ。", "そのちょうしなら、つぎのはっぴょうもせいこうしますよ。",
                     "At that rate the next one will succeed too."),
                ],
                "patterns": [
                    {
                        "text": "{x}のおかげで、成功しました",
                        "reading": "{x}のおかげで、せいこうしました",
                        "en": "Thanks to {x}, it worked out",
                        "values": [
                            ("準備", "じゅんび", "the preparation"),
                            ("練習", "れんしゅう", "the practice"),
                            ("みんなの手伝い", "みんなのてつだい", "everyone's help"),
                        ],
                    },
                    {
                        "text": "{x}のせいで、遅れました",
                        "reading": "{x}のせいで、おくれました",
                        "en": "Because of {x}, I was late",
                        "values": [
                            ("寝坊", "ねぼう", "oversleeping"),
                            ("雨", "あめ", "the rain"),
                            ("油断", "ゆだん", "my carelessness"),
                        ],
                    },
                ],
                "notes": [
                    "おかげで = thanks to (a good result); せいで = because of (a bad result, with a hint of blame).",
                    "せいか softens it to 'maybe it was because of…': 睡眠が足りなかったせいか.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 11 - Plans, Conditions & Consequences.  If, even if, and what
    # the schedule actually says.
    # -----------------------------------------------------------------------
    {
        "id": 11,
        "title": "Plans, Conditions & Consequences",
        "focus": "Set a condition, accept the risk, talk about the schedule, and finish a negotiation.",
        "gate": {"min_pron_score": 80.0, "min_accuracy": 80.0, "min_completeness": 88.0},
        "lessons": [
            {
                "id": 46,
                "title": "If it happens",
                "goal": "Set a condition and say what follows: 〜たら / 〜ば / 〜なら.",
                "vocab": [
                    ("晴れる", "はれる", "to clear up (weather)"),
                    ("中止", "ちゅうし", "cancellation"),
                    ("出発", "しゅっぱつ", "departure"),
                    ("傘", "かさ", "umbrella"),
                    ("心配", "しんぱい", "worry"),
                    ("天気予報", "てんきよほう", "weather forecast"),
                ],
                "dialogue": [
                    ("them", "明日の天気予報はどうですか。", "あしたのてんきよほうはどうですか。",
                     "What is the forecast for tomorrow?"),
                    ("you", "午後から雨だそうです。", "ごごからあめだそうです。",
                     "They say rain from the afternoon."),
                    ("them", "雨なら、遠足は中止しましょう。", "あめなら、えんそくはちゅうししましょう。",
                     "If it rains, let's call off the outing."),
                    ("you", "晴れたら、予定通り出発します。", "はれたら、よていどおりしゅっぱつします。",
                     "If it clears up, we'll leave as planned."),
                    ("them", "傘を持って行けば、心配はいりません。", "かさをもっていけば、しんぱいはいりません。",
                     "If we take umbrellas, there's nothing to worry about."),
                    ("you", "そうですね。六時に出発しましょう。", "そうですね。ろくじにしゅっぱつしましょう。",
                     "True. Let's set off at six."),
                    ("them", "早いほうが道が空いていますよ。", "はやいほうがみちがあいていますよ。",
                     "Earlier is better — the roads are emptier."),
                ],
                "patterns": [
                    {
                        "text": "{x}なら、中止します",
                        "reading": "{x}なら、ちゅうしします",
                        "en": "If there's {x}, we'll call it off",
                        "kind": "weather-noun",
                        "values": [
                            ("雨", "あめ", "rain"),
                            ("雪", "ゆき", "snow"),
                            ("大雨", "おおあめ", "heavy rain"),
                        ],
                    },
                    {
                        "text": "晴れたら{x}",
                        "reading": "はれたら{x}",
                        "en": "If it clears up, {x}",
                        "values": [
                            ("出発します", "しゅっぱつします", "we'll set off"),
                            ("外で食べます", "そとでたべます", "we'll eat outside"),
                            ("歩いて行きます", "あるいていきます", "we'll walk"),
                        ],
                    },
                ],
                "notes": [
                    "なら = 'if that is the case' (a condition on what was just said); たら = 'once it happens'.",
                    "ば is the general 'if': 傘を持って行けば、心配はいらない.",
                ],
            },
            {
                "id": 47,
                "title": "Even if",
                "goal": "Say a result still holds against the odds: 〜ても / 〜にもかかわらず.",
                "vocab": [
                    ("性能", "せいのう", "performance / spec"),
                    ("修理", "しゅうり", "repair"),
                    ("古い", "ふるい", "old"),
                    ("値段", "ねだん", "price"),
                    ("決心", "けっしん", "resolve / decision"),
                    ("納得", "なっとく", "being convinced"),
                    ("壊れる", "こわれる", "to break"),
                    ("それなら", "それなら", "in that case"),
                ],
                "dialogue": [
                    ("them", "このパソコン、古いですが性能はいいです。", "このパソコン、ふるいですがせいのうはいいです。",
                     "This PC is old, but it performs well."),
                    ("you", "修理すれば、まだ使えますね。", "しゅうりすれば、まだつかえますね。",
                     "If we repaired it, it would still be usable."),
                    ("them", "ええ。修理しても、値段は安いです。", "ええ。しゅうりしても、ねだんはやすいです。",
                     "Yes. Even with the repair, it's cheap."),
                    ("you", "壊れても、すぐ直ると思います。", "こわれても、すぐなおるとおもいます。",
                     "Even if it breaks, I think it can be fixed quickly."),
                    ("them", "古いにもかかわらず、人気があるんです。", "ふるいにもかかわらず、にんきがあるんです。",
                     "Despite being old, it's popular."),
                    ("you", "それなら、買う決心がつきました。", "それなら、かうけっしんがつきました。",
                     "In that case, I've made up my mind to buy it."),
                    ("them", "納得いくまで、ほかのも見てください。", "なっとくいくまで、ほかのもみてください。",
                     "Look at the others too, until you're satisfied."),
                ],
                "patterns": [
                    {
                        "text": "{x}ても、買います",
                        "reading": "{x}ても、かいます",
                        "en": "Even if it's {x}, I'll buy it",
                        "values": [
                            ("高く", "たかく", "expensive"),
                            ("古く", "ふるく", "old"),
                            ("壊れ", "こわれ", "broken"),
                        ],
                    },
                    {
                        "text": "{x}にもかかわらず、よく売れています",
                        "reading": "{x}にもかかわらず、よくうれています",
                        "en": "Despite {x}, it sells well",
                        "values": [
                            ("値段が高い", "ねだんがたかい", "the high price"),
                            ("古い", "ふるい", "being old"),
                            ("宣伝がない", "せんでんがない", "having no advertising"),
                        ],
                    },
                ],
                "notes": [
                    "〜ても = 'even if / even though': 高くても買う. The て-form carries the contrast.",
                    "〜にもかかわらず = 'despite', and it sounds written: 古いにもかかわらず、人気がある.",
                ],
            },
            {
                "id": 48,
                "title": "What is planned",
                "goal": "Talk about the schedule and how it turned out: 〜予定です / 〜ことになっています / 〜てしまいます.",
                "vocab": [
                    ("予定", "よてい", "plan / schedule"),
                    ("締め切り", "しめきり", "deadline"),
                    ("完成", "かんせい", "completion"),
                    ("遅れる", "おくれる", "to be late / delayed"),
                    ("徹夜", "てつや", "staying up all night"),
                    ("無理", "むり", "impossible / overdoing it"),
                ],
                "dialogue": [
                    ("them", "新しいシステムはいつ完成しますか。締め切りは今週です。", "あたらしいシステムはいつかんせいしますか。しめきりはこんしゅうです。",
                     "When will the new system be finished? The deadline is this week."),
                    ("you", "来週の水曜日に完成する予定です。少し遅れてしまいました。", "らいしゅうのすいようびにかんせいするよていです。すこしおくれてしまいました。",
                     "It's scheduled for next Wednesday. It has slipped a little."),
                    ("them", "徹夜で直すんですか。", "てつやでなおすんですか。",
                     "Are you fixing it overnight?"),
                    ("you", "いいえ、徹夜は無理です。人員を増やすことになっています。", "いいえ、てつやはむりです。じんいんをふやすことになっています。",
                     "No, that's too much. We're to add more people."),
                    ("them", "それなら間に合いますね。", "それならまにあいますね。",
                     "Then you'll make it."),
                    ("you", "ええ、金曜までには終わらせます。", "ええ、きんようまでにはおわらせます。",
                     "Yes, I'll get it finished by Friday."),
                ],
                "patterns": [
                    {
                        "text": "{x}に完成する予定です",
                        "reading": "{x}にかんせいするよていです",
                        "en": "It's scheduled for {x}",
                        "kind": "day",
                        "values": [
                            ("来週の水曜日", "らいしゅうのすいようび", "next Wednesday"),
                            ("今週の金曜日", "こんしゅうのきんようび", "this Friday"),
                            ("来月の十日", "らいげつのとおか", "the tenth of next month"),
                        ],
                    },
                    {
                        "text": "{x}てしまいました",
                        "reading": "{x}てしまいました",
                        "en": "It has {x}",
                        "values": [
                            ("遅れ", "おくれ", "slipped"),
                            ("壊れ", "こわれ", "broken"),
                            ("忘れられ", "わすれられ", "been forgotten"),
                        ],
                    },
                ],
                "notes": [
                    "〜予定です = it is planned; 〜ことになっています = it has been decided, usually by someone else.",
                    "〜てしまう marks a result you cannot undo, often a regret: 遅れてしまった.",
                ],
            },
            {
                "id": 49,
                "title": "Review: the late delivery",
                "goal": "A full N2 exchange: report the news, give the reason, set a condition, decide.",
                "vocab": [
                    ("納品", "のうひん", "delivery of goods"),
                    ("交渉", "こうしょう", "negotiation"),
                    ("延期", "えんき", "postponement"),
                    ("対応", "たいおう", "response / handling"),
                    ("損害", "そんがい", "loss / damage"),
                    ("客", "きゃく", "customer / client"),
                    ("回答", "かいとう", "reply / answer"),
                ],
                "dialogue": [
                    ("them", "納品が一週間遅れるそうですね。客にはもう話しましたか。", "のうひんがいっしゅうかんおくれるそうですね。きゃくにはもうはなしましたか。",
                     "I hear the delivery will be a week late. Have you told the client yet?"),
                    ("you", "ええ、部品が足りないため、遅れています。延期の交渉もしています。", "ええ、ぶひんがたりないため、おくれています。えんきのこうしょうもしています。",
                     "Yes — we're short of parts, so it's behind. And we're negotiating a postponement."),
                    ("them", "承諾してもらえますか。", "しょうだくしてもらえますか。",
                     "Will they agree to that?"),
                    ("you", "対応が早ければ、大丈夫だと思います。", "たいおうがはやれば、だいじょうぶだとおもいます。",
                     "If we move quickly, I think it will be fine."),
                    ("them", "遅れたら、損害も大きいでしょう。", "おくれたら、そんがいもおおきいでしょう。",
                     "If it slips, the losses will be large too."),
                    ("you", "そうならないように、今日中に回答します。", "そうならないように、こんじゅうにかいとうします。",
                     "So that doesn't happen, I'll reply by the end of today."),
                ],
                "patterns": [
                    {
                        "text": "{x}ため、遅れています",
                        "reading": "{x}ため、おくれています",
                        "en": "Because {x}, it's behind schedule",
                        "values": [
                            ("部品が足りない", "ぶひんがたりない", "we're short of parts"),
                            ("人手がいない", "ひとでがいない", "we're short-handed"),
                            ("機械が壊れた", "きかいがこわれた", "a machine broke down"),
                        ],
                    },
                    {
                        "text": "{x}れば、間に合います",
                        "reading": "{x}れば、まにあいます",
                        "en": "If {x}, we'll make it",
                        "values": [
                            ("対応が早け", "たいおうがはやけ", "we act quickly"),
                            ("今日中に終え", "こんじゅうにおえ", "we finish today"),
                            ("人手が増え", "ひとでがふえ", "we get more people"),
                        ],
                    },
                    {
                        "text": "{x}ように、今日中に回答します",
                        "reading": "{x}ように、こんじゅうにかいとうします",
                        "en": "So that {x}, I'll reply by the end of today",
                        "values": [
                            ("遅れない", "おくれない", "it doesn't slip"),
                            ("問題にならない", "もんだいにならない", "it doesn't become a problem"),
                            ("客を待たせない", "きゃくをまたせない", "the client isn't kept waiting"),
                        ],
                    },
                ],
                "notes": [
                    "〜ため（に） after a plain clause states a cause formally: 部品が足りないため.",
                    "〜ないように = 'so that … does not happen': 遅れないように.",
                ],
            },
        ],
    },
]


LEVEL = {
    "band": 2,
    "id": 4,
    # Passive, causative, 〜そうだ, 〜たら/ば/なら, 〜ても, 〜はず and 〜てしまう are
    # N4 grammar; 〜によると, 〜に違いない, 〜わけではない and 〜おかげで/せいで are
    # N3 (docs/COURSE_AUDIT.md, finding 1).
    "code": "N4–N3",
    "title": "JLPT N4–N3 · Opinions & reasons",
    "focus": "The core of N4 grammar - hearsay (〜そうです), reasons (〜ので / 〜ため), conditionals (〜ば / 〜たら / 〜なら), 〜ても, passive and causative, 〜はず, 〜てしまう - plus first N3 points: 〜によると, 〜に違いない, 〜わけではない, 〜おかげで / 〜せいで.",
    "gate": {"min_pron_score": 76.0, "min_accuracy": 76.0, "min_completeness": 86.0},
    "units": UNITS,
}

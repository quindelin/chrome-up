# -*- coding: utf-8 -*-
"""JLPT N1+ — beyond the exam.

Nothing here is in the exam syllabus. It is the register you meet in a
newspaper editorial, a conference Q&A, a formal address: dense 漢語, hedged
assertions, 慣用句, and the ability to say the same thing at three levels of
formality. The learner is expected to already control 敬語 — the work here is
choosing, not conjugating.

  text    the line as Japanese write it (kanji + kana, normal script)
  reading the same line written entirely in kana — the furigana slot
          printed above the line, including okurigana
  en      natural English

Pattern slots use the same three keys: text / reading / en, each carrying a
"{x}" placeholder that the value fills in.  "kind" is set only where the slot
takes plain interchangeable nouns (object / place / person / clock / day /
weather / food); verbal and abstract slots are left untagged on purpose.
"""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Unit 15 - Media & current affairs.  新聞, 社説, インタビュー.
    # -----------------------------------------------------------------------
    {
        "id": 15,
        "title": "Media & Current Affairs",
        "focus": "Newspaper headlines, editorials, being interviewed, and weighing two accounts of a story.",
        "gate": {"min_pron_score": 84.0, "min_accuracy": 84.0, "min_completeness": 90.0},
        "lessons": [
            {
                "id": 62,
                "title": "Newspaper headlines",
                "goal": "Read a headline's compressed grammar and explain a story's fallout.",
                "vocab": [
                    ("見出し", "みだし", "headline"),
                    ("報道", "ほうどう", "news coverage"),
                    ("報じる", "ほうじる", "to report (a story)"),
                    ("本紙", "ほんし", "this newspaper"),
                    ("独占", "どくせん", "exclusive (scoop)"),
                    ("波紋", "はもん", "ripples / repercussions"),
                ],
                "dialogue": [
                    ("them", "今朝の見出しをご覧になりましたか。", "けさのみだしをごらんになりましたか。",
                     "Did you see this morning's headline?"),
                    ("you", "はい。本紙が独占で報じた件ですね。", "はい。ほんしがどくせんでほうじたけんですね。",
                     "Yes — the story this paper broke exclusively."),
                    ("them", "見出しは省略が多くて読みにくいですね。",
                     "みだしはしょうりゃくがおおくてよみにくいですね。",
                     "Headlines leave so much out, they are hard to read."),
                    ("you", "助詞が省かれるので、慣れが必要です。", "じょしがはぶかれるので、なれがひつようです。",
                     "Particles get dropped, so it takes getting used to."),
                    ("them", "この波紋は広がりそうですか。", "このはもんはひろがりそうですか。",
                     "Do you think the repercussions will spread?"),
                    ("you", "他紙も追随すれば、避けられないでしょう。",
                     "たしもついずいすれば、さけられないでしょう。",
                     "If the other papers follow, it will be hard to avoid."),
                    ("them", "報道の姿勢も問われますね。", "ほうどうのしせいもとわれますね。",
                     "The stance of the coverage will be questioned too."),
                ],
                "patterns": [
                    {
                        "text": "本紙が{x}で報じました",
                        "reading": "ほんしが{x}でほうじました",
                        "en": "This paper reported it {x}",
                        "values": [
                            ("独占", "どくせん", "exclusively"),
                            ("速報", "そくほう", "as a flash report"),
                            ("続報", "ぞくほう", "as a follow-up"),
                        ],
                    },
                    {
                        "text": "{x}が問われています",
                        "reading": "{x}がとわれています",
                        "en": "{x} is being called into question",
                        "values": [
                            ("報道の姿勢", "ほうどうのしせい", "the stance of the coverage"),
                            ("企業の責任", "きぎょうのせきにん", "the company's responsibility"),
                            ("行政の対応", "ぎょうせいのたいおう", "the administration's response"),
                        ],
                    },
                ],
                "notes": [
                    "Headlines drop particles and だ: 首相、訪米へ = 'PM to visit the US'. "
                    "Read them as compressed, not as broken Japanese.",
                    "波紋が広がる = 'the ripples spread' — the standard reporting idiom "
                    "for the fallout of a story.",
                ],
            },
            {
                "id": 63,
                "title": "Reading an editorial",
                "goal": "Follow an editorial's argument, its tone, and where it stops short.",
                "vocab": [
                    ("社説", "しゃせつ", "editorial / leading article"),
                    ("論調", "ろんちょう", "tone of the argument"),
                    ("提起", "ていき", "raising (an issue)"),
                    ("警鐘", "けいしょう", "alarm bell / warning"),
                    ("踏み込む", "ふみこむ", "to go further into"),
                    ("提言", "ていげん", "recommendation"),
                ],
                "dialogue": [
                    ("them", "今朝の社説はどんな論調でしたか。", "けさのしゃせつはどんなろんちょうでしたか。",
                     "What was the tone of this morning's editorial?"),
                    ("you", "慎重な論調です。警鐘を鳴らす内容でした。",
                     "しんちょうなろんちょうです。けいしょうをならすないようでした。",
                     "Cautious. It was a warning piece."),
                    ("them", "具体的には何を提起していますか。", "ぐたいてきにはなにをていきしていますか。",
                     "What exactly does it raise?"),
                    ("you", "人口減少と地域の維持という難問です。",
                     "じんこうげんしょうとちいきのいじというなんもんです。",
                     "The hard problem of population decline and keeping regions alive."),
                    ("them", "解決策には踏み込んでいますか。", "かいけつさくにはふみこんでいますか。",
                     "Does it go as far as a solution?"),
                    ("you", "いいえ。提言は示していますが、具体策は次の機会です。",
                     "いいえ。ていげんはしめしていますが、ぐたいさくはつぎのきかいです。",
                     "No. It offers recommendations, but specifics are for another day."),
                    ("them", "社説らしい終わり方ですね。", "しゃせつらしいおわりかたですね。",
                     "A very editorial way to end."),
                ],
                "patterns": [
                    {
                        "text": "{x}に警鐘を鳴らしています",
                        "reading": "{x}にけいしょうをならしています",
                        "en": "It sounds a warning about {x}",
                        "values": [
                            ("人口減少", "じんこうげんしょう", "population decline"),
                            ("財政の悪化", "ざいせいのあっか", "the worsening public finances"),
                            ("医療の格差", "いりょうのかくさ", "inequality in healthcare"),
                        ],
                    },
                    {
                        "text": "具体的な{x}には踏み込んでいません",
                        "reading": "ぐたいてきな{x}にはふみこんでいません",
                        "en": "It does not go as far as a concrete {x}",
                        "values": [
                            ("解決策", "かいけつさく", "solution"),
                            ("工程表", "こうていひょう", "timetable"),
                            ("財源", "ざいげん", "source of funding"),
                        ],
                    },
                ],
                "notes": [
                    "警鐘を鳴らす = 'sound the alarm bell' — the idiom editorials reach "
                    "for with a slow-moving problem nobody is acting on.",
                    "社説 rarely names a solution; 提言 (a recommendation) is the usual "
                    "endpoint, and 具体策は今後の課題に is the usual escape.",
                ],
            },
            {
                "id": 64,
                "title": "Being interviewed",
                "goal": "Answer a journalist carefully and correct a loaded premise.",
                "vocab": [
                    ("取材", "しゅざい", "interview / newsgathering"),
                    ("所見", "しょけん", "observations (formal)"),
                    ("認識", "にんしき", "understanding / perception"),
                    ("軌道修正", "きどうしゅうせい", "changing course"),
                    ("含み", "ふくみ", "implication / what is left unsaid"),
                    ("留保", "りゅうほ", "reservation / caveat"),
                ],
                "dialogue": [
                    ("them", "本日は取材をお受けいただき、ありがとうございます。",
                     "ほんじつはしゅざいをおうけいただき、ありがとうございます。",
                     "Thank you for agreeing to this interview today."),
                    ("you", "こちらこそ。率直にお答えします。", "こちらこそ。そっちょくにおこたえします。",
                     "The pleasure is mine. I'll answer frankly."),
                    ("them", "計画は順調だという認識でよろしいですか。",
                     "けいかくはじゅんちょうだというにんしきでよろしいですか。",
                     "Is it fair to understand that the plan is on track?"),
                    ("you", "少し留保があります。全面的には順調ではありません。",
                     "すこしりゅうほがあります。ぜんめんてきにはじゅんちょうではありません。",
                     "With one caveat. It is not going smoothly across the board."),
                    ("them", "つまり、軌道修正の必要があると。", "つまり、きどうしゅうせいのひつようがあると。",
                     "In other words, a change of course is needed."),
                    ("you", "その含みでお読みいただければ結構です。",
                     "そのふくみでおよみいただければけっこうです。",
                     "You may read it that way, if you wish."),
                    ("them", "最後に今後の所見をお願いします。", "さいごにこんごのしょけんをおねがいします。",
                     "Finally, your observations going forward."),
                ],
                "patterns": [
                    {
                        "text": "{x}という認識でよろしいですか",
                        "reading": "{x}というにんしきでよろしいですか",
                        "en": "Is it fair to understand that {x}?",
                        "values": [
                            ("計画は順調", "けいかくはじゅんちょう", "the plan is on track"),
                            ("予算は十分", "よさんはじゅうぶん", "the budget is sufficient"),
                            ("影響は軽微", "えいきょうはけいび", "the impact is minor"),
                        ],
                    },
                    {
                        "text": "少し留保があります。{x}",
                        "reading": "すこしりゅうほがあります。{x}",
                        "en": "With one caveat: {x}",
                        "values": [
                            ("全面的には賛成できません", "ぜんめんてきにはさんせいできません",
                             "I cannot agree across the board"),
                            ("時期はまだ未定です", "じきはまだみていです", "the timing is not yet fixed"),
                            ("詳細は未確認です", "しょうさいはみかくにんです",
                             "the details are unconfirmed"),
                        ],
                    },
                ],
                "notes": [
                    "〜という認識でよろしいですか is the interviewer's checking frame. "
                    "Answering 留保があります lets you correct the premise without "
                    "ever saying 違います.",
                    "含みを持たせる = 'leave it implied' — how a public figure says "
                    "something without quite saying it.",
                ],
            },
            {
                "id": 65,
                "title": "Review: discussing the news",
                "goal": "Summarise a story, weigh two accounts, and state your own position.",
                "vocab": [
                    ("報道各社", "ほうどうかくしゃ", "the various news outlets"),
                    ("食い違い", "くいちがい", "discrepancy"),
                    ("検証", "けんしょう", "verification"),
                    ("推測", "すいそく", "conjecture"),
                    ("断定", "だんてい", "stating flatly"),
                    ("注視", "ちゅうし", "watching closely"),
                ],
                "dialogue": [
                    ("them", "報道各社で数字が食い違っていますね。", "ほうどうかくしゃですうじがくいちがっていますね。",
                     "The figures differ between outlets."),
                    ("you", "ええ、推測と確認済みの事実が混ざっています。",
                     "ええ、すいそくとかくにんずみのじじつがまざっています。",
                     "Yes — conjecture and confirmed fact are mixed together."),
                    ("them", "どちらを信じるべきでしょうか。", "どちらをしんじるべきでしょうか。",
                     "Which should we believe?"),
                    ("you", "現段階では断定を避け、検証を待つべきです。",
                     "げんだんかいではだんていをさけ、けんしょうをまつべきです。",
                     "At this stage we should avoid flat statements and wait for verification."),
                    ("them", "あなたはどう読みますか。", "あなたはどうよみますか。",
                     "How do you read it?"),
                    ("you", "影響は限定的だと見ています。ただ、注視はしています。",
                     "えいきょうはげんていてきだとみています。ただ、ちゅうしはしています。",
                     "I read the impact as limited. But I am watching closely."),
                    ("them", "慎重な立場ですね。", "しんちょうなたちばですね。",
                     "A cautious position."),
                ],
                "patterns": [
                    {
                        "text": "現段階では{x}を避けるべきです",
                        "reading": "げんだんかいでは{x}をさけるべきです",
                        "en": "At this stage we should avoid {x}",
                        "values": [
                            ("断定", "だんてい", "flat statements"),
                            ("憶測", "おくそく", "speculation"),
                            ("過度な期待", "かどなきたい", "excessive expectations"),
                        ],
                    },
                    {
                        "text": "影響は{x}と見ています",
                        "reading": "えいきょうは{x}とみています",
                        "en": "I read the impact as {x}",
                        "values": [
                            ("限定的", "げんていてき", "limited"),
                            ("一時的", "いちじてき", "temporary"),
                            ("無視できない規模", "むしできないきぼ", "too large to ignore"),
                        ],
                    },
                ],
                "notes": [
                    "と見ています / と見られる is the reporter's hedge: it states a "
                    "reading, never a fact.",
                    "断定を避ける = 'refrain from stating flatly' — the professional "
                    "habit when sources disagree.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 16 - Professional & academic.  専門用語, 論文, 発表.
    # -----------------------------------------------------------------------
    {
        "id": 16,
        "title": "Professional & Academic",
        "focus": "Technical terms and definitions, reading a paper, giving a presentation, and handling questions.",
        "gate": {"min_pron_score": 86.0, "min_accuracy": 86.0, "min_completeness": 90.0},
        "lessons": [
            {
                "id": 66,
                "title": "Technical terms",
                "goal": "Define a technical term and say when it does not apply.",
                "vocab": [
                    ("専門用語", "せんもんようご", "technical term"),
                    ("定義", "ていぎ", "definition"),
                    ("該当", "がいとう", "falling under (a category)"),
                    ("狭義", "きょうぎ", "narrow sense"),
                    ("広義", "こうぎ", "broad sense"),
                    ("用例", "ようれい", "example of use"),
                ],
                "dialogue": [
                    ("them", "その専門用語の定義を確認させてください。",
                     "そのせんもんようごのていぎをかくにんさせてください。",
                     "Let me confirm the definition of that term."),
                    ("you", "狭義では装置そのものを指します。", "きょうぎではそうちそのものをさします。",
                     "In the narrow sense it refers to the device itself."),
                    ("them", "広義ではどうなりますか。", "こうぎではどうなりますか。",
                     "And in the broad sense?"),
                    ("you", "周辺の仕組み全体を含みます。用例によります。",
                     "しゅうへんのしくみぜんたいをふくみます。ようれいによります。",
                     "It includes the whole surrounding system. It depends on the usage."),
                    ("them", "今回の件は定義に該当しますか。", "こんかいのけんはていぎにがいとうしますか。",
                     "Does this case fall under the definition?"),
                    ("you", "厳密には該当しません。類例として扱います。",
                     "げんみつにはがいとうしません。るいれいとしてあつかいます。",
                     "Strictly, no. We'll treat it as an analogous case."),
                    ("them", "その線引きで資料を作りましょう。", "そのせんびきでしりょうをつくりましょう。",
                     "Let's draft the materials with that distinction."),
                ],
                "patterns": [
                    {
                        "text": "{x}には該当しません",
                        "reading": "{x}にはがいとうしません",
                        "en": "It does not fall under {x}",
                        "values": [
                            ("今回の定義", "こんかいのていぎ", "this definition"),
                            ("広義の区分", "こうぎのくぶん", "the broad category"),
                            ("対象範囲", "たいしょうはんい", "the scope covered"),
                        ],
                    },
                    {
                        "text": "{x}によります",
                        "reading": "{x}によります",
                        "en": "It depends on {x}",
                        "values": [
                            ("用例", "ようれい", "the usage"),
                            ("分野", "ぶんや", "the field"),
                            ("解釈", "かいしゃく", "the interpretation"),
                        ],
                    },
                ],
                "notes": [
                    "狭義 / 広義 let you narrow or widen a definition before you commit "
                    "— the standard academic hedge.",
                    "該当する = 'fall under (a category)'. 該当しない excludes a case "
                    "without having to argue about it.",
                ],
            },
            {
                "id": 67,
                "title": "Reading a paper",
                "goal": "Describe a paper's method, its findings, and where it is weak.",
                "vocab": [
                    ("論文", "ろんぶん", "paper / thesis"),
                    ("手法", "しゅほう", "method / approach"),
                    ("妥当性", "だとうせい", "validity"),
                    ("有意差", "ゆういさ", "significant difference"),
                    ("追試", "ついし", "replication study"),
                    ("制約", "せいやく", "constraint"),
                ],
                "dialogue": [
                    ("them", "この論文の手法についてどう評価しますか。",
                     "このろんぶんのしゅほうについてどうひょうかしますか。",
                     "How do you rate the method in this paper?"),
                    ("you", "手順は明快ですが、標本がやや小さいです。",
                     "てじゅんはめいかいですが、ひょうほんがややちいさいです。",
                     "The procedure is clear, but the sample is rather small."),
                    ("them", "結果の妥当性に影響しますか。", "けっかのだとうせいにえいきょうしますか。",
                     "Does that affect the validity of the results?"),
                    ("you", "一部は。有意差は出ていますが、解釈には注意が要ります。",
                     "いちぶは。ゆういさはでていますが、かいしゃくにはちゅういがいります。",
                     "Partly. There is a significant difference, but interpretation needs care."),
                    ("them", "追試の予定はありますか。", "ついしのよていはありますか。",
                     "Is a replication planned?"),
                    ("you", "別の機関で進める予定です。制約は時間です。",
                     "べつのきかんですすめるよていです。せいやくはじかんです。",
                     "Another institution will run it. The constraint is time."),
                    ("them", "まずは検証を待ちましょう。", "まずはけんしょうをまちましょう。",
                     "Then let's wait for the verification."),
                ],
                "patterns": [
                    {
                        "text": "{x}がやや小さいです",
                        "reading": "{x}がややちいさいです",
                        "en": "{x} is rather small",
                        "values": [
                            ("標本", "ひょうほん", "the sample"),
                            ("対象数", "たいしょうすう", "the number of subjects"),
                            ("有効回答数", "ゆうこうかいとうすう", "the number of valid responses"),
                        ],
                    },
                    {
                        "text": "解釈には{x}が要ります",
                        "reading": "かいしゃくには{x}がいります",
                        "en": "Interpretation requires {x}",
                        "values": [
                            ("注意", "ちゅうい", "care"),
                            ("前提の確認", "ぜんていのかくにん", "checking the assumptions"),
                            ("別の視点", "べつのしてん", "another viewpoint"),
                        ],
                    },
                ],
                "notes": [
                    "有意差がある = 'there is a statistically significant difference'. "
                    "It says nothing about how large the effect is.",
                    "追試 (a replication study) is the standard answer to a small "
                    "sample — and the polite way to say a result is not settled.",
                ],
            },
            {
                "id": 68,
                "title": "Giving a presentation",
                "goal": "Structure a talk: frame, findings, limitations, next step.",
                "vocab": [
                    ("発表", "はっぴょう", "presentation"),
                    ("構成", "こうせい", "structure"),
                    ("要点", "ようてん", "the main points"),
                    ("補足", "ほそく", "supplementary detail"),
                    ("質疑", "しつぎ", "questions and answers"),
                    ("結び", "むすび", "closing / conclusion"),
                ],
                "dialogue": [
                    ("them", "発表の構成はどうなっていますか。", "はっぴょうのこうせいはどうなっていますか。",
                     "How is the presentation structured?"),
                    ("you", "三部構成です。背景、要点、今後の課題です。",
                     "さんぶこうせいです。はいけい、ようてん、こんごのかだいです。",
                     "Three parts: background, main points, and issues going forward."),
                    ("them", "補足はどう扱いますか。", "ほそくはどうあつかいますか。",
                     "How will you handle the supplementary detail?"),
                    ("you", "資料に譲ります。十五分あれば足ります。",
                     "しりょうにゆずります。じゅうごふんあればたります。",
                     "I'll leave it to the handout. Fifteen minutes is enough."),
                    ("them", "質疑は長くなりそうですか。", "しつぎはながくなりそうですか。",
                     "Do you expect a long Q&A?"),
                    ("you", "想定問答を用意しています。時間も確保しました。",
                     "そうていもんどうをよういしています。じかんもかくほしました。",
                     "I've prepared for likely questions and set time aside."),
                    ("them", "結びはどう締めますか。", "むすびはどうしめますか。",
                     "How will you close?"),
                ],
                "patterns": [
                    {
                        "text": "{x}部構成です",
                        "reading": "{x}ぶこうせいです",
                        "en": "It is structured in {x} parts",
                        "values": [
                            ("二", "に", "two"),
                            ("三", "さん", "three"),
                            ("四", "よん", "four"),
                        ],
                    },
                    {
                        "text": "補足は{x}に譲ります",
                        "reading": "ほそくは{x}にゆずります",
                        "en": "I'll leave the detail to the {x}",
                        "values": [
                            ("資料", "しりょう", "handout"),
                            ("別紙", "べっし", "separate sheet"),
                            ("質疑", "しつぎ", "Q&A"),
                        ],
                    },
                ],
                "notes": [
                    "結び is the closing section of a talk; むすびの言葉 is what a chair "
                    "says at the end of a conference.",
                    "〜に譲る = 'hand over to' — how you cut material without looking "
                    "unprepared.",
                ],
            },
            {
                "id": 69,
                "title": "Review: conference Q&A",
                "goal": "Field a hostile question, concede what is fair, and park the rest.",
                "vocab": [
                    ("質疑応答", "しつぎおうとう", "question-and-answer session"),
                    ("指摘", "してき", "point / objection raised"),
                    ("反論", "はんろん", "counter-argument"),
                    ("再考", "さいこう", "reconsideration"),
                    ("宿題", "しゅくだい", "unfinished business / action item"),
                    ("精査", "せいさ", "close examination"),
                ],
                "dialogue": [
                    ("them", "一点、指摘させていただいてよろしいですか。",
                     "いってん、してきさせていただいてよろしいですか。",
                     "May I raise one point?"),
                    ("you", "どうぞ。ご指摘はもっともだと思います。",
                     "どうぞ。ごしてきはもっともだとおもいます。",
                     "Please. I think your point is well taken."),
                    ("them", "では、前提条件を再考されますか。", "では、ぜんていじょうけんをさいこうされますか。",
                     "Then will you reconsider your assumptions?"),
                    ("you", "はい、精査した上で報告します。ご指摘には反論しません。",
                     "はい、せいさしたうえでほうこくします。ごしてきにははんろんしません。",
                     "Yes — I'll examine it closely and report back. I won't dispute your point."),
                    ("them", "それを宿題としてお受け取りください。", "それをしゅくだいとしておうけとりください。",
                     "Please take that away as an action item."),
                    ("you", "承知しました。次の機会に必ず触れます。",
                     "しょうちしました。つぎのきかいにかならずふれます。",
                     "Understood. I'll certainly address it next time."),
                ],
                "patterns": [
                    {
                        "text": "ご指摘は{x}です",
                        "reading": "ごしてきは{x}です",
                        "en": "Your point is {x}",
                        "values": [
                            ("もっとも", "もっとも", "well taken"),
                            ("妥当", "だとう", "valid"),
                            ("傾聴に値するもの", "けいちょうにあたいするもの",
                             "worth hearing out"),
                        ],
                    },
                    {
                        # A slot of bare ます-stems would put 行いした上で on the
                        # page (行い + した). Values carry the whole 〜した form so
                        # the frame stays honest for godan and する verbs alike.
                        "text": "{x}上で報告します",
                        "reading": "{x}うえでほうこくします",
                        "en": "I'll report after {x}",
                        "values": [
                            ("精査した", "せいさした", "examining it closely"),
                            ("再確認した", "さいかくにんした", "re-confirming"),
                            ("追加の実験を実施した", "ついかのじっけんをじっしした",
                             "running further experiments"),
                        ],
                    },
                ],
                "notes": [
                    "ご指摘はもっともです concedes a point without conceding the whole "
                    "argument — the standard academic move.",
                    "宿題として受け取る = 'take it away as an action item' — the polite "
                    "way to park a question you cannot answer on the spot.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 17 - Mastery review & expression.  表現の幅, 慣用句, 議論.
    # -----------------------------------------------------------------------
    {
        "id": 17,
        "title": "Mastery Review & Expression",
        "focus": "Range of register, idiom, deepening a debate, and delivering a short formal address.",
        "gate": {"min_pron_score": 88.0, "min_accuracy": 88.0, "min_completeness": 92.0},
        "lessons": [
            {
                "id": 70,
                "title": "Range of register",
                "goal": "Say the same thing at three levels of formality and choose between them.",
                "vocab": [
                    ("表現", "ひょうげん", "expression"),
                    ("改まる", "あらたまる", "to become formal"),
                    ("砕ける", "くだける", "to become casual"),
                    ("語彙", "ごい", "vocabulary"),
                    ("言い回し", "いいまわし", "turn of phrase"),
                    ("場面", "ばめん", "setting / situation"),
                ],
                "dialogue": [
                    ("them", "同じ内容を三つの段階で言ってみてください。",
                     "おなじないようをみっつのだんかいでいってみてください。",
                     "Try saying the same thing at three levels."),
                    ("you", "承知しました。では、まず丁寧な言い回しから。",
                     "しょうちしました。では、まずていねないいまわしから。",
                     "Certainly. First, the polite phrasing."),
                    ("them", "次は砕けた言い方でお願いします。", "つぎはくだけたいいかたでおねがいします。",
                     "Next, the casual version, please."),
                    ("you", "了解です。語彙も少し変わります。", "りょうかいです。ごいもすこしかわります。",
                     "Got it. The vocabulary changes a little too."),
                    ("them", "三つ目は改まった場面を想定します。", "みっつめはあらたまったばめんをそうていします。",
                     "The third assumes a formal setting."),
                    ("you", "では、最上級の敬語で申し上げます。", "では、さいじょうきゅうのけいごでもうしあげます。",
                     "Then I'll use the highest level of honorifics."),
                    ("them", "見事に使い分けられましたね。", "みごとにつかいわけられましたね。",
                     "You separated them beautifully."),
                ],
                "patterns": [
                    {
                        # The frame cannot carry な: 砕けた / 改まった are た-forms,
                        # and 砕けたな言い回し is not Japanese. な belongs to the
                        # value (丁寧な), the way 砕けた belongs to 砕けた alone.
                        "text": "{x}言い回しでお願いします",
                        "reading": "{x}いいまわしでおねがいします",
                        "en": "Please say it in a {x} way",
                        "values": [
                            ("丁寧な", "ていねいな", "polite"),
                            ("砕けた", "くだけた", "casual"),
                            ("改まった", "あらたまった", "formal"),
                        ],
                    },
                    {
                        "text": "場面によって{x}が変わります",
                        "reading": "ばめんによって{x}がかわります",
                        "en": "{x} changes depending on the setting",
                        "values": [
                            ("語彙", "ごい", "the vocabulary"),
                            ("敬語の度合い", "けいごのどあい", "the degree of politeness"),
                            ("声の調子", "こえのちょうし", "the tone of voice"),
                        ],
                    },
                ],
                "notes": [
                    "改まる (become formal) and 砕ける (become casual) are the pair for "
                    "describing register itself — what you need when talking about how "
                    "you are talking.",
                    "丁寧 / 砕けた / 改まった is the working three-level model; most "
                    "learners control only two of them.",
                ],
            },
            {
                "id": 71,
                "title": "Idioms",
                "goal": "Use 慣用句 naturally: 足を運ぶ, 気にかかる, 手を打つ.",
                "vocab": [
                    ("慣用句", "かんようく", "idiomatic phrase"),
                    ("足を運ぶ", "あしをはこぶ", "to make the trip / go in person"),
                    ("気にかかる", "きにかかる", "to weigh on one's mind"),
                    ("手を打つ", "てをうつ", "to take steps / act"),
                    ("拍子抜け", "ひょうしぬけ", "let-down / anticlimax"),
                    ("肩の力を抜く", "かたのちからをぬく", "to ease off / relax"),
                ],
                "dialogue": [
                    ("them", "わざわざ足を運んでいただき、恐縮です。",
                     "わざわざあしをはこんでいただき、きょうしゅくです。",
                     "I'm obliged to you for coming all this way."),
                    ("you", "いえ、気にかかっていたものですから。", "いえ、きにかかっていたものですから。",
                     "Not at all — it was on my mind."),
                    ("them", "結果は期待外れでした。拍子抜けですね。",
                     "けっかはきたいはずれでした。ひょうしぬけですね。",
                     "The result fell short. Something of a let-down."),
                    ("you", "ええ。早めに手を打たなかったのが悔やまれます。",
                     "ええ。はやめにてをうたなかったのがくやまれます。",
                     "Yes. I regret not acting sooner."),
                    ("them", "まだ取り戻せますよ。", "まだとりもどせますよ。",
                     "It can still be recovered."),
                    ("you", "そうですね。肩の力を抜いて考え直します。",
                     "そうですね。かたのちからをぬいてかんがえなおします。",
                     "True. I'll ease off and think it through again."),
                    ("them", "それが一番いいと思います。", "それがいちばんいいとおもいます。",
                     "I think that's the best course."),
                ],
                "patterns": [
                    {
                        "text": "{x}が気にかかっています",
                        "reading": "{x}がきにかかっています",
                        "en": "{x} is weighing on my mind",
                        "values": [
                            ("結果", "けっか", "the result"),
                            ("先方の反応", "せんぽうのはんのう", "how they will react"),
                            ("今後の費用", "こんごのひよう", "future costs"),
                        ],
                    },
                    {
                        # べき takes the dictionary form, so the values are plain
                        # verbs (手を打つ), never ます-stems (手を打ちべき).
                        "text": "早めに{x}べきでした",
                        "reading": "はやめに{x}べきでした",
                        "en": "I should have {x} sooner",
                        "values": [
                            ("手を打つ", "てをうつ", "taken steps"),
                            ("相談する", "そうだんする", "consulted someone"),
                            ("確認する", "かくにんする", "checked"),
                        ],
                    },
                ],
                "notes": [
                    "足を運ぶ = make the trip, and it carries the effort of going: "
                    "わざわざ足を運んでいただき thanks the visitor for coming.",
                    "拍子抜けする describes the FEELING after a build-up; 期待外れ "
                    "describes the event. They are not interchangeable.",
                ],
            },
            {
                "id": 72,
                "title": "Deepening a debate",
                "goal": "Challenge a premise, weigh two options, and argue for synthesis.",
                "vocab": [
                    ("議論", "ぎろん", "debate / discussion"),
                    ("枠組み", "わくぐみ", "framework"),
                    ("前提", "ぜんてい", "premise"),
                    ("天秤", "てんびん", "scales / balance"),
                    ("折衷", "せっちゅう", "splitting the difference"),
                    ("統合", "とうごう", "integration"),
                ],
                "dialogue": [
                    ("them", "議論が同じ枠組みの中で回っていますね。",
                     "ぎろんがおなじわくぐみのなかでまわっていますね。",
                     "The debate is going round inside the same framework."),
                    ("you", "ええ、前提を疑う必要があると思います。",
                     "ええ、ぜんていをうたがうひつようがあるとおもいます。",
                     "Yes — I think we need to question the premise."),
                    ("them", "どの前提でしょうか。", "どのぜんていでしょうか。",
                     "Which premise?"),
                    ("you", "成長が続くという前提です。それ自体が仮説です。",
                     "せいちょうがつづくというぜんていです。それじたいがかせつです。",
                     "That growth will continue. That itself is a hypothesis."),
                    ("them", "二つの案を天秤にかけるべきですか。", "ふたつのあんをてんびんにかけるべきですか。",
                     "Should we weigh the two options against each other?"),
                    ("you", "単純な折衷では弱いです。統合が必要です。",
                     "たんじゅんなせっちゅうではよわいです。とうごうがひつようです。",
                     "A simple compromise would be weak. We need integration."),
                    ("them", "なるほど。土台から組み直すということですね。",
                     "なるほど。どだいからくみなおすということですね。",
                     "I see — rebuild it from the foundations."),
                ],
                "patterns": [
                    {
                        "text": "{x}という前提を疑う必要があります",
                        "reading": "{x}というぜんていをうたがうひつようがあります",
                        "en": "We need to question the premise that {x}",
                        "values": [
                            ("成長が続く", "せいちょうがつづく", "growth will continue"),
                            ("需要がある", "じゅようがある", "there is demand"),
                            ("費用は一定", "ひようはいってい", "costs stay flat"),
                        ],
                    },
                    {
                        "text": "{x}では弱いです",
                        "reading": "{x}ではよわいです",
                        "en": "{x} would be too weak",
                        "values": [
                            ("単純な折衷", "たんじゅんなせっちゅう", "a simple compromise"),
                            ("部分的な修正", "ぶぶんてきなしゅうせい", "a partial fix"),
                            ("一時的な対応", "いちじてきなたいおう", "a stopgap"),
                        ],
                    },
                ],
                "notes": [
                    "天秤にかける = 'put on the scales' — comparing two options on "
                    "merit, not merely listing them.",
                    "折衷 (splitting the difference) and 統合 (combining into something "
                    "new) are the two ways out of a deadlock; serious writing prefers "
                    "the second.",
                ],
            },
            {
                "id": 73,
                "title": "Review: a short address",
                "goal": "Open, argue and close a short formal speech.",
                "vocab": [
                    ("挨拶", "あいさつ", "greeting / formal address"),
                    ("所信", "しょしん", "one's stated position"),
                    ("肝要", "かんよう", "essential / of first importance"),
                    ("微力", "びりょく", "one's modest ability"),
                    ("結び", "むすび", "closing / conclusion"),
                    ("所期", "しょき", "one's original aim"),
                ],
                "dialogue": [
                    ("them", "本日は一言ご挨拶をお願いできますか。",
                     "ほんじつはひとことごあいさつをおねがいできますか。",
                     "Could we ask you for a few words today?"),
                    ("you", "承知しました。所信の一端を述べさせていただきます。",
                     "しょうちしました。しょしんのいったんをのべさせていただきます。",
                     "Certainly. Let me state part of my position."),
                    ("them", "どこに力を入れますか。", "どこにちからをいれますか。",
                     "Where will you put your weight?"),
                    ("you", "人づくりが最も肝要です。所期の目標には時間が要ります。",
                     "ひとづくりがもっともかんようです。しょきのもくひょうにはじかんがいります。",
                     "Developing people matters most. The original goal still needs time."),
                    ("them", "結びに一言お願いします。", "むすびにひとことおねがいします。",
                     "A word in closing, please."),
                    ("you", "微力ながら、全力で務めさせていただきます。",
                     "びりょくながら、ぜんりょくでつとめさせていただきます。",
                     "My abilities are modest, but I will serve to the utmost."),
                ],
                "patterns": [
                    {
                        "text": "{x}が最も肝要だと考えます",
                        "reading": "{x}がもっともかんようだとかんがえます",
                        "en": "I consider {x} to be the most essential",
                        "values": [
                            ("人づくり", "ひとづくり", "developing people"),
                            ("信頼の回復", "しんらいのかいふく", "restoring trust"),
                            ("現場の改善", "げんばのかいぜん", "improving the front line"),
                        ],
                    },
                    {
                        "text": "微力ながら、{x}務めます",
                        "reading": "びりょくながら、{x}つとめます",
                        "en": "Modest though my ability is, I will {x}",
                        "values": [
                            ("全力で", "ぜんりょくで", "serve with all my strength"),
                            ("誠実に", "せいじつに", "serve sincerely"),
                            ("最後まで", "さいごまで", "serve to the end"),
                        ],
                    },
                ],
                "notes": [
                    "微力ながら is the fixed self-deprecation of a Japanese address — "
                    "ritual politeness, not information about your ability.",
                    "結びに = 'in closing': the marker that tells the room the address "
                    "is about to end.",
                ],
            },
        ],
    },
]


LEVEL = {
    "band": 0,
    "id": 6,
    "code": "N1+",
    "title": "JLPT N1+ · Mastery",
    "focus": "Beyond the exam: editorials, academic and professional register, idiom and rhetorical range.",
    "gate": {"min_pron_score": 84.0, "min_accuracy": 84.0, "min_completeness": 90.0},
    "units": UNITS,
}

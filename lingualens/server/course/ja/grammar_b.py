# -*- coding: utf-8 -*-
"""Grammar pages, lessons 37-73 (N3 through N1 and above).

Same contract as `grammar.py` - read that docstring before writing. In
short:

    GRAMMAR[lesson_id] = [
        {"point": "〜てしまう", "en": "finish completely, or regret",
         "formula": "V-て + しまう",
         "examples": [("宿題を忘れてしまいました。", "しゅくだいをわすれてしまいました。",
                       "I went and forgot the homework.")],
         "contrast": "…", "watch": "…"},
    ]

Two to four entries per lesson, two or three examples each, readings in
kana. Only grammar the lesson actually uses. At these bands the `contrast`
field is where most of the value is: 〜なら vs 〜たら, 〜ところを vs
〜ところへ, and the register difference between a written and a spoken
form of the same point.

Verify with:  .venv/bin/python server/course/ja/grammar.py
"""

GRAMMAR: dict = {}

GRAMMAR[37] = [
    {
        "point": "〜たことがあります",
        "en": "have done (at some point in your life)",
        "formula": "V-た + ことがあります",
        "examples": [
            ("海外に行ったことがありますか。", "かいがいにいったことがありますか。",
             "Have you ever been overseas?"),
            ("一人で旅行したことがあります。", "ひとりでりょこうしたことがあります。",
             "I have travelled alone before."),
            ("一度も運転したことがありません。", "いちどもうんてんしたことがありません。",
             "I have never once driven."),
        ],
        "contrast": "This is life experience, not recent history: 「先月京都に"
                    "行ったことがあります」 is wrong, because 先月 already places "
                    "the event - say 行きました. The pattern needs the past tense "
                    "on the verb and the present tense on あります: "
                    "行ったことがあります, never 行ったことがありました.",
        "watch": "It counts an experience, not a habit. 'I often go alone' is "
                 "よく一人で行きます, not 行ったことがあります.",
    },
    {
        "point": "〜たことはあります（が）",
        "en": "I have done it - but only that much",
        "formula": "V-た + ことはあります",
        "examples": [
            ("長距離のバスを運転したことはありますか。",
             "ちょうきょりのバスをうんてんしたことはありますか。",
             "Have you ever driven a long-distance bus?"),
            ("行ったことはありますが、一度だけです。",
             "いったことはありますが、いちどだけです。",
             "I have been, but only once."),
        ],
        "contrast": "が versus を changes what you are conceding. "
                    "行ったことがあります states the experience flatly; "
                    "行ったことはあります concedes it and usually goes on to "
                    "qualify it - 一度だけです、少しだけです. Use は when the "
                    "answer is 'yes, but…'.",
        "watch": "The negative of this one is 行ったことはありません / "
                 "行ったことはないです. が and は are both possible in the "
                 "positive; only は sounds natural in the negative.",
    },
    {
        "point": "一度は〜てみたい",
        "en": "would like to try it at least once",
        "formula": "一度（は） + V-て + みたいです",
        "examples": [
            ("一度は挑戦してみたいです。", "いちどはちょうせんしてみたいです。",
             "I'd like to try it at least once."),
            ("いつか海外で働いてみたいです。", "いつかかいがいではたらいてみたいです。",
             "Someday I'd like to try working overseas."),
        ],
        "contrast": "〜てみる is 'do it and see'; 〜てみたい is wanting that. "
                    "一度は marks the minimum: even one time would do. Without "
                    "は - 一度挑戦してみたい - it reads as a wish; with は it "
                    "reads as 'at the very least, once'.",
    },
]

GRAMMAR[38] = [
    {
        "point": "〜そうです（伝聞）",
        "en": "I heard that; they say that",
        "formula": "plain form + そうです",
        "examples": [
            ("部長が来月から転勤するそうです。",
             "ぶちょうがらいげつからてんきんするそうです。",
             "I hear the manager is being transferred from next month."),
            ("次の部長は東京から来るそうです。",
             "つぎのぶちょうはとうきょうからくるそうです。",
             "They say the next manager comes from Tokyo."),
        ],
        "contrast": "This is NOT the そうです that means 'it looks like'. "
                    "Hearsay そう follows a plain form and never changes: "
                    "転勤するそうです, 転勤したそうです, 忙しいそうです. "
                    "Appearance そう follows a stem and inflects as a na-"
                    "adjective: 忙しそうです, 雨が降りそうです. Plain form plus "
                    "そう can only ever be hearsay.",
        "watch": "It attaches to the plain form, so 転勤しますそうです is wrong "
                 "- strip the ます first.",
    },
    {
        "point": "〜によると / 〜の話では",
        "en": "according to; the source is",
        "formula": "N + によると / N + の話では",
        "examples": [
            ("同僚の話では、来月転勤するそうです。",
             "どうりょうのはなしでは、らいげつてんきんするそうです。",
             "According to my colleague, he transfers next month."),
            ("天気予報によると、午後から雨だそうです。",
             "てんきよほうによると、ごごからあめだそうです。",
             "According to the forecast, rain from the afternoon."),
        ],
        "contrast": "によると points at an institution or a publication "
                    "(天気予報、新聞、調査); の話では points at a person "
                    "(同僚の話では、佐藤さんの話では). Both normally arrive "
                    "with そうです on the end; either can also close with "
                    "〜ということです or 〜らしいです. Naming the source is how "
                    "you stop a piece of news sounding like a rumour.",
        "watch": "によると is written-ish. On the phone or across a desk, "
                 "〜の話では or a plain 〜そうです is more natural.",
    },
    {
        "point": "〜んですね",
        "en": "so the situation is that …",
        "formula": "plain form + んです / んですね",
        "examples": [
            ("今月いっぱいで、いなくなるんですね。",
             "こんげついっぱいで、いなくなるんですね。",
             "So he'll be gone by the end of this month."),
            ("噂じゃないんですね。", "うわさじゃないんですね。",
             "So it isn't a rumour."),
        ],
        "contrast": "そうです hands you someone else's information; んです "
                    "hands them back your understanding of it. After hearing "
                    "the news you confirm with んですね, not そうですね - "
                    "そうですね there would mean 'yes, I heard' rather than "
                    "'so that is how it stands'. んです is also the form that "
                    "asks for an explanation: どうして遅れたんですか.",
        "watch": "Before a noun or na-adjective stem it becomes なんです: "
                 "不便なんですね.",
    },
]

GRAMMAR[39] = [
    {
        "point": "〜ため（に）",
        "en": "because of; owing to (formal, written)",
        "formula": "plain form / N + のため + に",
        "examples": [
            ("電車が遅れたため、遅刻しました。",
             "でんしゃがおくれたため、ちこくしました。",
             "The train was delayed, so I was late."),
            ("事故のために、ほかの人も遅れました。",
             "じこのために、ほかのひともおくれました。",
             "Others were late too because of the accident."),
        ],
        "contrast": "ため（に） and ので both mean 'because', but ため belongs "
                    "to reports and explanations addressed to a superior, "
                    "and it sounds stiff in an apology. 遅刻した理由は、電車の"
                    "ためです is fine; すみません、電車のために遅れました sounds "
                    "like you are filing a report rather than apologising - "
                    "use ので there.",
        "watch": "ため also means 'for the sake of' (家族のために働く). Only the "
                 "context tells you which one you are reading.",
    },
    {
        "point": "〜ので",
        "en": "since; because (soft, spoken)",
        "formula": "plain form / N + な + ので",
        "examples": [
            ("事故があったので、遅れました。", "じこがあったので、おくれました。",
             "There was an accident, so I was late."),
            ("電車が止まったので、歩いて来ました。",
             "でんしゃがとまったので、あるいてきました。",
             "The train stopped, so I came on foot."),
        ],
        "contrast": "から states your reason and pushes it; ので presents it "
                    "as a fact and lets the listener draw the line. That is "
                    "why ので is the one you want for an excuse to a client or "
                    "a manager: 遅くなったので、失礼します. から can sound as "
                    "though you are insisting on your justification.",
        "watch": "Before a noun or na-adjective it is な + ので: 事故なので、"
                 "不便なので.",
    },
    {
        "point": "〜ばよかった",
        "en": "I should have done (and didn't)",
        "formula": "V-ば + よかったです",
        "examples": [
            ("もっと早く報告すればよかったです。",
             "もっとはやくほうこくすればよかったです。",
             "I should have reported it sooner."),
            ("早く出ればよかったです。", "はやくでればよかったです。",
             "I should have left earlier."),
        ],
        "contrast": "〜ばよかった is regret about a past you did not take; "
                    "〜たほうがいい is advice about a future you still have. "
                    "もっと早く報告したほうがよかったです is possible, but it "
                    "sounds like a judgement handed down after the fact, "
                    "whereas すればよかった carries the speaker's own regret.",
        "watch": "〜ばよかったのに adds 'if only'. With い-adjectives and nouns "
                 "it is 安ければよかった, 晴れならよかった.",
    },
]

GRAMMAR[40] = [
    {
        "point": "受身（〜れる / 〜られる）",
        "en": "be done to; something happens to you",
        "formula": "V-ない stem + れる / られる",
        "examples": [
            ("今朝、部長に呼ばれました。", "けさ、ぶちょうによばれました。",
             "The manager called me in this morning."),
            ("遅刻のことで注意されました。", "ちこくのことでちゅういされました。",
             "I was warned about my lateness."),
        ],
        "contrast": "The Japanese passive is not the English passive in "
                    "disguise. 呼ばれました is not a neutral 'I was called' - "
                    "it is 'I was called, and it happened to me'. Japanese "
                    "reaches for the passive especially when the event "
                    "affected the speaker, for better (褒められました) or worse "
                    "(注意されました).",
        "watch": "る-verbs take られる (見る→見られる), う-verbs take れる "
                 "(呼ぶ→呼ばれる), する→される, くる→こられる. The "
                 "る-verb passive and the potential are the same shape - "
                 "context separates them.",
    },
    {
        "point": "受身の「に」と「で」",
        "en": "who did it (に) versus where or what did it (で)",
        "formula": "人 + に + 受身 / 場所・出来事 + で + 受身",
        "examples": [
            ("会議で意見を言ったら、褒められました。",
             "かいぎでいけんをいったら、ほめられました。",
             "When I gave my opinion at the meeting, I was praised."),
            ("上司に認められたので、安心しました。",
             "じょうしにみとめられたので、あんしんしました。",
             "I was relieved that my boss had recognised it."),
        ],
        "contrast": "に marks the person who acted on you: 部長に呼ばれた. "
                    "で marks the place or the occasion it happened in: "
                    "会議で褒められた. With a thing - 電車の事故で遅れた - "
                    "Japanese often prefers の…で over a passive at all.",
        "watch": "に is also the suffering-passive marker: 雨に降られた "
                 "('the rain fell on me'). Context again: 財布を盗まれた has "
                 "no に because the thief is unknown.",
    },
    {
        "point": "〜ということです",
        "en": "that means; the upshot is that",
        "formula": "plain form + ということです",
        "examples": [
            ("上司に認められたということです。",
             "じょうしにみとめられたということです。",
             "It means your boss rates you."),
            ("つまり、遅刻は問題だということですか。",
             "つまり、ちこくはもんだいだということですか。",
             "In other words, the lateness is a problem?"),
        ],
        "contrast": "〜そうです reports what somebody said; 〜ということです "
                    "reports what follows from it. You answer news with "
                    "そうですか and then restate it as a conclusion with "
                    "ということですね. It is also the form for checking: "
                    "賛成できないということですか.",
    },
]

GRAMMAR[41] = [
    {
        "point": "使役（〜せる / 〜させる）",
        "en": "make or let someone do",
        "formula": "V-ない stem + せる / させる",
        "examples": [
            ("後輩にも手伝わせるつもりです。",
             "こうはいにもてつだわせるつもりです。",
             "I plan to have my junior help too."),
            ("お客さんを待たせるのは避けたいです。",
             "おきゃくさんをまたせるのはさけたいです。",
             "I'd rather not keep customers waiting."),
        ],
        "contrast": "The same form covers 'make' and 'let'. 手伝わせる is "
                    "'have them help' (permission or gentle direction); "
                    "待たせる is 'keep them waiting' (cause, usually unwanted). "
                    "Which reading you get depends on the verb: with a "
                    "verb nobody would want done to them, 使役 is coercion.",
        "watch": "Formation: る-verbs take させる (見る→見させる), う-verbs take "
                 "せる (待つ→待たせる, 手伝う→手伝わせる), する→させる, "
                 "くる→こさせる.",
    },
    {
        "point": "〜に〜させる",
        "en": "have a person do it (に marks the doer)",
        "formula": "人 + に + を + V-させる",
        "examples": [
            ("資料は後輩に用意させました。",
             "しりょうはこうはいによういさせました。",
             "I had my junior prepare the materials."),
            ("私にも手伝わせてください。", "わたしにもてつだわせてください。",
             "Please let me help too."),
        ],
        "contrast": "The person made to do it takes に, and the thing they do "
                    "keeps を: 後輩に資料を用意させました. Both as を - 後輩を"
                    "用意させました - is a classic error. When the verb is "
                    "intransitive there is no を to move, so に is the only "
                    "option anyway: 子どもを行かせる.",
        "watch": "〜させていただけますか / 〜させてください is 'let me do it', the "
                 "standard way to volunteer or to ask leave to act.",
    },
    {
        "point": "〜（さ）せられる",
        "en": "be made to do it",
        "formula": "V-（さ）せ + られる",
        "examples": [
            ("昨日は一時間待たされました。",
             "きのうはいちじかんまたされました。",
             "I was kept waiting an hour yesterday."),
            ("残業させられることもあります。",
             "ざんぎょうさせられることもあります。",
             "Sometimes we are made to work overtime."),
        ],
        "contrast": "待たせる is 'keep someone waiting'; 待たされる is 'be kept "
                    "waiting' - the causative-passive puts you back in the "
                    "victim's seat. It is the passive of the causative, and "
                    "it almost always carries unwillingness.",
        "watch": "う-verbs contract: 待たせられる → 待たされる, 行かせられる → "
                 "行かされる. する keeps the full form: させられる.",
    },
]

GRAMMAR[42] = [
    {
        "point": "〜によると、〜そうです",
        "en": "according to X, they say that …",
        "formula": "N + によると、plain form + そうです",
        "examples": [
            ("ニュースによると、経済が少し良くなるそうです。",
             "ニュースによると、けいざいがすこしよくなるそうです。",
             "According to the news, the economy is set to improve a little."),
            ("今朝のニュースによると、人口が減っているそうです。",
             "けさのニュースによると、じんこうがへっているそうです。",
             "According to this morning's news, the population is falling."),
        ],
        "contrast": "The source marker and the hearsay marker do different "
                    "jobs, and you can drop either: ニュースによると、景気は"
                    "回復する (source, stated as fact) or 景気は回復するそうです "
                    "(hearsay, source unstated). Together they are the "
                    "safest form - you neither invented it nor vouched for "
                    "it.",
        "watch": "によると must be followed by something that is reported, not "
                 "by your own opinion: ニュースによると、私はそう思います is "
                 "nonsense.",
    },
    {
        "point": "〜一方だ",
        "en": "keeps going one way only",
        "formula": "V-る + 一方だ",
        "examples": [
            ("人口は減る一方です。", "じんこうはへるいっぽうです。",
             "The population just keeps falling."),
            ("物価は上がる一方ですね。", "ぶっかはあがるいっぽうですね。",
             "Prices only ever go up."),
        ],
        "contrast": "〜一方だ is a trend with a complaint in it: one direction, "
                    "no sign of turning. Compare 〜つつある (gradually, neutral, "
                    "written) and 〜ばかりだ (nothing but, more colloquial and "
                    "more emotional). Use 一方 for a statistic you find "
                    "worrying.",
        "watch": "Dictionary form only: 減った一方だ is wrong. A separate "
                 "pattern, 〜一方（で）, means 'while on the other hand' - "
                 "収入は増える一方で、支出も増える.",
    },
    {
        "point": "〜と思っていました",
        "en": "I had thought (and now I know better)",
        "formula": "plain form + と思っていました",
        "examples": [
            ("人口は減る一方だと思っていました。",
             "じんこうはへるいっぽうだとおもっていました。",
             "I had thought the population only ever fell."),
            ("経済は良くなると思っていました。",
             "けいざいはよくなるとおもっていました。",
             "I had thought the economy would improve."),
        ],
        "contrast": "思っています is what you think now; 思っていました is what "
                    "you thought until just now, and it is the polite way to "
                    "be corrected. Stating the old wrong belief rather than "
                    "ただの「知りませんでした」 gives the other person something "
                    "to answer.",
        "watch": "With 私は attached, 思っていました stays as it is - this is a "
                 "reported thought, not a humble form.",
    },
]

GRAMMAR[43] = [
    {
        "point": "〜に違いない",
        "en": "it must be; I am certain",
        "formula": "plain form / N + に違いない",
        "examples": [
            ("社内にいた人に違いないです。", "しゃないにいたひとにちがいないです。",
             "It must be someone who was in the office."),
            ("鍵を持っていた人に違いありません。",
             "かぎをもっていたひとにちがいありません。",
             "It must be someone who had a key."),
        ],
        "contrast": "Three levels of commitment, and picking the wrong one is "
                    "what makes a learner sound reckless. 〜に違いない is "
                    "near-certainty from inference - the speaker has no proof "
                    "but no doubt either. 〜はずだ is expectation from what you "
                    "know. 〜と思います is a hedge you can retreat from. In a "
                    "report, only the last two are safe.",
        "watch": "It follows the plain form, so いたに違いない (a person who "
                 "was), not いた人だったに違いない. As a sentence ending it is "
                 "usually に違いない / に違いありません; に違いないです is common in "
                 "speech.",
    },
    {
        "point": "〜はずです",
        "en": "it should be; given what I know, it ought to be",
        "formula": "plain form / N + の + はずです",
        "examples": [
            ("それを見れば分かるはずです。", "それをみればわかるはずです。",
             "Looking at it should tell us."),
            ("記録が残っているはずです。", "きろくがのこっているはずです。",
             "The record should still be there."),
        ],
        "contrast": "はず is expectation, not certainty: it can be let down. "
                    "「彼は来るはずです」 means the arrangement says he comes; "
                    "「彼は来るに違いない」 means I would stake something on it. "
                    "はずがありません / はずがない denies the expectation: "
                    "彼がやったはずがない.",
        "watch": "Before a noun it needs の: 彼のもののはずです. With na-adjectives, "
                 "な: 必要なはずです. After 〜た it means 'I was sure it had "
                 "happened': 確かに鍵をかけたはずです.",
    },
    {
        "point": "〜と思います（判断を弱める）",
        "en": "I think - hedging a conclusion",
        "formula": "plain form + と思います / とは思いません",
        "examples": [
            ("逃げる人はいなかったと思います。",
             "にげるひとはいなかったとおもいます。",
             "I don't think anyone ran off."),
            ("社内の人だとは思いません。", "しゃないのひとだとはおもいません。",
             "I don't think it was anyone from inside the company."),
        ],
        "contrast": "Japanese puts the negation in the main clause, not the "
                    "subordinate one: 'I don't think anyone ran' is "
                    "逃げる人はいなかったと思います, never 逃げる人はいなかったと"
                    "思いません. Under a police-style question this is the "
                    "level to pick - はずです would sound like you are "
                    "vouching for it.",
        "watch": "For 'I don't think X' the adverb と is what takes the "
                 "negation: 〜とは思いません sounds firmer than 〜と思います.",
    },
]

GRAMMAR[44] = [
    {
        "point": "〜わけではない",
        "en": "it is not that …; that is not the reason",
        "formula": "plain form + わけではない",
        "examples": [
            ("反対しているわけではないんです。",
             "はんたいしているわけではないんです。",
             "No, it's not that I'm against it."),
            ("全部を直したいわけではありません。",
             "ぜんぶをなおしたいわけではありません。",
             "It's not that I want to revise all of it."),
        ],
        "contrast": "〜わけではない denies a conclusion somebody has just "
                    "drawn or is about to draw; 〜ない simply denies a fact. "
                    "「反対していません」 answers 'are you against it?'. "
                    "「反対しているわけではありません」 answers 'so you're against "
                    "it?' - it corrects the reading, and it usually goes on "
                    "to qualify.",
        "watch": "〜わけではありません is the same thing one register up. "
                 "〜ないわけでもない is the double negative: 'it's not that I'm "
                 "not…', i.e. partly yes.",
    },
    {
        "point": "〜というほどではない",
        "en": "not to that extent; not all that …",
        "formula": "plain form + というほどではない",
        "examples": [
            ("難しいというほどではありません。",
             "むずかしいというほどではありません。",
             "It's not all that difficult."),
            ("高いというほどではないですが、安くもありません。",
             "たかいというほどではないですが、やすくもありません。",
             "Not that it's expensive - but it isn't cheap either."),
        ],
        "contrast": "〜わけではない says 'that conclusion is wrong'; "
                    "〜というほどではない says 'that conclusion is too strong'. "
                    "A colleague calls the plan 難しい; 難しいわけではない "
                    "contradicts them, 難しいというほどではない concedes the "
                    "difficulty and trims it. In a Japanese meeting the "
                    "second is almost always the better move.",
        "watch": "It attaches to the plain form including い-adjectives and "
                 "nouns: 問題というほどではない.",
    },
    {
        "point": "〜ではなく",
        "en": "not X but Y",
        "formula": "N + ではなく（、…）",
        "examples": [
            ("全部ではなく、一部でいいと思います。",
             "ぜんぶではなく、いちぶでいいとおもいます。",
             "Not all of it - I think a part would do."),
            ("今日ではなく、明日でいいですか。",
             "きょうではなく、あしたでいいですか。",
             "Not today - is tomorrow all right?"),
        ],
        "contrast": "〜ではなく rejects one candidate and substitutes another; "
                    "〜じゃなくて is the spoken version and is the one you want "
                    "in conversation. ではなく is the written form and sounds "
                    "deliberate - it sets up a contrast the rest of the "
                    "sentence will resolve.",
        "watch": "It can take a whole clause: 直すのではなく、作り直すほうがいい.",
    },
]

GRAMMAR[45] = [
    {
        "point": "〜おかげで",
        "en": "thanks to (a good result)",
        "formula": "plain form / N + の + おかげで",
        "examples": [
            ("準備をしたおかげで、失敗しませんでした。",
             "じゅんびをしたおかげで、しっぱいしませんでした。",
             "Thanks to preparing, I didn't mess it up."),
            ("教えてもらったおかげで、分かりました。",
             "おしえてもらったおかげで、わかりました。",
             "Thanks to being shown, I understood."),
        ],
        "contrast": "おかげで is credit, and it points at something worth "
                    "thanking - someone's help, your own preparation, good "
                    "luck. せいで is blame. Using おかげで for a bad outcome "
                    "makes it sarcasm: 君のおかげで遅れた ('thanks to you, "
                    "we're late').",
        "watch": "おかげさまで is the fixed greeting-answer ('fine, thanks to "
                 "you'), not a causal clause. Before a noun it needs の: "
                 "先生のおかげで.",
    },
    {
        "point": "〜せいで",
        "en": "because of (a bad result, with blame in it)",
        "formula": "plain form / N + の + せいで",
        "examples": [
            ("油断したせいで、失敗しました。", "ゆだんしたせいで、しっぱいしました。",
             "I failed through letting my guard down."),
            ("電車のせいで、遅れました。", "でんしゃのせいで、おくれました。",
             "I was late because of the train."),
        ],
        "contrast": "せいで assigns fault; ため（に） states a cause neutrally and "
                    "belongs to reports. In front of a client, 電車のせいで遅れ"
                    "ました sounds like you are blaming the railway for you - "
                    "電車が遅れたため、遅刻いたしました is the professional "
                    "version. せい is for private conversation or for your own "
                    "fault.",
        "watch": "It is also how you deflect a worry: 気のせいです ('it's your "
                 "imagination').",
    },
    {
        "point": "〜せいか",
        "en": "maybe it was because of …",
        "formula": "plain form / N + の + せいか",
        "examples": [
            ("睡眠が足りなかったせいか、声が小さかったです。",
             "すいみんがたりなかったせいか、こえがちいさかったです。",
             "Maybe because I hadn't slept enough, my voice was quiet."),
            ("緊張のせいか、手が震えました。", "きんちょうのせいか、てがふるえました。",
             "Perhaps from nerves, my hands shook."),
        ],
        "contrast": "The か turns blame into a guess, and that is the whole "
                    "point: せいで accuses, せいか wonders. It lets you offer a "
                    "cause for something unflattering - your own quiet voice, "
                    "your own mistake - without committing to it. You can "
                    "hear the same softening in 〜のか and 〜ためか.",
        "watch": "It still only goes with undesirable results. For a good one, "
                 "reach for おかげか or just からか.",
    },
]

GRAMMAR[46] = [
    {
        "point": "〜なら",
        "en": "if it is the case that; given that",
        "formula": "plain form / N + なら",
        "examples": [
            ("雨なら、遠足は中止しましょう。", "あめなら、えんそくはちゅうししましょう。",
             "If it's rain, let's call off the outing."),
            ("行くなら、早いほうがいいです。", "いくなら、はやいほうがいいです。",
             "If you're going, sooner is better."),
        ],
        "contrast": "なら takes a condition that has already been raised and "
                    "responds to it: 'if that's how it stands'. たら takes an "
                    "event and follows it in time: 'once that happens'. So "
                    "雨なら中止します decides on the forecast, while "
                    "雨が降ったら中止します waits for the rain. Because なら can "
                    "precede its own condition, it is the natural form for "
                    "advice: 行くなら早いほうがいい.",
        "watch": "After a noun or na-adjective stem it attaches directly - "
                 "雨なら, 必要なら - with no だ and no な.",
    },
    {
        "point": "〜たら",
        "en": "once X happens; when X has happened",
        "formula": "V-た + ら",
        "examples": [
            ("晴れたら、予定通り出発します。",
             "はれたら、よていどおりしゅっぱつします。",
             "If it clears up, we'll leave as planned."),
            ("間に合わなかったら、連絡してください。",
             "まにあわなかったら、れんらくしてください。",
             "If you're not going to make it, get in touch."),
        ],
        "contrast": "たら is the all-purpose conditional and the only one of "
                    "the three that is comfortable with a clause that just "
                    "happens once: 家に帰ったら、電話します. ば is more formal and "
                    "more hypothetical, and it cannot take a one-off future "
                    "action in the main clause - 帰れば電話します is stiff. なら "
                    "cannot take a past-and-then reading at all.",
        "watch": "Before a noun or na-adjective it is だったら / なら: "
                 "雨だったら, 不便だったら.",
    },
    {
        "point": "〜ば",
        "en": "if; provided that (formal, hypothetical)",
        "formula": "V-ば form (V-え + ば)",
        "examples": [
            ("傘を持って行けば、心配はいりません。",
             "かさをもっていけば、しんぱいはいりません。",
             "If we take umbrellas, there's nothing to worry about."),
            ("早く出発すれば、道が空いています。",
             "はやくしゅっぱつすれば、みちがあいています。",
             "If we set off early, the roads are empty."),
        ],
        "contrast": "ば presents a general condition and its general "
                    "consequence - 'if you do X, then as a rule Y'. That is "
                    "why it is the form for rules, instructions and "
                    "assurances, and why 〜ばいい / 〜ばよかった are advice and "
                    "regret. It dislikes a main clause that is a one-time "
                    "volitional act: 晴れれば出発しましょう is unnatural, where "
                    "晴れたら出発しましょう is fine.",
        "watch": "い-adjectives: 安ければ. Nouns and na-adjectives: 雨なら／"
                 "雨であれば, 便利なら／便利であれば, and the であれば version is "
                 "written.",
    },
]

GRAMMAR[47] = [
    {
        "point": "〜ても",
        "en": "even if; even though",
        "formula": "V-て + も",
        "examples": [
            ("修理しても、値段は安いです。", "しゅうりしても、ねだんはやすいです。",
             "Even with the repair, it's cheap."),
            ("壊れても、すぐ直ると思います。", "こわれても、すぐなおるとおもいます。",
             "Even if it breaks, I think it can be fixed quickly."),
        ],
        "contrast": "ても is the concession that works in speech: one て-form "
                    "and one も, and it can concede a fact (高くても買う - it IS "
                    "expensive) or a hypothesis (壊れても - if it WERE to "
                    "break). のに is the same contrast plus disappointment: "
                    "高いのに売れている carries surprise; 高くても売れている does "
                    "not.",
        "watch": "After a noun or na-adjective it is でも: 不便でも、古いでも. "
                 "いくら〜ても is the emphatic version: 'no matter how much'.",
    },
    {
        "point": "〜にもかかわらず",
        "en": "despite; notwithstanding",
        "formula": "plain form / N + にもかかわらず",
        "examples": [
            ("古いにもかかわらず、人気があるんです。",
             "ふるいにもかかわらず、にんきがあるんです。",
             "Despite being old, it's popular."),
            ("値段が高いにもかかわらず、よく売れています。",
             "ねだんがたかいにもかかわらず、よくうれています。",
             "Despite the high price, it sells well."),
        ],
        "contrast": "Same meaning as 〜のに, one register apart. のに is "
                    "everyday and carries the speaker's feeling; にもかかわらず "
                    "is written, neutral and slightly cold, and it belongs in "
                    "reports: 雨天にもかかわらず、多数の参加者があった. Saying it "
                    "out loud in a shop sounds like a product review.",
        "watch": "It attaches to the plain form, so nouns and na-adjectives "
                 "appear bare: 古いにもかかわらず, 不便にもかかわらず - with no な "
                 "and no だ.",
    },
    {
        "point": "〜まで",
        "en": "until; as far as",
        "formula": "V-る + まで",
        "examples": [
            ("納得いくまで、ほかのも見てください。",
             "なっとくいくまで、ほかのもみてください。",
             "Look at the others too, until you're satisfied."),
            ("決心がつくまで、待ちます。", "けっしんがつくまで、まちます。",
             "I'll wait until you've made up your mind."),
        ],
        "contrast": "まで is 'up to and including that point'; までに is 'by "
                    "then, at some point before it'. 金曜まで待ちます is waiting "
                    "through Friday; 金曜までに連絡します is calling sometime "
                    "before Friday. Confusing them is one of the commonest "
                    "mistakes with deadlines.",
        "watch": "After a noun it marks the endpoint directly: 駅まで歩く. With "
                 "a continuing verb: 決心がつくまで待つ.",
    },
]

GRAMMAR[48] = [
    {
        "point": "〜予定です",
        "en": "it is scheduled to; the plan is to",
        "formula": "V-る + 予定です",
        "examples": [
            ("来週の水曜日に完成する予定です。",
             "らいしゅうのすいようびにかんせいするよていです。",
             "It's scheduled for next Wednesday."),
            ("今週中に終わらせる予定です。",
             "こんしゅうちゅうにおわらせるよていです。",
             "I plan to get it finished within this week."),
        ],
        "contrast": "予定 is a plan - yours, or the schedule's - and it can "
                    "slip without anybody being at fault. ことになっています is a "
                    "decision already made, usually by someone above you, and "
                    "breaking it is a problem. If the deadline moves, say "
                    "予定が遅れています; the decision frame would have to be "
                    "re-made, not merely revised.",
        "watch": "Dictionary form plus 予定です, and the negative is しない予定"
                 "です. する予定でした means the plan has been changed.",
    },
    {
        "point": "〜ことになっています",
        "en": "it has been decided that; it is arranged that",
        "formula": "V-る / V-ない + ことになっています",
        "examples": [
            ("人員を増やすことになっています。",
             "じんいんをふやすことになっています。",
             "It has been decided to add more people."),
            ("来月から新しい制度が始まることになっています。",
             "らいげつからあたらしいせいどがはじまることになっています。",
             "The new system is to start next month."),
        ],
        "contrast": "ことになっています is the settled arrangement - a rule, a "
                    "rota, a decision taken elsewhere. ことにしています is your "
                    "own standing practice ('I make a point of …'). One "
                    "letter apart and completely different: 毎日メールを確認する"
                    "ことにしています is a habit, not a policy.",
        "watch": "The 'it was arranged but did not happen' form is ことになって"
                 "いました.",
    },
    {
        "point": "〜てしまう",
        "en": "finish completely, or do it regrettably",
        "formula": "V-て + しまう",
        "examples": [
            ("少し遅れてしまいました。", "すこしおくれてしまいました。",
             "It has slipped a little."),
            ("締め切りを忘れてしまいました。", "しめきりをわすれてしまいました。",
             "I went and forgot the deadline."),
        ],
        "contrast": "〜てしまう marks a result you cannot undo; the regret is "
                    "in the situation, not in the grammar, so 早く終わってしまい"
                    "ました can be relief. Compare 〜ておく, which is doing it in "
                    "advance on purpose. Both past and present occur: 忘れて"
                    "しまう (it happens, and that's that).",
        "watch": "In speech it collapses: 忘れちゃった、やってしまった→やっちゃった, "
                 "and in casual Kansai-ish speech 〜てまう. Do not write these.",
    },
]

GRAMMAR[49] = [
    {
        "point": "〜ため（に）",
        "en": "because of; owing to (formal cause)",
        "formula": "plain form / N + の + ため（に）",
        "examples": [
            ("部品が足りないため、遅れています。",
             "ぶひんがたりないため、おくれています。",
             "We're short of parts, so it's behind schedule."),
            ("事故のために、納品が遅れました。",
             "じこのために、のうひんがおくれました。",
             "Delivery was delayed because of the accident."),
        ],
        "contrast": "ため（に） is the written register of ので: it states a "
                    "cause without the speaker's feelings in it, which is "
                    "exactly what a status report needs. Put ので in the same "
                    "sentence and it becomes an excuse. Put から in it and it "
                    "becomes an argument.",
        "watch": "ため after a plain clause carries no の: 足りないため. After a "
                 "noun it does: 事故のために.",
    },
    {
        "point": "〜ないように",
        "en": "so that … does not happen",
        "formula": "V-ない + ように",
        "examples": [
            ("そうならないように、今日中に回答します。",
             "そうならないように、こんじゅうにかいとうします。",
             "So that doesn't happen, I'll reply within today."),
            ("遅れないように、早めに出発します。",
             "おくれないように、はやめにしゅっぱつします。",
             "I'll set off early so as not to be late."),
        ],
        "contrast": "ように on a potential or negative verb is purpose; ように "
                    "on a plain verb of state is 'in the manner of'. "
                    "遅れないように（する）is so as not to be late; 彼が言ったように"
                    "（する）is as he said. ために also expresses purpose but "
                    "only with a verb of intention - 間に合うために早く出る - and "
                    "it never pairs with a negative.",
        "watch": "ようにします is 'make a point of doing'; ようになります is 'come "
                 "to do, become the case that'.",
    },
    {
        "point": "〜てもらう",
        "en": "have someone do it (for you)",
        "formula": "人 + に + V-て + もらう",
        "examples": [
            ("承諾してもらえますか。", "しょうだくしてもらえますか。",
             "Will they agree to it?"),
            ("部長に確認してもらいました。", "ぶちょうにかくにんしてもらいました。",
             "I had the manager check it."),
        ],
        "contrast": "てもらう is receiving the action (you benefit); てくれる is "
                    "the same event seen from the doer's side (they obliged "
                    "you); てあげる is you doing it for them, and it can sound "
                    "condescending to a superior. In a business report, "
                    "てもらう / ていただく is the safe one because it leaves the "
                    "credit with them.",
        "watch": "The potential てもらえますか is the standard soft request, "
                 "softer than てください. Humble form: ていただく.",
    },
]

GRAMMAR[50] = [
    {
        "point": "〜と申します",
        "en": "my name is (humble)",
        "formula": "N + と申します",
        "examples": [
            ("営業部の鈴木と申します。", "えいぎょうぶのすずきともうします。",
             "I'm Suzuki, from Sales."),
            ("私は山田と申します。", "わたしはやまだともうします。",
             "My name is Yamada."),
        ],
        "contrast": "申します is the humble form of 言います, so it lowers the "
                    "speaker - which is why it can only ever introduce YOU. "
                    "For someone else's name you need the respectful side: "
                    "鈴木とおっしゃいます, or simply 鈴木さんです. Saying 私の名前は"
                    "鈴木です to a client is not wrong, just unmarked - it "
                    "makes no move at all.",
        "watch": "The self-introduction is a package: 〜と申します。どうぞよろしく"
                 "お願いいたします。 Dropping the second half is what makes an "
                 "otherwise correct introduction sound brusque.",
    },
    {
        "point": "〜ております",
        "en": "I am doing (humble progressive)",
        "formula": "V-て + おります",
        "examples": [
            ("海外のお客様との契約を担当しております。",
             "かいがいのおきゃくさまとのけいやくをたんとうしております。",
             "I handle contracts with our overseas clients."),
            ("前職では同じ仕事をしておりました。",
             "ぜんしょくではおなじしごとをしておりました。",
             "In my previous post I did much the same work."),
        ],
        "contrast": "おります is the humble います - again, only about "
                    "yourself or your own company. For the other side you "
                    "need いらっしゃいます or おられます: 部長は会議に出席されて"
                    "おります is fine because the れる raises him back up; "
                    "部長は会議におります is not. With a thing as the subject, "
                    "plain あります is already polite enough - 資料はこちらに"
                    "ございます.",
        "watch": "おります also covers a state that began in the past and "
                 "continues: 三年ほど担当しております.",
    },
    {
        "point": "お／ご〜いたします",
        "en": "I do (humble verbal noun)",
        "formula": "お + V-ます stem / ご + sino-noun + いたします",
        "examples": [
            ("部の皆さんにご紹介いたします。", "ぶのみなさんにごしょうかいいたします。",
             "Let me introduce you to the department."),
            ("よろしくお願いいたします。", "よろしくおねがいいたします。",
             "I look forward to working with you."),
        ],
        "contrast": "The prefix marks whose action it is, not how polite it "
                    "is: ご連絡いたします is MY contacting you; ご連絡くださいます "
                    "is YOUR contacting me. The お-form takes a Japanese verb "
                    "stem (お待ちいたします), the ご-form a Chinese-derived noun "
                    "(ご案内いたします). Mixing them - お案内、ご待ち - sounds "
                    "immediately foreign.",
        "watch": "いたします is the humble します. Not every verb can take a "
                 "prefix; します itself must become いたします, never おしします.",
    },
]

GRAMMAR[51] = [
    {
        "point": "〜いただけますでしょうか",
        "en": "could I ask you to … (the safe business request)",
        "formula": "お + V-ます stem / ご + noun + いただけますでしょうか",
        "examples": [
            ("恐れ入りますが、至急ご確認いただけますでしょうか。",
             "おそれいりますが、しきゅうごかくにんいただけますでしょうか。",
             "Sorry to press you, but could you check this urgently?"),
            ("資料の送付をお願いしたいのですが。",
             "しりょうのそうふをおねがいしたいのですが。",
             "And I'd like to ask for the materials to be sent as well."),
        ],
        "contrast": "Sorted bluntest to softest: 〜てください (instruction, not "
                    "for a client), 〜ていただけますか (request), 〜ていただけます"
                    "でしょうか (request with distance), 〜ていただければ幸いです "
                    "(request as a favour), 〜お願いしたいのですが (wish, left "
                    "hanging so the other person can refuse). The longer the "
                    "form, the easier it is to say no to - which is the "
                    "point.",
        "watch": "いただけます is the potential of いただく, so it reads as 'can I "
                 "receive?', not 'please do'. いただけませんか also works; "
                 "いただけないでしょうか is the most tentative of the set.",
    },
    {
        "point": "承知いたしました / かしこまりました",
        "en": "certainly; understood",
        "formula": "fixed response forms",
        "examples": [
            ("承知いたしました。直ちに確認いたします。",
             "しょうちいたしました。ただちにかくにんいたします。",
             "Understood. I'll look into it immediately."),
            ("かしこまりました。終わり次第、連絡いたします。",
             "かしこまりました。おわりしだい、れんらくいたします。",
             "Certainly. I'll be in touch the moment it's finished."),
        ],
        "contrast": "Both mean yes. 承知いたしました is the neutral one for a "
                    "colleague or your own boss; かしこまりました is what you say "
                    "to a customer, and it carries 'at your service'. 分かり"
                    "ました is too plain for a client and 了解です too casual for "
                    "anyone senior - both are common inside a team.",
        "watch": "承知しました (without いたし) is one step down and fine between "
                 "equals. The past tense is fixed: you acknowledge what you "
                 "have just been told, so 承知しています would be odd.",
    },
    {
        "point": "〜次第",
        "en": "the moment X happens, I will …",
        "formula": "V-ます stem / noun + 次第",
        "examples": [
            ("終わり次第、連絡いたします。", "おわりしだい、れんらくいたします。",
             "I'll be in touch as soon as it's finished."),
            ("確認ができ次第、お送りします。", "かくにんができしだい、おおくりします。",
             "I'll send it the moment confirmation is in place."),
        ],
        "contrast": "次第 and 〜たら both mean 'when', but 次第 promises the "
                    "response is immediate and unconditional - it is a service "
                    "word. Compare 終わったら連絡します (I'll call when it's done, "
                    "some time after) with 終わり次第連絡いたします (the finishing "
                    "and the call are the same moment). Use it only for your "
                    "own next action, never as an instruction to the client.",
        "watch": "It takes the ます stem: 終わり次第, でき次第, 到着次第. The "
                 "following clause is always something the speaker does.",
    },
]

GRAMMAR[52] = [
    {
        "point": "あいにく",
        "en": "unfortunately (the softening before a refusal)",
        "formula": "あいにく + reason + まして / でして",
        "examples": [
            ("せっかくですが、あいにく先約がありまして。",
             "せっかくですが、あいにくせんやくがありまして。",
             "That is kind of you, but sadly I have a prior engagement."),
            ("あいにく本日は都合がつきません。",
             "あいにくほんじつはつごうがつきません。",
             "Unfortunately I can't manage today."),
        ],
        "contrast": "A Japanese refusal is built out of three moves in order: "
                    "thanks for the offer (せっかくですが / ありがたいのですが), "
                    "the softening adverb (あいにく), and a reason that is not "
                    "your preference (先約がありまして). The reason is what does "
                    "the refusing - never 'I don't want to'.",
        "watch": "あいにく belongs to bad news generally, not only to refusals: "
                 "あいにく売り切れです. It never takes a です after it.",
    },
    {
        "point": "〜（さ）せていただければと存じます",
        "en": "I would be grateful if I might be allowed to …",
        "formula": "V-（さ）せて + いただければ + と存じます",
        "examples": [
            ("今回だけは見送らせていただければと存じます。",
             "こんかいだけはみおくらせていただければとぞんじます。",
             "This once, I would be grateful to be allowed to pass."),
            ("一度検討させていただければと存じます。",
             "いちどけんとうさせていただければとぞんじます。",
             "I'd be grateful if I might examine it once."),
        ],
        "contrast": "This is a request wearing the shape of a wish: the "
                    "decision is handed back to the other person, and the "
                    "sentence ends without ever asking a question. Compare "
                    "the plain 見送ります (a decision, taken), 見送りたいです (a "
                    "wish, stated), and this (a wish, left for them to grant). "
                    "It is the most deferential way to say no in the language.",
        "watch": "存じます is the humble 思います. 〜と存じます after a plain clause "
                 "also just means 'I think', one register up: よろしいかと存じ"
                 "ます.",
    },
    {
        "point": "〜でしたら / 改めて",
        "en": "if it were that; on another occasion",
        "formula": "N + でしたら / 改めて + alternative",
        "examples": [
            ("来週でしたら、木曜の午後なら伺えます。",
             "らいしゅうでしたら、もくようのごごならうかがえます。",
             "Next week I could call on you on Thursday afternoon."),
            ("改めて来週はいかがでしょうか。", "あらためてらいしゅうはいかがでしょうか。",
             "Might I suggest next week instead?"),
        ],
        "contrast": "でしたら is なら with です attached - softer, and the form "
                    "you want when the condition is a suggestion rather than a "
                    "fact. The pair that makes a refusal work is refusal + "
                    "alternative: 今回は…、改めて来週は. Offering only the refusal "
                    "reads as closing the door; offering only the alternative "
                    "reads as ignoring the invitation.",
        "watch": "改めて means 'afresh, on a new occasion', not 'again' - for "
                 "that use もう一度.",
    },
]

GRAMMAR[53] = [
    {
        "point": "〜でございます",
        "en": "it is (polite copula)",
        "formula": "N + でございます",
        "examples": [
            ("お電話ありがとうございます。山川商事でございます。",
             "おでんわありがとうございます。やまかわしょうじでございます。",
             "Thank you for calling. Yamakawa Trading."),
            ("確認の件でございます。", "かくにんのけんでございます。",
             "It's about the confirmation."),
        ],
        "contrast": "ございます is the polite あります / です, and it is the "
                    "phone voice: a company names itself with でございます, never "
                    "です. For a thing that exists, ございます alone; for a "
                    "thing that is, でございます. On top of that, adding お to a "
                    "noun (お電話、お客様) is the same politeness showing up in a "
                    "different place.",
        "watch": "ございません is the negative, and ございます keeps its い→あ "
                 "shift in the polite negative: ございませんでした. There is no "
                 "*ございない.",
    },
    {
        "point": "恐れ入りますが、〜できますでしょうか",
        "en": "sorry to trouble you, but could I …?",
        "formula": "恐れ入りますが、+ request",
        "examples": [
            ("恐れ入りますが、担当者をお願いできますか。",
             "おそれいりますが、たんとうしゃをおねがいできますか。",
             "Sorry to trouble you, but could I speak to the person in charge?"),
            ("恐れ入りますが、もう一度おっしゃっていただけますか。",
             "おそれいりますが、もういちどおっしゃっていただけますか。",
             "Sorry to trouble you, but could you say that again?"),
        ],
        "contrast": "恐れ入りますが is the preface, not the request - it buys "
                    "goodwill before you ask for anything at all, including "
                    "things that cost the other person nothing. すみませんが is "
                    "the everyday equivalent and too light for a first "
                    "contact; 申し訳ありません is apology, not preface.",
        "watch": "It is also how you give unwelcome news: 恐れ入りますが、担当者は"
                 "ただ今席を外しております.",
    },
    {
        "point": "折り返し",
        "en": "the callback; by return",
        "formula": "折り返し + 連絡する / お願いする",
        "examples": [
            ("折り返しお願いできますでしょうか。",
             "おりかえしおねがいできますでしょうか。",
             "Might I ask him to call me back?"),
            ("佐藤から折り返し連絡いたします。",
             "さとうからおりかえしれんらくいたします。",
             "Sato will be back in touch with you."),
        ],
        "contrast": "折り返し is the noun for the return call itself, so it "
                    "replaces a whole clause: 折り返しお願いします is 'ring me "
                    "back', and 折り返し連絡いたします is 'we will ring you back'. "
                    "The receiver says かけ直します; the caller asks for 折り返し.",
        "watch": "It is telephone vocabulary only - in email you would write "
                 "追ってご連絡いたします.",
    },
]

GRAMMAR[54] = [
    {
        "point": "〜とは",
        "en": "as for X; what is called X (the word being defined)",
        "formula": "N + とは",
        "examples": [
            ("自由とは何だとお考えですか。", "じゆうとはなんだとおかんがえですか。",
             "What do you take freedom to be?"),
            ("余白とは、何のことでしょうか。", "よはくとは、なんのことでしょうか。",
             "What do you mean by slack?"),
        ],
        "contrast": "とは marks the term and usually prepares a definition, "
                    "so it normally arrives with 〜ということだ on the other end. "
                    "は alone would just mark a topic: 自由は大切です is a "
                    "statement about freedom; 自由とは何か is a question about "
                    "the word. というのは is the spoken equivalent.",
        "watch": "With a verb or clause before it, 〜とは also means 'the act "
                 "of' and often carries surprise: 辞めるとは思わなかった.",
    },
    {
        "point": "〜ということだ",
        "en": "it means that; the point is that",
        "formula": "plain form + ということだ",
        "examples": [
            ("選べる範囲がどこまで広いかということだと思います。",
             "えらべるはんいがどこまでひろいかということだとおもいます。",
             "I think it is a question of how wide the real choices are."),
            ("余白は無駄ではないということです。",
             "よはくはむだではないということです。",
             "It means slack is not waste."),
        ],
        "contrast": "This is the definition-delivering half of the 〜とは pair, "
                    "and it is also the abstract-noun maker: any clause plus "
                    "ということ becomes a thing you can discuss. Compare 〜というの"
                    "は, which does the same job in speech, and 〜というもの, which "
                    "adds 'the thing called…' and a note of generality.",
        "watch": "〜ということです after a clause you have just heard means 'so "
                 "the upshot is'; 〜ということになりました means 'it was decided "
                 "that'.",
    },
    {
        "point": "〜か（埋め込み疑問）",
        "en": "whether / how / what - a question used as a noun",
        "formula": "question word clause (plain form) + か + を / が",
        "examples": [
            ("範囲がどこまで広いかが問題です。",
             "はんいがどこまでひろいかがもんだいです。",
             "The question is how far the range extends."),
            ("何を求めるべきかを考えます。", "なにをもとめるべきかをかんがえます。",
             "I think about what we should be looking for."),
        ],
        "contrast": "The か turns a question into a noun phrase, so no です is "
                    "needed inside it - 広いですか would be wrong here, and the "
                    "particle after か is が or を, not は. Without the の you "
                    "sometimes see (広いかどうか) the question is yes/no; with a "
                    "question word the bare か is enough.",
        "watch": "Question-word clauses drop を before か in casual speech "
                 "(何を求めるべきか考えます) but keep it in writing.",
    },
]

GRAMMAR[55] = [
    {
        "point": "〜に基づいて",
        "en": "on the basis of; grounded in",
        "formula": "N + に基づいて",
        "examples": [
            ("実績に基づいて判断します。", "じっせきにもとづいてはんだんします。",
             "I judge on the basis of the record."),
            ("数字に基づいて説明いたします。", "すうじにもとづいてせつめいいたします。",
             "Let me explain it on the basis of the figures."),
        ],
        "contrast": "に基づいて binds a conclusion to something checkable - "
                    "data, a rule, a documented precedent. をもとに means 'taking "
                    "X as the raw material', and it fits a draft, an idea, a "
                    "story: この案をもとに作り直す. The difference is whether you "
                    "are standing on the thing (基) or building out of it "
                    "(もと). With 経験を基に the two are close, but 基にする is "
                    "'use as a foundation' and 基づく is 'follow from'.",
        "watch": "に基づく is the verb form (事実に基づく説明), に基づき the written "
                 "conjunction, に基づいた the modifier. もとづく is written with "
                 "the づ you hear.",
    },
    {
        "point": "〜を挙げる",
        "en": "cite; list (as grounds)",
        "formula": "N + を + 挙げる",
        "examples": [
            ("根拠として三つ挙げます。", "こんきょとしてみっつあげます。",
             "I would cite three grounds."),
            ("費用、時間、満足度を挙げます。",
             "ひよう、じかん、まんぞくどをあげます。",
             "Cost, time and satisfaction - I'd cite those."),
        ],
        "contrast": "挙げる in argument is 'cite', not 'raise'. 例を挙げる is "
                    "'give an example'; 手を挙げる is 'raise a hand'. The near "
                    "miss is 上げる, which is to raise something in value or "
                    "position - 価格を上げる. Grounds are 挙げる.",
        "watch": "The として form is the argumentative one: 根拠として挙げる, "
                 "理由として挙げる.",
    },
    {
        "point": "〜ように見える",
        "en": "it looks as though; it appears that",
        "formula": "plain form + ように見える",
        "examples": [
            ("費用の根拠は少し弱いように見えます。",
             "ひようのこんきょはすこしよわいようにみえます。",
             "The cost argument looks a little thin."),
            ("十分なように見えて、実は足りません。",
             "じゅうぶんのようにみえて、じつはたりません。",
             "It looks sufficient, but in fact it is not enough."),
        ],
        "contrast": "ように見える says how it looks, and it usually signals that "
                    "looks are not the whole story - the sentence after it "
                    "often corrects them. そうです（様態）is a stronger, more "
                    "immediate impression from appearances; と思われる is an "
                    "inference, and in writing it is the safest of the three "
                    "because it does not commit you to having looked at "
                    "anything.",
        "watch": "With nouns and na-adjectives: 十分なように見える, "
                 "必要なようには見えない.",
    },
]

GRAMMAR[56] = [
    {
        "point": "〜の背景にある",
        "en": "what lies behind it (the background cause)",
        "formula": "N + の背景に + ある / あると考えます",
        "examples": [
            ("この問題の背景には何があるとお考えですか。",
             "このもんだいのはいけいにはなにがあるとおかんがえですか。",
             "What do you think lies behind this problem?"),
            ("世代間の負担の偏りが背景にあります。",
             "せだいかんのふたんのかたよりがはいけいにあります。",
             "An uneven share of the burden between generations lies behind it."),
        ],
        "contrast": "背景 is the scene behind the event; 要因 is the part of "
                    "that scene you could actually act on; 原因 is the single "
                    "thing that set it off. Serious discussion keeps them "
                    "apart: '人口構成が背景にあり、賃金が伸びないことが要因です' says "
                    "the deep shape and the actionable lever in one line.",
        "watch": "背景にある takes に because ある is a location verb: 背景には. "
                 "背景を説明します uses を because 説明する is transitive.",
    },
    {
        "point": "〜に影響を及ぼす",
        "en": "exert an influence on",
        "formula": "N + に + 影響を及ぼす",
        "examples": [
            ("社会にどんな影響を及ぼしますか。",
             "しゃかいにどんなえいきょうをおよぼしますか。",
             "What effect does that exert on society?"),
            ("家計にも影響が及んでいます。", "かけいにもえいきょうがおよんでいます。",
             "The effects are reaching household budgets too."),
        ],
        "contrast": "及ぼす is transitive - someone exerts it - while 及ぶ is "
                    "intransitive - the effect reaches. Both take に for what "
                    "is affected: 社会に影響を及ぼす, 社会に影響が及ぶ. 影響を与える "
                    "and 影響がある are the plainer versions; 及ぼす is the one "
                    "that appears in analysis because it can carry a "
                    "direction and a distance.",
        "watch": "及ぶ also means 'not match': 及ばない (no match for). Context "
                 "separates it from 'reach'.",
    },
    {
        "point": "〜が要因です",
        "en": "the factor is; a contributing cause is",
        "formula": "plain form + ことが要因です / N + が要因です",
        "examples": [
            ("賃金が伸びないことが要因です。", "ちんぎんがのびないことがよういんです。",
             "Wages that no longer rise are the factor."),
            ("人口の構成が要因の一つです。", "じんこうのこうせいがよういんのひとつです。",
             "The shape of the population is one factor."),
        ],
        "contrast": "要因 is a contributing factor among several, which is why "
                    "it so often arrives with 一つ or 大きい. 原因 points at a "
                    "single culprit and sounds like you have finished "
                    "investigating; 理由 is a reason a person gives. In a "
                    "discussion of something as large as demography, 要因 is "
                    "the honest word.",
        "watch": "要因です takes a whole clause before it only through こと: "
                 "伸びないことが要因です, not 伸びない要因です.",
    },
]

GRAMMAR[57] = [
    {
        "point": "〜べきだ",
        "en": "it ought to be; one should",
        "formula": "V-る + べきだ / べきではありません",
        "examples": [
            ("安全を優先すべきだと考えます。", "あんぜんをゆうせんすべきだとかんがえます。",
             "I believe safety has to come first."),
            ("どちらを優先すべきでしょうか。", "どちらをゆうせんすべきでしょうか。",
             "Which should take priority?"),
        ],
        "contrast": "べきだ is a judgement about what is right; 〜たほうがいい is "
                    "advice about what would be better. 安全を優先したほうがいい"
                    "です suggests a course of action; 優先すべきです says anything "
                    "else would be wrong. That is why べき belongs to argument "
                    "and ほうがいい to conversation - and why べきです about "
                    "someone else's conduct can sound like a telling-off.",
        "watch": "As a modifier it is べき + noun: 優先すべき点, 守るべき約束. The "
                 "negative is べきではない / べきではありません. するべき and すべき "
                 "are both correct.",
    },
    {
        "point": "〜形にする",
        "en": "settle it as; make it into the form of",
        "formula": "plain form / N + の + 形にする",
        "examples": [
            ("範囲を決めて妥協する形にします。",
             "はんいをきめてだきょうするかたちにします。",
             "We set its scope and compromise within it."),
            ("全体で支える形にします。", "ぜんたいでささえるかたちにします。",
             "I'll make it a structure the whole group carries."),
        ],
        "contrast": "形にする is how you describe a decision's shape without "
                    "committing to the mechanism - useful when you are "
                    "announcing a compromise you have not fully designed. "
                    "ことにする is a decision in your own head ('I've decided "
                    "to'), ようにする is an effort over time ('I'll make a point "
                    "of'), and 方針にする is the formal policy version.",
        "watch": "As a modifier or a heading it is 〜という形で: 妥協という形で決め"
                 "ました.",
    },
    {
        "point": "〜になる",
        "en": "end up as; turn out to be",
        "formula": "N / na-adj stem + になる",
        "examples": [
            ("その判断で誰が不利になりますか。",
             "そのはんだんでだれがふりになりますか。",
             "Who loses out under that decision?"),
            ("若い世代の負担になります。", "わかいせだいのふたんになります。",
             "It becomes a burden on the young."),
        ],
        "contrast": "になる is change of state - becoming - while にする is "
                    "someone making it so. 負担になる is 'it ends up a burden'; "
                    "負担にする is 'they make it a burden'. With 不利 the "
                    "distinction is exactly the one you want in an argument "
                    "about who bears a cost: nobody chose it, it fell out that "
                    "way.",
        "watch": "不利 is a noun, and it takes な before a noun: 不利な立場. "
                 "There is no verb *不利する.",
    },
]

GRAMMAR[58] = [
    {
        "point": "〜と思われる",
        "en": "it appears that; it is thought that (impersonal)",
        "formula": "plain form + と思われる",
        "examples": [
            ("しばらくは続くと思われます。", "しばらくはつづくとおもわれます。",
             "It seems likely to run on for a while."),
            ("影響は限定的だと思われます。", "えいきょうはげんていてきだとおもわれます。",
             "The impact appears to be limited."),
        ],
        "contrast": "思う belongs to the speaker; 思われる belongs to nobody in "
                    "particular, which is exactly what a forecast needs. It is "
                    "the spontaneous-passive use: the thought forms itself. "
                    "Compare 〜と考えられる (it can be reasoned that - "
                    "intellectual) and 〜と見られる (it is read as - the "
                    "reporter's hedge). All three keep the writer out of the "
                    "sentence.",
        "watch": "The が version exists too - 〜と思われますが - and it is the "
                 "standard way to state a finding and immediately limit it: "
                 "続くと思われますが、確実ではありません.",
    },
    {
        "point": "〜べきでしょう",
        "en": "one probably should (softened obligation)",
        "formula": "V-る + べきでしょう / べきだろう",
        "examples": [
            ("解釈には、その幅を含めるべきでしょう。",
             "かいしゃくには、そのはばをふくめるべきでしょう。",
             "Any reading of them should surely allow for that spread."),
            ("この段階では断定は避けるべきでしょう。",
             "このだんかいではだんていはさけるべきでしょう。",
             "At this stage, one should probably avoid flat statements."),
        ],
        "contrast": "べきだ is a position; べきでしょう is a position offered for "
                    "agreement. Adding でしょう does not make it less true, it "
                    "makes it less yours alone - which is why a hedged "
                    "document is full of it. 〜べきではないでしょうか turns the "
                    "same form into the politest way to disagree.",
        "watch": "でしょう is です + う; in written Japanese you will meet だろう "
                 "instead, and after べき both are correct.",
    },
    {
        "point": "〜を避ける / 断定を避ける",
        "en": "refrain from; avoid doing",
        "formula": "N + を + 避ける / V-る + のを避ける",
        "examples": [
            ("まだ傾向が読めないため、断定は避けたいです。",
             "まだけいこうがよめないため、だんていはさけたいです。",
             "The trend is still unreadable, so I'd rather not commit myself."),
            ("確実だとは言えません。", "かくじつだとはいえません。",
             "One can't call it certain."),
        ],
        "contrast": "避ける is the deliberate one: you could have committed and "
                    "chose not to. 〜ないようにする is milder and more like a "
                    "habit ('I try not to'). The professional form is the "
                    "noun-plus-避ける pairing: 断定を避ける, 表現を避ける, 単純化を"
                    "避ける - it names the thing you declined to do.",
        "watch": "避けたいです is a wish about your own conduct and is safe; "
                 "避けてください would be an instruction to somebody else.",
    },
]

GRAMMAR[59] = [
    {
        "point": "〜こそ",
        "en": "precisely; the very thing",
        "formula": "N + こそ",
        "examples": [
            ("意思決定の速さこそが課題だと考えます。",
             "いしけっていのはやさこそがかだいだとかんがえます。",
             "The speed of decision-making is precisely the problem."),
            ("今回こそ変えるべきです。", "こんかいこそかえるべきです。",
             "This time, of all times, we must change it."),
        ],
        "contrast": "こそ singles out one candidate as the real one, and it "
                    "replaces が or を rather than following them: 速さこそが課題"
                    "だ, not 速さがこそ. だけ merely limits ('only'); こそ insists "
                    "('this, and not the things you were looking at'). It is "
                    "the emphatic form of a debate answer.",
        "watch": "〜からこそ is the reason-emphatic: 分かっているからこそ言うのです. "
                 "With ば: あなただからこそ頼むのです.",
    },
    {
        "point": "〜だけは",
        "en": "this one thing at least",
        "formula": "N + だけは",
        "examples": [
            ("お客様との信頼だけは守るべきです。",
             "おきゃくさまとのしんらいだけはまもるべきです。",
             "Trust with our customers, come what may."),
            ("最低限、そこだけは変えません。", "さいていげん、そこだけはかえません。",
             "At the very least, that one point stays."),
        ],
        "contrast": "だけは marks the minimum you refuse to give up, so it "
                    "normally arrives with a promise - 守る、変えない、確保する. "
                    "だけ alone is just 'only' and can sound like you are "
                    "dismissing the rest: 信頼だけ守る ('I'll keep trust, and "
                    "forget the rest'). The は is what makes it a floor rather "
                    "than a limit.",
        "watch": "With a verb it is V-るだけは: 確認するだけはしました ('I did at "
                 "least check').",
    },
    {
        "point": "〜ようにする / 〜仕組みにする",
        "en": "arrange it so that; build a structure that",
        "formula": "V-る / V-ない + ようにする / plain form + 仕組みにする",
        "examples": [
            ("回答の期限を決め、必ず守る仕組みにします。",
             "かいとうのきげんをきめ、かならずまもるしくみにします。",
             "We set a deadline for replies, and build a structure that keeps "
             "it."),
            ("期限を必ず守るようにします。", "きげんをかならずまもるようにします。",
             "I'll make a point of always keeping the deadline."),
        ],
        "contrast": "ようにする is a personal resolve - it rests on somebody "
                    "remembering. 仕組みにする is a structural fix: the outcome "
                    "no longer depends on willpower. In a business answer, "
                    "promising the second is stronger than promising the "
                    "first, and that is why 仕組み shows up wherever a promise "
                    "has to survive a change of staff.",
        "watch": "ようになります is the intransitive pair - it describes the "
                 "result, not the effort: 守られるようになりました.",
    },
]

GRAMMAR[60] = [
    {
        "point": "〜ものだ",
        "en": "that is how things are (by nature or by custom)",
        "formula": "plain form + ものだ",
        "examples": [
            ("約束は守るものだと教わってきました。",
             "やくそくはまもるものだとおそわってきました。",
             "I was brought up to believe promises are there to be kept."),
            ("まず形を覚えれば、後で意味が分かるものです。",
             "まずかたちをおぼえれば、あとでいみがわかるものです。",
             "Learn the shape first; the meaning comes afterwards."),
        ],
        "contrast": "ものだ states a general truth of the world or of custom - "
                    "'this is what one does'. 〜べきだ says what ought to be "
                    "done and can be argued with; ものだ presents it as simply "
                    "how it is. 約束は守るべきです is a position; 約束は守るもの"
                    "です is an upbringing.",
        "watch": "〜たものだ is a different pattern entirely: nostalgia. よく"
                 "遊んだものです = 'I used to play there often'.",
    },
    {
        "point": "〜ものではない",
        "en": "it is not something one does",
        "formula": "plain form + ものではない",
        "examples": [
            ("失敗は恐れるものではないと伝えたいです。",
             "しっぱいはおそれるものではないとつたえたいです。",
             "That failure is nothing to be afraid of - that's what I want to "
             "pass on."),
            ("人の失敗を笑うものではありません。",
             "ひとのしっぱいをわらうものではありません。",
             "One does not laugh at other people's failures."),
        ],
        "contrast": "ものではない forbids on the grounds of how the world "
                    "works; 〜てはいけません forbids as a rule. The first is what "
                    "you say to a junior as guidance - it educates rather than "
                    "orders - and the second is what you say in a manual. "
                    "恐れてはいけません would sound like a regulation.",
        "watch": "In speech もんじゃない is common: 急ぐもんじゃない. Do not write "
                 "it in a report.",
    },
    {
        "point": "〜てくる（現在まで続く）",
        "en": "have been doing, up to now",
        "formula": "V-て + くる / きました",
        "examples": [
            ("そう教わってきました。", "そうおそわってきました。",
             "That is how I have been taught."),
            ("ずっとこのやり方でやってきました。",
             "ずっとこのやりかたでやってきました。",
             "I have always done it this way."),
        ],
        "contrast": "〜てくる looks back at a line of continuity from the past "
                    "to now; 〜てきた is the same thing narrated; 〜ている is just "
                    "the present state with no history in it. 教わっています is "
                    "'I am being taught'; 教わってきました is 'I have been taught, "
                    "over years, and that is why I think this'. It is the "
                    "form you reach for when your experience is your "
                    "evidence.",
        "watch": "The other てくる - 'come and do' (買ってくる) and 'start to' "
                 "(雨が降ってきた) - is unrelated. Context separates them.",
    },
]

GRAMMAR[61] = [
    {
        "point": "持ち帰る / 〜（さ）せていただけますか",
        "en": "take it back (to my own people)",
        "formula": "提案 + を + 持ち帰る",
        "examples": [
            ("この提案、一度持ち帰らせていただけますか。",
             "このていあん、いちどもちかえらせていただけますか。",
             "Might I take this proposal back with me once?"),
            ("社内で相談させていただけますか。",
             "しゃないでそうだんさせていただけますか。",
             "Might I consult my own people on it?"),
        ],
        "contrast": "持ち帰る literally means carry it home; in a meeting it "
                    "means 'I do not have authority to answer'. That is why "
                    "it works as a soft no: the reason is structural, not a "
                    "judgement on the proposal. Compare 検討します, which is the "
                    "vaguer and more evasive relative - 持ち帰る at least names "
                    "a next step.",
        "watch": "The させていただけますか wrapper is what makes it a request: "
                 "持ち帰ります alone would be an announcement.",
    },
    {
        "point": "〜ということです（読みを訂正する）",
        "en": "what I mean is that …; that is not quite it",
        "formula": "plain form + ということです",
        "examples": [
            ("別の角度からも見たいということです。",
             "べつのかくどからもみたいということです。",
             "Only that I would like to see it from another angle."),
            ("賛成できないということではありません。",
             "さんせいできないということではありません。",
             "It's not that I cannot agree to it."),
        ],
        "contrast": "The Japanese meeting rarely contains the word いいえ. "
                    "Where English would say 'no, that's not what I meant', "
                    "Japanese restates the intended meaning and lets the "
                    "difference show: 賛成できないということではありません. Answering "
                    "with a flat 違います is possible but it makes the other "
                    "person's reading into an error they committed.",
        "watch": "〜ということですか is the same move from the other chair - "
                 "checking the reading rather than asserting it.",
    },
    {
        "point": "〜た上で",
        "en": "after doing; having done",
        "formula": "V-た + 上で",
        "examples": [
            ("検討した上で、今週中に書面でお答えいたします。",
             "けんとうしたうえで、こんしゅうちゅうにしょめんでおこたえいたします。",
             "Once we have examined it, in writing, within this week."),
            ("十分に話し合った上で決めます。",
             "じゅうぶんにはなしあったうえできめます。",
             "We will decide after talking it through properly."),
        ],
        "contrast": "上で insists the first step is completed before the "
                    "second begins - it is a sequence, and a guarantee. てから "
                    "is the everyday equivalent without the guarantee; ながら "
                    "overlaps them. In a commitment to a deadline, 検討した上で"
                    "お答えします is what lets the other person hold you to a "
                    "date.",
        "watch": "上で after a noun means 'in terms of' - 金額の上では問題ない - "
                 "and that is spelled 上, not うえ.",
    },
]

GRAMMAR[62] = [
    {
        "point": "見出しの省略（助詞・だの脱落）",
        "en": "headline grammar: particles and だ dropped",
        "formula": "N、N + へ / か / も（助詞なし）",
        "examples": [
            ("首相、訪米へ", "しゅしょう、ほうべいへ",
             "PM to visit the US."),
            ("新制度、四月から", "しんせいど、しがつから",
             "New system from April."),
        ],
        "contrast": "Read a headline as compressed, not as broken Japanese. "
                    "The comma does the work of は or が, だ is absent at the "
                    "end, and a single へ or か carries the predicate: 訪米へ "
                    "means 「向かう」. The same compression gives 名詞止め - "
                    "ending on a noun (導入へ、撤回か) - the written register's "
                    "way of withholding tense altogether.",
        "watch": "The quote marker survives: 社長「撤退なし」. Past tense too, "
                 "when it matters: 首相が表明.",
    },
    {
        "point": "〜を報じる",
        "en": "report (a story)",
        "formula": "N + を + 報じる",
        "examples": [
            ("本紙が独占で報じた件ですね。", "ほんしがどくせんでほうじたけんですね。",
             "The story this paper broke exclusively."),
            ("各紙が一斉に報じました。", "かくしがいっせいにほうじました。",
             "All the papers carried it at once."),
        ],
        "contrast": "報じる is the newsroom's own verb - a paper 報じる and a "
                    "story is 報じられる. 伝える is neutral transmission, 知らせる "
                    "is telling a person, 報道する is the activity as a whole. "
                    "Which outlet did it is the point, so the agent is nearly "
                    "always named: 本紙が、他紙も.",
        "watch": "独占 (an exclusive) is a noun: 独占で報じた.",
    },
    {
        "point": "〜が問われる",
        "en": "is called into question",
        "formula": "N + が + 問われる",
        "examples": [
            ("報道の姿勢も問われますね。", "ほうどうのしせいもとわれますね。",
             "The stance of the coverage will be questioned too."),
            ("対応の遅れが問われています。", "たいおうのおくれがとわれています。",
             "The slowness of the response is under question."),
        ],
        "contrast": "A passive with no named agent, and that is the point: "
                    "nobody in particular is asking, but an answer is owed. "
                    "批判される names a judgement and takes sides; 問われる stays "
                    "inside the news register.",
        "watch": "問う is the active verb (記者が問う); 問われる is what appears "
                 "in analysis.",
    },
    {
        "point": "波紋が広がる",
        "en": "the ripples spread - fallout grows",
        "formula": "波紋が広がる / 波紋を呼ぶ",
        "examples": [
            ("この波紋は広がりそうですか。", "このはもんはひろがりそうですか。",
             "Do you think the repercussions will spread?"),
            ("波紋は他社にも広がりました。", "はもんはたしゃにもひろがりました。",
             "The ripples reached other companies too."),
        ],
        "contrast": "The standard reporting idiom for second-order effects, "
                    "deliberately vague about direction: not 被害 (damage), "
                    "not 批判 (criticism), just spreading. 波紋を呼ぶ is the "
                    "same idea at the moment it starts.",
        "watch": "Written register. In conversation say 影響が広がる.",
    },
]

GRAMMAR[63] = [
    {
        "point": "〜に警鐘を鳴らす",
        "en": "sound the alarm about",
        "formula": "N + に + 警鐘を鳴らす",
        "examples": [
            ("人口減少に警鐘を鳴らしています。",
             "じんこうげんしょうにけいしょうをならしています。",
             "It sounds a warning about population decline."),
            ("もっと早く警鐘を鳴らすべきでした。",
             "もっとはやくけいしょうをならすべきでした。",
             "The alarm should have been raised much sooner."),
        ],
        "contrast": "警鐘を鳴らす is the editorial's idiom for a slow problem "
                    "nobody is acting on - it carries both urgency and "
                    "neglect. 警告する is a formal warning from someone with "
                    "authority; 注意を促す merely asks for care. Only 警鐘 has "
                    "the 'nobody is listening' note.",
        "watch": "The problem takes に: 地域の維持に警鐘を鳴らす.",
    },
    {
        "point": "〜を提起する",
        "en": "raise (an issue); put forward",
        "formula": "N + を + 提起する",
        "examples": [
            ("人口減少という難問を提起しています。",
             "じんこうげんしょうというなんもんをていきしています。",
             "It raises the hard problem of population decline."),
            ("地域の維持という問題を提起しました。",
             "ちいきのいじというもんだいをていきしました。",
             "It raised the question of keeping regions alive."),
        ],
        "contrast": "提起する puts an issue on the table; 提案する offers a way "
                    "forward; 提言する is what a committee hands down. An "
                    "editorial usually does only the first, which is why it "
                    "can end without a solution and still have done its job.",
        "watch": "A written suru-noun - 提起をする is not used.",
    },
    {
        "point": "〜には踏み込んでいない",
        "en": "it does not go as far as",
        "formula": "N + には + 踏み込む / 踏み込んでいない",
        "examples": [
            ("解決策には踏み込んでいません。", "かいけつさくにはふみこんでいません。",
             "It does not go as far as a solution."),
            ("具体策には踏み込まないまま終わります。",
             "ぐたいさくにはふみこまないままおわります。",
             "It ends without ever reaching concrete measures."),
        ],
        "contrast": "踏み込む is literally stepping into something, and in "
                    "commentary it means entering territory that commits you. "
                    "The negative is the standard way to say what a text "
                    "declined to do. 触れていない ('does not mention') is weaker "
                    "and merely notes an absence.",
        "watch": "踏み込んだ議論 is the positive form: a discussion that went "
                 "deep.",
    },
    {
        "point": "〜は今後の課題に（提言どまり）",
        "en": "X is left as a matter for later",
        "formula": "N + は今後の課題（にする / としている）",
        "examples": [
            ("提言は示していますが、具体策は次の機会です。",
             "ていげんはしめしていますが、ぐたいさくはつぎのきかいです。",
             "It offers recommendations, but specifics are for another day."),
            ("詳細は今後の課題としています。",
             "しょうさいはこんごのかだいとしています。",
             "The detail is left as a matter for the future."),
        ],
        "contrast": "提言 (a recommendation) is the usual endpoint of a 社説; "
                    "解決 (a solution) would end the argument, and a newspaper "
                    "rarely claims one. Recognising the shape is half of "
                    "reading an editorial: the recommendation is the content, "
                    "the missing specifics are the genre.",
        "watch": "今後の課題にする is also a meeting phrase for parking an item - "
                 "the same move as 宿題にする.",
    },
]

GRAMMAR[64] = [
    {
        "point": "〜という認識でよろしいですか",
        "en": "is it fair to understand that …?",
        "formula": "plain form + という認識でよろしいですか",
        "examples": [
            ("計画は順調だという認識でよろしいですか。",
             "けいかくはじゅんちょうだというにんしきでよろしいですか。",
             "Is it fair to understand that the plan is on track?"),
            ("来月までに終わるという認識でよろしいですか。",
             "らいげつまでにおわるというにんしきでよろしいですか。",
             "Is it fair to understand that it finishes next month?"),
        ],
        "contrast": "The interviewer's checking frame: it puts a reading on "
                    "the record and asks you to sign it. It is not a yes/no "
                    "question about a fact - 順調ですか would be that. 認識 names "
                    "the shared understanding itself, so answering it means "
                    "agreeing to a wording, not reporting a state of affairs.",
        "watch": "The answer is a degree, not はい or いいえ: 少し留保があります、"
                 "そのとおりです、それで結構です.",
    },
    {
        "point": "留保 / 全面的には〜ない",
        "en": "with one caveat; not across the board",
        "formula": "留保がある / 全面的には + negative",
        "examples": [
            ("少し留保があります。全面的には順調ではありません。",
             "すこしりゅうほがあります。ぜんめんてきにはじゅんちょうではありません。",
             "With one caveat. It is not going smoothly across the board."),
            ("全面的には賛成できません。", "ぜんめんてきにはさんせいできません。",
             "I cannot agree to it in its entirety."),
        ],
        "contrast": "This is how a public figure says 違います without saying "
                    "it. The move is: concede the frame (少し留保があります), then "
                    "qualify the scope (全面的には…ない). 全面的に否定する would be "
                    "a fight; 全面的には賛成できない is a correction with the door "
                    "open.",
        "watch": "留保 is a noun: 留保します also exists ('I reserve my "
                 "position'), and 留保付きで承認する is the committee form.",
    },
    {
        "point": "含みを持たせる",
        "en": "leave it implied; say it without saying it",
        "formula": "N + の含みで / 含みを持たせる",
        "examples": [
            ("その含みでお読みいただければ結構です。",
             "そのふくみでおよみいただければけっこうです。",
             "You may read it that way, if you wish."),
            ("含みを持たせた言い方ですね。", "ふくみをもたせたいいかたですね。",
             "That is a way of putting it with something left unsaid."),
        ],
        "contrast": "含み is what a sentence carries but does not state. Saying "
                    "その含みでお読みいただければ allows a journalist to print the "
                    "stronger version while the speaker has only allowed it - "
                    "a useful arrangement for both sides, and one of the "
                    "reasons 断定を避ける is a professional habit rather than "
                    "weakness.",
        "watch": "含みを持たせる is the verb form; 含みのある言い方 is the "
                 "adjectival one.",
    },
]

GRAMMAR[65] = [
    {
        "point": "〜と見ています / 〜と見られる",
        "en": "I read it as; it is seen as",
        "formula": "plain form + と見る / と見られる",
        "examples": [
            ("影響は限定的だと見ています。", "えいきょうはげんていてきだとみています。",
             "I read the impact as limited."),
            ("被害は小さいと見られます。", "ひがいはちいさいとみられます。",
             "The damage is seen as small."),
        ],
        "contrast": "見る here is not seeing but reading - the reporter's verb "
                    "for a judgement about evidence. と思う is private; と見る "
                    "implies a basis you could show someone. と見られる drops the "
                    "reader entirely, so it is the safest form in print.",
        "watch": "見ている is the state ('I take the view'), 見ているところです would "
                 "be literal watching - context separates them.",
    },
    {
        "point": "断定を避ける",
        "en": "refrain from stating flatly",
        "formula": "N + を避ける / V-るのを避ける",
        "examples": [
            ("現段階では断定を避け、検証を待つべきです。",
             "げんだんかいではだんていをさけ、けんしょうをまつべきです。",
             "At this stage we should avoid flat statements and wait for "
             "verification."),
            ("断定は避けたいと思います。", "だんていはさけたいとおもいます。",
             "I would rather not commit myself to that."),
        ],
        "contrast": "The choice is not between certainty and vagueness; it is "
                    "between what the sources support and what they do not. "
                    "断定する would be claiming the facts are settled; 断定を避ける "
                    "names exactly why you are not claiming it. 分かりません is "
                    "the learner's version of the same honesty and sounds like "
                    "ignorance.",
        "watch": "現段階では is the time marker that usually accompanies it: it "
                 "promises a later, firmer answer.",
    },
    {
        "point": "食い違う / 混ざっている",
        "en": "differ between accounts; be mixed together",
        "formula": "N + で / と + 食い違う / 混ざる",
        "examples": [
            ("報道各社で数字が食い違っていますね。",
             "ほうどうかくしゃですうじがくいちがっていますね。",
             "The figures differ between outlets."),
            ("推測と確認済みの事実が混ざっています。",
             "すいそくとかくにんずみのじじつがまざっています。",
             "Conjecture and confirmed fact are mixed together."),
        ],
        "contrast": "食い違う is disagreement between two accounts that should "
                    "match; 異なる is merely 'differ', with no failure implied. "
                    "混ざる says two grades of claim have been put in the same "
                    "sentence and cannot now be told apart - which is the "
                    "more serious complaint.",
        "watch": "確認済み (already confirmed) is the useful word here: it is "
                 "the label that separates fact from 推測.",
    },
]

GRAMMAR[66] = [
    {
        "point": "狭義 / 広義",
        "en": "in the narrow / broad sense",
        "formula": "狭義では / 広義では + clause",
        "examples": [
            ("狭義では装置そのものを指します。",
             "きょうぎではそうちそのものをさします。",
             "In the narrow sense it refers to the device itself."),
            ("広義では周辺の仕組み全体を含みます。",
             "こうぎではしゅうへんのしくみぜんたいをふくみます。",
             "In the broad sense it includes the whole surrounding system."),
        ],
        "contrast": "The pair lets you set the width of a term before you "
                    "commit to anything, which is the standard academic hedge: "
                    "狭義では該当しないが、広義では該当する. Without it, a disagreement "
                    "about a definition goes round in circles because the two "
                    "sides are using one word at two widths.",
        "watch": "Both are nouns, so the frame is 狭義では / 狭義において. There is "
                 "no na-adjective form - 狭義な意味 is wrong, use 狭義の意味.",
    },
    {
        "point": "〜に該当する",
        "en": "fall under; be covered by",
        "formula": "N + に + 該当する / 該当しない",
        "examples": [
            ("今回の件は定義に該当しますか。",
             "こんかいのけんはていぎにがいとうしますか。",
             "Does this case fall under the definition?"),
            ("厳密には該当しません。", "げんみつにはがいとうしません。",
             "Strictly, it does not fall under it."),
        ],
        "contrast": "該当する is the technical verb for category membership, "
                    "and its value is that it is binary: a case either falls "
                    "under a rule or it does not, with no argument. 当てはまる is "
                    "the everyday equivalent ('applies'); 適用する is what you do "
                    "with the rule once it does apply.",
        "watch": "該当する takes に for the category. 該当する者 is the standard "
                 "form-notice wording for 'those to whom this applies'.",
    },
    {
        "point": "〜によります",
        "en": "it depends on",
        "formula": "N + によります / によって違います",
        "examples": [
            ("用例によります。", "ようれいによります。",
             "It depends on the usage."),
            ("解釈によって結論が変わります。",
             "かいしゃくによってけつろんがかわります。",
             "The conclusion changes depending on the reading."),
        ],
        "contrast": "によります answers a definition question honestly, and it "
                    "is how you refuse to be pinned to a single sense of a "
                    "word. 場合による is the plainer, spoken version. Note the "
                    "other により - 'by means of' and 'according to' - is the "
                    "same shape with a different job: 法律により定める.",
        "watch": "によります is intransitive and stands alone; よります alone is not "
                 "used this way.",
    },
    {
        "point": "〜として扱う",
        "en": "treat as; handle as",
        "formula": "N + として + 扱う / 扱われる",
        "examples": [
            ("類例として扱います。", "るいれいとしてあつかいます。",
             "We'll treat it as an analogous case."),
            ("例外として扱うのが安全です。", "れいがいとしてあつかうのがあんぜんです。",
             "It is safer to treat it as an exception."),
        ],
        "contrast": "として marks the capacity you are assigning something, and "
                    "扱う makes it clear the assignment is a decision rather "
                    "than a fact. That is how you extend a rule to a case it "
                    "does not literally cover without having to amend the "
                    "rule.",
        "watch": "扱う is transitive (類例として扱う); 扱われる the passive. The "
                 "noun 扱い is common in headings: 類例としての扱い.",
    },
]

GRAMMAR[67] = [
    {
        "point": "やや（評価を弱める）",
        "en": "somewhat; rather (the academic hedge)",
        "formula": "やや + adjective / verb",
        "examples": [
            ("標本がやや小さいです。", "ひょうほんがややちいさいです。",
             "The sample is rather small."),
            ("効果はやや限定的です。", "こうかはややげんていてきです。",
             "The effect is somewhat limited."),
        ],
        "contrast": "やや is the reviewer's adverb: it lets you criticise "
                    "without attacking, and it is quantitative rather than "
                    "emotional. 少し is conversational and about amount; やや is "
                    "about degree on a scale and belongs to writing. "
                    "やや小さい invites a fix; 小さい invites an argument.",
        "watch": "It pairs with がやや、はやや, and with verbs: やや遅れている. "
                 "It never takes な.",
    },
    {
        "point": "〜には〜が要ります",
        "en": "requires; calls for",
        "formula": "N + には + N + が要ります",
        "examples": [
            ("解釈には注意が要ります。", "かいしゃくにはちゅういがいります。",
             "Interpretation requires care."),
            ("追試には時間が要ります。", "ついしにはじかんがいります。",
             "A replication takes time."),
        ],
        "contrast": "要る is plain 'be needed', and with には it says what this "
                    "particular step costs: 解釈には注意が要る. 必要です is the "
                    "same idea one register up and more official; 〜が必要です is "
                    "the form for a report, 〜が要ります the form for a "
                    "discussion.",
        "watch": "The thing needed takes が, and the activity that needs it "
                 "takes には. 要ります is written 要る in plain form.",
    },
    {
        "point": "有意差がある",
        "en": "there is a statistically significant difference",
        "formula": "有意差がある / 有意差は出ている",
        "examples": [
            ("有意差は出ていますが、差は小さいです。",
             "ゆういさはでていますが、さはちいさいです。",
             "There is a significant difference, but it is small."),
            ("手法の妥当性に影響します。", "しゅほうのだとうせいにえいきょうします。",
             "It affects the validity of the method."),
        ],
        "contrast": "有意差 says the difference is unlikely to be chance; it "
                    "says nothing about how large it is. Conflating the two is "
                    "the commonest misreading of a paper, and 差は小さい in the "
                    "same breath is how a careful reviewer prevents it.",
        "watch": "妥当性 (validity) is about whether the method measures what "
                 "it claims to; 信頼性 (reliability) is about whether it does "
                 "so consistently.",
    },
]

GRAMMAR[68] = [
    {
        "point": "〜部構成",
        "en": "structured in N parts",
        "formula": "number + 部構成（です / にする）",
        "examples": [
            ("三部構成です。背景、要点、今後の課題です。",
             "さんぶこうせいです。はいけい、ようてん、こんごのかだいです。",
             "Three parts: background, main points, and issues going forward."),
            ("二部構成にしましょう。", "にぶこうせいにしましょう。",
             "Let's make it two parts."),
        ],
        "contrast": "構成 is the word for the shape of a talk, and 〜部構成 names "
                    "the number of blocks. It is a structure word, not a "
                    "content word: 三部構成です tells the room how to listen "
                    "before you say anything. 三つの部分に分けます describes the "
                    "same thing as an action and sounds improvised.",
        "watch": "The counting word is 部, so 三個構成 is wrong. 構成する is the "
                 "verb: 三部で構成する.",
    },
    {
        "point": "〜に譲る",
        "en": "leave it to; hand over to",
        "formula": "N + に + 譲る",
        "examples": [
            ("補足は資料に譲ります。", "ほそくはしりょうにゆずります。",
             "I'll leave the supplementary detail to the handout."),
            ("詳しい数字は資料に譲ります。", "くわしいすうじはしりょうにゆずります。",
             "I'll leave the detailed figures to the handout."),
        ],
        "contrast": "This is how you cut material without looking unprepared: "
                    "the content exists, it is simply in the other document. "
                    "省きます ('I'll omit it') admits a gap; 割愛します is the "
                    "stiffer version of 譲る; 後で触れます defers it to your own "
                    "later slide.",
        "watch": "譲る also means 'yield' to a person (席を譲る) - same verb, "
                 "different object.",
    },
    {
        "point": "〜ば足ります",
        "en": "X is enough; X will do",
        "formula": "N + があれば / N + で + 足ります",
        "examples": [
            ("十五分あれば足ります。", "じゅうごふんあればたります。",
             "Fifteen minutes is enough."),
            ("五分もあれば足ります。", "ごふんもあればたります。",
             "Even five minutes would be enough."),
        ],
        "contrast": "足ります is sufficiency measured against a requirement; "
                    "十分です is sufficiency as a judgement. 十五分あれば足ります "
                    "answers the schedule; 十五分で十分です answers the audience. "
                    "足りる is intransitive, so the amount takes で or があれば.",
        "watch": "The negative 足りない is extremely common: 時間が足りない、説得力"
                 "が足りない.",
    },
]

GRAMMAR[69] = [
    {
        "point": "ご指摘はもっともです",
        "en": "your point is well taken",
        "formula": "ご指摘はもっともです / ご指摘のとおりです",
        "examples": [
            ("ご指摘はもっともだと思います。", "ごしてきはもっともだとおもいます。",
             "I think your point is well taken."),
            ("ご指摘のとおりです。", "ごしてきのとおりです。",
             "You are quite right."),
        ],
        "contrast": "もっとも concedes the point without conceding the "
                    "argument: it says the objection is valid, not that the "
                    "thesis falls. おっしゃるとおりです concedes more broadly; "
                    "そのとおりです is fuller agreement still. In academic Q&A, "
                    "もっともです plus a restatement is the standard move.",
        "watch": "もっとも is also a conjunction meaning 'though; however' at "
                 "the start of a sentence - unrelated to this use.",
    },
    {
        "point": "〜（さ）せていただいてよろしいですか",
        "en": "may I …? (asking leave to act)",
        "formula": "V-（さ）せて + いただいて + よろしいですか",
        "examples": [
            ("一点、指摘させていただいてよろしいですか。",
             "いってん、してきさせていただいてよろしいですか。",
             "May I raise one point?"),
            ("質問させていただいてよろしいですか。",
             "しつもんさせていただいてよろしいですか。",
             "May I ask a question?"),
        ],
        "contrast": "This asks permission for your own action and is the "
                    "conference-standard opening for anything adversarial. "
                    "Compare 〜ていいですか (casual, to a peer), 〜てもよろしい"
                    "でしょうか (asking whether THEY mind, no させ), and this one, "
                    "which wraps the act in させてもらう so the floor's owner "
                    "grants it.",
        "watch": "させていただく is the humble form; overusing it outside formal "
                 "settings sounds stiff. With a superior, させていただけますか is "
                 "safer still.",
    },
    {
        "point": "〜として受け取る",
        "en": "take it away as; accept it as",
        "formula": "N + として + 受け取る / お受け取りください",
        "examples": [
            ("それを宿題としてお受け取りください。",
             "それをしゅくだいとしておうけとりください。",
             "Please take that away as an action item."),
            ("今後の課題として受け取ります。",
             "こんごのかだいとしてうけとります。",
             "I take that as a matter to address going forward."),
        ],
        "contrast": "This is the polite way to park a question you cannot "
                    "answer on the spot: you do not refuse it, you accept it "
                    "in a category that has a later date attached. 分かりません "
                    "ends the exchange; 宿題として受け取ります schedules it - and "
                    "the speaker is then obliged to 触れる next time.",
        "watch": "お受け取りください is the honorific instruction; 受け取ります is "
                 "what the answerer says.",
    },
]

GRAMMAR[70] = [
    {
        "point": "改まる / 砕ける",
        "en": "become formal / become casual - the register pair",
        "formula": "改まった / 砕けた + 場面・言い方",
        "examples": [
            ("場面によって言い回しが変わります。",
             "ばめんによっていいまわしがかわります。",
             "The phrasing changes depending on the setting."),
            ("砕けた言い方でもう一度お願いします。",
             "くだけたいいかたでもういちどおねがいします。",
             "The casual version once more, please."),
        ],
        "contrast": "These two are the vocabulary for talking about register "
                    "itself. 改まる is the direction towards formality, 砕ける "
                    "towards ease, and both describe the situation as much as "
                    "the words: 改まった場面、砕けた会話. 丁寧 is a judgement about "
                    "the wording ('polite'), not about how far along the scale "
                    "it sits.",
        "watch": "砕ける is intransitive - the conversation relaxes. To relax "
                 "it yourself you say 砕けた言い方にします.",
    },
    {
        "point": "承知しました / 了解です / かしこまりました",
        "en": "one 'yes' at three levels",
        "formula": "fixed response forms",
        "examples": [
            ("承知しました。", "しょうちしました。",
             "Understood. (neutral polite - colleague or boss)"),
            ("了解です。", "りょうかいです。",
             "Got it. (casual - inside your own team)"),
            ("かしこまりました。", "かしこまりました。",
             "Certainly. (formal - customer-facing)"),
        ],
        "contrast": "Three sentences, one meaning, three relationships. What "
                    "changes is not the information but the distance: 了解です "
                    "assumes equality, 承知しました assumes a working relationship, "
                    "かしこまりました assumes you are being asked. Most learners "
                    "control two of the three and use the middle one "
                    "everywhere.",
        "watch": "了解 is often avoided upwards - to a client or a senior "
                 "partner it can sound curt. 承知いたしました is 承知しました one step "
                 "up.",
    },
    {
        "point": "〜と申し上げます",
        "en": "I say / I state (most humble)",
        "formula": "N + と + 申し上げます",
        "examples": [
            ("最上級の敬語で申し上げます。",
             "さいじょうきゅうのけいごでもうしあげます。",
             "I'll use the highest level of honorifics."),
            ("一言ご挨拶を申し上げます。", "ひとことごあいさつをもうしあげます。",
             "Let me offer a few words of greeting."),
        ],
        "contrast": "申し上げます is the humble top of the scale - 言います → "
                    "申します → 申し上げます. It lowers the speaker, so it is for "
                    "your own words only; for someone else's you need おっしゃ"
                    "います. In a formal address it is routine rather than "
                    "extreme: the setting, not the word, supplies the "
                    "formality.",
        "watch": "It attaches to a quotation or to a suru-noun: ご挨拶を申し上げ"
                 "ます、〜と申し上げます. Never *申し上げますか to a superior.",
    },
]

GRAMMAR[71] = [
    {
        "point": "足を運ぶ",
        "en": "make the trip (with the effort of going)",
        "formula": "N + に / まで + 足を運ぶ",
        "examples": [
            ("わざわざ足を運んでいただき、恐縮です。",
             "わざわざあしをはこんでいただき、きょうしゅくです。",
             "I'm obliged to you for coming all this way."),
            ("現地まで足を運びました。", "げんちまであしをはこびました。",
             "I went out to the site myself."),
        ],
        "contrast": "来る and 行く are neutral about effort; 足を運ぶ is not - it "
                    "counts the journey as a thing somebody spent. That is why "
                    "わざわざ足を運んでいただき thanks the visitor rather than merely "
                    "noting the visit, and why 現地まで足を運ぶ implies you did not "
                    "just read a report.",
        "watch": "Your own trip is 足を運びます; theirs is 足を運んでいただく. The "
                 "idiom is written-ish but common in polite speech.",
    },
    {
        "point": "気にかかる",
        "en": "weigh on one's mind",
        "formula": "N + が + 気にかかる / 気にかかっている",
        "examples": [
            ("気にかかっていたものですから。", "きにかかっていたものですから。",
             "It was on my mind, you see."),
            ("その数字がずっと気にかかっています。",
             "そのすうじがずっときにかかっています。",
             "Those figures have been on my mind the whole time."),
        ],
        "contrast": "気になる is 'I'm curious / I fancy it' and can be light; "
                    "気にかかる is a worry you have not put down, and it "
                    "frequently supplies the reason for an unprompted visit or "
                    "call. 心配する is stronger and more active - it suggests you "
                    "are doing something about it.",
        "watch": "The subject takes が: 気にかかる. The transitive is 気にかける - "
                 "actively to mind something.",
    },
    {
        "point": "手を打つ",
        "en": "take steps; act (before it is too late)",
        "formula": "（今のうちに / 早めに）+ 手を打つ",
        "examples": [
            ("早めに手を打たなかったのが悔やまれます。",
             "はやめにてをうたなかったのがくやまれます。",
             "I regret not acting sooner."),
            ("今のうちに手を打ちましょう。", "いまのうちにてをうちましょう。",
             "Let's take steps while we still can."),
        ],
        "contrast": "手を打つ is 'do something about it', and it is nearly "
                    "always about timing - 早めに、今のうちに. 対策をとる is the "
                    "plainer, bureaucratic version; 手を打つ sounds like someone "
                    "acting on judgement. Note the unrelated homonym meaning "
                    "'to clap / to strike a deal'.",
        "watch": "It is an idiom with 手 as the object: 手を打つ, never 手を打ち"
                 "する.",
    },
    {
        "point": "拍子抜け / 期待外れ",
        "en": "let-down / falling short of expectations",
        "formula": "拍子抜けする / 期待外れだ",
        "examples": [
            ("結果は期待外れでした。拍子抜けですね。",
             "けっかはきたいはずれでした。ひょうしぬけですね。",
             "The result fell short. Something of a let-down."),
            ("肩の力を抜いて考え直します。",
             "かたのちからをぬいてかんがえなおします。",
             "I'll ease off and think it through again."),
        ],
        "contrast": "期待外れ describes the EVENT - it did not live up to what "
                    "was expected. 拍子抜け describes the FEELING afterwards, "
                    "the deflation when a build-up comes to nothing. They are "
                    "not interchangeable: a result can be 期待外れ without anyone "
                    "feeling 拍子抜け, and you can feel 拍子抜け about a total "
                    "non-event.",
        "watch": "肩の力を抜く is the remedy idiom: relax, stop bracing. It is "
                 "advice about stance, not about effort.",
    },
]

GRAMMAR[72] = [
    {
        "point": "〜という前提を疑う",
        "en": "question the premise that …",
        "formula": "plain form + という前提 / 前提を疑う",
        "examples": [
            ("成長が続くという前提を疑う必要があります。",
             "せいちょうがつづくというぜんていをうたがうひつようがあります。",
             "We need to question the premise that growth will continue."),
            ("その前提自体が仮説です。", "そのぜんていじたいがかせつです。",
             "That premise is itself a hypothesis."),
        ],
        "contrast": "Attacking a conclusion keeps you inside the other side's "
                    "framework; attacking a premise changes the debate. 前提 is "
                    "what the argument rests on and does not defend, so naming "
                    "it - 成長が続くという前提 - is the strongest move available in "
                    "a discussion that has stopped moving.",
        "watch": "前提を疑う takes を. The adverbial frame is 前提として: 成長が続く"
                 "ことを前提としている.",
    },
    {
        "point": "天秤にかける",
        "en": "put on the scales; weigh against each other",
        "formula": "N + を + 天秤にかける",
        "examples": [
            ("二つの案を天秤にかけるべきですか。",
             "ふたつのあんをてんびんにかけるべきですか。",
             "Should we weigh the two options against each other?"),
            ("費用と効果を天秤にかけます。", "ひようとこうかをてんびんにかけます。",
             "Let's weigh cost against effect."),
        ],
        "contrast": "天秤にかける is comparing on merit with a decision at the "
                    "end of it; 比べる is mere comparison, and 並べる mere "
                    "listing. The scales metaphor carries the point that "
                    "choosing one means the other goes up - which is why the "
                    "next sentence is usually about 折衷 or 統合.",
        "watch": "The object takes を and the pair is joined by と: AとBを天秤に"
                 "かける.",
    },
    {
        "point": "折衷 / 統合",
        "en": "splitting the difference versus combining into something new",
        "formula": "N + の折衷 / N + を統合する",
        "examples": [
            ("単純な折衷では弱いです。統合が必要です。",
             "たんじゅんなせっちゅうではよわいです。とうごうがひつようです。",
             "A simple compromise would be weak. We need integration."),
            ("折衷ではなく、統合を目指します。",
             "せっちゅうではなく、とうごうをめざします。",
             "Not a compromise - I am aiming at integration."),
        ],
        "contrast": "The two ways out of a deadlock. 折衷 (also 妥協) takes a "
                    "bit of each side and satisfies nobody fully; 統合 builds "
                    "something that contains both. Serious argument prefers "
                    "the second, and saying so - 単純な折衷では弱い - is a way "
                    "of rejecting a peace offer without rejecting peace.",
        "watch": "折衷 is a noun: 折衷する also exists, but 折衷案 (the "
                 "compromise proposal) is the form you will actually meet.",
    },
]

GRAMMAR[73] = [
    {
        "point": "〜（さ）せていただきます",
        "en": "let me … (the address opening)",
        "formula": "V-（さ）せて + いただきます",
        "examples": [
            ("所信の一端を述べさせていただきます。",
             "しょしんのいったんをのべさせていただきます。",
             "Let me state part of my position."),
            ("一言ご挨拶をさせていただきます。",
             "ひとことごあいさつをさせていただきます。",
             "Allow me a few words of greeting."),
        ],
        "contrast": "The opening of a Japanese address is permission-shaped: "
                    "you do not take the floor, you are allowed it. 述べます "
                    "would be a claim; 述べさせていただきます is a request already "
                    "granted by the room. Every ceremonial speech opens this "
                    "way, and the formality is in the frame rather than in the "
                    "vocabulary.",
        "watch": "一端 (one part, one end of it) is the modesty word: you are "
                 "not stating everything, only a part.",
    },
    {
        "point": "〜が肝要です",
        "en": "X is the essential thing",
        "formula": "N + が + 肝要です / 肝要だと考えます",
        "examples": [
            ("人づくりが最も肝要です。", "ひとづくりがもっともかんようです。",
             "Developing people matters most."),
            ("信頼関係の構築が肝要だと考えます。",
             "しんらいかんけいのこうちくがかんようだとかんがえます。",
             "I consider building trust to be the essential thing."),
        ],
        "contrast": "肝要 belongs to the speech and the editorial, not to "
                    "conversation: 大切です and 重要です are the everyday forms, "
                    "必要です states a requirement. 肝要 picks one thing out as "
                    "the one that matters, so it is usually preceded by 最も.",
        "watch": "It is a na-adjective: 肝要な点、肝要です. It rarely takes a "
                 "person as its subject.",
    },
    {
        "point": "微力ながら",
        "en": "modest though my ability is",
        "formula": "微力ながら、（全力で）+ V",
        "examples": [
            ("微力ながら、全力で務めさせていただきます。",
             "びりょくながら、ぜんりょくでつとめさせていただきます。",
             "My abilities are modest, but I will serve to the utmost."),
            ("微力ながら、努力いたします。", "びりょくながら、どりょくいたします。",
             "Humble as my powers are, I will do my utmost."),
        ],
        "contrast": "This is fixed self-deprecation, not information about "
                    "your ability - a competent appointee says it too. The "
                    "second half carries the message (全力で、努力して), the first "
                    "half is the ritual. Omitting it makes a Japanese address "
                    "sound boastful regardless of what the rest says.",
        "watch": "ながら here is concessive ('although'), not simultaneous "
                 "('while'). 微力です alone, stated as information, would be "
                 "odd.",
    },
    {
        "point": "結びに",
        "en": "in closing",
        "formula": "結びに + 一言 / 結びの言葉",
        "examples": [
            ("結びに一言お願いします。", "むすびにひとことおねがいします。",
             "A word in closing, please."),
            ("結びの言葉を述べさせていただきます。",
             "むすびのことばをのべさせていただきます。",
             "Let me offer the closing words."),
        ],
        "contrast": "結び is the closing section itself, and 結びに is the marker "
                    "that tells the room the address is about to end - "
                    "listeners begin to sit differently. 最後に is the everyday "
                    "equivalent; 終わりに is for documents. 所期 (originally "
                    "intended) belongs to the same formal register: 所期の目標.",
        "watch": "結び is written むすび, the same word as the 結び of a knot or "
                 "a contract.",
    },
]

# -*- coding: utf-8 -*-
"""Grammar pages, lessons 1-36 (N5, N4, N3) - the beginner half.

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
kana. Only grammar the lesson actually uses.

This half is written for a learner who cannot yet infer a pattern from
examples alone, so: plain です／ます throughout, short sentences, no
literary register, and every contrast is with something the learner has
already met or is about to meet a few lessons later.

Verify with:  .venv/bin/python server/course/ja/grammar.py
"""

GRAMMAR: dict = {}

GRAMMAR[1] = [
    {
        "point": "こんにちは / おはようございます",
        "en": "hello; good morning",
        "formula": "fixed greetings, by time of day",
        "examples": [
            ("こんにちは。", "こんにちは。", "Hello. (used through the day)"),
            ("おはようございます。", "おはようございます。", "Good morning."),
            ("こんばんは。", "こんばんは。", "Good evening."),
        ],
        "contrast": "こんにちは、こんばんは and さようなら all end in the kana は "
                    "but it is read 'wa' - they are old phrases frozen in "
                    "hiragana, not the topic particle は. おはようございます is the "
                    "polite form; おはよう alone is for family and close "
                    "friends, never for a stranger or a colleague.",
        "watch": "こんにちは is written 今日は, but it is always spelled in "
                 "hiragana. Writing it in kanji marks you out immediately.",
    },
    {
        "point": "〜ですか / はい、〜です",
        "en": "is it …? / yes, it is",
        "formula": "N / な-adj stem + ですか → はい、N です",
        "examples": [
            ("お元気ですか。", "おげんきですか。", "How are you?"),
            ("はい、元気です。", "はい、げんきです。", "Yes, I'm well."),
        ],
        "contrast": "ですか turns any statement into a yes/no question - "
                    "nothing else moves. The negative question is 元気じゃあり"
                    "ませんか, and the plain negative answer is 元気じゃありません. "
                    "Note that はい means 'yes, what you said is right', so "
                    "answering はい to 元気じゃありませんか would mean 'yes, I am not "
                    "well'.",
        "watch": "The お in お元気です is politeness prefix, not part of the "
                 "word: about yourself you say 元気です.",
    },
    {
        "point": "さようなら / またね",
        "en": "goodbye; see you",
        "formula": "fixed leave-taking",
        "examples": [
            ("さようなら。", "さようなら。", "Goodbye."),
            ("さようなら。またね。", "さようなら。またね。", "Goodbye. See you."),
        ],
        "contrast": "さようなら is for partings with some distance in them - "
                    "leaving a shop, ending a term, going home from an "
                    "office. For people you expect to see again tomorrow, "
                    "またね、じゃあね、また明日 are the usual choices, and さようなら "
                    "there can sound final.",
    },
]

GRAMMAR[2] = [
    {
        "point": "お願いします",
        "en": "… please (making a request)",
        "formula": "N + をお願いします / N、お願いします",
        "examples": [
            ("コーヒー、お願いします。", "コーヒー、おねがいします。",
             "A coffee, please."),
            ("これをお願いします。", "これをおねがいします。", "This one, please."),
        ],
        "contrast": "お願いします is the safest word in the language: it turns "
                    "any noun into a request, so you can order, ask and "
                    "book without knowing the verb. ください is the same idea "
                    "aimed at a thing you want handed over (水をください); "
                    "お願いします is broader and softer.",
        "watch": "The お is part of the fixed phrase, so おねがいします in "
                 "hiragana is normal in casual writing.",
    },
    {
        "point": "すみません / ごめんなさい",
        "en": "sorry; excuse me",
        "formula": "fixed apologies",
        "examples": [
            ("すみません、おそくなりました。", "すみません、おそくなりました。",
             "Sorry, I'm late."),
            ("ごめんなさい。", "ごめんなさい。", "I'm sorry."),
        ],
        "contrast": "すみません does three jobs: 'excuse me' to get "
                    "attention, 'sorry' for a small trouble you caused, and "
                    "'thank you' for a favour that cost someone something. "
                    "ごめんなさい is apology only and it is more personal - it "
                    "asks to be forgiven, so it suits a friend or a real "
                    "mistake rather than being two minutes late.",
        "watch": "For being late at work, 遅れてすみません is the safe form; "
                 "遅刻しました is the plain statement of fact.",
    },
    {
        "point": "大丈夫です",
        "en": "it's fine; I'm all right",
        "formula": "大丈夫です / 大丈夫ですか",
        "examples": [
            ("大丈夫ですよ。", "だいじょうぶですよ。", "It's fine."),
            ("大丈夫ですか。", "だいじょうぶですか。", "Are you all right?"),
        ],
        "contrast": "大丈夫 answers both worry and refusal. As an answer to "
                    "an apology it means 'no harm done'; as an answer to "
                    "'shall I…?' it means 'no thank you'. いいです can do the "
                    "same jobs but is also plain 'good', so 大丈夫です is the "
                    "less ambiguous way to reassure someone.",
        "watch": "The よ on the end is what makes it reassurance rather "
                 "than just an answer.",
    },
]

GRAMMAR[3] = [
    {
        "point": "〜が分かります",
        "en": "understand; know (a language)",
        "formula": "N + が + 分かります / 分かりません",
        "examples": [
            ("日本語がわかりますか。", "にほんごがわかりますか。",
             "Do you understand Japanese?"),
            ("すみません、よくわかりません。", "すみません、よくわかりません。",
             "Sorry, I don't really understand."),
        ],
        "contrast": "分かる is one of a small group of verbs that take が "
                    "rather than を for what you understand - the same "
                    "family as できます、あります、好きです. をわかります is a mistake "
                    "beginners make constantly. With は instead - "
                    "日本語はわかります - you get 'Japanese I understand (but "
                    "maybe not the rest)'.",
        "watch": "わかる is usually written in hiragana. 分かりました means 'I "
                 "see / understood', and it answers an explanation, not a "
                 "question.",
    },
    {
        "point": "よく / 少し / あまり",
        "en": "well / a little / not very",
        "formula": "adverb + verb (あまり + negative)",
        "examples": [
            ("はい、少しわかります。", "はい、すこしわかります。", "Yes, a little."),
            ("あまりわかりません。", "あまりわかりません。", "I don't understand much."),
        ],
        "contrast": "少し and よく both go with a positive verb; あまり is the "
                    "odd one out and expects a negative on the end - "
                    "あまりわかりません, never あまりわかります. English 'I don't "
                    "understand very well' maps onto あまり rather than onto "
                    "全然 (which is 'not at all').",
    },
    {
        "point": "〜で話しましょう",
        "en": "let's speak in …",
        "formula": "N + で + V-ましょう",
        "examples": [
            ("じゃあ、英語で話しましょう。", "じゃあ、えいごではなしましょう。",
             "Then let's speak English."),
            ("日本語で話しましょう。", "にほんごではなしましょう。",
             "Let's speak Japanese."),
        ],
        "contrast": "で after a language or a tool is 'by means of': 英語で、"
                    "ペンで、箸で. It is not the で of place - 駅で話します would be "
                    "'speak at the station'. ましょう is 'let's', the inclusive "
                    "suggestion; ませんか ('won't you?') invites instead.",
    },
]

GRAMMAR[4] = [
    {
        "point": "初めまして / よろしくお願いします",
        "en": "how do you do / pleased to meet you",
        "formula": "fixed introduction pair",
        "examples": [
            ("初めまして。", "はじめまして。", "How do you do."),
            ("マイクです。よろしくお願いします。", "マイクです。よろしくおねがいします。",
             "I'm Mike. Pleased to meet you."),
        ],
        "contrast": "よろしくお願いします has no single English equivalent: it is "
                    "the politeness that closes an introduction and opens "
                    "the relationship - roughly 'I look forward to dealing "
                    "with you'. It also ends requests (よろしくお願いします = 'I "
                    "leave it in your hands'), which is why it appears at "
                    "the end of emails too.",
        "watch": "Say your name with です, not といいます, at this level: "
                 "マイクです.",
    },
    {
        "point": "〜はどこですか",
        "en": "where is …?",
        "formula": "N + は + どこですか → N です",
        "examples": [
            ("出身はどこですか。", "しゅっしんはどこですか。", "Where are you from?"),
            ("アメリカです。", "アメリカです。", "America."),
        ],
        "contrast": "どこ asks for a place and the answer is just the place "
                    "plus です - you do not need a verb. どちら is the polite "
                    "version of どこ and is what you will hear in a shop or a "
                    "hotel: お出身はどちらですか.",
        "watch": "は marks what you are asking about. Replace it with が "
                 "(どこが) and you are asking which place, out of several, is "
                 "the one.",
    },
    {
        "point": "あなたは？ / そうですか",
        "en": "and you? / I see",
        "formula": "N + は？ / そうですか",
        "examples": [
            ("アメリカです。あなたは？", "アメリカです。あなたは？", "America. And you?"),
            ("そうですか。", "そうですか。", "I see."),
        ],
        "contrast": "Dropping the verb and leaving は？ turns a question "
                    "around in one syllable - あなたは？ is 'and you?'. そうです"
                    "か is the listener's 'I see', and with a falling "
                    "intonation it simply acknowledges; with a rising one it "
                    "expresses surprise.",
        "watch": "あなた is not as everyday as English 'you' - between people "
                 "who know each other's names, use the name plus さん.",
    },
]

GRAMMAR[5] = [
    {
        "point": "これ / それ / あれ",
        "en": "this / that / that over there",
        "formula": "これ・それ・あれ + は / を",
        "examples": [
            ("これはいくらですか。", "これはいくらですか。", "How much is this?"),
            ("これは千円です。", "これはせんえんです。", "This one is a thousand yen."),
        ],
        "contrast": "The こ・そ・あ row is about distance from the two people "
                    "talking: これ is near me, それ is near you, あれ is near "
                    "neither. It is not 'this' versus 'that' in the English "
                    "sense - a thing in your hand is それ to me even though "
                    "you would call it これ.",
        "watch": "For more than one thing: これら、それら. Before a noun, この、"
                 "その、あの - この本, not これ本.",
    },
    {
        "point": "〜はいくらですか",
        "en": "how much is …?",
        "formula": "N + は + いくらですか → number + 円です",
        "examples": [
            ("すみません、これはいくらですか。", "すみません、これはいくらですか。",
             "Excuse me, how much is this?"),
            ("三千円です。", "さんぜんえんです。", "Three thousand yen."),
        ],
        "contrast": "いくら asks for an amount of money; いくつ asks for a "
                    "number of things; 何時 asks for a time. All three are "
                    "'how much / how many' split by category, and each "
                    "answers with a bare number plus です.",
        "watch": "円 is read えん. Prices above ten thousand are counted in "
                 "万: 一万円 = いちまんえん.",
    },
    {
        "point": "〜をください",
        "en": "give me …; I'll take …",
        "formula": "N + を + ください",
        "examples": [
            ("じゃあ、これをください。", "じゃあ、これをください。", "Then I'll take this one."),
            ("お茶をください。", "おちゃをください。", "Tea please."),
        ],
        "contrast": "ください after a noun is 'give me that' - it is the "
                    "shopping word. お願いします after a noun is broader and "
                    "softer ('this one, please'), and it works for orders "
                    "that are not a simple handover.",
        "watch": "ください can also follow a て-form as an instruction "
                 "(待ってください = 'please wait') - unrelated to this use.",
    },
]

GRAMMAR[6] = [
    {
        "point": "〜はどこですか",
        "en": "where is …?",
        "formula": "N + は + どこですか → N です / N にあります",
        "examples": [
            ("すみません、トイレはどこですか。", "すみません、トイレはどこですか。",
             "Excuse me, where is the restroom?"),
            ("駅はあそこです。", "えきはあそこです。", "The station is over there."),
        ],
        "contrast": "Asking where something IS uses あります／います; asking "
                    "where something will HAPPEN uses で: パーティーはどこですか "
                    "asks the place, and どこでしますか asks where you will hold "
                    "it. With どこです you can answer with a place word alone "
                    "(あそこです), which is why it is the beginner's question.",
        "watch": "あそこ / そこ / ここ follow the same こ・そ・あ distance rule as "
                 "これ・それ・あれ.",
    },
    {
        "point": "〜て、〜（て形の接続）",
        "en": "do X and then Y; do X, and",
        "formula": "V-て、clause",
        "examples": [
            ("まっすぐ行って、左です。", "まっすぐいって、ひだりです。",
             "Go straight, it's on the left."),
            ("駅を出て、右へ行きます。", "えきをでて、みぎへいきます。",
             "Leave the station and go right."),
        ],
        "contrast": "The て-form is the glue of Japanese: it joins two "
                    "actions in order (出て、行く), and the tense falls on the "
                    "last verb only. から also puts things in order but "
                    "insists on 'after X, and only then Y'; て just strings "
                    "them together.",
        "watch": "Formation: 行く→行って, 乗る→乗って, 飲む→飲んで, "
                 "食べる→食べて. The て-form never changes for politeness.",
    },
    {
        "point": "遠いです / 近くです",
        "en": "it is far / it is close",
        "formula": "い-adjective + です / N + です",
        "examples": [
            ("遠いですか。", "とおいですか。", "Is it far?"),
            ("いいえ、近くです。", "いいえ、ちかくです。", "No, it's close."),
        ],
        "contrast": "遠い is an い-adjective and takes です directly; 近く is a "
                    "noun and needs です too, but its negative and its "
                    "adverb forms differ: 遠くないです (adjective) versus "
                    "近くではありません (noun). Listen for which one a word is "
                    "before you build a sentence on it.",
        "watch": "近い also exists as an adjective, but 近くです is the common "
                 "answer form.",
    },
]

GRAMMAR[7] = [
    {
        "point": "〜に行きたいです",
        "en": "I want to go to …",
        "formula": "place + に + 行きたいです",
        "examples": [
            ("空港に行きたいです。", "くうこうにいきたいです。",
             "I want to go to the airport."),
            ("日本に行きたいです。", "にほんにいきたいです。", "I want to go to Japan."),
        ],
        "contrast": "に marks the destination you are going TO; で marks the "
                    "place where the action happens. 空港に行きます is 'go to the "
                    "airport'; 空港で食べます is 'eat at the airport'. へ also "
                    "marks direction and is a little softer, but に is the "
                    "one for a stated destination.",
        "watch": "たい makes the verb into an い-adjective, so it conjugates "
                 "like one: 行きたいです、行きたくないです、行きたかったです.",
    },
    {
        "point": "〜に乗ります",
        "en": "take / get on (a vehicle)",
        "formula": "vehicle + に + 乗ります / を + 降ります",
        "examples": [
            ("じゃあ、電車に乗ります。", "じゃあ、でんしゃにのります。",
             "Then I'll take the train."),
            ("次の駅で降ります。", "つぎのえきでおります。",
             "I'll get off at the next station."),
        ],
        "contrast": "Getting on takes に (乗ります is a verb of arriving at a "
                    "surface), getting off takes を (降ります moves you off "
                    "it): 電車に乗る、電車を降りる. Beginners often use を for "
                    "both.",
        "watch": "バスに乗ります、タクシーに乗ります - the vehicle is に, the place "
                 "you do it is で: 駅で乗ります.",
    },
    {
        "point": "〜ですか、〜ですか",
        "en": "X or Y? (offering a choice)",
        "formula": "N + ですか、N + ですか",
        "examples": [
            ("タクシーですか、電車ですか。", "タクシーですか、でんしゃですか。",
             "Taxi or train?"),
            ("コーヒーですか、お茶ですか。", "コーヒーですか、おちゃですか。",
             "Coffee or tea?"),
        ],
        "contrast": "This is not a yes/no question - it is two questions "
                    "placed side by side, and the answer is simply the one "
                    "you want: 電車です. The later, fuller version is "
                    "どちらがいいですか ('which is better?'), used when the choice "
                    "is not a simple either/or.",
        "watch": "The first ですか rises in pitch, the second falls - the "
                 "whole thing is one question, not two.",
    },
]

GRAMMAR[8] = [
    {
        "point": "どうやって〜ますか",
        "en": "how do I …?",
        "formula": "どうやって + V-ますか",
        "examples": [
            ("空港へはどうやって行きますか。", "くうこうへはどうやっていきますか。",
             "How do I get to the airport?"),
            ("どうやって作りますか。", "どうやってつくりますか。", "How do you make it?"),
        ],
        "contrast": "どうやって asks for the METHOD ('by what means'); どう asks "
                    "for the manner or the state ('how is it?'). どうでしたか "
                    "after a trip means 'how was it?', not 'how did you get "
                    "there?'.",
        "watch": "The は in 空港へは is the topic marker added to へ - it sets "
                 "up 'as for getting to the airport'.",
    },
    {
        "point": "〜で（手段・交通）",
        "en": "by (means of transport or method)",
        "formula": "N + で + V",
        "examples": [
            ("地下鉄で二駅です。", "ちかてつでにえきです。", "Two stops by subway."),
            ("電車で行きます。", "でんしゃでいきます。", "I'll go by train."),
        ],
        "contrast": "で is the particle of means and of location-of-action, "
                    "and one sentence can hold both: 駅で電車で… is impossible, "
                    "but 駅で切符を買う (location) and 電車で行く (means) show the "
                    "two jobs apart. に marks where you end up; で marks what "
                    "you use on the way.",
        "watch": "Walking is 歩いて, not 歩きで - the て-form carries it.",
    },
    {
        "point": "〜てください",
        "en": "please do …",
        "formula": "V-て + ください",
        "examples": [
            ("三駅目で乗り換えてください。", "さんえきめでのりかえてください。",
             "Please change at the third stop."),
            ("まっすぐ行ってください。", "まっすぐいってください。", "Please go straight."),
        ],
        "contrast": "てください is the direct request - to a stranger, a child, "
                    "or in an instruction. てくださいませんか and ていただけますか are "
                    "the softer forms, and お〜ください (お持ちください) is the "
                    "polite form you see on signs.",
        "watch": "The negative is 〜ないでください, not 〜なくてください: "
                 "乗り換えないでください.",
    },
]

GRAMMAR[9] = [
    {
        "point": "〜まで",
        "en": "as far as; up to",
        "formula": "place / time + まで",
        "examples": [
            ("このホテルまでお願いします。", "このホテルまでおねがいします。",
             "To this hotel, please."),
            ("駅まで歩きます。", "えきまであるきます。", "I'll walk as far as the station."),
        ],
        "contrast": "まで is the endpoint, and it includes the endpoint - you "
                    "actually go there. までに is 'by (some time before then)' "
                    "and is about deadlines: 九時までに来ます = 'come by nine'. "
                    "Confusing the two is the commonest mistake with まで.",
        "watch": "With から it makes a range: 駅から空港まで = 'from the station "
                 "to the airport'.",
    },
    {
        "point": "〜てください（依頼）",
        "en": "please do …",
        "formula": "V-て + ください",
        "examples": [
            ("ここで止めてください。", "ここでとめてください。", "Please stop here."),
            ("荷物は後ろに置いてください。", "にもつはうしろにおいてください。",
             "Please put the luggage in the back."),
        ],
        "contrast": "止めます is transitive ('I stop it'), 止まります is "
                    "intransitive ('it stops'). With てください you are asking "
                    "the driver to stop the car, so it is 止めてください, not "
                    "止まってください - that one would mean 'please come to a halt "
                    "yourself'.",
        "watch": "The place of the action takes で: ここで止めてください.",
    },
    {
        "point": "〜くらい（およその量）",
        "en": "about; roughly",
        "formula": "amount / time + くらい（ぐらい）",
        "examples": [
            ("いいえ、十分くらいです。", "いいえ、じゅっぷんくらいです。",
             "No, about ten minutes."),
            ("二千円くらいです。", "にせんえんくらいです。", "It's about two thousand yen."),
        ],
        "contrast": "くらい is an approximation and leans low ('about ten "
                    "minutes, maybe less'); ごろ attaches only to points in "
                    "time (三時ごろ = 'around three') and cannot be used for "
                    "an amount. ぐらい is the same word with rendaku - both "
                    "are correct, くらい is more common after a number.",
        "watch": "It follows the number directly: 十分くらい, never くらい十分.",
    },
]

GRAMMAR[10] = [
    {
        "point": "〜で（動作の場所）",
        "en": "at / in (where the action happens)",
        "formula": "place + で + V",
        "examples": [
            ("切符はどこで買いますか。", "きっぷはどこでかいますか。",
             "Where do I buy a ticket?"),
            ("あの券売機で買ってください。", "あのけんばいきでかってください。",
             "Please buy one at that machine."),
        ],
        "contrast": "に is where something exists (駅にホームがあります); で is "
                    "where something happens (駅で買います). The same place takes "
                    "a different particle depending on the verb, which is "
                    "why 日本に買いました is wrong but 日本で買いました is right.",
        "watch": "With あります／います, always に or には - never で.",
    },
    {
        "point": "〜番（番号を聞く）",
        "en": "number … (asking which number)",
        "formula": "N + は + 何番ですか → number + 番 + N です",
        "examples": [
            ("ホームは何番ですか。", "ホームはなんばんですか。", "Which platform is it?"),
            ("三番ホームです。", "さんばんホームです。", "Platform three."),
        ],
        "contrast": "番 is the counter for things in a numbered order - "
                    "platforms, bus stops, sizes. 何番 asks 'which number' "
                    "rather than 'how many': 何番線 is 'which line', 何番目 is "
                    "'which one in the sequence'.",
        "watch": "三番 is read さんばん - the ん of 三 is a full syllable, so "
                 "it is three beats, not two.",
    },
    {
        "point": "〜は何時ですか",
        "en": "what time is …?",
        "formula": "N + は + 何時ですか → time + です",
        "examples": [
            ("次の電車は何時ですか。", "つぎのでんしゃはなんじですか。",
             "What time is the next train?"),
            ("十時五分です。", "じゅうじごふんです。", "Ten oh five."),
        ],
        "contrast": "何時 (なんじ) asks for the hour on the clock; 何時に (なんじ"
                    "に) asks at what time something happens - 何時に出ますか. The "
                    "に is the same time-particle you use in 五時に出ます.",
        "watch": "Minutes are 〜分: 五分 is ごふん, 十分 is じゅっぷん. Several of "
                 "them change their reading, so learn each as a word.",
    },
]

GRAMMAR[11] = [
    {
        "point": "おなかがすきました",
        "en": "I'm hungry",
        "formula": "N + が + すきました / すいています",
        "examples": [
            ("おなかがすきましたね。", "おなかがすきましたね。",
             "You're hungry, aren't you."),
            ("おなかがすきました。", "おなかがすきました。", "I'm hungry."),
        ],
        "contrast": "Japanese says 'my stomach has become empty', not 'I am "
                    "hungry' - the subject is おなか and it takes が. There is "
                    "no adjective meaning 'hungry', so 私はすきました is wrong: the "
                    "stomach is the subject.",
        "watch": "The state form おなかがすいています is more common than the "
                 "change-of-state すきました in answer to a question.",
    },
    {
        "point": "〜を食べます / 飲みます",
        "en": "eat / drink (something)",
        "formula": "N + を + 食べます / 飲みます",
        "examples": [
            ("何を食べますか。", "なにをたべますか。", "What shall we eat?"),
            ("ラーメンを食べます。", "ラーメンをたべます。", "I'll eat ramen."),
        ],
        "contrast": "を marks the thing the verb acts on, and it stays を no "
                    "matter what you are doing to it. が marks the subject "
                    "that does the acting, and を marks the object - "
                    "私はラーメンを食べます has both.",
        "watch": "何 before を is なに; before です it is なん - これは何ですか.",
    },
    {
        "point": "〜にあります",
        "en": "there is (at a place)",
        "formula": "place + に + N + があります / います",
        "examples": [
            ("ここにメニューがあります。", "ここにメニューがあります。",
             "There's a menu here."),
            ("駅の近くに店があります。", "えきのちかくにみせがあります。",
             "There's a shop near the station."),
        ],
        "contrast": "あります is for things that do not move; います is for "
                    "people and animals: メニューがあります but 店員がいます. "
                    "Beginners say 人があります and it is always wrong.",
        "watch": "The place takes に, and は replaces に when you want to "
                 "contrast: ここにはメニューがあります.",
    },
]

GRAMMAR[12] = [
    {
        "point": "〜をください / をお願いします",
        "en": "… please (ordering)",
        "formula": "N + を + ください / をお願いします",
        "examples": [
            ("お茶をください。", "おちゃをください。", "Tea please."),
            ("ラーメンをお願いします。", "ラーメンをおねがいします。", "Ramen please."),
        ],
        "contrast": "をください is literally 'give me' and is fine at a counter; "
                    "をお願いします is the softer, more general request and is the "
                    "one to use in a restaurant you are sitting down in. "
                    "Both take を for the thing you want.",
        "watch": "お茶を一つください uses 一つ as the counter for cups when you "
                 "have not learned 杯 yet.",
    },
    {
        "point": "〜くします / 〜くしないでください",
        "en": "make it … / please don't make it …",
        "formula": "い-adj stem + く + します / しないでください",
        "examples": [
            ("辛くしますか。", "からくしますか。", "Shall I make it spicy?"),
            ("いいえ、辛くしないでください。", "いいえ、からくしないでください。",
             "No, please don't make it spicy."),
        ],
        "contrast": "Remove the final い of an adjective and add く and you "
                    "have an adverb: 辛い → 辛く. Add する and it becomes 'make "
                    "it spicy'; add なる and it becomes 'become spicy'. The "
                    "する／なる pair is the whole of 'change' in Japanese.",
        "watch": "な-adjectives use に instead: きれいにします, 静かにしてください.",
    },
    {
        "point": "〜ないでください",
        "en": "please don't …",
        "formula": "V-ない + で + ください",
        "examples": [
            ("ここで食べないでください。", "ここでたべないでください。",
             "Please don't eat here."),
            ("まだ飲まないでください。", "まだのまないでください。",
             "Please don't drink it yet."),
        ],
        "contrast": "ないでください is the negative of てください, and the negative "
                    "goes on the verb before で, never on ください. くださいません "
                    "would be 'don't you want to give me?' - a different "
                    "sentence entirely.",
        "watch": "〜なくてください does not exist. The negative ない-form: "
                 "飲む→飲まない, 食べる→食べない, する→しない, 来る→来ない.",
    },
]

GRAMMAR[13] = [
    {
        "point": "〜かったです（い形容詞の過去）",
        "en": "it was … (past of an い-adjective)",
        "formula": "い-adj stem + かったです / くなかったです",
        "examples": [
            ("おいしかったです。", "おいしかったです。", "It was delicious."),
            ("高くなかったです。", "たかくなかったです。", "It wasn't expensive."),
        ],
        "contrast": "The past of an い-adjective is made on the adjective "
                    "itself: drop い, add かった (おいしい → おいしかった). The past "
                    "of a noun or a な-adjective is made on です: 元気でした, "
                    "雨でした. Beginners put でした on adjectives and it never "
                    "works.",
        "watch": "おいしい keeps its し: おいし + かった + です. Spelling it "
                 "おいかったです, dropping the し, is a common early error.",
    },
    {
        "point": "全部で",
        "en": "in total",
        "formula": "全部で + amount + です",
        "examples": [
            ("全部で二千五百円です。", "ぜんぶでにせんごひゃくえんです。",
             "That's two thousand five hundred yen in total."),
            ("全部で三人です。", "ぜんぶでさんにんです。", "Three people in total."),
        ],
        "contrast": "で here is the 'by this measure' で: it sets the unit you "
                    "are counting in. 全部 is 'all of it', so 全部で means "
                    "'counting everything'. みんなで is a different phrase - "
                    "'all of us together'.",
        "watch": "全部をください is 'give me all of them' - で rather than を is "
                 "what makes it a total.",
    },
    {
        "point": "〜えます（可能形）",
        "en": "can …; is it possible to …",
        "formula": "V-ます stem + えます (る-verbs) / V-え + ます (う-verbs)",
        "examples": [
            ("カードは使えますか。", "カードはつかえますか。", "Can I use a card?"),
            ("はい、使えます。", "はい、つかえます。", "Yes, you can."),
        ],
        "contrast": "The potential says the option exists; できます is the same "
                    "idea with a noun (カードができます) and is also the plain "
                    "'I can do it'. With 分かります and できます the object takes "
                    "が rather than を, so カードを使えます is common but "
                    "カードが使えます is the careful form.",
        "watch": "Formation: 使う→使える, 飲む→飲める, 食べる→食べられる, "
                 "見る→見られる. The shortened 食べれます is casual.",
    },
]

GRAMMAR[14] = [
    {
        "point": "〜ませんか（誘い）",
        "en": "won't you …? shall we …?",
        "formula": "V-ます stem + ませんか",
        "examples": [
            ("一緒に昼ごはんを食べに行きませんか。",
             "いっしょにひるごはんをたべにいきませんか。",
             "Shall we go for lunch together?"),
            ("あした、映画を見ませんか。", "あした、えいがをみませんか。",
             "Would you like to see a film tomorrow?"),
        ],
        "contrast": "ませんか INVITES - it asks the other person to join you. "
                    "ましょう (行きましょう) is 'let's', and it assumes the answer "
                    "is yes. When the plan depends on them, ませんか is the "
                    "safer of the two.",
        "watch": "The answer is いいですね (that sounds good) or すみません、ちょっと "
                 "(sorry, that's difficult) - a soft refusal without a "
                 "reason is normal.",
    },
    {
        "point": "〜に行きます（目的）",
        "en": "go to (do something)",
        "formula": "V-ます stem / verbal noun + に + 行きます",
        "examples": [
            ("昼ごはんを食べに行きます。", "ひるごはんをたべにいきます。",
             "I'm going to eat lunch."),
            ("駅に切符を買いに行きます。", "えきにきっぷをかいにいきます。",
             "I'm going to the station to buy a ticket."),
        ],
        "contrast": "に between two verbs is purpose: the second verb is the "
                    "journey and the first is the errand. て行きます is different "
                    "- 食べて行きます means 'eat and then go', two separate "
                    "events in order.",
        "watch": "With a verbal noun you can drop を: 買い物に行きます, "
                 "散歩に行きます.",
    },
    {
        "point": "〜はどうですか（提案）",
        "en": "how about …?",
        "formula": "N / time + は + どうですか",
        "examples": [
            ("十二時はどうですか。", "じゅうにじはどうですか。", "How about twelve?"),
            ("あしたはどうですか。", "あしたはどうですか。", "How about tomorrow?"),
        ],
        "contrast": "どうですか asks for an opinion on a suggestion; いかがです"
                    "か is the same question one register up, and is what a "
                    "shop assistant says. どうしますか is 'what shall we do?' - "
                    "it asks for the plan, not for a reaction to one.",
        "watch": "The は marks the proposal as the topic: replace it with が "
                 "and you are asking which one is good.",
    },
]

GRAMMAR[15] = [
    {
        "point": "〜と（並べる）",
        "en": "and (joining things, complete list)",
        "formula": "N + と + N",
        "examples": [
            ("餃子とお水をお願いします。", "ぎょうざとおみずをおねがいします。",
             "Dumplings and water please."),
            ("父と母がいます。", "ちちとははがいます。", "My father and mother are here."),
        ],
        "contrast": "と joins a COMPLETE list - everything you mean. や joins "
                    "a sample ('things like A and B') and is vaguer: "
                    "餃子やお水を注文しました suggests there was more too. For long "
                    "lists of actions, use the て-form instead (食べて、飲んで、"
                    "帰りました).",
        "watch": "と is also 'with' (友達と行きます) and the quote marker "
                 "(と思います) - context tells you which.",
    },
    {
        "point": "お〜ください（丁寧な依頼）",
        "en": "please … (polite request)",
        "formula": "お + V-ます stem + ください",
        "examples": [
            ("少々お待ちください。", "しょうしょうおまちください。",
             "One moment please."),
            ("こちらへお入りください。", "こちらへおはいりください。",
             "Please come in this way."),
        ],
        "contrast": "お〜ください is the shop and notice-board form: politer "
                    "than 待ってください, shorter than お待ちになってください. You will "
                    "hear it everywhere as a customer, and you use it in "
                    "signs and formal writing rather than to a friend.",
        "watch": "ご〜ください with Chinese-derived nouns: ご利用ください, 注意して"
                 "ご覧ください.",
    },
    {
        "point": "〜名さまですか",
        "en": "how many people?",
        "formula": "N + は + 何名さまですか → number + 名です",
        "examples": [
            ("何名さまですか。", "なんめいさまですか。", "How many are you?"),
            ("二人です。", "ふたりです。", "Two."),
        ],
        "contrast": "The お／さま wrapping is shop politeness aimed at the "
                    "customer: you ask 何名さまですか, and about your own group "
                    "you answer plainly 二人です. Counters for people: 一人、"
                    "二人、三人 - the first two are irregular.",
        "watch": "With 何 the reading changes: 何名 is なんめい, 何人 is なんにん.",
    },
]

GRAMMAR[16] = [
    {
        "point": "〜てもいいですか",
        "en": "may I …?",
        "formula": "V-て + も + いいですか",
        "examples": [
            ("着てみてもいいですか。", "きてみてもいいですか。",
             "May I try this on?"),
            ("ここに座ってもいいですか。", "ここにすわってもいいですか。",
             "May I sit here?"),
        ],
        "contrast": "てもいいですか asks permission for YOU to act; てください "
                    "asks the other person to act. The answer is はい、どうぞ "
                    "('go ahead') or すみません、ちょっと. For a softer version, "
                    "てもいいでしょうか.",
        "watch": "The negative permission - 'may I not…?' - is 〜なくてもいいです"
                 "か, and 'you need not' is 〜なくてもいいです.",
    },
    {
        "point": "〜てみる",
        "en": "try doing (and see)",
        "formula": "V-て + みる",
        "examples": [
            ("着てみます。", "きてみます。", "I'll try it on."),
            ("食べてみてください。", "たべてみてください。", "Please try eating it."),
        ],
        "contrast": "てみる is doing something once to find out what it is "
                    "like: 着てみる = 'try on (and see if it fits)'. してみる "
                    "without a verb is meaningless; する alone is just 'do'. "
                    "着てみる covers anything you wear on the body - a coat, a "
                    "hat, shoes.",
        "watch": "てみます, not てみります - みる conjugates normally: みて、みます、"
                 "みた.",
    },
    {
        "point": "〜はありますか",
        "en": "do you have …?",
        "formula": "N + は / が + ありますか",
        "examples": [
            ("小さいサイズはありますか。", "ちいさいサイズはありますか。",
             "Do you have a smaller size?"),
            ("ほかの色はありますか。", "ほかのいろはありますか。",
             "Do you have other colours?"),
        ],
        "contrast": "ありますか asks whether the thing exists at all; あります、"
                    "どこですか asks where it is once you know it does. With は "
                    "you are singling this item out from the others on the "
                    "shelf, which is why shop Japanese uses は rather than が "
                    "here.",
        "watch": "The answer is はい、あります / すみません、ありません.",
    },
]

GRAMMAR[17] = [
    {
        "point": "〜くなりませんか / 〜くなります",
        "en": "can you make it …? / it becomes …",
        "formula": "い-adj stem + く + なりませんか / なります",
        "examples": [
            ("少し高いですね。安くなりませんか。",
             "すこしたかいですね。やすくなりませんか。",
             "A bit expensive. Can you make it cheaper?"),
            ("だんだん安くなりました。", "だんだんやすくなりました。",
             "It gradually got cheaper."),
        ],
        "contrast": "なる is change that happens by itself; する is change "
                    "someone makes. 安くなる = 'it gets cheaper' (the market "
                    "did it); 安くする = 'I make it cheaper' (the shop did it). "
                    "Asking a shopkeeper 安くなりませんか politely puts the change "
                    "on the price rather than on the person.",
        "watch": "な-adjectives use に: 便利になります, 静かになります.",
    },
    {
        "point": "もう少し",
        "en": "a bit more",
        "formula": "もう少し + adjective / verb",
        "examples": [
            ("もう少し負けてください。", "もうすこしまけてください。",
             "Please take a bit more off."),
            ("もう少し安いのはありませんか。", "もうすこしやすいのはありませんか。",
             "Isn't there anything a bit cheaper?"),
        ],
        "contrast": "少し is 'a little'; もう少し is 'a little MORE' - it "
                    "presupposes some has already happened, which is why it "
                    "is the natural word in a negotiation. もっと is the "
                    "plainer 'more' and can sound blunter.",
        "watch": "もう also means 'already' (もう食べました). Before a quantity it "
                 "is 'another; further'.",
    },
    {
        "point": "〜で（値段・条件）",
        "en": "for (a price); with (a condition)",
        "formula": "amount + で",
        "examples": [
            ("じゃあ、九千円で。", "じゃあ、きゅうせんえんで。", "Then nine thousand."),
            ("二つで千円です。", "ふたつでせんえんです。", "A thousand yen for two."),
        ],
        "contrast": "で after a price sets the terms the deal closes on: "
                    "九千円で（お願いします）. This is the same で as the means-particle "
                    "in カードで払います - roughly 'with/by this'. に after a price "
                    "would be 'at' in the sense of a rate, and is used for "
                    "exchange and tax.",
        "watch": "Trailing で is normal in shops - the rest of the sentence "
                 "is understood.",
    },
]

GRAMMAR[18] = [
    {
        "point": "〜はありますか / 売り切れです",
        "en": "do you have …? / it's sold out",
        "formula": "N + は + ありますか → あります / 売り切れです",
        "examples": [
            ("充電器はありますか。", "じゅうでんきはありますか。",
             "Do you have chargers?"),
            ("すみません、売り切れです。", "すみません、うりきれです。",
             "Sorry, sold out."),
        ],
        "contrast": "ありません says the thing is not here; 売り切れです says it "
                    "was here and has gone. ありません can mean 'we never stock "
                    "them', so 売り切れ is the word that tells you to come "
                    "back later.",
        "watch": "切れ comes from 切れる ('be cut off / run out'), so the same "
                 "shape appears in 品切れ (out of stock) and 電池切れ (flat "
                 "battery).",
    },
    {
        "point": "いつ",
        "en": "when",
        "formula": "いつ + V-ますか / N です",
        "examples": [
            ("いつ入荷しますか。", "いつにゅうかしますか。", "When will you get more?"),
            ("あしたの午後です。", "あしたのごごです。", "Tomorrow afternoon."),
        ],
        "contrast": "いつ asks for a point or period in time and is answered "
                    "with a time word plus です. 何時 is only for clock times. "
                    "With に - いつにしますか - you are asking which time to "
                    "choose from a set.",
        "watch": "Time words like あした、今日、毎週 take no に when used on their "
                 "own: あした行きます, not あしたに行きます.",
    },
    {
        "point": "また来ます",
        "en": "I'll come back / again",
        "formula": "また + V",
        "examples": [
            ("また来ます。", "またきます。", "I'll come back."),
            ("またあした。", "またあした。", "See you tomorrow."),
        ],
        "contrast": "また is 'again, another time'; まだ is 'not yet'. They "
                    "sound almost identical to an English ear and mean "
                    "opposite things - また来ます (I'll come again) versus まだ"
                    "来ません (hasn't come yet).",
        "watch": "まだ来ていません is 'still hasn't arrived'; また来ていません is not "
                 "a sentence.",
    },
]

GRAMMAR[19] = [
    {
        "point": "〜で払います",
        "en": "pay by (card, cash)",
        "formula": "N + で + 払います",
        "examples": [
            ("カードで払ってもいいですか。", "カードではらってもいいですか。",
             "May I pay by card?"),
            ("現金で払います。", "げんきんではらいます。", "I'll pay in cash."),
        ],
        "contrast": "で marks the means: カードで、現金で、スマホで. を marks the "
                    "thing being handed over: お金を払います. So カードで払います is "
                    "'pay with a card' and カードを払います would be 'pay the card' "
                    "- which is what beginners say by mistake.",
        "watch": "The shop's own question is お支払いはどうなさいますか or simply "
                 "現金ですか、カードですか.",
    },
    {
        "point": "〜は要ります / 要りません",
        "en": "need / don't need",
        "formula": "N + は / が + 要ります / 要りません",
        "examples": [
            ("袋は要りません。", "ふくろはいりません。", "I don't need a bag."),
            ("お箸は要りますか。", "おはしはいりますか。", "Do you need chopsticks?"),
        ],
        "contrast": "要ります is a plain 'is needed', and with は it says 'as "
                    "for that item - no'. いらない is the casual version and "
                    "sounds abrupt to a shop assistant; 要りません and いいです are "
                    "the polite refusals.",
        "watch": "It is an intransitive verb, so the thing needed takes が or "
                 "は, never を.",
    },
    {
        "point": "〜へどうぞ",
        "en": "this way please; go ahead",
        "formula": "place + へ + どうぞ",
        "examples": [
            ("はい、レジへどうぞ。", "はい、レジへどうぞ。",
             "Yes, please come to the till."),
            ("こちらへどうぞ。", "こちらへどうぞ。", "This way, please."),
        ],
        "contrast": "へ marks direction and is slightly softer and more "
                    "inviting than に, which is why it is the particle of "
                    "signs and ushering: こちらへどうぞ、二階へどうぞ. で would be "
                    "'do it at' and would not move anyone.",
        "watch": "へ is pronounced 'e', never 'he', when it is a particle.",
    },
]

GRAMMAR[20] = [
    {
        "point": "〜ますか（動詞の疑問）",
        "en": "shall I …? do you …? (verb question)",
        "formula": "N + を + V-ますか",
        "examples": [
            ("温めますか。", "あたためますか。", "Shall I heat it up?"),
            ("これをお願いします。", "これをおねがいします。", "This one please."),
        ],
        "contrast": "ますか on a verb is either a plain question ('do you?') "
                    "or, said by shop staff, an offer ('shall I?'). The "
                    "answer to an offer is はい、お願いします or いいえ、大丈夫です. "
                    "Adding か to ます rather than to the dictionary form is "
                    "what makes the polite question.",
        "watch": "ますか is not ましょう: 温めましょう would be 'let's heat it', "
                 "which is not the assistant's question.",
    },
    {
        "point": "〜は要りますか / ください",
        "en": "do you need …? / please give me",
        "formula": "N + は + 要りますか → ください / 大丈夫です",
        "examples": [
            ("お箸は要りますか。", "おはしはいりますか。", "Do you need chopsticks?"),
            ("はい、ください。", "はい、ください。", "Yes please."),
        ],
        "contrast": "ください is the one-word 'yes please' at a counter, "
                    "shorter than お願いします and aimed at the thing being handed "
                    "over. To decline, 大丈夫です is more natural than 要りません, "
                    "which can sound like a firm statement.",
        "watch": "ください cannot be used about yourself wanting something in "
                 "the abstract - 水がください is wrong, 水をください is right.",
    },
    {
        "point": "全部でいくらですか",
        "en": "how much is it all together?",
        "formula": "全部で + いくらですか → amount + です",
        "examples": [
            ("全部でいくらですか。", "ぜんぶでいくらですか。", "How much is it in total?"),
            ("六百八十円です。", "ろっぴゃくはちじゅうえんです。",
             "Six hundred and eighty yen."),
        ],
        "contrast": "いくらですか asks for the price of one thing; 全部でいくら"
                    "ですか asks for the total after several. 全部で also works in "
                    "the answer, not just the question: 全部で六百八十円です.",
        "watch": "Number readings change with the counter: 六百 is ろっぴゃく, "
                 "六時 is ろくじ. Learn them as you meet them.",
    },
]

GRAMMAR[21] = [
    {
        "point": "今何時ですか / 〜時です",
        "en": "what time is it? / it is … o'clock",
        "formula": "今 + 何時ですか → time + です",
        "examples": [
            ("すみません、今何時ですか。", "すみません、いまなんじですか。",
             "Excuse me, what time is it now?"),
            ("三時半です。", "さんじはんです。", "Half past three."),
        ],
        "contrast": "何時 is なんじ, but 何時でも ('any time') and 何時に ('at what "
                    "time') follow the same reading. The hour itself uses じ: "
                    "三時、五時、九時. English 'o'clock' has no equivalent word - "
                    "the 時 carries it.",
        "watch": "四時 is よじ, not しじ; 七時 is しちじ (くじ is 九時). The four and "
                 "seven readings are the ones that trip people up.",
    },
    {
        "point": "半（〜時半）",
        "en": "half past",
        "formula": "hour + 時 + 半",
        "examples": [
            ("三時半です。", "さんじはんです。", "It's half past three."),
            ("七時半に会いましょう。", "しちじはんにあいましょう。",
             "Let's meet at half past seven."),
        ],
        "contrast": "半 is 'half' and it goes after 時, so 三時半 is 3:30 - "
                    "Japanese counts forward from the hour rather than "
                    "towards the next one. Minutes otherwise use 分: 三分 "
                    "(さんぷん), 十分 (じゅっぷん), 十五分 (じゅうごふん).",
        "watch": "There is no 'quarter past' - it is 十五分過ぎ if you want to "
                 "be precise, but most people say 十五分.",
    },
    {
        "point": "〜に出ます / 来ます（時のに）",
        "en": "leave / come at (a time)",
        "formula": "time + に + V",
        "examples": [
            ("五時に出ます。", "ごじにでます。", "I'm leaving at five."),
            ("六時に来ます。", "ろくじにきます。", "I'll come at six."),
        ],
        "contrast": "に after a clock time marks the moment the action lands "
                    "on: 五時に出ます. Relative words - あした、今日、毎朝 - take no "
                    "に. ごろ ('around') replaces に when you are being vague: "
                    "五時ごろ出ます.",
        "watch": "に never attaches to 今: 今出ます, not 今に出ます.",
    },
]

GRAMMAR[22] = [
    {
        "point": "今日 / 明日 / 昨日",
        "en": "today / tomorrow / yesterday",
        "formula": "time word (+ は) + clause",
        "examples": [
            ("明日、都合はどうですか。", "あした、つごうはどうですか。",
             "How's tomorrow for you?"),
            ("昨日は暇でした。", "きのうはひまでした。", "I was free yesterday."),
        ],
        "contrast": "今日 is きょう, 明日 is あした, 昨日 is きのう - all three are "
                    "irregular and are learned as words, not from the kanji. "
                    "They take no に on their own (あした会いましょう), though に "
                    "returns with a clock time (あした三時に).",
        "watch": "明日 is also read あす in news and formal speech; あした is the "
                 "everyday word.",
    },
    {
        "point": "〜はちょっと（やわらかい断り）",
        "en": "X is a bit difficult (soft refusal)",
        "formula": "N + は + ちょっと",
        "examples": [
            ("明日はちょっと。", "あしたはちょっと。", "Tomorrow's difficult."),
            ("その日はちょっと…。", "そのひはちょっと…。", "That day is a bit…"),
        ],
        "contrast": "ちょっと trails off and leaves the refusal unsaid, which "
                    "is exactly why it works: 明日はだめです states a rejection, "
                    "明日はちょっと hints at one and lets the other person "
                    "propose again. Trailing が and けど do the same job for "
                    "verbs.",
        "watch": "ちょっと also means 'a little' (ちょっと高いです) and 'excuse me' "
                 "(ちょっとすみません).",
    },
    {
        "point": "〜に会いましょう",
        "en": "let's meet at / on",
        "formula": "time / day + に + 会いましょう",
        "examples": [
            ("三時に会いましょう。", "さんじにあいましょう。", "Let's meet at three."),
            ("土曜日に会いましょう。", "どようびにあいましょう。", "Let's meet on Saturday."),
        ],
        "contrast": "ましょう is 'let's' - a proposal including the listener. "
                    "ませんか invites and waits for agreement; ましょう assumes "
                    "it. Days of the week take に optionally (土曜日に／土曜日), "
                    "clock times always take it.",
        "watch": "The negative proposal is 会いませんか ('shall we not meet?'), "
                 "never 会いましょうか in this sense - that one asks 'shall I?'.",
    },
]

GRAMMAR[23] = [
    {
        "point": "〜ました（丁寧な過去）",
        "en": "did; was (polite past)",
        "formula": "V-ます stem + ました / ませんでした",
        "examples": [
            ("ごめんなさい、遅れました。", "ごめんなさい、おくれました。",
             "Sorry, I'm late."),
            ("駅に着きました。", "えきにつきました。", "I arrived at the station."),
        ],
        "contrast": "ました is the polite past; でした is the past of です and of "
                    "な-adjectives and nouns. 遅れました is a verb, 暇でした is a "
                    "noun - the two never swap. The polite negative past is "
                    "ませんでした (遅れませんでした), not ませんです.",
        "watch": "遅れました literally means 'I have become late', so it is the "
                 "form for an apology; 遅刻しました is the plainer statement.",
    },
    {
        "point": "すぐ / だけ",
        "en": "right away / only",
        "formula": "すぐ + V / N + だけ",
        "examples": [
            ("すぐ行きます。", "すぐいきます。", "I'm coming right away."),
            ("五分だけ待ちます。", "ごふんだけまちます。", "I'll wait just five minutes."),
        ],
        "contrast": "すぐ is immediacy ('at once'); だけ is limitation ('only "
                    "this much'). しか does the same job as だけ but forces a "
                    "negative verb: 五分しか待ちません = 'I'll only wait five "
                    "minutes'.",
        "watch": "だけ replaces を and が rather than following them: これだけ, "
                 "not これをだけ.",
    },
    {
        "point": "〜てください（待ってください）",
        "en": "please wait",
        "formula": "V-て + ください",
        "examples": [
            ("少し待ってください。", "すこしまってください。", "Please wait a moment."),
            ("ここで待っていてください。", "ここでまっていてください。",
             "Please wait here."),
        ],
        "contrast": "待ってください is 'wait' as a single instruction; 待っていて"
                    "ください is 'keep waiting' - the います adds the continuing "
                    "state. When you are asking someone to hold on while you "
                    "hurry, the second is the natural one.",
        "watch": "On the phone, 少々お待ちください is the polite form; 待って is "
                 "abrupt outside a family.",
    },
]

GRAMMAR[24] = [
    {
        "point": "〜と思います",
        "en": "I think that …",
        "formula": "plain form + と思います",
        "examples": [
            ("とてもおいしいと思います。", "とてもおいしいとおもいます。",
             "I think it's very good."),
            ("あしたは雨だと思います。", "あしたはあめだとおもいます。",
             "I think it will rain tomorrow."),
        ],
        "contrast": "The clause before と is in the PLAIN form, not the ます "
                    "form - おいしいですと思います is wrong twice over. The politeness "
                    "of the sentence sits on 思います alone. と思っています is 'I have "
                    "been thinking', and it sounds more considered.",
        "watch": "For 'I don't think X', Japanese negates the main verb: "
                 "おいしいとは思いません, not おいしくないと思います.",
    },
    {
        "point": "〜から（理由）",
        "en": "because",
        "formula": "clause + から、clause",
        "examples": [
            ("辛すぎるからです。", "からすぎるからです。", "Because they're too spicy."),
            ("高いから、買いません。", "たかいから、かいません。",
             "It's expensive, so I won't buy it."),
        ],
        "contrast": "から gives your reason and states it plainly; ので presents "
                    "it more softly and is the one to use when the reason is "
                    "an apology or a request. どうしてですか asks 'why' and the "
                    "answer comes with からです on the end - the です is what turns "
                    "a reason into a sentence.",
        "watch": "からです after a plain clause needs nothing in between for "
                 "な-adjectives: 便利だからです.",
    },
    {
        "point": "〜が好きです / 〜は好きじゃありません",
        "en": "like / don't like",
        "formula": "N + が + 好きです / N + は + 好きじゃありません",
        "examples": [
            ("ラーメンが好きです。", "ラーメンがすきです。", "I like ramen."),
            ("辛いのは好きじゃありません。", "からいのはすきじゃありません。",
             "I don't like spicy things."),
        ],
        "contrast": "好き is a な-adjective, so the thing liked takes が: "
                    "ラーメンが好きです. Switching が to は marks a contrast - "
                    "ラーメンは好きです means 'ramen I like (but not everything)'. "
                    "The negative is 好きじゃありません or 好きではありません, or "
                    "casually 好きじゃないです.",
        "watch": "The の in 辛いのは turns the adjective into a thing: 'spicy "
                 "things'. Without it, 辛いは好きじゃありません is not a sentence.",
    },
]

GRAMMAR[25] = [
    {
        "point": "〜に住んでいます",
        "en": "live in / at",
        "formula": "place + に + 住んでいます",
        "examples": [
            ("今どこに住んでいますか。", "いまどこにすんでいますか。",
             "Where do you live now?"),
            ("ホテルに住んでいます。", "ホテルにすんでいます。",
             "I'm staying at a hotel."),
        ],
        "contrast": "住む is a verb of existing somewhere, so the place takes "
                    "に, not で. ホテルで住んでいます would be 'do the living at the "
                    "hotel', which is not what anyone means. The います form "
                    "is used because living somewhere is a continuing state, "
                    "not a repeated event.",
        "watch": "For a short stay, 泊まっています ('I'm staying') is more "
                 "accurate than 住んでいます, which implies a home.",
    },
    {
        "point": "〜ています（継続）",
        "en": "am doing; have been doing",
        "formula": "V-て + います",
        "examples": [
            ("日本語を勉強しています。", "にほんごをべんきょうしています。",
             "I'm studying Japanese."),
            ("大阪に住んでいます。", "おおさかにすんでいます。", "I live in Osaka."),
        ],
        "contrast": "ています covers three things English splits: an action in "
                    "progress (食べています = 'I'm eating'), a continuing state "
                    "(住んでいます = 'I live'), and a habit or a result that "
                    "persists (結婚しています = 'I'm married'). ます alone is future "
                    "or habit, never 'right now'.",
        "watch": "知っています is 'I know it' (a state), not 'I am finding out' "
                 "- that is 知りました.",
    },
    {
        "point": "まだ / まだまだです",
        "en": "not yet; far from it",
        "formula": "まだ + negative / まだ + affirmative",
        "examples": [
            ("まだ上手じゃありません。", "まだじょうずじゃありません。",
             "I'm not good yet."),
            ("いいえ、まだまだです。", "いいえ、まだまだです。", "No, not yet."),
        ],
        "contrast": "まだ with a negative is 'not yet'; まだ with an "
                    "affirmative is 'still' (まだ勉強しています = 'still "
                    "studying'). まだまだです is the fixed way to deflect a "
                    "compliment - accepting one outright sounds arrogant in "
                    "Japanese, and the ritual reply is to deny it twice.",
        "watch": "もう ('already') is the opposite: もう食べました = 'I've eaten "
                 "already'.",
    },
]

GRAMMAR[26] = [
    {
        "point": "〜に起きます / 寝ます",
        "en": "get up / go to bed at",
        "formula": "time + に + V",
        "examples": [
            ("七時に起きます。", "しちじにおきます。", "I get up at seven."),
            ("十二時ごろ寝ます。", "じゅうにじごろねます。", "I go to bed around midnight."),
        ],
        "contrast": "に after a clock time pins the action to a moment; "
                    "ごろ ('around') replaces it when you are being vague - "
                    "you cannot have both に and ごろ. 毎朝 ('every morning') "
                    "sets the frequency and takes no particle at all.",
        "watch": "七時 is しちじ; 四時 is よじ. Both are irregular enough to be "
                 "learned as words.",
    },
    {
        "point": "ごろ / ぐらい",
        "en": "around (a time) / about (an amount)",
        "formula": "time + ごろ / amount + ぐらい（くらい）",
        "examples": [
            ("十二時ごろ寝ます。", "じゅうにじごろねます。", "I go to bed around midnight."),
            ("三十分ぐらいかかります。", "さんじっぷんぐらいかかります。",
             "It takes about thirty minutes."),
        ],
        "contrast": "ごろ attaches only to a point in time (三時ごろ); ぐらい "
                    "attaches to an amount or a duration (三十分ぐらい、千円ぐらい). "
                    "They look like the same word because they are - ごろ is the "
                    "time-only use of it.",
        "watch": "Neither takes に after it: 三時ごろに is wrong.",
    },
    {
        "point": "〜からです（始まり）",
        "en": "starts at / from",
        "formula": "time / place + から",
        "examples": [
            ("会社は九時からです。", "かいしゃはくじからです。", "Work starts at nine."),
            ("駅から歩きます。", "えきからあるきます。", "I'll walk from the station."),
        ],
        "contrast": "から is the starting point in time or in space, and it "
                    "pairs with まで for the end: 九時から五時まで. The other から - "
                    "'because' - comes at the END of a clause instead: "
                    "高いから買いません.",
        "watch": "からです at the end of a sentence is usually the reason "
                 "'it's because…', not a starting point.",
    },
]

GRAMMAR[27] = [
    {
        "point": "〜がします（誰が）",
        "en": "I do it (が marks the doer)",
        "formula": "person + が + V",
        "examples": [
            ("私がします。", "わたしがします。", "I'll do it."),
            ("誰が掃除しますか。", "だれがそうじしますか。", "Who does the cleaning?"),
        ],
        "contrast": "は presents the topic ('as for me, I do it'); が picks "
                    "out who, and it is the particle of the answer to 誰が. "
                    "私はします sounds like 'I do it (and maybe others don't / "
                    "others do something else)' - が is the plain selection.",
        "watch": "Question words take が, never は: 誰が、何が、どれが.",
    },
    {
        "point": "あまり〜ないです",
        "en": "not very …",
        "formula": "あまり + い-adj stem + くないです / な-adj + じゃありません",
        "examples": [
            ("あまり広くないです。", "あまりひろくないです。", "It isn't very big."),
            ("あまり好きじゃありません。", "あまりすきじゃありません。",
             "I don't like it very much."),
        ],
        "contrast": "あまり expects a negative on the end of the sentence - "
                    "あまり広いです is not Japanese. とても is the opposite and "
                    "expects a positive: とても広いです. English 'not very' and "
                    "'very' are one word apart here but the whole sentence "
                    "changes shape.",
        "watch": "全然 is stronger - 'not at all': 全然広くないです.",
    },
    {
        "point": "〜も（〜も）",
        "en": "also; too",
        "formula": "N + も (replaces を / が)",
        "examples": [
            ("週末に洗濯もします。", "しゅうまつにせんたくもします。",
             "I also do laundry at the weekend."),
            ("私も行きます。", "わたしもいきます。", "I'm going too."),
        ],
        "contrast": "も replaces を and が rather than following them: 洗濯も"
                    "します, not 洗濯をもします. With に、で、へ it is kept: 週末にもします. "
                    "The difference from と is that と lists ('A and B') while "
                    "も adds ('A, and B as well').",
        "watch": "In a negative sentence も becomes 'neither': 洗濯もしません.",
    },
]

GRAMMAR[28] = [
    {
        "point": "〜はどうですか",
        "en": "how is …?",
        "formula": "N + は + どうですか → い-adj / N です",
        "examples": [
            ("今日の天気はどうですか。", "きょうのてんきはどうですか。",
             "How's the weather today?"),
            ("曇りです。少し涼しいです。", "くもりです。すこしすずしいです。",
             "Cloudy. A little cool."),
        ],
        "contrast": "どうですか asks for a description and is answered with an "
                    "adjective or a noun plus です; どうでしたか is the past form "
                    "('how was it?'). どんな asks 'what kind of': どんな天気ですか. "
                    "Both begin with どう／どんな, and both want an adjective "
                    "back.",
        "watch": "どうですか is also used as a suggestion (お茶はどうですか = 'how "
                 "about tea?'), so context decides whether it is a question "
                 "or a proposal.",
    },
    {
        "point": "たぶん〜と思います",
        "en": "probably; I think it probably will",
        "formula": "たぶん + clause（plain form）+ と思います",
        "examples": [
            ("たぶん降ると思います。", "たぶんふるとおもいます。",
             "I think it probably will rain."),
            ("たぶん大丈夫だと思います。", "たぶんだいじょうぶだとおもいます。",
             "I think it will probably be fine."),
        ],
        "contrast": "たぶん on its own is 'probably', and でしょう is the same "
                    "estimate attached to the sentence end (降るでしょう). Adding "
                    "と思います keeps the estimate visibly yours, which is the "
                    "politer of the two.",
        "watch": "たぶん and きっと ('certainly') both go with でしょう, but たぶん "
                 "with です alone is odd: say たぶんそうです.",
    },
    {
        "point": "〜くなります（変化）",
        "en": "become …",
        "formula": "い-adj stem + く + なります",
        "examples": [
            ("週末は暖かくなるといいですね。", "しゅうまつはあたたかくなるといいですね。",
             "It'd be nice if it got warm this weekend."),
            ("だんだん涼しくなります。", "だんだんすずしくなります。",
             "It gradually gets cooler."),
        ],
        "contrast": "なる is change that happens by itself (暖かくなる); する is "
                    "change someone makes (暖かくする). For な-adjectives swap く "
                    "for に: 便利になります, 静かになります.",
        "watch": "〜くなるといいですね is the fixed 'it would be nice if…' shape - "
                 "a wish about a change, not a prediction.",
    },
]

GRAMMAR[29] = [
    {
        "point": "〜が悪いです / いいです",
        "en": "is bad / is good (a part of you)",
        "formula": "N + が + adjective + です",
        "examples": [
            ("顔色が悪いですよ。", "かおいろがわるいですよ。", "You look pale."),
            ("少し気分が悪いです。", "すこしきぶんがわるいです。", "I feel a bit off."),
        ],
        "contrast": "Japanese states what is wrong with a part rather than "
                    "how a person feels: 気分が悪いです ('my condition is bad'), "
                    "not 私は悪いです (which would mean 'I am a bad person'). "
                    "Every symptom follows this shape - 頭が痛いです、のどが痛いです.",
        "watch": "顔色 is 'the colour of your face', and 顔色が悪いです is the "
                 "standard 'you look unwell'.",
    },
    {
        "point": "〜があります（症状）",
        "en": "have (a fever, a cough)",
        "formula": "symptom + が + あります / 出ます",
        "examples": [
            ("熱がありますか。", "ねつがありますか。", "Do you have a fever?"),
            ("少しあります。咳も出ます。", "すこしあります。せきもでます。",
             "A little. I also have a cough."),
        ],
        "contrast": "熱がある uses ある because a temperature is something you "
                    "have; 咳が出る uses 出る because a cough is something that "
                    "comes out. Both are fixed collocations, so learn the "
                    "symptom and its verb together.",
        "watch": "病気です is 'I'm ill' generally; 病気があります is not used.",
    },
    {
        "point": "〜たいです",
        "en": "want to …",
        "formula": "V-ます stem + たいです",
        "examples": [
            ("今日はゆっくり休みたいです。", "きょうはゆっくりやすみたいです。",
             "I'd like to rest today."),
            ("薬を飲みたくないです。", "くすりをのみたくないです。",
             "I don't want to take medicine."),
        ],
        "contrast": "たい conjugates as an い-adjective, so the negative is "
                    "たくないです and the past たかったです. The object can stay を "
                    "(水を飲みたいです), unlike 好き which needs が. ほしいです is 'I want "
                    "a thing' and takes が.",
        "watch": "たいです spoken about someone else's wants is wrong - use "
                 "たがっています for that.",
    },
]

GRAMMAR[30] = [
    {
        "point": "父 / お父さん",
        "en": "my father / your father",
        "formula": "plain term for your own family; お〜さん for others",
        "examples": [
            ("父と母と兄と私です。", "ちちとははとあにとわたしです。",
             "My dad, my mum, my older brother and me."),
            ("お父さんは元気ですか。", "おとうさんはげんきですか。",
             "Is your father well?"),
        ],
        "contrast": "Japanese family words come in two sets. About your own "
                    "family to an outsider: 父、母、兄、姉、妹. About someone "
                    "else's family, or to your own family: お父さん、お母さん、"
                    "お兄さん. Calling your own father お父さん to a stranger "
                    "sounds like you are praising him.",
        "watch": "ご家族 is 'your family'; 家族 alone is the neutral word, and "
                 "私の家族 is fine in writing.",
    },
    {
        "point": "〜に似ています",
        "en": "resemble; look like",
        "formula": "person + に + 似ています",
        "examples": [
            ("お母さんに似ていますか。", "おかあさんににていますか。",
             "Do you resemble your mother?"),
            ("父に似ています。", "ちちににています。", "I take after my father."),
        ],
        "contrast": "似る is a state, so it lives in the ています form: "
                    "似ています, not 似ます. The person you resemble takes に, and "
                    "the と particle would mean 'resemble together with' - "
                    "not what you want.",
        "watch": "背が高いです is 'he is tall' - 背 means height, and it takes "
                 "が because it is the thing being described.",
    },
    {
        "point": "どんな人ですか",
        "en": "what kind of person is …?",
        "formula": "どんな + N + ですか → な-adj / い-adj + N です",
        "examples": [
            ("お兄さんはどんな人ですか。", "おにいさんはどんなひとですか。",
             "What kind of person is your brother?"),
            ("優しい人です。", "やさしいひとです。", "He's a kind person."),
        ],
        "contrast": "どんな asks for a description, and the answer is an "
                    "adjective in front of the noun: 優しい人、面白い人、静かな人. "
                    "どの人 is 'which person' - a choice from a group, not a "
                    "description.",
        "watch": "な-adjectives need な before the noun: 親切な人です, never "
                 "親切の人です. い-adjectives go straight on: 優しい人です.",
    },
]

GRAMMAR[31] = [
    {
        "point": "〜ませんか（誘い）",
        "en": "want to …? shall we …?",
        "formula": "V-ます stem + ませんか",
        "examples": [
            ("土曜日に買い物に行きませんか。", "どようびにかいものにいきませんか。",
             "Want to go shopping on Saturday?"),
            ("あした会いませんか。", "あしたあいませんか。", "Shall we meet tomorrow?"),
        ],
        "contrast": "ませんか invites and waits for the other person's answer; "
                    "ましょう ('let's') proposes and assumes agreement. With "
                    "someone you do not know well, ませんか is the safer of the "
                    "two because it leaves room to decline.",
        "watch": "The answer is いいですね ('that sounds good') or すみません、"
                 "ちょっと ('sorry, that's difficult').",
    },
    {
        "point": "〜に / 〜で（時間と場所）",
        "en": "at (a time) / at (a place)",
        "formula": "time + に / place + で",
        "examples": [
            ("午後二時に駅の改札でどうですか。",
             "ごごにじにえきのかいさつでどうですか。",
             "Two in the afternoon at the station gates?"),
            ("土曜日の午後はどうですか。", "どようびのごごはどうですか。",
             "How about Saturday afternoon?"),
        ],
        "contrast": "に marks the time the event lands on; で marks the place "
                    "the event happens in; を marks a place you move through "
                    "or leave (駅を出る). One meeting can hold all three: "
                    "二時に駅の改札で会いましょう.",
        "watch": "Relative days take no に: 土曜日会いましょう, though 土曜日に is "
                 "also fine and slightly more precise.",
    },
    {
        "point": "〜ないようにします",
        "en": "make sure not to …",
        "formula": "V-ない + ように + します",
        "examples": [
            ("遅れないようにします。", "おくれないようにします。",
             "I'll make sure not to be late."),
            ("忘れないようにします。", "わすれないようにします。",
             "I'll make a point of not forgetting."),
        ],
        "contrast": "ようにします is an effort you make over time, so it is the "
                    "form for a promise about your own conduct. ようにしてくだ"
                    "さい asks someone else to make the effort, and ようになり"
                    "ます describes a change that has already happened.",
        "watch": "The positive version is するようにします ('make a point of "
                 "doing'), not するようになります.",
    },
]

GRAMMAR[32] = [
    {
        "point": "〜ことです（動詞を名詞に）",
        "en": "the thing of …-ing (making a verb into a noun)",
        "formula": "V-る + こと",
        "examples": [
            ("音楽を聞くことと映画を見ることです。",
             "おんがくをきくこととえいがをみることです。",
             "Listening to music and watching films."),
            ("読書も好きです。", "どくしょもすきです。", "I like reading too."),
        ],
        "contrast": "こと turns a verb into a thing you can talk about, list "
                    "or like: 映画を見ることが好きです. の is the other nominaliser and "
                    "picks out something concrete or immediate (見るのが好きです), "
                    "while こと is more general and abstract - hobbies take "
                    "こと.",
        "watch": "ことです at the end of a sentence can also mean 'you should / "
                 "it is decided that': 九時に出ることです.",
    },
    {
        "point": "〜ています（習慣）",
        "en": "have been …-ing",
        "formula": "V-て + います",
        "examples": [
            ("先月からギターを練習しています。", "せんげつからギターをれんしゅうしています。",
             "I've been practising guitar since last month."),
            ("毎日少しずつ練習しています。", "まいにちすこしずつれんしゅうしています。",
             "I practise a little every day."),
        ],
        "contrast": "The same ています that means 'right now' also means 'have "
                    "been doing, as a habit, since…'. から marks where the "
                    "habit started: 先月から. A plain ます (毎日練習します) states "
                    "the habit without the continuity.",
        "watch": "少しずつ is 'little by little' - ずつ is 'at a time', and it "
                 "attaches to amounts: 一つずつ、二人ずつ.",
    },
    {
        "point": "〜から（起点）",
        "en": "since; from",
        "formula": "time / place + から",
        "examples": [
            ("先月から練習しています。", "せんげつかられんしゅうしています。",
             "I've been practising since last month."),
            ("子どものときから好きです。", "こどものときからすきです。",
             "I've liked it since I was a child."),
        ],
        "contrast": "から with ています is 'have been doing since'; から with a "
                    "one-off verb is simply 'from': 九時から始まります. まで gives "
                    "the far end (九時から五時まで), and からだけで ('from X alone') "
                    "is a different から again.",
        "watch": "Don't confuse it with sentence-end から meaning 'because'.",
    },
]

GRAMMAR[33] = [
    {
        "point": "〜のほうが好きです",
        "en": "I prefer A (to B)",
        "formula": "A + のほうが +  adjective / 好きです",
        "examples": [
            ("日本の車のほうが好きです。", "にほんのくるまのほうがすきです。",
             "I prefer Japanese cars."),
            ("古いので十分です。", "ふるいのでじゅうぶんです。",
             "An old one is enough."),
        ],
        "contrast": "Japanese has no word for 'than' in this pattern: Aのほう"
                    "がBより好きです is possible, but the ほう alone already carries "
                    "the comparison, and より is optional and often dropped. "
                    "どちらがいいですか asks which of two, and のほうが answers it.",
        "watch": "ほう is written 方 and read ほう - it means 'the one of / the "
                 "direction of'.",
    },
    {
        "point": "どっち / どちら",
        "en": "which (of two)",
        "formula": "A と B と、どっち / どちらが … ですか",
        "examples": [
            ("日本の車とドイツの車と、どっちがいいですか。",
             "にほんのくるまとドイツのくるまと、どっちがいいですか。",
             "Japanese cars or German cars, which do you prefer?"),
            ("新しいのと古いの、どちらがほしいですか。",
             "あたらしいのとふるいの、どちらがほしいですか。",
             "A new one or an old one, which do you want?"),
        ],
        "contrast": "どっち is casual, どちら is polite - same meaning, and both "
                    "are strictly for two. For three or more use どれ ('which "
                    "one') or どの + noun. The と after each option is the "
                    "quoting と: 'A and B - which?'",
        "watch": "The の in 新しいの is the noun-replacer: 'the new one'. It "
                 "lets you avoid repeating the noun.",
    },
    {
        "point": "〜で十分です",
        "en": "… is enough",
        "formula": "N + で + 十分です / 十分ではありません",
        "examples": [
            ("古いので十分です。", "ふるいのでじゅうぶんです。", "An old one is enough."),
            ("千円で十分ですか。", "せんえんでじゅうぶんですか。",
             "Is a thousand yen enough?"),
        ],
        "contrast": "十分 is a な-adjective meaning 'enough', and で sets the "
                    "terms - 'with this, it is sufficient'. 足ります is the verb "
                    "version (千円で足ります), and it is about having enough of a "
                    "quantity rather than being satisfied with a thing.",
        "watch": "たくさん is 'a lot' and is the opposite in feel, though not "
                 "strictly: まだ足りません is 'still not enough'.",
    },
]

GRAMMAR[34] = [
    {
        "point": "います / 出ております",
        "en": "is here / has stepped out (humble)",
        "formula": "N + は + いますか / 出ております",
        "examples": [
            ("田中さんはいますか。", "たなかさんはいますか。", "Is Mr Tanaka there?"),
            ("今ちょっと出ております。", "いまちょっとでております。",
             "He's stepped out for a moment."),
        ],
        "contrast": "います is the plain 'is present'; おります is the humble "
                    "form, used by the person answering about their own "
                    "colleague. 出ております is not 'he went out' but 'he is out "
                    "at the moment' - a state, built from 出る + ています in its "
                    "humble form.",
        "watch": "いる／います is only for people and animals; a thing is "
                 "あります. 田中さんがあります is impossible.",
    },
    {
        "point": "〜をお願いできますか",
        "en": "could I ask for …?",
        "formula": "N + を + お願いできますか",
        "examples": [
            ("伝言をお願いできますか。", "でんごんをおねがいできますか。",
             "Could you take a message?"),
            ("折り返しの電話をお願いします。", "おりかえしのでんわをおねがいします。",
             "A callback, please."),
        ],
        "contrast": "お願いできますか is the potential - 'is it possible to ask?' "
                    "- and it is one step softer than お願いします, which is a "
                    "request stated flatly. On the phone, where nobody can "
                    "see you nod, the softer form is the safer one.",
        "watch": "できますか asks about possibility, not willingness - for "
                 "'would you mind' use いただけますか.",
    },
    {
        "point": "折り返し",
        "en": "the return call",
        "formula": "折り返し + の電話 / お電話します",
        "examples": [
            ("折り返しの電話をお願いします。", "おりかえしのでんわをおねがいします。",
             "A callback, please."),
            ("折り返しお電話します。", "おりかえしおでんわします。",
             "I'll call you back."),
        ],
        "contrast": "折り返し is the noun for the call that comes back, so it "
                    "replaces a whole clause: 折り返しお願いします is 'ring me back'. "
                    "後でかけます ('I'll call later') says the same thing without "
                    "the telephone-register word.",
        "watch": "It is phone vocabulary - in writing you would say 追ってご連絡"
                 "いたします.",
    },
]

GRAMMAR[35] = [
    {
        "point": "〜たいんですが",
        "en": "I'd like to …, but (would that be all right?)",
        "formula": "V-ます stem + たい + んですが",
        "examples": [
            ("この服を返品したいんですが。", "このふくをへんぴんしたいんですが。",
             "I'd like to return this, but…"),
            ("交換したいんですが。", "こうかんしたいんですが。",
             "I'd like to exchange it, but…"),
        ],
        "contrast": "The trailing が means 'but' and leaves the sentence "
                    "hanging so the other person can respond - it is the "
                    "softest way to make a request that might be refused. "
                    "返品したいです states the want; 返品したいんですが asks "
                    "permission without ever asking a question.",
        "watch": "んです is the spoken form of のです, and both need the plain "
                 "form before them: したいんです, not しますんです.",
    },
    {
        "point": "〜はいかがですか",
        "en": "how about …? (polite)",
        "formula": "N + は + いかがですか",
        "examples": [
            ("交換はいかがですか。", "こうかんはいかがですか。",
             "How about an exchange?"),
            ("こちらはいかがですか。", "こちらはいかがですか。", "How about this one?"),
        ],
        "contrast": "いかがですか is どうですか one register up - it is the shop "
                    "assistant's and the host's word, and it is never used "
                    "about yourself. Offering a suggestion to a friend, "
                    "どうですか is enough.",
        "watch": "いかがでしょうか is softer still; the でしょう moves the decision "
                 "further towards the other person.",
    },
    {
        "point": "〜んです（説明）",
        "en": "the fact is; the reason is",
        "formula": "plain form + んです / んですが",
        "examples": [
            ("サイズが合わなかったんです。", "サイズがあわなかったんです。",
             "The size didn't fit."),
            ("ちょっと大きかったんです。", "ちょっとおおきかったんです。",
             "It was a little too big."),
        ],
        "contrast": "んです wraps a fact as an explanation: サイズが合いませんでした "
                    "states it, サイズが合わなかったんです explains it. That is why it "
                    "belongs in an apology or a request - it hands over the "
                    "background rather than just the outcome.",
        "watch": "んです needs the PLAIN form before it, so 合いませんでしたんです is "
                 "wrong - it is 合わなかったんです.",
    },
]

GRAMMAR[36] = [
    {
        "point": "〜たいのですが",
        "en": "I'd like to … (soft opening)",
        "formula": "V-ます stem + たい + のですが",
        "examples": [
            ("新しい口座を開きたいのですが。", "あたらしいこうざをひらきたいのですが。",
             "I'd like to open a new account."),
            ("カードを作りたいのですが。", "カードをつくりたいのですが。",
             "I'd like to get a card."),
        ],
        "contrast": "〜たいんですが (spoken) and 〜たいのですが (slightly more "
                    "formal) are the same move: state what you want, trail "
                    "off on が, and let the clerk take over. Ending the "
                    "sentence instead - 開きたいです - is fine but sounds like an "
                    "announcement.",
        "watch": "開く has two readings: あく (it opens, intransitive) and "
                 "ひらく (you open it). 口座を開く is こうざをひらく.",
    },
    {
        "point": "〜はかかりますか",
        "en": "does it take (time, money)?",
        "formula": "N + が / は + かかります",
        "examples": [
            ("手数料はかかりますか。", "てすうりょうはかかりますか。", "Is there a fee?"),
            ("どのくらいかかりますか。", "どのくらいかかりますか。", "How long will it take?"),
        ],
        "contrast": "かかる is what time or money costs you, and the amount "
                    "takes no particle - 三十分かかります、千円かかります. 無料です "
                    "('it's free') is the usual answer at a bank counter, and "
                    "かかりません is the plain negative.",
        "watch": "The subject takes が or は, never を: 時間がかかります.",
    },
    {
        "point": "〜で終わります",
        "en": "finish in (an amount of time)",
        "formula": "time + で + 終わります",
        "examples": [
            ("二十分ぐらいで終わります。", "にじっぷんぐらいでおわります。",
             "It'll be done in about twenty minutes."),
            ("三時ごろに終わります。", "さんじごろにおわります。",
             "It finishes around three."),
        ],
        "contrast": "で after a duration is 'in/within that much': 二十分で終わり"
                    "ます = 'it will be finished within twenty minutes'. に after "
                    "a clock time is the moment it ends (三時に終わります). Mixing "
                    "them - 二十分に終わります - is a common early error.",
        "watch": "終わります is intransitive ('it ends'); 終えます is transitive "
                 "('I finish it').",
    },
]

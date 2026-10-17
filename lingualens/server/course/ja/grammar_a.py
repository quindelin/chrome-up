# -*- coding: utf-8 -*-
"""Grammar pages, lessons 1-36 (N5, N4, N3).

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

Verify with:  .venv/bin/python server/course/ja/grammar.py
"""

GRAMMAR: dict = {}

GRAMMAR[1] = [
    {"point": "〜ですか", "en": "yes/no question: put か on the end of the statement",
     "formula": "N / な-adj + ですか",
     "examples": [
         ("お元気ですか。", "おげんきですか。", "Are you well?"),
         ("元気ですか。", "げんきですか。", "Are you well? (plain, among friends)"),
     ],
     "contrast": "Word order never changes - Japanese does not invert the way English does. "
                 "You say the sentence and add か. With a question word it still takes か in "
                 "polite speech (おなまえはなんですか), though casual speech drops it (おなまえは？).",
     "watch": "こんにちは ends in は but is a greeting: not a topic particle, not a question. "
              "It is always written in hiragana and the は is read 'wa'."},
    {"point": "ございます", "en": "the stiff polite form, frozen into greetings",
     "formula": "お + adj/noun + ございます (fixed phrases only)",
     "examples": [
         ("おはようございます。", "おはようございます。", "Good morning."),
         ("ありがとうございます。", "ありがとうございます。", "Thank you very much."),
     ],
     "contrast": "です states a fact and goes anywhere; ございます is the formal version and "
                 "survives almost only inside set greetings. You cannot upgrade an ordinary "
                 "sentence with it: ×げんきございます.",
     "watch": "ありがとう → ありがとうございます → どうも、ありがとうございます: one thank-you at three levels."},
    {"point": "〜ね", "en": "sentence-ending ね: shared ground, or just warmth",
     "formula": "文 + ね",
     "examples": [
         ("またね。", "またね。", "See you."),
         ("さようなら。またね。", "さようなら。またね。", "Goodbye. See you."),
     ],
     "contrast": "よ hands over information the listener does not have (おいしいですよ); "
                 "ね assumes you share it or want them to agree (おいしいですね). よ aimed uphill "
                 "sounds pushy, and ね used to tell someone their own news sounds strange.",
     "watch": "On a greeting nothing is being confirmed - またね is only softness."},
]

GRAMMAR[2] = [
    {"point": "〜てください", "en": "please do this",
     "formula": "V-て形 + ください",
     "examples": [
         ("どうぞ、すわってください。", "どうぞ、すわってください。", "Please, sit down."),
         ("ここで止めてください。", "ここでとめてください。", "Please stop here."),
     ],
     "contrast": "ください after a て-form means 'please do'; after a noun it means 'give me' "
                 "(おちゃをください). Same word, two jobs, decided by what precedes it. "
                 "おねがいします is the softer ask - 〜てください is a direction, and to a stranger "
                 "it can sound like one.",
     "watch": "It is a request, not a rule. For 'you must not' the form is 〜てはいけません."},
    {"point": "〜はどうですか", "en": "how about this? - offering, or asking for a verdict",
     "formula": "N + はどうですか",
     "examples": [
         ("お茶はどうですか。", "おちゃはどうですか。", "How about some tea?"),
         ("十二時はどうですか。", "じゅうにじはどうですか。", "How about twelve?"),
     ],
     "contrast": "どうですか asks what someone thinks of a thing already on the table; "
                 "〜ませんか invites them to do something (ひるごはんをたべにいきませんか). "
                 "いかがですか is the same question put politely, to a customer.",
     "watch": "どうですか is level-to-level. Uphill, use いかがですか, or simply offer with どうぞ."},
    {"point": "お願いします", "en": "I'm asking for this - turns a noun into a request",
     "formula": "N + （を）お願いします",
     "examples": [
         ("コーヒー、お願いします。", "コーヒー、おねがいします。", "Coffee, please."),
         ("ラーメンをお願いします。", "ラーメンをおねがいします。", "Ramen please."),
     ],
     "contrast": "おねがいします places an order; ください points at the thing (これをください). "
                 "Both work at a counter; on the phone or with a stranger おねがいします is the "
                 "safer of the two.",
     "watch": "It also closes an introduction and a phone call, where it asks for goodwill "
              "rather than for an object."},
    {"point": "すみません / ごめんなさい", "en": "excuse me vs sorry",
     "formula": "すみません / ごめんなさい",
     "examples": [
         ("すみません、おそくなりました。", "すみません、おそくなりました。", "Sorry, I'm late."),
         ("ごめんなさい、遅れました。", "ごめんなさい、おくれました。", "Sorry, I'm late."),
     ],
     "contrast": "すみません is the small one: getting attention, a minor fault, thanks-for-your-trouble. "
                 "ごめんなさい is a real apology to someone who has been wronged. Bumping a stranger "
                 "is すみません; keeping a friend waiting is ごめんなさい.",
     "watch": "すみません in front of a question is not an apology at all - it is 'excuse me' "
              "(すみません、トイレはどこですか。)."},
]

GRAMMAR[3] = [
    {"point": "〜がわかります", "en": "to understand - the thing understood is the subject",
     "formula": "N + が + わかります / わかりません",
     "examples": [
         ("日本語がわかりますか。", "にほんごがわかりますか。", "Do you understand Japanese?"),
         ("はい、少しわかります。", "はい、すこしわかります。", "Yes, a little."),
     ],
     "contrast": "わかります is intransitive: what is understood takes が, never を - "
                 "×にほんごをわかります. Contrast べんきょうします, which is transitive and does "
                 "take を (にほんごをべんきょうしています).",
     "watch": "よくわかりません ('I don't really understand') is the standard soft no, "
              "gentler than a bare わかりません."},
    {"point": "〜ましょう", "en": "let's - a proposal that includes the listener",
     "formula": "V-ます形の語幹 + ましょう",
     "examples": [
         ("じゃあ、英語で話しましょう。", "じゃあ、えいごではなしましょう。", "Then let's speak English."),
         ("三時に会いましょう。", "さんじにあいましょう。", "Let's meet at three."),
     ],
     "contrast": "ましょう assumes yes; ませんか asks (たべにいきませんか). Neither is a polite "
                 "'I will' - for your own plan use plain ます (ろくじにきます). わたしは…ましょう "
                 "about yourself alone sounds wrong.",
     "watch": "The casual equivalent is 〜よう / 〜しよう (いこう); it does not belong in polite speech."},
    {"point": "〜で（手段・言語）", "en": "by means of; in (a language)",
     "formula": "N + で",
     "examples": [
         ("英語で話しましょう。", "えいごではなしましょう。", "Let's speak in English."),
         ("地下鉄で二駅です。", "ちかてつでにえきです。", "Two stops on the subway."),
     ],
     "contrast": "で marks the means (えいごで, ちかてつで, カードではらう); に marks the destination "
                 "or the thing boarded (くうこうにいきます, でんしゃにのります). If 'by' or 'using' "
                 "fits the English, it is で.",
     "watch": "で is also the place where an action happens (ここでとめてください) - three jobs, "
              "one particle, resolved by the verb."},
]

GRAMMAR[4] = [
    {"point": "〜は（主題）", "en": "は marks what you are talking about",
     "formula": "N + は",
     "examples": [
         ("出身はどこですか。", "しゅっしんはどこですか。", "Where are you from?"),
         ("わたしは日本です。", "わたしはにほんです。", "I'm from Japan."),
     ],
     "contrast": "は presents the topic; が picks out who or what. わたしはにほんです = 'as for me, "
                 "Japan'; わたしがにほんです would mean 'I am the one'. When a question word is the "
                 "subject the answer takes が (だれがしますか → わたしがします).",
     "watch": "は can swallow the rest of the sentence: おなまえは？ = 'your name?'"},
    {"point": "そうですか", "en": "I see / is that so?",
     "formula": "そうですか / そうですね",
     "examples": [
         ("そうですか。", "そうですか。", "I see."),
         ("本当ですか。", "ほんとうですか。", "Really?"),
     ],
     "contrast": "そうです asserts ('that's right'); そうですか acknowledges. ほんとうですか questions "
                 "whether a thing is true - そうですか only registers that you heard it. Said flat it "
                 "is 'I see'; with a rising end it is 'really?'.",
     "watch": "そうですね is the agreement form, and is safer than そうです when you only half agree."},
    {"point": "よろしくお願いします", "en": "the politeness that closes an introduction",
     "formula": "よろしくお願いします",
     "examples": [
         ("マイクです。よろしくお願いします。", "マイクです。よろしくおねがいします。",
          "I'm Mike. Pleased to meet you."),
         ("わかりました。よろしくお願いします。", "わかりました。よろしくおねがいします。",
          "Understood. Thank you in advance."),
     ],
     "contrast": "ありがとうございます looks back at what was done; よろしくおねがいします looks forward "
                 "at what you are asking for. It closes an introduction because the introduction is "
                 "itself a request for goodwill.",
     "watch": "No single English equivalent - 'nice to meet you', 'thanks in advance' and 'regards' "
              "are all the same phrase, depending on where it is said."},
]

GRAMMAR[5] = [
    {"point": "これ・それ・あれ", "en": "this, that (near you), that (over there)",
     "formula": "これ / それ / あれ / どれ",
     "examples": [
         ("これはいくらですか。", "これはいくらですか。", "How much is this?"),
         ("これは千円です。", "これはせんえんです。", "This one is a thousand yen."),
     ],
     "contrast": "これ is near the speaker, それ near the listener, あれ near neither - the split is by "
                 "person, not by metres. Before a noun they become この／その／あの (このほん); "
                 "これ never takes a noun directly after it.",
     "watch": "どれ is the question form ('which one?') - the set runs こ / そ / あ / ど."},
    {"point": "〜をください", "en": "give me that",
     "formula": "N + を + ください",
     "examples": [
         ("じゃあ、これをください。", "じゃあ、これをください。", "Then I'll take this one."),
         ("お茶をください。", "おちゃをください。", "Tea please."),
     ],
     "contrast": "Noun + ください hands you the thing; verb-て + ください asks you to do something "
                 "(すわってください). Same word, two jobs.",
     "watch": "おねがいします is the politer order (ラーメンをおねがいします); ください is fine at a "
              "counter but brusque in a restaurant."},
    {"point": "い形容詞", "en": "adjectives that conjugate on their own",
     "formula": "いadj + です ／ いadj（＋い）+ N",
     "examples": [
         ("高いですね。", "たかいですね。", "That's expensive."),
         ("これは安いです。", "これはやすいです。", "This one is cheap."),
     ],
     "contrast": "い-adjectives carry the whole load themselves: たかい → たかくない → たかかった → "
                 "たかくて. な-adjectives cannot: they need な before a noun (げんきなひと) and です at "
                 "the end (げんきです). ×たかいなねだん is the classic mistake.",
     "watch": "The い drops before く (たかい → たかくない) but stays before a noun (たかいねだん)."},
]

GRAMMAR[6] = [
    {"point": "どこですか", "en": "where is it?",
     "formula": "N + はどこですか",
     "examples": [
         ("すみません、トイレはどこですか。", "すみません、トイレはどこですか。",
          "Excuse me, where is the restroom?"),
         ("駅はあそこです。", "えきはあそこです。", "The station is over there."),
     ],
     "contrast": "どこ is plain 'where'; どちら is the polite form and also means 'which one / which "
                 "way' (どちらがいいですか). To a stranger use どちら. The question word does not move "
                 "to the front - トイレはどこですか is literally 'the restroom, where is it?'",
     "watch": "ここ / そこ / あそこ answer it, and follow the same speaker-listener split as "
              "これ / それ / あれ."},
    {"point": "〜て、〜（連結）", "en": "joining two clauses with the て-form",
     "formula": "V-て形、…",
     "examples": [
         ("まっすぐ行って、左です。", "まっすぐいって、ひだりです。", "Go straight, it's on the left."),
         ("まっすぐ行って、右です。", "まっすぐいって、みぎです。", "Go straight, it's on the right."),
     ],
     "contrast": "て just links - sequence, manner, or a loose reason that the listener works out. "
                 "てから says explicitly 'after doing X' and nothing else. いってから、ひだりです would "
                 "put the turn much later than it happens.",
     "watch": "The て-form carries no tense of its own; the final verb in the sentence sets it."},
    {"point": "すみません（呼びかけ）", "en": "excuse me - getting someone's attention",
     "formula": "すみません、…",
     "examples": [
         ("すみません、トイレはどこですか。", "すみません、トイレはどこですか。",
          "Excuse me, where is the restroom?"),
         ("すみません、これはいくらですか。", "すみません、これはいくらですか。",
          "Excuse me, how much is this?"),
     ],
     "contrast": "Before a question すみません is 'excuse me' and means no apology at all. "
                 "ごめんなさい is the apology, and implies someone has been wronged. You can say "
                 "すみません to somebody you have done nothing to; you cannot say ごめんなさい to them.",
     "watch": "It also means 'thank you for your trouble' when someone has gone out of their way."},
]

GRAMMAR[7] = [
    {"point": "〜たいです", "en": "I want to do",
     "formula": "V-ます形の語幹 + たいです",
     "examples": [
         ("空港に行きたいです。", "くうこうにいきたいです。", "I want to go to the airport."),
         ("散歩に行きたいです。", "さんぽにいきたいです。", "I'd like to go for a walk."),
     ],
     "contrast": "たいです states your own wish. いきたいですか asked of someone else is intrusive - "
                 "use いきませんか to invite them. ほしいです wants a thing "
                 "(あたらしいのがほしいです); たいです wants an action.",
     "watch": "たい behaves like an い-adjective (いきたい → いきたくない → いきたかった), and its "
              "object may be を or が (おちゃがのみたいです)."},
    {"point": "に（行き先） vs で（手段）", "en": "に lands you somewhere; で is how you got there",
     "formula": "N + に + いきます／のります ／ N + で + いきます",
     "examples": [
         ("空港に行きたいです。", "くうこうにいきたいです。", "I want to go to the airport."),
         ("じゃあ、電車に乗ります。", "じゃあ、でんしゃにのります。", "Then I'll take the train."),
     ],
     "contrast": "でんしゃにのります = get on the train (に = the thing boarded); でんしゃでいきます = "
                 "go by train (で = the means). Swap them and you describe a different event. Verbs "
                 "of being (います, あります, すんでいます) take に and never で.",
     "watch": "へ can replace に for direction but keeps a sense of 'heading towards' - and it is "
              "pronounced え."},
    {"point": "Aですか、Bですか", "en": "either/or - the comma does the work",
     "formula": "A + ですか、B + ですか",
     "examples": [
         ("タクシーですか、電車ですか。", "タクシーですか、でんしゃですか。", "Taxi or train?"),
         ("カードですか、現金ですか。", "カードですか、げんきんですか。", "Card or cash?"),
     ],
     "contrast": "There is no word for 'or' here - two nouns, two ですか, one comma. "
                 "どちらがいいですか is the version that actually asks for a preference; "
                 "Aですか、Bですか only lays out the labels.",
     "watch": "For more than two options, 〜や〜 lists them without claiming the list is complete "
              "(ぎょうざやラーメン)."},
]

GRAMMAR[8] = [
    {"point": "どうやって", "en": "how, by what route or method",
     "formula": "どうやって + V",
     "examples": [
         ("すみません、空港へはどうやって行きますか。", "すみません、くうこうへはどうやっていきますか。",
          "Excuse me, how do I get to the airport?"),
         ("駅へはどうやって行きますか。", "えきへはどうやっていきますか。",
          "How do I get to the station?"),
     ],
     "contrast": "どうやって wants a method as the answer; どう is 'how' in general "
                 "(どうですか = how is it?); どのぐらい asks how long or how much "
                 "(さんじっぷんぐらいです). Only どうやって can be answered with ちかてつで.",
     "watch": "どうやっていきますか asks the route; なんじにいきますか asks the departure. Both are "
              "'how' in a careless English translation."},
    {"point": "〜へ（方向）", "en": "towards - the directional particle",
     "formula": "N + へ（＋は）",
     "examples": [
         ("空港へはどうやって行きますか。", "くうこうへはどうやっていきますか。",
          "How do I get to the airport?"),
         ("こちらへどうぞ。", "こちらへどうぞ。", "This way please."),
     ],
     "contrast": "へ and に both mark direction and are often interchangeable, but に is the default "
                 "for a destination (くうこうにいきます) and へ keeps a sense of 'heading towards'. "
                 "Adding は (くうこうへは) makes the destination the topic you are asking about.",
     "watch": "へ is pronounced え. Yes, really."},
    {"point": "〜目（序数）", "en": "the nth one - order, not count",
     "formula": "助数詞 + 目（め）",
     "examples": [
         ("三駅目で乗り換えてください。", "さんえきめでのりかえてください。",
          "Please change at the third stop."),
         ("次の駅で降ります。", "つぎのえきでおります。", "I'll get off at the next station."),
     ],
     "contrast": "さんえきめ = the third station; さんえき = three stations. め counts order, 番 "
                 "labels an item (さんばんホーム = platform three), つ／こ counts things "
                 "(みっつ = three of them). 三駅目で and 三駅で are different instructions.",
     "watch": "次 and 前 give you the same idea without counting: つぎのえき (next station), "
              "まえのえき (the one before)."},
]

GRAMMAR[9] = [
    {"point": "〜まで", "en": "as far as, up to",
     "formula": "N + まで",
     "examples": [
         ("すみません、このホテルまでお願いします。", "すみません、このホテルまでおねがいします。",
          "To this hotel, please."),
         ("駅までお願いします。", "えきまでおねがいします。", "To the station, please."),
     ],
     "contrast": "まで gives the far end of a range and から gives the near end "
                 "(えきからホテルまで). に just names the point: ホテルにいきます says where you are "
                 "going, ホテルまでいきます says you are covering the whole distance.",
     "watch": "With a time word it means 'until': くじまで = until nine o'clock."},
    {"point": "〜くらい / 〜ごろ", "en": "about - an amount vs a point in time",
     "formula": "数量 + くらい ／ 時刻 + ごろ",
     "examples": [
         ("いいえ、十分くらいです。", "いいえ、じゅっぷんくらいです。", "No, about ten minutes."),
         ("十二時ごろ寝ます。", "じゅうにじごろねます。", "I go to bed around midnight."),
     ],
     "contrast": "くらい is 'about' for an amount (じゅっぷんくらい = about ten minutes); ごろ is "
                 "'about' for a clock time (じゅうにじごろ). じゅうにじくらい means 'about twelve "
                 "hours', which is not what you meant.",
     "watch": "ぐらい and くらい are the same word; くらい is the more usual pronunciation."},
    {"point": "で（動作の場所）", "en": "where the action happens",
     "formula": "場所 + で + V",
     "examples": [
         ("じゃあ、ここで止めてください。", "じゃあ、ここでとめてください。", "Then please stop here."),
         ("あの券売機で買ってください。", "あのけんばいきでかってください。",
          "Please buy one at that machine."),
     ],
     "contrast": "で is the stage an action plays out on; に is the destination, or the place where "
                 "something exists. Verbs of being take に and never で: えきにいます, ×えきでいます. "
                 "ここにとめてください would mean 'park it into here'.",
     "watch": "で is also the means (でんしゃで). Same particle - the verb tells you which one it is."},
]

GRAMMAR[10] = [
    {"point": "なん / なに", "en": "one question word, two readings, split by the particle",
     "formula": "なん + です／で／の／か ／ なに + を／が／に",
     "examples": [
         ("ホームは何番ですか。", "ホームはなんばんですか。", "Which platform?"),
         ("次の電車は何時ですか。", "つぎのでんしゃはなんじですか。", "What time is the next train?"),
     ],
     "contrast": "なん before です, で, の and counters (なんじ, なんばん, なんですか); なに before を, "
                 "が and に (なにをたべますか, なにがありますか). It is one word - the reading changes, "
                 "the meaning does not.",
     "watch": "なにをたべますか and なんじですか look like two different words in romaji and are the "
              "same kanji."},
    {"point": "わかりました vs わかっています", "en": "'understood' vs 'I already know'",
     "formula": "わかりました ／ わかっています",
     "examples": [
         ("わかりました。ホームは何番ですか。", "わかりました。ホームはなんばんですか。",
          "Got it. Which platform?"),
         ("はい、わかっています。", "はい、わかっています。", "Yes, I know already."),
     ],
     "contrast": "わかりました is the moment of understanding - the answer to an explanation just "
                 "given. わかっています is a state: you knew before. Replying to an explanation with "
                 "わかっています sounds impatient, as if they need not have bothered.",
     "watch": "わかりました is the past form of わかります, but it means 'I have now understood', not "
              "'I understood and then forgot'."},
]

GRAMMAR[11] = [
    {"point": "〜に〜があります", "en": "there is a thing at a place",
     "formula": "場所 + に + N + が + あります",
     "examples": [
         ("ここにメニューがあります。", "ここにメニューがあります。", "There's a menu here."),
         ("メニューはありますか。", "メニューはありますか。", "Is there a menu?"),
     ],
     "contrast": "あります is for things that do not move on their own; います is for people and "
                 "animals (たなかさんはいますか). Using あります for a person is a genuine insult. "
                 "が introduces something new; は asks about something already under discussion "
                 "(メニューはありますか).",
     "watch": "The thing present takes が, never を - あります has no object. And the place takes に."},
    {"point": "〜よ（終助詞）", "en": "I'm telling you - information the listener does not have",
     "formula": "文 + よ",
     "examples": [
         ("いいですね。おいしいですよ。", "いいですね。おいしいですよ。", "Good choice. It's delicious."),
         ("大丈夫ですよ。", "だいじょうぶですよ。", "It's fine."),
     ],
     "contrast": "よ gives; ね shares. おいしいですよ = 'it is good, you'll see'; おいしいですね = "
                 "'it's good, isn't it'. よ aimed uphill sounds pushy because it claims the other "
                 "person did not know.",
     "watch": "ですよ is also a soft reassurance: だいじょうぶですよ = 'honestly, it's fine'."},
]

GRAMMAR[12] = [
    {"point": "〜ないでください", "en": "please don't",
     "formula": "V-ない形 + で + ください",
     "examples": [
         ("いいえ、辛くしないでください。", "いいえ、からくしないでください。",
          "No, please don't make it spicy."),
         ("あまり辛くしないでください。", "あまりからくしないでください。",
          "Please don't make it too spicy."),
     ],
     "contrast": "〜てください asks for an action; 〜ないでください asks for its absence. Both are "
                 "requests to a person in front of you. 〜てはいけません is a rule, not a request - "
                 "do not use it to ask a waiter for anything.",
     "watch": "ないで, not なくて: the negative て-form is ないでください."},
    {"point": "〜くする / 〜くなる", "en": "make it X vs become X",
     "formula": "いadj→く + する／なる ／ なadj→に + する／なる",
     "examples": [
         ("辛くしますか。", "からくしますか。", "Spicy?"),
         ("少し辛くします。", "すこしからくします。", "I'll make it a bit spicy."),
     ],
     "contrast": "する needs someone doing it (からくします = I'll make it spicy); なる happens on its "
                 "own (やすくなりました = it got cheaper, おそくなりました = I ended up late). "
                 "やすくなりませんか therefore asks the shop to let the price fall rather than to "
                 "lower it - which is why it is polite.",
     "watch": "な-adjectives take に instead of く: げんきになります, べんりになります."},
    {"point": "お・ご + 名詞", "en": "the polite wrapper on a noun",
     "formula": "お + 和語 ／ ご + 漢語",
     "examples": [
         ("お飲み物は？", "おのみものは？", "And to drink?"),
         ("ご注文は？", "ごちゅうもんは？", "What's your order?"),
     ],
     "contrast": "お goes with native Japanese words (おちゃ, おみず, おのみもの); ご goes with "
                 "Chinese-derived ones (ごちゅうもん, ごかぞく, ごしゅみ). It marks the word as "
                 "belonging politely to the other person, or simply as refined.",
     "watch": "There are exceptions (おでんわ) and words that never take it (くるま). When in doubt "
              "leave it off - おつくえ is worse than つくえ."},
]
# @@NEXT@@

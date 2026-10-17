# -*- coding: utf-8 -*-
"""JLPT N3 — daily life in detail.

Pimsleur-style.  Polite base (です/ます) with a few plain-form lines in the
later units.  Each lesson's vocabulary is re-used in the dialogue so the
learner meets the words twice in one sitting.

  text    the line as Japanese write it (kanji + kana, normal script)
  reading the same line written entirely in kana — the furigana slot
          printed above the line, including okurigana
  en      natural English

Pattern slots use the same three keys: text / reading / en, each carrying a
"{x}" placeholder that the value fills in.
"""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Unit 6 - Daily Life.  Routines, the home, the weather, and health.
    # -----------------------------------------------------------------------
    {
        "id": 6,
        "title": "Daily Life",
        "focus": "Talk about your day, your home, the weather, and your health.",
        "gate": {"min_pron_score": 70.0, "min_accuracy": 70.0, "min_completeness": 82.0},
        "lessons": [
            {
                "id": 26,
                "title": "My day",
                "goal": "Describe a normal day: when you wake up, commute, and sleep.",
                "vocab": [
                    ("起きます", "おきます", "to wake up / get up"),
                    ("寝ます", "ねます", "to sleep / go to bed"),
                    ("朝", "あさ", "morning"),
                    ("通勤", "つうきん", "commuting"),
                    ("会社", "かいしゃ", "company / office"),
                    ("ごろ", "ごろ", "around (a time)"),
                ],
                "dialogue": [
                    ("them", "毎朝、何時に起きますか。", "まいあさ、なんじにおきますか。",
                     "What time do you get up every morning?"),
                    ("you", "七時に起きます。会社は九時からです。", "しちじにおきます。かいしゃはくじからです。",
                     "I get up at seven. Work starts at nine."),
                    ("them", "通勤はどのぐらいかかりますか。", "つうきんはどのぐらいかかりますか。",
                     "How long does your commute take?"),
                    ("you", "三十分ぐらいです。", "さんじっぷんぐらいです。",
                     "About thirty minutes."),
                    ("them", "何時に寝ますか。", "なんじにねますか。",
                     "What time do you go to bed?"),
                    ("you", "十二時ごろ寝ます。", "じゅうにじごろねます。",
                     "I go to bed around midnight."),
                ],
                "patterns": [
                    {
                        "text": "私は{x}に起きます",
                        "reading": "わたしは{x}におきます",
                        "en": "I get up at {x}",
                        "kind": "clock",
                        "values": [
                            ("七時", "しちじ", "seven o'clock"),
                            ("六時半", "ろくじはん", "half past six"),
                            ("八時", "はちじ", "eight o'clock"),
                        ],
                    },
                    {
                        "text": "{x}時に寝ます",
                        "reading": "{x}じにねます",
                        "en": "I go to bed at {x} o'clock",
                        "values": [
                            ("十一", "じゅういち", "eleven"),
                            ("十二", "じゅうに", "twelve"),
                            ("一", "いち", "one"),
                        ],
                    },
                ],
                "notes": [
                    "ごろ after a time = 'around (that time)': 十二時ごろ.",
                ],
            },
            {
                "id": 27,
                "title": "At home",
                "goal": "Describe your home and the chores you do there.",
                "vocab": [
                    ("掃除", "そうじ", "cleaning"),
                    ("洗濯", "せんたく", "laundry"),
                    ("料理", "りょうり", "cooking"),
                    ("部屋", "へや", "room"),
                    ("広い", "ひろい", "spacious / big"),
                    ("狭い", "せまい", "cramped / small"),
                ],
                "dialogue": [
                    ("them", "お家は何部屋ありますか。", "おうちはなんへやありますか。",
                     "How many rooms does your place have?"),
                    ("you", "三部屋あります。あまり広くないです。", "さんべやあります。あまりひろくないです。",
                     "Three rooms. Not very big."),
                    ("them", "誰が掃除しますか。", "だれがそうじしますか。",
                     "Who does the cleaning?"),
                    ("you", "私がします。週末に洗濯もします。", "わたしがします。しゅうまつにせんたくもします。",
                     "I do. I also do laundry on weekends."),
                    ("them", "料理はよくしますか。", "りょうりはよくしますか。",
                     "Do you cook often?"),
                    ("you", "時々します。台所は狭いですが、好きです。", "ときどきします。だいどころはせまいですが、すきです。",
                     "Sometimes. The kitchen is cramped, but I like it."),
                ],
                "patterns": [
                    {
                        "text": "{x}は私がします",
                        "reading": "{x}はわたしがします",
                        "en": "I do the {x}",
                        "values": [
                            ("掃除", "そうじ", "cleaning"),
                            ("洗濯", "せんたく", "laundry"),
                            ("料理", "りょうり", "cooking"),
                        ],
                    },
                    {
                        "text": "週末に{x}",
                        "reading": "しゅうまつに{x}",
                        "en": "on weekends, {x}",
                        "values": [
                            ("掃除します", "そうじします", "I clean"),
                            ("料理を作ります", "りょうりをつくります", "I cook"),
                            ("休みます", "やすみます", "I rest"),
                        ],
                    },
                ],
                "notes": [
                    "〜も in a positive sentence = 'also': 洗濯もします = 'I also do laundry.'",
                ],
            },
            {
                "id": 28,
                "title": "The weather",
                "goal": "Ask about and describe the weather and what you'll do because of it.",
                "vocab": [
                    ("天気", "てんき", "weather"),
                    ("雨", "あめ", "rain"),
                    ("曇り", "くもり", "cloudy"),
                    ("晴れ", "はれ", "sunny"),
                    ("暖かい", "あたたかい", "warm"),
                    ("涼しい", "すずしい", "pleasantly cool"),
                ],
                "dialogue": [
                    ("them", "今日の天気はどうですか。", "きょうのてんきはどうですか。",
                     "How's the weather today?"),
                    ("you", "曇りです。少し涼しいです。", "くもりです。すこしすずしいです。",
                     "Cloudy. A little cool."),
                    ("them", "明日は雨が降るでしょうか。", "あしたはあめがふるでしょうか。",
                     "Do you think it'll rain tomorrow?"),
                    ("you", "たぶん降ると思います。", "たぶんふるとおもいます。",
                     "I think it probably will."),
                    ("them", "週末は暖かくなるといいですね。", "しゅうまつはあたたかくなるといいですね。",
                     "It'd be nice if it got warm this weekend."),
                    ("you", "ええ、散歩に行きたいです。", "ええ、さんぽにいきたいです。",
                     "Yes, I'd like to go for a walk."),
                ],
                "patterns": [
                    {
                        "text": "明日は{x}です",
                        "reading": "あしたは{x}です",
                        "en": "Tomorrow is {x}",
                        "kind": "weather-adj",
                        "values": [
                            ("晴れ", "はれ", "sunny"),
                            ("雨", "あめ", "rainy"),
                            ("曇り", "くもり", "cloudy"),
                        ],
                    },
                    {
                        "text": "今日は少し{x}",
                        "reading": "きょうはすこし{x}",
                        "en": "Today is a little {x}",
                        "values": [
                            ("涼しいです", "すずしいです", "cool"),
                            ("暑いです", "あついです", "hot"),
                            ("寒いです", "さむいです", "cold"),
                        ],
                    },
                ],
                "notes": [
                    "〜と思います = 'I think …': 降ると思います.  降る (ふ) is plain-form; the polite wrapper is the verb in the sentence.",
                ],
            },
            {
                "id": 29,
                "title": "I'm not feeling well",
                "goal": "Describe how you feel and ask for simple medical advice.",
                "vocab": [
                    ("気分", "きぶん", "how you feel / mood"),
                    ("熱", "ねつ", "fever"),
                    ("咳", "せき", "cough"),
                    ("薬", "くすり", "medicine"),
                    ("病院", "びょういん", "hospital / clinic"),
                    ("休む", "やすむ", "to rest"),
                ],
                "dialogue": [
                    ("them", "大丈夫ですか。顔色が悪いですよ。", "だいじょうぶですか。かおいろがわるいですよ。",
                     "Are you OK? You look pale."),
                    ("you", "ええ、少し気分が悪いです。", "ええ、すこしきぶんがわるいです。",
                     "Yeah, I feel a bit off."),
                    ("them", "熱がありますか。", "ねつがありますか。",
                     "Do you have a fever?"),
                    ("you", "少しあります。咳も出ます。", "すこしあります。せきもでます。",
                     "A little. I also have a cough."),
                    ("them", "薬を飲みましたか。", "くすりをのみましたか。",
                     "Did you take any medicine?"),
                    ("you", "はい、今日はゆっくり休みたいです。", "はい、きょうはゆっくりやすみたいです。",
                     "Yes, I'd like to rest slowly today."),
                ],
                "patterns": [
                    {
                        "text": "少し{x}があります",
                        "reading": "すこし{x}があります",
                        "en": "I have a bit of {x}",
                        "values": [
                            ("熱", "ねつ", "a fever"),
                            ("咳", "せき", "a cough"),
                            ("頭痛", "ずつう", "a headache"),
                        ],
                    },
                    {
                        "text": "{x}方がいいですか",
                        "reading": "{x}ほうがいいですか",
                        "en": "Should I {x}?",
                        "values": [
                            ("病院に行った", "びょういんにいった", "go to the hospital"),
                            ("薬を飲んだ", "くすりをのんだ", "take some medicine"),
                            ("休んだ", "やすんだ", "rest"),
                        ],
                    },
                ],
                "notes": [
                    "顔色 (かおいろ) = 'complexion / colour of one's face'.  顔色が悪いです is the standard 'you look unwell'.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 7 - People & Plans.  Family, meeting up, hobbies, comparing.
    # -----------------------------------------------------------------------
    {
        "id": 7,
        "title": "People & Plans",
        "focus": "Describe family, arrange to meet, share hobbies, and compare things.",
        "gate": {"min_pron_score": 72.0, "min_accuracy": 72.0, "min_completeness": 84.0},
        "lessons": [
            {
                "id": 30,
                "title": "My family",
                "goal": "Introduce your family and describe each member in a sentence.",
                "vocab": [
                    ("家族", "かぞく", "family"),
                    ("父", "ちち", "my father"),
                    ("母", "はは", "my mother"),
                    ("兄", "あに", "my older brother"),
                    ("優しい", "やさしい", "kind / gentle"),
                    ("似る", "にる", "to resemble"),
                ],
                "dialogue": [
                    ("them", "ご家族は何人ですか。", "ごかぞくはなんにんですか。",
                     "How many people are in your family?"),
                    ("you", "四人です。父と母と兄と私です。", "よにんです。ちちとははとあにとわたしです。",
                     "Four. My dad, my mum, my older brother and me."),
                    ("them", "お兄さんはどんな人ですか。", "おにいさんはどんなひとですか。",
                     "What kind of person is your older brother?"),
                    ("you", "優しい人です。背が高いです。", "やさしいひとです。せがたかいです。",
                     "He's kind. He's tall."),
                    ("them", "お母さんに似ていますか。", "おかあさんににていますか。",
                     "Do you resemble your mother?"),
                    ("you", "はい、みんなそう言います。", "はい、みんなそういいます。",
                     "Yes, everyone says so."),
                ],
                "patterns": [
                    {
                        "text": "{x}に似ています",
                        "reading": "{x}ににています",
                        "en": "I resemble {x}",
                        "kind": "person",
                        "values": [
                            ("父", "ちち", "my father"),
                            ("母", "はは", "my mother"),
                            ("兄", "あに", "my older brother"),
                        ],
                    },
                    {
                        "text": "{x}は優しい人です",
                        "reading": "{x}はやさしいひとです",
                        "en": "{x} is a kind person",
                        "kind": "person",
                        "values": [
                            ("父", "ちち", "my father"),
                            ("母", "はは", "my mother"),
                            ("主人", "しゅじん", "my husband"),
                        ],
                    },
                ],
                "notes": [
                    "Humility: 父/母 = my own parents; お父さん/お母さん = someone else's.  Same idea with 兄 vs お兄さん.",
                ],
            },
            {
                "id": 31,
                "title": "Let's meet",
                "goal": "Arrange a meeting, fix a place and time, and promise not to be late.",
                "vocab": [
                    ("約束", "やくそく", "appointment / promise"),
                    ("待ち合わせ", "まちあわせ", "meeting up"),
                    ("都合", "つごう", "(one's) schedule / convenience"),
                    ("改札", "かいさつ", "ticket gates"),
                    ("遅れる", "おくれる", "to be late"),
                    ("楽しみ", "たのしみ", "looking forward to"),
                ],
                "dialogue": [
                    ("them", "土曜日に買い物に行きませんか。", "どようびにかいものにいきませんか。",
                     "Want to go shopping on Saturday?"),
                    ("you", "いいですね。待ち合わせは何時がいいですか。", "いいですね。まちあわせはなんじがいいですか。",
                     "Sounds good. What time should we meet?"),
                    ("them", "午後二時に駅の改札でどうですか。ご都合はどうですか。",
                     "ごごにじにえきのかいさつでどうですか。ごつごうはどうですか。",
                     "Two in the afternoon at the station ticket gates? Does that suit you?"),
                    ("you", "大丈夫です。遅れないようにします。", "だいじょうぶです。おくれないようにします。",
                     "Sure. I'll make sure not to be late."),
                    ("them", "よかった。楽しみですね。", "よかった。たのしみですね。",
                     "Great. I'm looking forward to it."),
                    ("you", "私もです。じゃあ、土曜日の約束ですね。", "わたしもです。じゃあ、どようびのやくそくですね。",
                     "Me too. So we have a plan for Saturday."),
                ],
                "patterns": [
                    {
                        "text": "{x}に会いましょう",
                        "reading": "{x}にあいましょう",
                        "en": "Let's meet at {x}",
                        "values": [
                            ("三時", "さんじ", "three o'clock"),
                            ("駅前", "えきまえ", "in front of the station"),
                            ("改札", "かいさつ", "the ticket gates"),
                        ],
                    },
                    {
                        "text": "{x}はどうですか",
                        "reading": "{x}はどうですか",
                        "en": "How about {x}?",
                        "values": [
                            ("土曜日の午後", "どようびのごご", "Saturday afternoon"),
                            ("駅の近く", "えきのちかく", "near the station"),
                            ("来週", "らいしゅう", "next week"),
                        ],
                    },
                ],
                "notes": [
                    "〜ないようにします = 'I'll make sure not to …': 遅れないようにします.",
                ],
            },
            {
                "id": 32,
                "title": "Hobbies",
                "goal": "Talk about hobbies, how long you've had them, and how often you do them.",
                "vocab": [
                    ("趣味", "しゅみ", "hobby"),
                    ("映画", "えいが", "movie"),
                    ("音楽", "おんがく", "music"),
                    ("読書", "どくしょ", "reading (books)"),
                    ("練習", "れんしゅう", "practice"),
                    ("始める", "はじめる", "to start (something)"),
                ],
                "dialogue": [
                    ("them", "ご趣味は何ですか。", "ごしゅみはなんですか。",
                     "What are your hobbies?"),
                    ("you", "音楽を聞くことと映画を見ることです。読書も好きです。",
                     "おんがくをきくこととえいがをみることです。どくしょもすきです。",
                     "Listening to music and watching movies. I like reading too."),
                    ("them", "最近、何か始めましたか。", "さいきん、なにかはじめましたか。",
                     "Have you started anything recently?"),
                    ("you", "先月からギターを練習しています。", "せんげつからギターをれんしゅうしています。",
                     "I've been practicing guitar since last month."),
                    ("them", "毎日するんですか。", "まいにちするんですか。",
                     "Every day?"),
                    ("you", "はい、少しずつ上達したいんです。", "はい、すこしずつじょうたつしたいんです。",
                     "Yes, I want to improve little by little."),
                ],
                "patterns": [
                    {
                        "text": "{x}を練習しています",
                        "reading": "{x}をれんしゅうしています",
                        "en": "I'm practicing {x}",
                        "values": [
                            ("ギター", "ギター", "guitar"),
                            ("ピアノ", "ピアノ", "piano"),
                            ("日本語", "にほんご", "Japanese"),
                        ],
                    },
                    {
                        "text": "{x}ことが好きです",
                        "reading": "{x}ことがすきです",
                        "en": "I like {x}-ing",
                        "values": [
                            ("料理を作る", "りょうりをつくる", "to cook"),
                            ("音楽を聞く", "おんがくをきく", "to listen to music"),
                            ("本を読む", "ほんをよむ", "to read books"),
                        ],
                    },
                ],
                "notes": [
                    "〜ています on a habit = 'have been …-ing': 練習しています = 'I've been practicing'.",
                ],
            },
            {
                "id": 33,
                "title": "Comparing things",
                "goal": "Compare two options, state a preference, and give a short reason.",
                "vocab": [
                    ("どっち", "どっち", "which (of two, casual)"),
                    ("どちら", "どちら", "which (of two, polite)"),
                    ("新しい", "あたらしい", "new"),
                    ("古い", "ふるい", "old"),
                    ("便利", "べんり", "convenient / practical"),
                    ("例えば", "たとえば", "for example"),
                ],
                "dialogue": [
                    ("them", "日本の車とドイツの車と、どっちがいいですか。", "にほんのくるまとドイツのくるまと、どっちがいいですか。",
                     "Japanese cars or German cars, which do you prefer?"),
                    ("you", "日本の車のほうが好きです。便利です。", "にほんのくるまのほうがすきです。べんりです。",
                     "I prefer Japanese cars. They're practical."),
                    ("them", "新しいのと古いの、どちらがほしいですか。", "あたらしいのとふるいの、どちらがほしいですか。",
                     "A new one or an old one, which do you want?"),
                    ("you", "古いので十分です。例えば、十年ものでも。", "ふるいのでじゅうぶんです。たとえば、じゅうねんものでも。",
                     "An old one is enough. For example, even a ten-year-old one."),
                    ("them", "それは賢いですね。", "それはかしこいですね。",
                     "That's a smart choice."),
                    ("you", "ええ、お金を貯めたいんです。", "ええ、おかねをためたいんです。",
                     "Yeah, I want to save money."),
                ],
                "patterns": [
                    {
                        "text": "{x}のほうが好きです",
                        "reading": "{x}のほうがすきです",
                        "en": "I prefer {x}",
                        "values": [
                            ("日本", "にほん", "Japan"),
                            ("こちら", "こちら", "this one / here"),
                            ("小さい", "ちいさい", "the smaller one"),
                        ],
                    },
                    {
                        "text": "{x}と比べて",
                        "reading": "{x}とくらべて",
                        "en": "compared with {x}",
                        "values": [
                            ("前", "まえ", "before"),
                            ("去年", "きょねん", "last year"),
                            ("去年の冬", "きょねんのふゆ", "last winter"),
                        ],
                    },
                ],
                "notes": [
                    "A のほうが B: 'A rather than B'.  No 'than' particle — ほう ga carries the comparison.",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------------
    # Unit 8 - Getting Things Done.  Phone calls, returns, banking, experience.
    # -----------------------------------------------------------------------
    {
        "id": 8,
        "title": "Getting Things Done",
        "focus": "Handle phone calls, returns, banking, and talk about past experiences.",
        "gate": {"min_pron_score": 74.0, "min_accuracy": 74.0, "min_completeness": 85.0},
        "lessons": [
            {
                "id": 34,
                "title": "On the phone",
                "goal": "Ask for someone, leave a message, and ask for a callback.",
                "vocab": [
                    ("電話", "でんわ", "phone / phone call"),
                    ("伝言", "でんごん", "message"),
                    ("番号", "ばんごう", "number"),
                    ("折り返し", "おりかえし", "calling back"),
                    ("失礼します", "しつれいします", "excuse me (on phone / leaving)"),
                    ("もう一度", "もういちど", "one more time"),
                ],
                "dialogue": [
                    ("them", "はい、山田です。", "はい、やまだです。",
                     "Hello, Yamada speaking."),
                    ("you", "すみません、田中さんはいますか。", "すみません、たなかさんはいますか。",
                     "Sorry, is Mr Tanaka there?"),
                    ("them", "すみません、今ちょっと出ております。", "すみません、いまちょっとでております。",
                     "Sorry, he's stepped out for a moment."),
                    ("you", "そうですか。伝言をお願いできますか。", "そうですか。でんごんをおねがいできますか。",
                     "I see. Could you take a message?"),
                    ("them", "はい、大丈夫です。番号をどうぞ。", "はい、だいじょうぶです。ばんごうをどうぞ。",
                     "Yes, of course. Your number, please."),
                    ("you", "折り返しの電話を、お願いします。失礼します。",
                     "おりかえしのでんわを、おねがいします。しつれいします。",
                     "A callback, please. Thank you, goodbye."),
                ],
                "patterns": [
                    {
                        "text": "{x}をお願いします",
                        "reading": "{x}をおねがいします",
                        "en": "{x}, please",
                        "kind": "object",
                        "values": [
                            ("伝言", "でんごん", "a message"),
                            ("予約", "よやく", "a reservation"),
                            ("折り返し", "おりかえし", "a callback"),
                        ],
                    },
                    {
                        "text": "{x}をお願いします",
                        "reading": "{x}をおねがいします",
                        "en": "Please {x}",
                        "values": [
                            ("もう一度", "もういちど", "say it again"),
                            ("ゆっくり話して", "ゆっくりはなして", "speak slowly"),
                            ("待って", "まって", "wait"),
                        ],
                    },
                ],
                "notes": [
                    "出る (でる) here = 'to leave the room / step out'.  出ております is the humble form of います.",
                ],
            },
            {
                "id": 35,
                "title": "Returning something",
                "goal": "Return or exchange a purchase, and explain the problem.",
                "vocab": [
                    ("返品", "へんぴん", "returning (a purchase)"),
                    ("交換", "こうかん", "exchange"),
                    ("合う", "あう", "to fit / to match"),
                    ("サイズ", "サイズ", "size"),
                    ("助かる", "たすかる", "to be a help / to save (someone) trouble"),
                    ("レシート", "レシート", "receipt"),
                ],
                "dialogue": [
                    ("you", "すみません、この服を返品したいんですが。", "すみません、このふくをへんぴんしたいんですが。",
                     "Sorry, I'd like to return this piece of clothing."),
                    ("them", "はい、何か問題がありますか。", "はい、なにかもんだいがありますか。",
                     "Yes, is there a problem?"),
                    ("you", "サイズが合わなかったんです。", "サイズがあわなかったんです。",
                     "The size didn't fit."),
                    ("them", "交換はいかがですか。同じもので別のサイズを。", "こうかんはいかがですか。おなじものでべつのサイズを。",
                     "How about an exchange? Same item, different size."),
                    ("you", "それは助かります。ありがとうございます。", "それはたすかります。ありがとうございます。",
                     "That would really help. Thank you."),
                    ("them", "では、レシートを見せてください。", "では、レシートをみせてください。",
                     "Then please show me the receipt."),
                ],
                "patterns": [
                    {
                        "text": "{x}はいかがですか",
                        "reading": "{x}はいかがですか",
                        "en": "How about {x}?",
                        "values": [
                            ("交換", "こうかん", "an exchange"),
                            ("返品", "へんぴん", "a return"),
                            ("修理", "しゅうり", "a repair"),
                        ],
                    },
                    {
                        "text": "{x}したいんですが",
                        "reading": "{x}したいんですが",
                        "en": "I'd like to {x}, but…",
                        "values": [
                            ("返品", "へんぴん", "return (it)"),
                            ("交換", "こうかん", "exchange (it)"),
                            ("注文をキャンセル", "ちゅうもんをキャンセル", "cancel the order"),
                        ],
                    },
                ],
                "notes": [
                    "〜たいんですが = softener: 'I'd like to …, but (would that be OK)?'  Very common at the start of a request.",
                ],
            },
            {
                "id": 36,
                "title": "At the bank",
                "goal": "Open an account, hand over ID, and ask about fees.",
                "vocab": [
                    ("銀行", "ぎんこう", "bank"),
                    ("口座", "こうざ", "account"),
                    ("開く", "ひらく", "to open"),
                    ("身分証明書", "みぶんしょうめいしょ", "ID"),
                    ("手数料", "てすうりょう", "fee / commission"),
                    ("無料", "むりょう", "free (of charge)"),
                ],
                "dialogue": [
                    ("them", "いらっしゃいませ。ご用件は何でしょうか。", "いらっしゃいませ。ごようけんはなんでしょうか。",
                     "Welcome. What can I do for you?"),
                    ("you", "新しい口座を開きたいのですが。この銀行は初めてです。",
                     "あたらしいこうざをひらきたいのですが。このぎんこうははじめてです。",
                     "I'd like to open a new account. It's my first time at this bank."),
                    ("them", "身分証明書をお願いします。", "みぶんしょうめいしょをおねがいします。",
                     "Please may I see your ID."),
                    ("you", "手数料はかかりますか。", "てすうりょうはかかりますか。",
                     "Is there a fee?"),
                    ("them", "いいえ、無料です。二十分ぐらいで終わります。", "いいえ、むりょうです。にじっぷんぐらいでおわります。",
                     "No, it's free. It'll take about twenty minutes."),
                    ("you", "わかりました。よろしくお願いします。", "わかりました。よろしくおねがいします。",
                     "Understood. Thank you in advance."),
                ],
                "patterns": [
                    {
                        "text": "{x}はいくらですか",
                        "reading": "{x}はいくらですか",
                        "en": "How much is the {x}?",
                        "values": [
                            ("手数料", "てすうりょう", "fee"),
                            ("年会費", "ねんかいひ", "annual fee"),
                            ("利息", "りそく", "interest"),
                        ],
                    },
                    {
                        "text": "{x}をお願いします",
                        "reading": "{x}をおねがいします",
                        "en": "{x}, please",
                        "kind": "object",
                        "values": [
                            ("身分証明書", "みぶんしょうめいしょ", "your ID"),
                            ("パスポート", "パスポート", "your passport"),
                            ("サイン", "サイン", "your signature"),
                        ],
                    },
                ],
                "notes": [
                    "開く has two readings: あく (intransitive: it opens) and ひらく (transitive: you open it).  口座を開く = こうざをひらく.",
                ],
            },
            {
                "id": 37,
                "title": "Have you ever…? (〜たことがあります)",
                "goal": "Talk about life experiences with 〜たことがあります.",
                "vocab": [
                    ("一度", "いちど", "once"),
                    ("二度", "にど", "twice"),
                    ("海外", "かいがい", "overseas / abroad"),
                    ("旅行", "りょこう", "travel / trip"),
                    ("運転", "うんてん", "driving"),
                    ("挑戦", "ちょうせん", "challenge / try"),
                ],
                "dialogue": [
                    ("them", "海外に行ったことがありますか。", "かいがいにいったことがありますか。",
                     "Have you ever been overseas?"),
                    ("you", "はい、二度あります。韓国と台湾です。", "はい、にどあります。かんこくとたいわんです。",
                     "Yes, twice. Korea and Taiwan."),
                    ("them", "一人で旅行したことがありますか。", "ひとりでりょこうしたことがありますか。",
                     "Have you ever traveled alone?"),
                    ("you", "あります。京都に行ったことがあります。", "あります。きょうとにいったことがあります。",
                     "Yes. I've been to Kyoto."),
                    ("them", "長距離のバスを運転したことはありますか。", "ちょうきょりのバスをうんてんしたことはありますか。",
                     "Have you ever driven a long-distance bus?"),
                    ("you", "ないです。でも、一度は挑戦してみたいです。", "ないです。でも、いちどはちょうせんしてみたいです。",
                     "Not yet. But I'd like to try it at least once."),
                ],
                "patterns": [
                    {
                        "text": "{x}に行ったことがあります",
                        "reading": "{x}にいったことがあります",
                        "en": "I have been to {x}",
                        "kind": "place",
                        "values": [
                            ("京都", "きょうと", "Kyoto"),
                            ("大阪", "おおさか", "Osaka"),
                            ("北海道", "ほっかいどう", "Hokkaido"),
                        ],
                    },
                    {
                        "text": "{x}したことがあります",
                        "reading": "{x}したことがあります",
                        "en": "I have {x} before",
                        "values": [
                            ("一人暮らし", "ひとりぐらし", "lived alone"),
                            ("スカイダイビング", "スカイダイビング", "gone skydiving"),
                            ("和菓子を作った", "わがしをつくった", "made Japanese sweets"),
                        ],
                    },
                ],
                "notes": [
                    "Vたことがあります = 'have V-ed (in your life)'.  Negative is Vたことがありません / Vたことはないです.",
                ],
            },
        ],
    },
]


LEVEL = {
    "band": 3,
    "id": 3,
    "code": "N3",
    "title": "JLPT N3 · Daily life",
    "focus": "Routines, home, weather, health, family, plans, hobbies, comparisons, and life experience (〜たことがあります).",
    "gate": {"min_pron_score": 70.0, "min_accuracy": 70.0, "min_completeness": 82.0},
    "units": UNITS,
}

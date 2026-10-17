# -*- coding: utf-8 -*-
"""
Pimsleur-style Japanese course data.

Pedagogy mirrors the Pimsleur method:
  * every lesson is built around one short, spoken conversation
  * new words are introduced inside that conversation, never in lists first
  * "them" lines are listening input, "you" lines must be spoken aloud
  * graduated interval recall: items come back at 10s -> 30s -> 75s gaps
  * difficulty tightens per unit (longer lines, stricter passing score)

Data layout: (text, reading, english, optional note)
  text    the line the way Japanese write it (漢字かな交じり)
  reading the same line in kana - this is the pinyin slot on the glasses
Dialogue layout: (speaker, text, reading, english)

Units 1-3 are JLPT N5, units 4-5 are JLPT N4.
"""

# ---------------------------------------------------------------------------
# Unit 1 - Greetings & courtesy. Short lines, very forgiving gate.
# ---------------------------------------------------------------------------
UNIT_1 = {
    "id": 1,
    "title": "Greetings & Courtesy",
    "focus": "Survive the first thirty seconds: hello, please, thank you, sorry.",
    "gate": {"min_pron_score": 62.0, "min_accuracy": 62.0, "min_completeness": 75.0},
    "lessons": [
        {
            "id": 1,
            "title": "Hello",
            "goal": "Greet someone, say you are well, and say goodbye.",
            "vocab": [
                ("こんにちは", "こんにちは", "hello", ""),
                ("おはようございます", "おはようございます", "good morning", ""),
                ("こんばんは", "こんばんは", "good evening", ""),
                ("ありがとう", "ありがとう", "thank you", ""),
                ("どういたしまして", "どういたしまして", "you're welcome", ""),
                ("さようなら", "さようなら", "goodbye", ""),
            ],
            "dialogue": [
                ("them", "こんにちは。", "こんにちは。", "Hello."),
                ("you", "こんにちは。", "こんにちは。", "Hello."),
                ("them", "お元気ですか。", "おげんきですか。", "How are you?"),
                ("you", "はい、元気です。", "はい、げんきです。", "Yes, I'm well."),
                ("them", "さようなら。", "さようなら。", "Goodbye."),
                ("you", "さようなら。またね。", "さようなら。またね。", "Goodbye. See you."),
            ],
            "notes": [
                "こんにちは is written 今日は, but it is always spelled in hiragana "
                "and the は is read 'wa'."
            ],
        },
        {
            "id": 2,
            "title": "Please & sorry",
            "goal": "Use お願いします to ask, and apologise when you are late.",
            "vocab": [
                ("お願いします", "おねがいします", "please", ""),
                ("すみません", "すみません", "excuse me / sorry", ""),
                ("ごめんなさい", "ごめんなさい", "I'm sorry", ""),
                ("大丈夫です", "だいじょうぶです", "it's fine / no problem", ""),
                ("どうぞ", "どうぞ", "here you go / go ahead", ""),
                ("ありがとうございます", "ありがとうございます", "thank you very much", ""),
            ],
            "dialogue": [
                ("them", "どうぞ、すわってください。", "どうぞ、すわってください。", "Please, sit down."),
                ("you", "ありがとうございます。", "ありがとうございます。", "Thank you very much."),
                ("them", "お茶はどうですか。", "おちゃはどうですか。", "How about some tea?"),
                ("you", "すみません、おそくなりました。", "すみません、おそくなりました。", "Sorry, I'm late."),
                ("them", "大丈夫ですよ。", "だいじょうぶですよ。", "It's fine."),
                ("you", "どうも、ありがとうございます。", "どうも、ありがとうございます。", "Thanks very much."),
            ],
            "notes": [
                "おねがいします turns any noun into a request: コーヒー、おねがいします."
            ],
        },
        {
            "id": 3,
            "title": "I don't understand",
            "goal": "Slow the conversation down and switch to English if you must.",
            "vocab": [
                ("分かりません", "わかりません", "I don't understand", ""),
                ("もう一度", "もういちど", "one more time", ""),
                ("ゆっくり", "ゆっくり", "slowly", ""),
                ("英語", "えいご", "English", ""),
                ("日本語", "にほんご", "Japanese", ""),
                ("少し", "すこし", "a little", ""),
            ],
            "dialogue": [
                ("them", "こんにちは。日本語がわかりますか。", "こんにちは。にほんごがわかりますか。",
                 "Hello. Do you understand Japanese?"),
                ("you", "すみません、よくわかりません。", "すみません、よくわかりません。",
                 "Sorry, I don't really understand."),
                ("them", "英語がわかりますか。", "えいごがわかりますか。", "Do you understand English?"),
                ("you", "はい、少しわかります。", "はい、すこしわかります。", "Yes, a little."),
                ("them", "じゃあ、英語で話しましょう。", "じゃあ、えいごではなしましょう。",
                 "Then let's speak English."),
                ("you", "はい、お願いします。", "はい、おねがいします。", "Yes, please."),
            ],
            "notes": [
                "もう一度、ゆっくりおねがいします = 'once more, slowly, please' - "
                "the single most useful phrase at N5."
            ],
        },
        {
            "id": 4,
            "title": "Where are you from",
            "goal": "Introduce yourself, ask a nationality, close the introduction politely.",
            "vocab": [
                ("初めまして", "はじめまして", "nice to meet you", ""),
                ("名前", "なまえ", "name", ""),
                ("出身", "しゅっしん", "where you come from", ""),
                ("アメリカ", "アメリカ", "America", ""),
                ("日本", "にほん", "Japan", ""),
                ("よろしくお願いします", "よろしくおねがいします", "pleased to meet you", ""),
            ],
            "dialogue": [
                ("them", "初めまして。お名前は？", "はじめまして。おなまえは？",
                 "Nice to meet you. What's your name?"),
                ("you", "マイクです。よろしくお願いします。", "マイクです。よろしくおねがいします。",
                 "I'm Mike. Pleased to meet you."),
                ("them", "出身はどこですか。", "しゅっしんはどこですか。", "Where are you from?"),
                ("you", "アメリカです。あなたは？", "アメリカです。あなたは？", "America. And you?"),
                ("them", "わたしは日本です。", "わたしはにほんです。", "I'm from Japan."),
                ("you", "そうですか。", "そうですか。", "I see."),
            ],
            "notes": [
                "よろしくおねがいします has no single English equivalent - it is the "
                "politeness that closes an introduction."
            ],
        },
        {
            "id": 5,
            "title": "This, that, how much",
            "goal": "Point at a thing, ask the price, and buy it.",
            "vocab": [
                ("これ", "これ", "this one", ""),
                ("それ", "それ", "that one", ""),
                ("いくら", "いくら", "how much", ""),
                ("高い", "たかい", "expensive", ""),
                ("安い", "やすい", "cheap", ""),
                ("ください", "ください", "please give me", ""),
            ],
            "dialogue": [
                ("them", "いらっしゃいませ。", "いらっしゃいませ。", "Welcome."),
                ("you", "すみません、これはいくらですか。", "すみません、これはいくらですか。",
                 "Excuse me, how much is this?"),
                ("them", "三千円です。", "さんぜんえんです。", "Three thousand yen."),
                ("you", "高いですね。", "たかいですね。", "That's expensive."),
                ("them", "これは千円です。", "これはせんえんです。", "This one is a thousand yen."),
                ("you", "じゃあ、これをください。", "じゃあ、これをください。", "Then I'll take this one."),
            ],
            "notes": ["ください after a noun means 'give me that': これをください。"],
        },
    ],
}

# ---------------------------------------------------------------------------
# Unit 2 - Getting around. Directions, transport, tickets.
# ---------------------------------------------------------------------------
UNIT_2 = {
    "id": 2,
    "title": "Getting Around",
    "focus": "Ask where things are, understand directions, take a train or a taxi.",
    "gate": {"min_pron_score": 66.0, "min_accuracy": 66.0, "min_completeness": 78.0},
    "lessons": [
        {
            "id": 6,
            "title": "Where is...?",
            "goal": "Ask for a place and follow two directions.",
            "vocab": [
                ("トイレ", "トイレ", "restroom", ""),
                ("駅", "えき", "station", ""),
                ("まっすぐ", "まっすぐ", "straight ahead", ""),
                ("右", "みぎ", "right", ""),
                ("左", "ひだり", "left", ""),
                ("近く", "ちかく", "nearby", ""),
            ],
            "dialogue": [
                ("you", "すみません、トイレはどこですか。", "すみません、トイレはどこですか。",
                 "Excuse me, where is the restroom?"),
                ("them", "まっすぐ行って、左です。", "まっすぐいって、ひだりです。",
                 "Go straight, it's on the left."),
                ("you", "遠いですか。", "とおいですか。", "Is it far?"),
                ("them", "いいえ、近くです。", "いいえ、ちかくです。", "No, it's close."),
                ("you", "ありがとうございます。", "ありがとうございます。", "Thank you."),
                ("them", "どういたしまして。", "どういたしまして。", "You're welcome."),
            ],
            "notes": [],
        },
        {
            "id": 7,
            "title": "I want to go to...",
            "goal": "Name a destination and choose between taxi and train.",
            "vocab": [
                ("空港", "くうこう", "airport", ""),
                ("行きたいです", "いきたいです", "I want to go", ""),
                ("タクシー", "タクシー", "taxi", ""),
                ("電車", "でんしゃ", "train", ""),
                ("バス", "バス", "bus", ""),
                ("乗ります", "のります", "to ride, to take", ""),
            ],
            "dialogue": [
                ("you", "空港に行きたいです。", "くうこうにいきたいです。", "I want to go to the airport."),
                ("them", "タクシーですか、電車ですか。", "タクシーですか、でんしゃですか。",
                 "Taxi or train?"),
                ("you", "いくらですか。", "いくらですか。", "How much is it?"),
                ("them", "タクシーは八千円です。電車は千二百円です。",
                 "タクシーははっせんえんです。でんしゃはせんにひゃくえんです。",
                 "The taxi is eight thousand yen, the train twelve hundred."),
                ("you", "じゃあ、電車に乗ります。", "じゃあ、でんしゃにのります。", "Then I'll take the train."),
                ("them", "駅はあそこです。", "えきはあそこです。", "The station is over there."),
            ],
            "notes": [],
        },
        {
            "id": 8,
            "title": "How do I get there?",
            "goal": "Ask for a route and understand stop counts and transfers.",
            "vocab": [
                ("どうやって", "どうやって", "how, by what means", ""),
                ("地下鉄", "ちかてつ", "subway", ""),
                ("乗り換え", "のりかえ", "transfer, changing trains", ""),
                ("降ります", "おります", "to get off", ""),
                ("歩いて", "あるいて", "on foot", ""),
                ("何番", "なんばん", "which number", ""),
            ],
            "dialogue": [
                ("you", "すみません、空港へはどうやって行きますか。",
                 "すみません、くうこうへはどうやっていきますか。",
                 "Excuse me, how do I get to the airport?"),
                ("them", "地下鉄で二駅です。", "ちかてつでにえきです。", "Two stops on the subway."),
                ("you", "乗り換えはありますか。", "のりかえはありますか。", "Is there a transfer?"),
                ("them", "はい、三駅目で乗り換えてください。", "はい、さんえきめでのりかえてください。",
                 "Yes, please change at the third stop."),
                ("you", "わかりました。ありがとうございます。", "わかりました。ありがとうございます。",
                 "Got it, thank you."),
                ("them", "いいえ、どういたしまして。", "いいえ、どういたしまして。", "Not at all."),
            ],
            "notes": [],
        },
        {
            "id": 9,
            "title": "Taking a taxi",
            "goal": "Give a destination, ask how long, and stop the taxi.",
            "vocab": [
                ("ここ", "ここ", "here", ""),
                ("ホテル", "ホテル", "hotel", ""),
                ("止めてください", "とめてください", "please stop", ""),
                ("荷物", "にもつ", "luggage", ""),
                ("十分", "じゅっぷん", "ten minutes", ""),
                ("後ろ", "うしろ", "the back", ""),
            ],
            "dialogue": [
                ("you", "すみません、このホテルまでお願いします。",
                 "すみません、このホテルまでおねがいします。", "To this hotel, please."),
                ("them", "はい。荷物は後ろにどうぞ。", "はい。にもつはうしろにどうぞ。",
                 "Sure. Put your luggage in the back."),
                ("you", "遠いですか。", "とおいですか。", "Is it far?"),
                ("them", "いいえ、十分くらいです。", "いいえ、じゅっぷんくらいです。",
                 "No, about ten minutes."),
                ("you", "じゃあ、ここで止めてください。", "じゃあ、ここでとめてください。",
                 "Then please stop here."),
                ("them", "はい、二千円です。", "はい、にせんえんです。", "Sure - two thousand yen."),
            ],
            "notes": [],
        },
        {
            "id": 10,
            "title": "Review: at the station",
            "goal": "Buy a ticket, find the platform, ask when the next train is.",
            "vocab": [
                ("切符", "きっぷ", "ticket", ""),
                ("券売機", "けんばいき", "ticket machine", ""),
                ("ホーム", "ホーム", "platform", ""),
                ("次", "つぎ", "next", ""),
                ("急行", "きゅうこう", "express train", ""),
                ("何時", "なんじ", "what time", ""),
            ],
            "dialogue": [
                ("you", "すみません、切符はどこで買いますか。", "すみません、きっぷはどこでかいますか。",
                 "Excuse me, where do I buy a ticket?"),
                ("them", "あの券売機で買ってください。", "あのけんばいきでかってください。",
                 "Please buy one at that machine."),
                ("you", "わかりました。ホームは何番ですか。", "わかりました。ホームはなんばんですか。",
                 "Got it. Which platform?"),
                ("them", "三番ホームです。", "さんばんホームです。", "Platform three."),
                ("you", "次の電車は何時ですか。", "つぎのでんしゃはなんじですか。",
                 "What time is the next train?"),
                ("them", "十時五分です。", "じゅうじごふんです。", "Ten oh five."),
            ],
            "notes": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Unit 3 - Food & ordering.
# ---------------------------------------------------------------------------
UNIT_3 = {
    "id": 3,
    "title": "Food & Ordering",
    "focus": "Order a meal, customise it, ask for the bill, invite someone to eat.",
    "gate": {"min_pron_score": 70.0, "min_accuracy": 70.0, "min_completeness": 80.0},
    "lessons": [
        {
            "id": 11,
            "title": "I'm hungry",
            "goal": "Say you are hungry and choose from a menu.",
            "vocab": [
                ("おなかがすきました", "おなかがすきました", "I'm hungry", ""),
                ("食べます", "たべます", "to eat", ""),
                ("メニュー", "メニュー", "menu", ""),
                ("おいしい", "おいしい", "delicious", ""),
                ("レストラン", "レストラン", "restaurant", ""),
                ("何", "なに", "what", ""),
            ],
            "dialogue": [
                ("them", "おなかがすきましたね。", "おなかがすきましたね。", "You're hungry, aren't you."),
                ("you", "はい。何を食べますか。", "はい。なにをたべますか。", "Yes. What shall we eat?"),
                ("them", "ここにメニューがあります。", "ここにメニューがあります。",
                 "There's a menu here."),
                ("you", "じゃあ、これをお願いします。", "じゃあ、これをおねがいします。",
                 "Then this one please."),
                ("them", "いいですね。おいしいですよ。", "いいですね。おいしいですよ。",
                 "Good choice. It's delicious."),
                ("you", "楽しみです。", "たのしみです。", "I'm looking forward to it."),
            ],
            "notes": [],
        },
        {
            "id": 12,
            "title": "Ordering",
            "goal": "Order a dish, refuse spice, and ask for a drink.",
            "vocab": [
                ("ラーメン", "ラーメン", "ramen", ""),
                ("餃子", "ぎょうざ", "dumplings", ""),
                ("辛い", "からい", "spicy", ""),
                ("お茶", "おちゃ", "tea", ""),
                ("飲みます", "のみます", "to drink", ""),
                ("野菜", "やさい", "vegetables", ""),
            ],
            "dialogue": [
                ("them", "ご注文は？", "ごちゅうもんは？", "What's your order?"),
                ("you", "ラーメンをお願いします。", "ラーメンをおねがいします。", "Ramen please."),
                ("them", "辛くしますか。", "からくしますか。", "Spicy?"),
                ("you", "いいえ、辛くしないでください。", "いいえ、からくしないでください。",
                 "No, please don't make it spicy."),
                ("them", "お飲み物は？", "おのみものは？", "And to drink?"),
                ("you", "お茶をください。", "おちゃをください。", "Tea please."),
            ],
            "notes": [
                "〜ないでください = 'please don't …'. 辛くしないでください is how you "
                "say no to chilli."
            ],
        },
        {
            "id": 13,
            "title": "The bill",
            "goal": "Compliment the food, ask for the bill, and pay.",
            "vocab": [
                ("おいしかったです", "おいしかったです", "it was delicious", ""),
                ("お会計", "おかいけい", "the bill", ""),
                ("全部で", "ぜんぶで", "in total", ""),
                ("カード", "カード", "card", ""),
                ("現金", "げんきん", "cash", ""),
                ("使えます", "つかえます", "can be used", ""),
            ],
            "dialogue": [
                ("you", "おいしかったです。", "おいしかったです。", "It was delicious."),
                ("them", "ありがとうございます。", "ありがとうございます。", "Thank you."),
                ("you", "お会計をお願いします。", "おかいけいをおねがいします。", "The bill please."),
                ("them", "全部で二千五百円です。", "ぜんぶでにせんごひゃくえんです。",
                 "That's two thousand five hundred yen in total."),
                ("you", "カードは使えますか。", "カードはつかえますか。", "Can I use a card?"),
                ("them", "はい、使えます。", "はい、つかえます。", "Yes, you can."),
            ],
            "notes": [],
        },
        {
            "id": 14,
            "title": "Let's eat together",
            "goal": "Invite someone, set a time, and offer to pay.",
            "vocab": [
                ("一緒に", "いっしょに", "together", ""),
                ("暇", "ひま", "free time", ""),
                ("昼ごはん", "ひるごはん", "lunch", ""),
                ("食べに行きませんか", "たべにいきませんか", "shall we go and eat?", ""),
                ("ごちそうします", "ごちそうします", "it's my treat", ""),
                ("十二時", "じゅうにじ", "twelve o'clock", ""),
            ],
            "dialogue": [
                ("you", "あした、暇ですか。", "あした、ひまですか。", "Are you free tomorrow?"),
                ("them", "はい、暇ですよ。", "はい、ひまですよ。", "Yes, I am."),
                ("you", "一緒に昼ごはんを食べに行きませんか。",
                 "いっしょにひるごはんをたべにいきませんか。", "Shall we go for lunch together?"),
                ("them", "いいですね。何時ですか。", "いいですね。なんじですか。",
                 "Sounds good. What time?"),
                ("you", "十二時はどうですか。わたしがごちそうします。",
                 "じゅうにじはどうですか。わたしがごちそうします。",
                 "How about twelve? It's my treat."),
                ("them", "いいですよ。ありがとうございます。", "いいですよ。ありがとうございます。",
                 "Fine with me. Thank you."),
            ],
            "notes": [],
        },
        {
            "id": 15,
            "title": "Review: at the restaurant",
            "goal": "Run a full restaurant exchange from door to table.",
            "vocab": [
                ("いらっしゃいませ", "いらっしゃいませ", "welcome (to the shop)", ""),
                ("何名", "なんめい", "how many people", ""),
                ("二人", "ふたり", "two people", ""),
                ("お水", "おみず", "water", ""),
                ("少々お待ちください", "しょうしょうおまちください", "one moment please", ""),
                ("注文", "ちゅうもん", "order", ""),
            ],
            "dialogue": [
                ("them", "いらっしゃいませ。何名さまですか。", "いらっしゃいませ。なんめいさまですか。",
                 "Welcome. How many?"),
                ("you", "二人です。", "ふたりです。", "Two."),
                ("them", "こちらへどうぞ。メニューです。", "こちらへどうぞ。メニューです。",
                 "This way please. Here's the menu."),
                ("you", "ありがとうございます。", "ありがとうございます。", "Thank you."),
                ("them", "ご注文はお決まりですか。", "ごちゅうもんはおきまりですか。",
                 "Are you ready to order?"),
                ("you", "はい、餃子とお水をお願いします。", "はい、ぎょうざとおみずをおねがいします。",
                 "Yes - dumplings and water please."),
                ("them", "はい、少々お待ちください。", "はい、しょうしょうおまちください。",
                 "Certainly, one moment please."),
            ],
            "notes": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Unit 4 - Shopping. Sizes, prices, stock, paying.
# ---------------------------------------------------------------------------
UNIT_4 = {
    "id": 4,
    "title": "Shopping",
    "focus": "Try things on, ask for a better price, ask for stock, and pay.",
    "gate": {"min_pron_score": 72.0, "min_accuracy": 72.0, "min_completeness": 82.0},
    "lessons": [
        {
            "id": 16,
            "title": "Can I try it on?",
            "goal": "Ask to try something, then ask for a different size or colour.",
            "vocab": [
                ("着てみてもいいですか", "きてみてもいいですか", "may I try it on?", ""),
                ("大きい", "おおきい", "big", ""),
                ("小さい", "ちいさい", "small", ""),
                ("サイズ", "サイズ", "size", ""),
                ("色", "いろ", "colour", ""),
                ("似合います", "にあいます", "to suit (someone)", ""),
            ],
            "dialogue": [
                ("you", "すみません、着てみてもいいですか。", "すみません、きてみてもいいですか。",
                 "Excuse me, may I try this on?"),
                ("them", "はい、どうぞ。", "はい、どうぞ。", "Yes, go ahead."),
                ("you", "少し大きいです。小さいサイズはありますか。",
                 "すこしおおきいです。ちいさいサイズはありますか。",
                 "It's a bit big. Do you have a smaller size?"),
                ("them", "はい、こちらです。", "はい、こちらです。", "Yes, here you are."),
                ("you", "いいですね。ほかの色はありますか。", "いいですね。ほかのいろはありますか。",
                 "Nice. Do you have other colours?"),
                ("them", "黒と白があります。", "くろとしろがあります。", "We have black and white."),
            ],
            "notes": [
                "〜てもいいですか = 'may I …?'. 着てみる is 'to try on' for anything "
                "you wear on the body."
            ],
        },
        {
            "id": 17,
            "title": "Can you make it cheaper?",
            "goal": "React to a price and negotiate it down.",
            "vocab": [
                ("安くなりませんか", "やすくなりませんか", "can you make it cheaper?", ""),
                ("予算", "よさん", "budget", ""),
                ("負けてください", "まけてください", "please give me a discount", ""),
                ("一万円", "いちまんえん", "ten thousand yen", ""),
                ("買います", "かいます", "to buy", ""),
                ("もう少し", "もうすこし", "a little more", ""),
            ],
            "dialogue": [
                ("you", "これはいくらですか。", "これはいくらですか。", "How much is this?"),
                ("them", "一万二千円です。", "いちまんにせんえんです。", "Twelve thousand yen."),
                ("you", "少し高いですね。安くなりませんか。", "すこしたかいですね。やすくなりませんか。",
                 "A bit expensive. Can you make it cheaper?"),
                ("them", "一万円はどうですか。", "いちまんえんはどうですか。", "How about ten thousand?"),
                ("you", "もう少し負けてください。", "もうすこしまけてください。",
                 "Please take a bit more off."),
                ("them", "じゃあ、九千円で。", "じゃあ、きゅうせんえんで。", "Then nine thousand."),
            ],
            "notes": [],
        },
        {
            "id": 18,
            "title": "Do you have...?",
            "goal": "Ask for stock and find out when it arrives.",
            "vocab": [
                ("充電器", "じゅうでんき", "charger", ""),
                ("売り切れ", "うりきれ", "sold out", ""),
                ("入荷", "にゅうか", "restock, delivery", ""),
                ("いつ", "いつ", "when", ""),
                ("午後", "ごご", "afternoon", ""),
                ("また来ます", "またきます", "I'll come again", ""),
            ],
            "dialogue": [
                ("you", "すみません、充電器はありますか。", "すみません、じゅうでんきはありますか。",
                 "Excuse me, do you have chargers?"),
                ("them", "すみません、売り切れです。", "すみません、うりきれです。", "Sorry, sold out."),
                ("you", "いつ入荷しますか。", "いつにゅうかしますか。", "When will you get more?"),
                ("them", "あしたの午後です。", "あしたのごごです。", "Tomorrow afternoon."),
                ("you", "わかりました。また来ます。", "わかりました。またきます。",
                 "Got it, I'll come back."),
                ("them", "ありがとうございます。お待ちしています。",
                 "ありがとうございます。おまちしています。", "Thank you, we'll expect you."),
            ],
            "notes": [],
        },
        {
            "id": 19,
            "title": "Paying",
            "goal": "Choose a payment method, refuse a bag, take a receipt.",
            "vocab": [
                ("払います", "はらいます", "to pay", ""),
                ("レジ", "レジ", "checkout, register", ""),
                ("袋", "ふくろ", "bag", ""),
                ("要ります", "いります", "to need", ""),
                ("ポイントカード", "ポイントカード", "loyalty card", ""),
                ("領収書", "りょうしゅうしょ", "receipt", ""),
            ],
            "dialogue": [
                ("you", "カードで払ってもいいですか。", "カードではらってもいいですか。",
                 "May I pay by card?"),
                ("them", "はい、レジへどうぞ。", "はい、レジへどうぞ。", "Yes, please come to the till."),
                ("you", "袋は要りません。", "ふくろはいりません。", "I don't need a bag."),
                ("them", "ポイントカードはありますか。", "ポイントカードはありますか。",
                 "Do you have a loyalty card?"),
                ("you", "いいえ、ありません。", "いいえ、ありません。", "No, I don't."),
                ("them", "はい、領収書です。ありがとうございます。",
                 "はい、りょうしゅうしょです。ありがとうございます。",
                 "Here's your receipt. Thank you."),
            ],
            "notes": [],
        },
        {
            "id": 20,
            "title": "Review: at the convenience store",
            "goal": "Buy a hot bento, get chopsticks, pay.",
            "vocab": [
                ("コンビニ", "コンビニ", "convenience store", ""),
                ("お弁当", "おべんとう", "boxed lunch", ""),
                ("温めます", "あたためます", "to heat up", ""),
                ("箸", "はし", "chopsticks", ""),
                ("レシート", "レシート", "receipt", ""),
                ("全部", "ぜんぶ", "everything", ""),
            ],
            "dialogue": [
                ("them", "いらっしゃいませ。", "いらっしゃいませ。", "Welcome."),
                ("you", "これをお願いします。", "これをおねがいします。", "This one please."),
                ("them", "温めますか。", "あたためますか。", "Shall I heat it up?"),
                ("you", "はい、お願いします。", "はい、おねがいします。", "Yes please."),
                ("them", "お箸は要りますか。", "おはしはいりますか。", "Do you need chopsticks?"),
                ("you", "はい、ください。全部でいくらですか。", "はい、ください。ぜんぶでいくらですか。",
                 "Yes please. How much in total?"),
                ("them", "六百八十円です。", "ろっぴゃくはちじゅうえんです。",
                 "Six hundred and eighty yen."),
            ],
            "notes": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Unit 5 - Time, plans & real opinions. Longest lines, strictest gate.
# ---------------------------------------------------------------------------
UNIT_5 = {
    "id": 5,
    "title": "Time, Plans & Opinions",
    "focus": "Tell the time, make plans, apologise, and give reasons.",
    "gate": {"min_pron_score": 75.0, "min_accuracy": 75.0, "min_completeness": 85.0},
    "lessons": [
        {
            "id": 21,
            "title": "What time is it?",
            "goal": "Ask and tell the time, including half past.",
            "vocab": [
                ("今", "いま", "now", ""),
                ("何時", "なんじ", "what time", ""),
                ("三時半", "さんじはん", "half past three", ""),
                ("午前", "ごぜん", "a.m.", ""),
                ("午後", "ごご", "p.m.", ""),
                ("来ます", "きます", "to come", ""),
            ],
            "dialogue": [
                ("you", "すみません、今何時ですか。", "すみません、いまなんじですか。",
                 "Excuse me, what time is it now?"),
                ("them", "三時半です。", "さんじはんです。", "Half past three."),
                ("you", "ありがとうございます。何時に出ますか。",
                 "ありがとうございます。なんじにでますか。", "Thanks. What time are you leaving?"),
                ("them", "五時に出ます。", "ごじにでます。", "I'm leaving at five."),
                ("you", "じゃあ、わたしは六時に来ます。", "じゃあ、わたしはろくじにきます。",
                 "Then I'll come at six."),
                ("them", "わかりました。また後で。", "わかりました。またあとで。", "Right. See you later."),
            ],
            "notes": ["半 = half, so 三時半 is 3:30. Minutes are 〜分 (ふん / ぷん)."],
        },
        {
            "id": 22,
            "title": "Days & dates",
            "goal": "Talk about today, tomorrow and the weekend; set a day.",
            "vocab": [
                ("今日", "きょう", "today", ""),
                ("明日", "あした", "tomorrow", ""),
                ("昨日", "きのう", "yesterday", ""),
                ("週末", "しゅうまつ", "weekend", ""),
                ("土曜日", "どようび", "Saturday", ""),
                ("都合", "つごう", "convenience, schedule", ""),
            ],
            "dialogue": [
                ("them", "明日、都合はどうですか。", "あした、つごうはどうですか。",
                 "How's tomorrow for you?"),
                ("you", "明日はちょっと。週末はどうですか。", "あしたはちょっと。しゅうまつはどうですか。",
                 "Tomorrow's difficult. How about the weekend?"),
                ("them", "週末は大丈夫です。", "しゅうまつはだいじょうぶです。", "The weekend is fine."),
                ("you", "じゃあ、土曜日の午後はどうですか。", "じゃあ、どようびのごごはどうですか。",
                 "Then how about Saturday afternoon?"),
                ("them", "いいですよ。三時に会いましょう。", "いいですよ。さんじにあいましょう。",
                 "Fine. Let's meet at three."),
                ("you", "わかりました。土曜日に会いましょう。", "わかりました。どようびにあいましょう。",
                 "Right, see you Saturday."),
            ],
            "notes": [],
        },
        {
            "id": 23,
            "title": "I'm late",
            "goal": "Apologise for being late and promise to hurry.",
            "vocab": [
                ("遅れました", "おくれました", "I'm late", ""),
                ("ごめんなさい", "ごめんなさい", "I'm sorry", ""),
                ("待ってください", "まってください", "please wait", ""),
                ("急ぎます", "いそぎます", "to hurry", ""),
                ("すぐ", "すぐ", "right away", ""),
                ("五分", "ごふん", "five minutes", ""),
            ],
            "dialogue": [
                ("you", "ごめんなさい、遅れました。", "ごめんなさい、おくれました。",
                 "Sorry, I'm late."),
                ("them", "大丈夫ですよ。今どこですか。", "だいじょうぶですよ。いまどこですか。",
                 "It's fine. Where are you now?"),
                ("you", "駅です。すぐ行きます。", "えきです。すぐいきます。",
                 "At the station. I'm coming right away."),
                ("them", "わかりました。五分だけ待ちます。", "わかりました。ごふんだけまちます。",
                 "OK. I'll wait five minutes."),
                ("you", "ありがとうございます。急ぎます。", "ありがとうございます。いそぎます。",
                 "Thanks, I'll hurry."),
            ],
            "notes": [],
        },
        {
            "id": 24,
            "title": "I think... because...",
            "goal": "Give an opinion and a reason - the start of real conversation.",
            "vocab": [
                ("と思います", "とおもいます", "I think that …", ""),
                ("どうして", "どうして", "why", ""),
                ("から", "から", "because", ""),
                ("でも", "でも", "but", ""),
                ("好きです", "すきです", "to like", ""),
                ("どうですか", "どうですか", "how is it?", ""),
            ],
            "dialogue": [
                ("them", "日本の食べ物はどうですか。", "にほんのたべものはどうですか。",
                 "What do you think of Japanese food?"),
                ("you", "とてもおいしいと思います。", "とてもおいしいとおもいます。",
                 "I think it's very good."),
                ("them", "何が好きですか。", "なにがすきですか。", "What do you like?"),
                ("you", "ラーメンが好きです。でも、辛いのは好きじゃありません。",
                 "ラーメンがすきです。でも、からいのはすきじゃありません。",
                 "I like ramen. But I don't like spicy things."),
                ("them", "どうしてですか。", "どうしてですか。", "Why is that?"),
                ("you", "辛すぎるからです。", "からすぎるからです。", "Because they're too spicy."),
            ],
            "notes": [
                "Plain form + とおもいます = 'I think that …'. から at the end of a "
                "clause gives the reason."
            ],
        },
        {
            "id": 25,
            "title": "Review: a real conversation",
            "goal": "Hold a short free conversation about yourself.",
            "vocab": [
                ("勉強しています", "べんきょうしています", "I am studying", ""),
                ("どのくらい", "どのくらい", "how long", ""),
                ("三か月", "さんかげつ", "three months", ""),
                ("まだ", "まだ", "still, not yet", ""),
                ("本当ですか", "ほんとうですか", "really?", ""),
                ("面白い", "おもしろい", "interesting", ""),
            ],
            "dialogue": [
                ("them", "こんにちは。出身はどこですか。", "こんにちは。しゅっしんはどこですか。",
                 "Hello. Where are you from?"),
                ("you", "アメリカです。あなたは？", "アメリカです。あなたは？", "America. And you?"),
                ("them", "わたしは大阪です。今どこに住んでいますか。",
                 "わたしはおおさかです。いまどこにすんでいますか。",
                 "I'm from Osaka. Where do you live now?"),
                ("you", "ホテルに住んでいます。近くです。", "ホテルにすんでいます。ちかくです。",
                 "I'm staying at a hotel. It's nearby."),
                ("them", "日本で何をしていますか。", "にほんでなにをしていますか。",
                 "What are you doing in Japan?"),
                ("you", "日本語を勉強しています。とても面白いです。",
                 "にほんごをべんきょうしています。とてもおもしろいです。",
                 "I'm studying Japanese. It's really interesting."),
                ("them", "本当ですか。どのくらい勉強しましたか。",
                 "ほんとうですか。どのくらいべんきょうしましたか。",
                 "Really? How long have you studied?"),
                ("you", "三か月です。まだ上手じゃありません。", "さんかげつです。まだじょうずじゃありません。",
                 "Three months. I'm not good yet."),
                ("them", "上手ですよ！", "じょうずですよ！", "You're good!"),
                ("you", "いいえ、まだまだです。", "いいえ、まだまだです。", "No, not yet."),
            ],
            "notes": [
                "まだまだです is the standard way to deflect a compliment - accepting "
                "one outright sounds arrogant."
            ],
        },
    ],
}

UNITS = [UNIT_1, UNIT_2, UNIT_3, UNIT_4, UNIT_5]

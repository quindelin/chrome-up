# -*- coding: utf-8 -*-
"""Reading passages, lessons 4-25 (N5 through early N4).

Same contract as `readings.py` - read that docstring before writing. In
short:

    PASSAGES[lesson_id] = {
        "title": "…", "title_en": "…",
        "chunks": [("日本語。", "にほんご。", "English."), …],
        "questions": [{"q": "…", "q_reading": "…", "q_en": "…",
                       "a": "…", "a_reading": "…", "a_en": "…",
                       "keywords": ["…"], "min_chars": 6}],
    }

Three or five chunks, one sentence each, each under 45 characters. The
passage uses the vocabulary and grammar of that lesson and earlier, and
only kanji the course has already taught - lessons 4-12 are still mostly
kana. One question, answerable from the text.

Verify with:  .venv/bin/python server/course/ja/readings.py
"""

PASSAGES: dict = {
    4: {
        "title": "マイクさんの出身",
        "title_en": "Where Mike is from",
        "chunks": [
            (
                "ともだちはアメリカの出身です。",
                "ともだちはアメリカのしゅっしんです。",
                "My friend is from America.",
            ),
            (
                "名前はマイクです。",
                "なまえはマイクです。",
                "His name is Mike.",
            ),
            (
                "日本語はまだ少しむずかしいです。",
                "にほんごはまだすこしむずかしいです。",
                "Japanese is still a little difficult for him.",
            ),
            (
                "「はじめまして、マイクです」と日本語でいいます。",
                "「はじめまして、マイクです」とにほんごでいいます。",
                "In Japanese he says, 'How do you do, I'm Mike'.",
            ),
            (
                "みんなに「よろしくお願いします」といいます。",
                "みんなに「よろしくおねがいします」といいます。",
                "To everyone he says 'pleased to meet you'.",
            ),
        ],
        "questions": [
            {
                "q": "マイクさんの出身はどこですか。",
                "q_reading": "マイクさんのしゅっしんはどこですか。",
                "q_en": "Where is Mike from?",
                "a": "アメリカの出身です。",
                "a_reading": "アメリカのしゅっしんです。",
                "a_en": "He is from America.",
                "keywords": ["アメリカ", "出身"],
                "min_chars": 6,
            },
        ],
    },
    5: {
        "title": "いくらですか",
        "title_en": "How much is it?",
        "chunks": [
            (
                "みせにパンとお茶があります。",
                "みせにパンとおちゃがあります。",
                "At the shop there is bread and tea.",
            ),
            (
                "「これはいくらですか」と、みせのひとにききます。",
                "「これはいくらですか」と、みせのひとにききます。",
                "He asks the shop assistant how much this is.",
            ),
            (
                "パンは高いですが、お茶は安いです。",
                "パンはたかいですが、おちゃはやすいです。",
                "The bread is expensive, but the tea is cheap.",
            ),
            (
                "「じゃあ、お茶をください」といって、かいます。",
                "「じゃあ、おちゃをください」といって、かいます。",
                "'Tea then, please,' he says, and buys it.",
            ),
        ],
        "questions": [
            {
                "q": "みせでなにをかいますか。",
                "q_reading": "みせでなにをかいますか。",
                "q_en": "What does he buy at the shop?",
                "a": "安いお茶をかいます。",
                "a_reading": "やすいおちゃをかいます。",
                "a_en": "He buys the cheap tea.",
                "keywords": ["安い", "お茶"],
                "min_chars": 6,
            },
        ],
    },
    6: {
        "title": "トイレはどこ",
        "title_en": "Where is the toilet?",
        "chunks": [
            (
                "駅の近くにトイレがあります。",
                "えきのちかくにトイレがあります。",
                "There is a toilet near the station.",
            ),
            (
                "「トイレはどこですか」と、駅のひとにききます。",
                "「トイレはどこですか」と、えきのひとにききます。",
                "He asks someone at the station where the toilet is.",
            ),
            (
                "「まっすぐ行って、右です」とこたえます。",
                "「まっすぐいって、みぎです」とこたえます。",
                "'Go straight on, it is on the right,' comes the answer.",
            ),
            (
                "「ありがとうございます」といって、まっすぐ行きます。",
                "「ありがとうございます」といって、まっすぐいきます。",
                "He says thank you and goes straight on.",
            ),
        ],
        "questions": [
            {
                "q": "トイレはどこにありますか。",
                "q_reading": "トイレはどこにありますか。",
                "q_en": "Where is the toilet?",
                "a": "駅の近くにあります。",
                "a_reading": "えきのちかくにあります。",
                "a_en": "It is near the station.",
                "keywords": ["駅", "近く"],
                "min_chars": 6,
            },
        ],
    },
    7: {
        "title": "空港へ",
        "title_en": "To the airport",
        "chunks": [
            (
                "わたしは空港に行きたいです。",
                "わたしはくうこうにいきたいです。",
                "I want to go to the airport.",
            ),
            (
                "電車とバスがあります。",
                "でんしゃとバスがあります。",
                "There is a train and a bus.",
            ),
            (
                "タクシーは高いですが、電車は安いです。",
                "タクシーはたかいですが、でんしゃはやすいです。",
                "The taxi is expensive, but the train is cheap.",
            ),
            (
                "ですから、電車に乗ります。",
                "ですから、でんしゃにのります。",
                "So I take the train.",
            ),
        ],
        "questions": [
            {
                "q": "なにに乗りますか。",
                "q_reading": "なににのりますか。",
                "q_en": "What does he take?",
                "a": "電車に乗ります。",
                "a_reading": "でんしゃにのります。",
                "a_en": "He takes the train.",
                "keywords": ["電車", "乗ります"],
                "min_chars": 6,
            },
        ],
    },
    8: {
        "title": "どうやって行きますか",
        "title_en": "How do I get there?",
        "chunks": [
            (
                "空港へはどうやって行きますか。",
                "くうこうへはどうやっていきますか。",
                "How do you get to the airport?",
            ),
            (
                "地下鉄で二駅です。",
                "ちかてつでにえきです。",
                "It is two stops on the subway.",
            ),
            (
                "三駅目で乗り換えて、電車に乗ります。",
                "さんえきめでのりかえて、でんしゃにのります。",
                "Change at the third stop and take the train.",
            ),
            (
                "駅を降りて、少し歩きます。",
                "えきをおりて、すこしあるきます。",
                "Get off at the station and walk a little.",
            ),
        ],
        "questions": [
            {
                "q": "三駅目でなにをしますか。",
                "q_reading": "さんえきめでなにをしますか。",
                "q_en": "What do you do at the third stop?",
                "a": "三駅目で乗り換えます。",
                "a_reading": "さんえきめでのりかえます。",
                "a_en": "You change trains at the third stop.",
                "keywords": ["三駅目", "乗り換え"],
                "min_chars": 6,
            },
        ],
    },
    9: {
        "title": "タクシーで",
        "title_en": "By taxi",
        "chunks": [
            (
                "タクシーに乗ります。",
                "タクシーにのります。",
                "He takes a taxi.",
            ),
            (
                "荷物は後ろにあります。",
                "にもつはうしろにあります。",
                "The luggage is at the back.",
            ),
            (
                "ホテルまで十分くらいです。",
                "ホテルまでじゅっぷんくらいです。",
                "It is about ten minutes to the hotel.",
            ),
            (
                "「ここで止めてください」といって、降ります。",
                "「ここでとめてください」といって、おります。",
                "'Stop here, please,' he says, and gets out.",
            ),
        ],
        "questions": [
            {
                "q": "ホテルまで何分くらいですか。",
                "q_reading": "ホテルまでなんぷんくらいですか。",
                "q_en": "About how many minutes is it to the hotel?",
                "a": "十分くらいです。",
                "a_reading": "じゅっぷんくらいです。",
                "a_en": "About ten minutes.",
                "keywords": ["十分"],
                "min_chars": 6,
            },
        ],
    },
    10: {
        "title": "駅で",
        "title_en": "At the station",
        "chunks": [
            (
                "駅で切符を買います。",
                "えきできっぷをかいます。",
                "He buys a ticket at the station.",
            ),
            (
                "あの券売機で買ってください。",
                "あのけんばいきでかってください。",
                "Please buy it at that ticket machine.",
            ),
            (
                "ホームは三番です。",
                "ホームはさんばんです。",
                "The platform is number three.",
            ),
            (
                "次の電車は十時五分です。",
                "つぎのでんしゃはじゅうじごふんです。",
                "The next train is at ten oh five.",
            ),
        ],
        "questions": [
            {
                "q": "次の電車は何時ですか。",
                "q_reading": "つぎのでんしゃはなんじですか。",
                "q_en": "What time is the next train?",
                "a": "十時五分です。",
                "a_reading": "じゅうじごふんです。",
                "a_en": "Ten oh five.",
                "keywords": ["十時", "五分"],
                "min_chars": 6,
            },
        ],
    },
    11: {
        "title": "おなかがすきました",
        "title_en": "I'm hungry",
        "chunks": [
            (
                "おなかがすきました。",
                "おなかがすきました。",
                "I am hungry.",
            ),
            (
                "ここにメニューがあります。",
                "ここにメニューがあります。",
                "There is a menu here.",
            ),
            (
                "「何を食べますか」と、ともだちにききます。",
                "「なにをたべますか」と、ともだちにききます。",
                "He asks a friend what they will eat.",
            ),
            (
                "「これをお願いします」といって、たのみます。",
                "「これをおねがいします」といって、たのみます。",
                "'This one, please,' he says, and orders it.",
            ),
        ],
        "questions": [
            {
                "q": "ここに何がありますか。",
                "q_reading": "ここになにがありますか。",
                "q_en": "What is here?",
                "a": "メニューがあります。",
                "a_reading": "メニューがあります。",
                "a_en": "There is a menu.",
                "keywords": ["メニュー"],
                "min_chars": 6,
            },
        ],
    },
    12: {
        "title": "ラーメンと餃子",
        "title_en": "Ramen and gyoza",
        "chunks": [
            (
                "ここはラーメンのみせです。",
                "ここはラーメンのみせです。",
                "This is a ramen shop.",
            ),
            (
                "ラーメンと餃子をお願いします。",
                "ラーメンとぎょうざをおねがいします。",
                "Ramen and gyoza, please.",
            ),
            (
                "「辛くしますか」ときかれました。",
                "「からくしますか」ときかれました。",
                "He was asked whether to make it spicy.",
            ),
            (
                "「いいえ、辛くしないでください」といって、お茶を飲みます。",
                "「いいえ、からくしないでください」といって、おちゃをのみます。",
                "'No, please don't make it spicy,' he says, and drinks tea.",
            ),
        ],
        "questions": [
            {
                "q": "何を飲みますか。",
                "q_reading": "なにをのみますか。",
                "q_en": "What does he drink?",
                "a": "お茶を飲みます。",
                "a_reading": "おちゃをのみます。",
                "a_en": "He drinks tea.",
                "keywords": ["お茶", "飲みます"],
                "min_chars": 6,
            },
        ],
    },
    13: {
        "title": "お会計",
        "title_en": "The bill",
        "chunks": [
            (
                "ごはんはおいしかったです。",
                "ごはんはおいしかったです。",
                "The meal was delicious.",
            ),
            (
                "「お会計をお願いします」といいます。",
                "「おかいけいをおねがいします」といいます。",
                "He says, 'The bill, please'.",
            ),
            (
                "全部で二千五百円です。",
                "ぜんぶでにせんごひゃくえんです。",
                "It comes to two thousand five hundred yen.",
            ),
            (
                "「カードは使えますか」と、みせのひとにききます。",
                "「カードはつかえますか」と、みせのひとにききます。",
                "He asks the assistant whether he can use a card.",
            ),
        ],
        "questions": [
            {
                "q": "全部でいくらですか。",
                "q_reading": "ぜんぶでいくらですか。",
                "q_en": "How much is it all together?",
                "a": "全部で二千五百円です。",
                "a_reading": "ぜんぶでにせんごひゃくえんです。",
                "a_en": "Two thousand five hundred yen in total.",
                "keywords": ["二千五百円"],
                "min_chars": 8,
            },
        ],
    },
    14: {
        "title": "一緒に昼ごはん",
        "title_en": "Lunch together",
        "chunks": [
            (
                "あした、暇ですか。",
                "あした、ひまですか。",
                "Are you free tomorrow?",
            ),
            (
                "一緒に昼ごはんを食べに行きませんか。",
                "いっしょにひるごはんをたべにいきませんか。",
                "Won't you come and have lunch with me?",
            ),
            (
                "十二時にレストランで会いませんか。",
                "じゅうにじにレストランであいませんか。",
                "Shall we meet at the restaurant at twelve?",
            ),
            (
                "わたしがごちそうしますよ。",
                "わたしがごちそうしますよ。",
                "It is my treat.",
            ),
        ],
        "questions": [
            {
                "q": "何時に会いますか。",
                "q_reading": "なんじにあいますか。",
                "q_en": "What time do they meet?",
                "a": "十二時に会います。",
                "a_reading": "じゅうにじにあいます。",
                "a_en": "They meet at twelve.",
                "keywords": ["十二時"],
                "min_chars": 6,
            },
        ],
    },
    15: {
        "title": "レストランで",
        "title_en": "At the restaurant",
        "chunks": [
            (
                "みせのひとが「いらっしゃいませ」といいます。",
                "みせのひとが「いらっしゃいませ」といいます。",
                "The waiter says 'welcome'.",
            ),
            (
                "「二人です」とこたえると、メニューをくれました。",
                "「ふたりです」とこたえると、メニューをくれました。",
                "When he answers 'two', they hand him a menu.",
            ),
            (
                "「ご注文はお決まりですか」ときかれました。",
                "「ごちゅうもんはおきまりですか」ときかれました。",
                "He was asked whether he was ready to order.",
            ),
            (
                "「餃子とお水をお願いします」とたのみました。",
                "「ぎょうざとおみずをおねがいします」とたのみました。",
                "'Gyoza and water, please,' he ordered.",
            ),
        ],
        "questions": [
            {
                "q": "何を注文しましたか。",
                "q_reading": "なにをちゅうもんしましたか。",
                "q_en": "What did they order?",
                "a": "餃子とお水を注文しました。",
                "a_reading": "ぎょうざとおみずをちゅうもんしました。",
                "a_en": "They ordered gyoza and water.",
                "keywords": ["餃子", "お水"],
                "min_chars": 8,
            },
        ],
    },
    16: {
        "title": "サイズと色",
        "title_en": "Size and colour",
        "chunks": [
            (
                "「着てみてもいいですか」と、みせのひとにききます。",
                "「きてみてもいいですか」と、みせのひとにききます。",
                "He asks the assistant if he can try it on.",
            ),
            (
                "これは少し大きいです。",
                "これはすこしおおきいです。",
                "This one is a little big.",
            ),
            (
                "小さいサイズはありますか。",
                "ちいさいサイズはありますか。",
                "Do you have a smaller size?",
            ),
            (
                "「ほかの色はありますか」というと、黒と白があります。",
                "「ほかのいろはありますか」というと、くろとしろがあります。",
                "When he asks for other colours, there are black and white.",
            ),
        ],
        "questions": [
            {
                "q": "ほかの色はありますか。",
                "q_reading": "ほかのいろはありますか。",
                "q_en": "Are there other colours?",
                "a": "はい、黒と白があります。",
                "a_reading": "はい、くろとしろがあります。",
                "a_en": "Yes, there is black and white.",
                "keywords": ["黒", "白"],
                "min_chars": 8,
            },
        ],
    },
    17: {
        "title": "安くなりませんか",
        "title_en": "Can you make it cheaper?",
        "chunks": [
            (
                "これは一万二千円です。",
                "これはいちまんにせんえんです。",
                "This one is twelve thousand yen.",
            ),
            (
                "「少し高いですね」と、みせのひとにいいました。",
                "「すこしたかいですね」と、みせのひとにいいました。",
                "'That is a bit expensive,' he said to the assistant.",
            ),
            (
                "「もう少し負けてください」とたのみます。",
                "「もうすこしまけてください」とたのみます。",
                "'Please knock a bit more off,' he asks.",
            ),
            (
                "じゃあ、九千円で買います。",
                "じゃあ、きゅうせんえんでかいます。",
                "All right, I will buy it for nine thousand yen.",
            ),
        ],
        "questions": [
            {
                "q": "いくらで買いましたか。",
                "q_reading": "いくらでかいましたか。",
                "q_en": "How much did he buy it for?",
                "a": "九千円で買いました。",
                "a_reading": "きゅうせんえんでかいました。",
                "a_en": "He bought it for nine thousand yen.",
                "keywords": ["九千円"],
                "min_chars": 8,
            },
        ],
    },
    18: {
        "title": "売り切れ",
        "title_en": "Sold out",
        "chunks": [
            (
                "すみません、充電器はありますか。",
                "すみません、じゅうでんきはありますか。",
                "Excuse me, do you have a charger?",
            ),
            (
                "「すみません、売り切れです」と、みせのひとがこたえます。",
                "「すみません、うりきれです」と、みせのひとがこたえます。",
                "'Sorry, we are sold out,' the assistant answers.",
            ),
            (
                "「いつ入荷しますか」と、もう一度ききます。",
                "「いつにゅうかしますか」と、もういちどききます。",
                "He asks once more when it comes in.",
            ),
            (
                "あしたの午後にもう一度来ます。",
                "あしたのごごにもういちどきます。",
                "He will come again tomorrow afternoon.",
            ),
        ],
        "questions": [
            {
                "q": "充電器はいつ入荷しますか。",
                "q_reading": "じゅうでんきはいつにゅうかしますか。",
                "q_en": "When does the charger come in?",
                "a": "あしたの午後に入荷します。",
                "a_reading": "あしたのごごににゅうかします。",
                "a_en": "It comes in tomorrow afternoon.",
                "keywords": ["午後", "入荷"],
                "min_chars": 8,
            },
        ],
    },
    19: {
        "title": "レジで",
        "title_en": "At the till",
        "chunks": [
            (
                "カードで払ってもいいですか。",
                "カードではらってもいいですか。",
                "May I pay by card?",
            ),
            (
                "「はい、レジへどうぞ」と、みせのひとがいいます。",
                "「はい、レジへどうぞ」と、みせのひとがいいます。",
                "'Yes, this way to the till,' says the assistant.",
            ),
            (
                "袋は要りませんが、領収書はください。",
                "ふくろはいりませんが、りょうしゅうしょはください。",
                "He does not need a bag, but he would like a receipt.",
            ),
            (
                "「ポイントカードはありますか」ときかれました。",
                "「ポイントカードはありますか」ときかれました。",
                "He was asked whether he has a points card.",
            ),
        ],
        "questions": [
            {
                "q": "領収書は要りますか。",
                "q_reading": "りょうしゅうしょはいりますか。",
                "q_en": "Does he need a receipt?",
                "a": "はい、領収書は要ります。",
                "a_reading": "はい、りょうしゅうしょはいります。",
                "a_en": "Yes, he needs a receipt.",
                "keywords": ["領収書", "要ります"],
                "min_chars": 8,
            },
        ],
    },
    20: {
        "title": "コンビニで",
        "title_en": "At the convenience store",
        "chunks": [
            (
                "コンビニでお弁当を買います。",
                "コンビニでおべんとうをかいます。",
                "He buys a bento at the convenience store.",
            ),
            (
                "「温めますか」ときかれました。",
                "「あたためますか」ときかれました。",
                "He was asked whether to heat it up.",
            ),
            (
                "「お箸は要りますか」と、またきかれました。",
                "「おはしはいりますか」と、またきかれました。",
                "Then they asked whether he needs chopsticks.",
            ),
            (
                "「はい、ください」といって、六百八十円払いました。",
                "「はい、ください」といって、ろっぴゃくはちじゅうえんはらいました。",
                "'Yes, please,' he says, and pays six hundred and eighty yen.",
            ),
        ],
        "questions": [
            {
                "q": "全部でいくらですか。",
                "q_reading": "ぜんぶでいくらですか。",
                "q_en": "How much is it in total?",
                "a": "全部で六百八十円です。",
                "a_reading": "ぜんぶでろっぴゃくはちじゅうえんです。",
                "a_en": "Six hundred and eighty yen in total.",
                "keywords": ["六百八十円"],
                "min_chars": 8,
            },
        ],
    },
    21: {
        "title": "今何時ですか",
        "title_en": "What time is it?",
        "chunks": [
            (
                "すみません、今何時ですか。",
                "すみません、いまなんじですか。",
                "Excuse me, what time is it now?",
            ),
            (
                "「三時半です」とこたえてくれました。",
                "「さんじはんです」とこたえてくれました。",
                "'Half past three,' came the answer.",
            ),
            (
                "わたしは五時に出ます。",
                "わたしはごじにでます。",
                "I am leaving at five.",
            ),
            (
                "じゃあ、六時に来ます。",
                "じゃあ、ろくじにきます。",
                "Then I will come at six.",
            ),
        ],
        "questions": [
            {
                "q": "今、何時ですか。",
                "q_reading": "いま、なんじですか。",
                "q_en": "What time is it now?",
                "a": "三時半です。",
                "a_reading": "さんじはんです。",
                "a_en": "It is half past three.",
                "keywords": ["三時半"],
                "min_chars": 6,
            },
        ],
    },
    22: {
        "title": "週末の都合",
        "title_en": "Plans for the weekend",
        "chunks": [
            (
                "明日、都合はどうですか。",
                "あした、つごうはどうですか。",
                "How does tomorrow look for you?",
            ),
            (
                "「すみません、明日はちょっと」とこたえます。",
                "「すみません、あしたはちょっと」とこたえます。",
                "'Sorry, tomorrow is a bit difficult,' comes the reply.",
            ),
            (
                "「じゃあ、土曜日の午後はどうですか」とききます。",
                "「じゃあ、どようびのごごはどうですか」とききます。",
                "'Then how about Saturday afternoon?' he asks.",
            ),
            (
                "土曜日の三時に会いましょう。",
                "どようびのさんじにあいましょう。",
                "Let us meet at three on Saturday.",
            ),
        ],
        "questions": [
            {
                "q": "何曜日の何時に会いますか。",
                "q_reading": "なんようびのなんじにあいますか。",
                "q_en": "On what day and at what time do they meet?",
                "a": "土曜日の三時に会います。",
                "a_reading": "どようびのさんじにあいます。",
                "a_en": "They meet at three on Saturday.",
                "keywords": ["土曜日", "三時"],
                "min_chars": 8,
            },
        ],
    },
    23: {
        "title": "遅れました",
        "title_en": "I'm late",
        "chunks": [
            (
                "ごめんなさい、遅れました。",
                "ごめんなさい、おくれました。",
                "Sorry, I am late.",
            ),
            (
                "「大丈夫ですよ」といって、待ってくれました。",
                "「だいじょうぶですよ」といって、まってくれました。",
                "'It is fine,' they say, and wait for him.",
            ),
            (
                "「今、駅です」とこたえて、急ぎます。",
                "「いま、えきです」とこたえて、いそぎます。",
                "'I am at the station now,' he answers, and hurries.",
            ),
            (
                "「五分だけ待ってください」とたのみました。",
                "「ごふんだけまってください」とたのみました。",
                "He asked them to wait just five minutes.",
            ),
        ],
        "questions": [
            {
                "q": "そのひとは今、どこにいますか。",
                "q_reading": "そのひとはいま、どこにいますか。",
                "q_en": "Where is he right now?",
                "a": "今、駅にいます。",
                "a_reading": "いま、えきにいます。",
                "a_en": "He is at the station now.",
                "keywords": ["駅", "います"],
                "min_chars": 6,
            },
        ],
    },
    24: {
        "title": "日本の食べ物",
        "title_en": "Japanese food",
        "chunks": [
            (
                "日本の食べ物はどうですか。",
                "にほんのたべものはどうですか。",
                "What do you think of Japanese food?",
            ),
            (
                "とてもおいしいと思います。",
                "とてもおいしいとおもいます。",
                "I think it is very good.",
            ),
            (
                "ラーメンが好きですが、辛いのは好きじゃありません。",
                "ラーメンがすきですが、からいのはすきじゃありません。",
                "I like ramen, but I do not like spicy things.",
            ),
            (
                "辛すぎるからです。",
                "からすぎるからです。",
                "It is because they are too spicy.",
            ),
        ],
        "questions": [
            {
                "q": "どうして辛いのが好きじゃありませんか。",
                "q_reading": "どうしてからいのがすきじゃありませんか。",
                "q_en": "Why doesn't he like spicy food?",
                "a": "辛すぎるからです。",
                "a_reading": "からすぎるからです。",
                "a_en": "Because it is too spicy.",
                "keywords": ["辛すぎる"],
                "min_chars": 6,
            },
        ],
    },
    25: {
        "title": "日本語の勉強",
        "title_en": "Studying Japanese",
        "chunks": [
            (
                "出身はアメリカですが、今は日本に住んでいます。",
                "しゅっしんはアメリカですが、いまはにほんにすんでいます。",
                "He is from America, but now he lives in Japan.",
            ),
            (
                "日本語を勉強しています。",
                "にほんごをべんきょうしています。",
                "He is studying Japanese.",
            ),
            (
                "三か月勉強しましたが、まだ上手じゃありません。",
                "さんかげつべんきょうしましたが、まだじょうずじゃありません。",
                "He studied for three months, but he is not good at it yet.",
            ),
            (
                "日本語はむずかしいですが、とても面白いです。",
                "にほんごはむずかしいですが、とてもおもしろいです。",
                "Japanese is hard, but it is very interesting.",
            ),
        ],
        "questions": [
            {
                "q": "どのくらい日本語を勉強しましたか。",
                "q_reading": "どのくらいにほんごをべんきょうしましたか。",
                "q_en": "How long has he studied Japanese?",
                "a": "三か月勉強しました。",
                "a_reading": "さんかげつべんきょうしました。",
                "a_en": "He studied for three months.",
                "keywords": ["三か月"],
                "min_chars": 8,
            },
        ],
    },
}

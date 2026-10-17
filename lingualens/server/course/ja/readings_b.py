# -*- coding: utf-8 -*-
"""Reading passages, lessons 26-49 (N4 through N3).

Same contract as `readings.py` - read that docstring before writing. In
short:

    PASSAGES[lesson_id] = {
        "title": "…", "title_en": "…",
        "chunks": [("日本語。", "にほんご。", "English."), …],
        "questions": [{"q": "…", "q_reading": "…", "q_en": "…",
                       "a": "…", "a_reading": "…", "a_en": "…",
                       "keywords": ["…"], "min_chars": 6}],
    }

Four to six chunks by now, one sentence each, each under 45 characters.
The passage uses the vocabulary and grammar of that lesson and earlier.
One question, answerable from the text, and it should be a question you
can only answer by having read the passage - not one you could guess from
the title.

Verify with:  .venv/bin/python server/course/ja/readings.py
"""

PASSAGES: dict = {
    26: {
        "title": "わたしの一日",
        "title_en": "My day",
        "chunks": [
            (
                "毎朝、七時ごろ起きます。",
                "まいあさ、しちじごろおきます。",
                "Every morning I get up at about seven.",
            ),
            (
                "七時半にうちを出ます。",
                "しちじはんにうちをでます。",
                "I leave the house at half past seven.",
            ),
            (
                "通勤は三十分ぐらいです。",
                "つうきんはさんじっぷんぐらいです。",
                "The commute takes about thirty minutes.",
            ),
            (
                "会社は九時から六時までです。",
                "かいしゃはくじからろくじまでです。",
                "The working day runs from nine until six.",
            ),
            (
                "よるは十二時ごろ寝ます。",
                "よるはじゅうにじごろねます。",
                "At night I go to bed at about twelve.",
            ),
        ],
        "questions": [
            {
                "q": "会社は何時から何時までですか。",
                "q_reading": "かいしゃはなんじからなんじまでですか。",
                "q_en": "What time does the working day run from and to?",
                "a": "九時から六時までです。",
                "a_reading": "くじからろくじまでです。",
                "a_en": "From nine until six.",
                "keywords": ["九時", "六時"],
                "min_chars": 6,
            },
        ],
    },
    27: {
        "title": "私の部屋",
        "title_en": "My rooms",
        "chunks": [
            (
                "私の家には三部屋あります。",
                "わたしのいえにはさんべやあります。",
                "There are three rooms in my house.",
            ),
            (
                "あまり広くないですが、明るいです。",
                "あまりひろくないですが、あかるいです。",
                "It isn't very big, but it is bright.",
            ),
            (
                "台所は狭いですが、料理は好きです。",
                "だいどころはせまいですが、りょうりはすきです。",
                "The kitchen is cramped, but I like cooking.",
            ),
            (
                "掃除は私がします。",
                "そうじはわたしがします。",
                "I am the one who does the cleaning.",
            ),
            (
                "洗濯は週末にします。",
                "せんたくはしゅうまつにします。",
                "I do the laundry at the weekend.",
            ),
        ],
        "questions": [
            {
                "q": "台所は広いですか。",
                "q_reading": "だいどころはひろいですか。",
                "q_en": "Is the kitchen big?",
                "a": "いいえ、狭いです。",
                "a_reading": "いいえ、せまいです。",
                "a_en": "No, it is cramped.",
                "keywords": ["狭い"],
                "min_chars": 4,
            },
        ],
    },
    28: {
        "title": "今日の天気",
        "title_en": "Today's weather",
        "chunks": [
            (
                "今朝は曇りで、少し涼しかったです。",
                "けさはくもりで、すこしすずしかったです。",
                "This morning was cloudy and a little cool.",
            ),
            (
                "午後から雨が降ると思います。",
                "ごごからあめがふるとおもいます。",
                "I think it will rain from the afternoon.",
            ),
            (
                "明日は晴れるでしょう。",
                "あしたははれるでしょう。",
                "Tomorrow will probably be sunny.",
            ),
            (
                "晴れた日は、散歩に行きたいです。",
                "はれたひは、さんぽにいきたいです。",
                "On clear days I want to go for a walk.",
            ),
            (
                "雨の日は、家でゆっくりします。",
                "あめのひは、いえでゆっくりします。",
                "On rainy days I take it easy at home.",
            ),
            (
                "週末は暖かくなるといいですね。",
                "しゅうまつはあたたかくなるといいですね。",
                "I hope it turns warm at the weekend.",
            ),
        ],
        "questions": [
            {
                "q": "今朝の天気はどうでしたか。",
                "q_reading": "けさのてんきはどうでしたか。",
                "q_en": "What was the weather like this morning?",
                "a": "曇りで、少し涼しかったです。",
                "a_reading": "くもりで、すこしすずしかったです。",
                "a_en": "It was cloudy and a little cool.",
                "keywords": ["曇り", "涼し"],
                "min_chars": 8,
            },
        ],
    },
    29: {
        "title": "今日は休みます",
        "title_en": "I'm taking today off",
        "chunks": [
            (
                "今朝から少し気分が悪いです。",
                "けさからすこしきぶんがわるいです。",
                "I have felt a little unwell since this morning.",
            ),
            (
                "少し熱があって、咳も出ます。",
                "すこしねつがあって、せきもでます。",
                "I have a slight temperature and a cough as well.",
            ),
            (
                "薬を飲んで、少し休みました。",
                "くすりをのんで、すこしやすみました。",
                "I took some medicine and rested a while.",
            ),
            (
                "午後から病院へ行きます。",
                "ごごからびょういんへいきます。",
                "I am going to the hospital this afternoon.",
            ),
            (
                "今日は家でゆっくり休みたいです。",
                "きょうはいえでゆっくりやすみたいです。",
                "I want to rest quietly at home today.",
            ),
        ],
        "questions": [
            {
                "q": "午後からどこへ行きますか。",
                "q_reading": "ごごからどこへいきますか。",
                "q_en": "Where are you going this afternoon?",
                "a": "病院へ行きます。",
                "a_reading": "びょういんへいきます。",
                "a_en": "I am going to the hospital.",
                "keywords": ["病院"],
                "min_chars": 5,
            },
        ],
    },
    30: {
        "title": "私の家族",
        "title_en": "My family",
        "chunks": [
            (
                "私の家族は四人です。",
                "わたしのかぞくはよにんです。",
                "There are four people in my family.",
            ),
            (
                "父と母と兄と私です。",
                "ちちとははとあにとわたしです。",
                "My father, my mother, my brother and me.",
            ),
            (
                "父は背が高いです。",
                "ちちはせがたかいです。",
                "My father is tall.",
            ),
            (
                "兄は優しい人です。",
                "あにはやさしいひとです。",
                "My brother is a kind person.",
            ),
            (
                "母は料理が上手です。",
                "はははりょうりがじょうずです。",
                "My mother is a good cook.",
            ),
            (
                "みんなは私が母に似ていると言います。",
                "みんなはわたしがははににているといいます。",
                "Everyone says I take after my mother.",
            ),
        ],
        "questions": [
            {
                "q": "母は何が上手ですか。",
                "q_reading": "はははなにがじょうずですか。",
                "q_en": "What is your mother good at?",
                "a": "料理が上手です。",
                "a_reading": "りょうりがじょうずです。",
                "a_en": "She is good at cooking.",
                "keywords": ["料理", "上手"],
                "min_chars": 6,
            },
        ],
    },
    31: {
        "title": "土曜日の約束",
        "title_en": "Plans for Saturday",
        "chunks": [
            (
                "土曜日にともだちと買い物に行きます。",
                "どようびにともだちとかいものにいきます。",
                "On Saturday I am going shopping with a friend.",
            ),
            (
                "午後は二人とも都合がいいです。",
                "ごごはふたりともつごうがいいです。",
                "The afternoon suits both of us.",
            ),
            (
                "駅の改札で二時に会いましょう。",
                "えきのかいさつでにじにあいましょう。",
                "Let's meet at the station barrier at two.",
            ),
            (
                "遅れないようにします。",
                "おくれないようにします。",
                "I will make sure I am not late.",
            ),
            (
                "とても楽しみです。",
                "とてもたのしみです。",
                "I am really looking forward to it.",
            ),
        ],
        "questions": [
            {
                "q": "何時にどこで会いますか。",
                "q_reading": "なんじにどこであいますか。",
                "q_en": "At what time and where are you meeting?",
                "a": "二時に駅の改札で会います。",
                "a_reading": "にじにえきのかいさつであいます。",
                "a_en": "At two, at the station barrier.",
                "keywords": ["二時", "改札"],
                "min_chars": 8,
            },
        ],
    },
    32: {
        "title": "私の趣味",
        "title_en": "My hobbies",
        "chunks": [
            (
                "私の趣味は音楽を聞くことです。",
                "わたしのしゅみはおんがくをきくことです。",
                "My hobby is listening to music.",
            ),
            (
                "映画を見ることも好きです。",
                "えいがをみることもすきです。",
                "I like watching films as well.",
            ),
            (
                "読書も時々します。",
                "どくしょもときどきします。",
                "I read too, now and then.",
            ),
            (
                "先月からギターを練習しています。",
                "せんげつからギターをれんしゅうしています。",
                "I have been practising the guitar since last month.",
            ),
            (
                "少しずつ上手になりたいです。",
                "すこしずつじょうずになりたいです。",
                "I want to get better little by little.",
            ),
        ],
        "questions": [
            {
                "q": "いつからギターを練習していますか。",
                "q_reading": "いつからギターをれんしゅうしていますか。",
                "q_en": "Since when have you been practising the guitar?",
                "a": "先月から練習しています。",
                "a_reading": "せんげつかられんしゅうしています。",
                "a_en": "Since last month.",
                "keywords": ["先月", "練習"],
                "min_chars": 8,
            },
        ],
    },
    33: {
        "title": "どちらにしますか",
        "title_en": "Which one shall I take",
        "chunks": [
            (
                "古い本と新しい本を読みました。",
                "ふるいほんとあたらしいほんをよみました。",
                "I read an old book and a new one.",
            ),
            (
                "新しい本のほうがおもしろかったです。",
                "あたらしいほんのほうがおもしろかったです。",
                "The new one was more interesting.",
            ),
            (
                "古い本は少しむずかしかったです。",
                "ふるいほんはすこしむずかしかったです。",
                "The old one was a little difficult.",
            ),
            (
                "新しい本は、むずかしいことばがすくないです。",
                "あたらしいほんは、むずかしいことばがすくないです。",
                "The new one has few difficult words.",
            ),
            (
                "だから、新しい本のほうが好きです。",
                "だから、あたらしいほんのほうがすきです。",
                "So I prefer the new one.",
            ),
            (
                "古い本は来年、もう一度読みます。",
                "ふるいほんはらいねん、もういちどよみます。",
                "I will read the old one again next year.",
            ),
        ],
        "questions": [
            {
                "q": "新しい本と古い本と、どちらが好きですか。",
                "q_reading": "あたらしいほんとふるいほんと、どちらがすきですか。",
                "q_en": "Which do you prefer, the new book or the old one?",
                "a": "新しい本のほうが好きです。",
                "a_reading": "あたらしいほんのほうがすきです。",
                "a_en": "I prefer the new one.",
                "keywords": ["新しい", "好き"],
                "min_chars": 8,
            },
        ],
    },
    34: {
        "title": "伝言メモ",
        "title_en": "Phone message",
        "chunks": [
            (
                "三時に田中さんから電話がありました。",
                "さんじにたなかさんからでんわがありました。",
                "At three there was a call from Tanaka.",
            ),
            (
                "山田さんは今、ちょっと出ています。",
                "やまださんはいま、ちょっとでています。",
                "Yamada is out at the moment.",
            ),
            (
                "田中さんの番号はノートに書きました。",
                "たなかさんのばんごうはノートにかきました。",
                "I wrote Tanaka's number in the notebook.",
            ),
            (
                "田中さんが折り返しの電話を待っています。",
                "たなかさんがおりかえしのでんわをまっています。",
                "Tanaka is waiting for you to call back.",
            ),
            (
                "五時までに電話してください。",
                "ごじまでにでんわしてください。",
                "Please call before five.",
            ),
        ],
        "questions": [
            {
                "q": "田中さんの番号はどこに書きましたか。",
                "q_reading": "たなかさんのばんごうはどこにかきましたか。",
                "q_en": "Where did you write Tanaka's number?",
                "a": "ノートに書きました。",
                "a_reading": "ノートにかきました。",
                "a_en": "I wrote it in the notebook.",
                "keywords": ["ノート"],
                "min_chars": 5,
            },
        ],
    },
    35: {
        "title": "昨日の買い物",
        "title_en": "Yesterday's shopping",
        "chunks": [
            (
                "昨日、みせで服を買いました。",
                "きのう、みせでふくをかいました。",
                "Yesterday I bought some clothes at a shop.",
            ),
            (
                "家で着てみると、サイズが合いませんでした。",
                "いえできてみると、サイズがあいませんでした。",
                "When I tried them on at home the size did not fit.",
            ),
            (
                "今日、みせへ返品に行きました。",
                "きょう、みせへへんぴんにいきました。",
                "Today I went back to the shop to return them.",
            ),
            (
                "同じ服の別のサイズを出してくれました。",
                "おなじふくのべつのサイズをだしてくれました。",
                "They brought out the same clothes in another size.",
            ),
            (
                "サイズを交換して、とても助かりました。",
                "サイズをこうかんして、とてもたすかりました。",
                "They exchanged the size and it really helped.",
            ),
            (
                "次はサイズをよく見てから買います。",
                "つぎはサイズをよくみてからかいます。",
                "Next time I will check the size before buying.",
            ),
        ],
        "questions": [
            {
                "q": "どうして服を返品しましたか。",
                "q_reading": "どうしてふくをへんぴんしましたか。",
                "q_en": "Why did you return the clothes?",
                "a": "サイズが合わなかったからです。",
                "a_reading": "サイズがあわなかったからです。",
                "a_en": "Because the size did not fit.",
                "keywords": ["サイズ", "合わ"],
                "min_chars": 8,
            },
        ],
    },
    36: {
        "title": "新しい口座",
        "title_en": "A new account",
        "chunks": [
            (
                "今日、初めてこの銀行へ行きました。",
                "きょう、はじめてこのぎんこうへいきました。",
                "Today I went to this bank for the first time.",
            ),
            (
                "新しい口座を開きたいと話しました。",
                "あたらしいこうざをひらきたいとはなしました。",
                "I said I wanted to open a new account.",
            ),
            (
                "身分証明書を見せました。",
                "みぶんしょうめいしょをみせました。",
                "I showed them my identification.",
            ),
            (
                "手数料は無料でした。",
                "てすうりょうはむりょうでした。",
                "There was no fee.",
            ),
            (
                "二十分ぐらいで終わりました。",
                "にじっぷんぐらいでおわりました。",
                "It was finished in about twenty minutes.",
            ),
            (
                "これからこの銀行を使います。",
                "これからこのぎんこうをつかいます。",
                "From now on I will use this bank.",
            ),
        ],
        "questions": [
            {
                "q": "何分ぐらいで終わりましたか。",
                "q_reading": "なんぷんぐらいでおわりましたか。",
                "q_en": "About how many minutes did it take?",
                "a": "二十分ぐらいで終わりました。",
                "a_reading": "にじっぷんぐらいでおわりました。",
                "a_en": "It was finished in about twenty minutes.",
                "keywords": ["二十分", "終わり"],
                "min_chars": 8,
            },
        ],
    },
    37: {
        "title": "海外旅行",
        "title_en": "Travel abroad",
        "chunks": [
            (
                "私は海外に二度行ったことがあります。",
                "わたしはかいがいににどいったことがあります。",
                "I have been abroad twice.",
            ),
            (
                "韓国と台湾へ行きました。",
                "かんこくとたいわんへいきました。",
                "I went to Korea and Taiwan.",
            ),
            (
                "一人で旅行したこともあります。",
                "ひとりでりょこうしたこともあります。",
                "I have travelled alone too.",
            ),
            (
                "長距離のバスを運転したことはありません。",
                "ちょうきょりのバスをうんてんしたことはありません。",
                "I have never driven a long-distance bus.",
            ),
            (
                "でも、一度は挑戦してみたいです。",
                "でも、いちどはちょうせんしてみたいです。",
                "But I would like to try it once.",
            ),
            (
                "来年、また海外へ行きたいです。",
                "らいねん、またかいがいへいきたいです。",
                "Next year I want to go abroad again.",
            ),
        ],
        "questions": [
            {
                "q": "海外に何度行ったことがありますか。",
                "q_reading": "かいがいになんどいったことがありますか。",
                "q_en": "How many times have you been abroad?",
                "a": "二度行ったことがあります。",
                "a_reading": "にどいったことがあります。",
                "a_en": "I have been twice.",
                "keywords": ["二度", "行った"],
                "min_chars": 7,
            },
        ],
    },
    38: {
        "title": "部長の転勤",
        "title_en": "The manager's transfer",
        "chunks": [
            (
                "部長が来月から転勤するそうです。",
                "ぶちょうがらいげつからてんきんするそうです。",
                "I hear the manager is transferring from next month.",
            ),
            (
                "同僚の佐藤さんに聞きました。",
                "どうりょうのさとうさんにききました。",
                "I heard it from my colleague Sato.",
            ),
            (
                "佐藤さんの話では、噂ではありません。",
                "さとうさんのはなしでは、うわさではありません。",
                "According to Sato it is not a rumour.",
            ),
            (
                "本当に今月いっぱいでいなくなります。",
                "ほんとうにこんげついっぱいでいなくなります。",
                "He really is leaving at the end of this month.",
            ),
            (
                "次の部長は東京から来るそうです。",
                "つぎのぶちょうはとうきょうからくるそうです。",
                "They say the next manager is coming from Tokyo.",
            ),
            (
                "それは知りませんでした。",
                "それはしりませんでした。",
                "I did not know that.",
            ),
        ],
        "questions": [
            {
                "q": "誰にその話を聞きましたか。",
                "q_reading": "だれにそのはなしをききましたか。",
                "q_en": "Who did you hear that from?",
                "a": "同僚の佐藤さんに聞きました。",
                "a_reading": "どうりょうのさとうさんにききました。",
                "a_en": "I heard it from my colleague Sato.",
                "keywords": ["佐藤"],
                "min_chars": 8,
            },
        ],
    },
    39: {
        "title": "遅刻の理由",
        "title_en": "Why I was late",
        "chunks": [
            (
                "今朝は遅刻して、すみませんでした。",
                "けさはちこくして、すみませんでした。",
                "I am sorry I was late this morning.",
            ),
            (
                "電車の事故の影響で、遅れました。",
                "でんしゃのじこのえいきょうで、おくれました。",
                "I was delayed because of a train accident.",
            ),
            (
                "事故のために、ほかの人も遅れたそうです。",
                "じこのために、ほかのひともおくれたそうです。",
                "Apparently other people were late too, because of it.",
            ),
            (
                "もっと早く報告すればよかったです。",
                "もっとはやくほうこくすればよかったです。",
                "I should have reported it sooner.",
            ),
            (
                "明日は気をつけます。",
                "あしたはきをつけます。",
                "I will be careful tomorrow.",
            ),
        ],
        "questions": [
            {
                "q": "どうして遅れましたか。",
                "q_reading": "どうしておくれましたか。",
                "q_en": "Why were you late?",
                "a": "電車の事故の影響で、遅れました。",
                "a_reading": "でんしゃのじこのえいきょうで、おくれました。",
                "a_en": "Because of a train accident.",
                "keywords": ["事故", "影響"],
                "min_chars": 10,
            },
        ],
    },
    40: {
        "title": "会議のあとで",
        "title_en": "After the meeting",
        "chunks": [
            (
                "今朝、部長に呼ばれました。",
                "けさ、ぶちょうによばれました。",
                "This morning I was called in by the manager.",
            ),
            (
                "遅刻のことで注意されました。",
                "ちこくのことでちゅういされました。",
                "I was told off about being late.",
            ),
            (
                "会議で意見を言いました。",
                "かいぎでいけんをいいました。",
                "I gave my opinion at the meeting.",
            ),
            (
                "そのあと、上司に褒められました。",
                "そのあと、じょうしにほめられました。",
                "After that I was praised by my boss.",
            ),
            (
                "少し困りましたが、いい一日でした。",
                "すこしこまりましたが、いいいちにちでした。",
                "It was awkward at times, but a good day.",
            ),
        ],
        "questions": [
            {
                "q": "会議のあと、誰に褒められましたか。",
                "q_reading": "かいぎのあと、だれにほめられましたか。",
                "q_en": "After the meeting, who praised you?",
                "a": "上司に褒められました。",
                "a_reading": "じょうしにほめられました。",
                "a_en": "I was praised by my boss.",
                "keywords": ["上司", "褒められ"],
                "min_chars": 8,
            },
        ],
    },
    41: {
        "title": "新しい企画",
        "title_en": "The new project",
        "chunks": [
            (
                "新しい企画は私が担当します。",
                "あたらしいきかくはわたしがたんとうします。",
                "I am in charge of the new project.",
            ),
            (
                "一人では大変なので、後輩にも手伝わせます。",
                "ひとりではたいへんなので、こうはいにもてつだわせます。",
                "It is a lot for one person, so I will have a junior help too.",
            ),
            (
                "資料は後輩に用意させました。",
                "しりょうはこうはいによういさせました。",
                "I had the junior prepare the materials.",
            ),
            (
                "時間は足ります。",
                "じかんはたります。",
                "There is enough time.",
            ),
            (
                "お客さんを待たせるのは避けたいです。",
                "おきゃくさんをまたせるのはさけたいです。",
                "I want to avoid keeping the customers waiting.",
            ),
            (
                "明日までに資料を全部用意します。",
                "あしたまでにしりょうをぜんぶよういします。",
                "I will have all the materials ready by tomorrow.",
            ),
        ],
        "questions": [
            {
                "q": "資料は誰に用意させましたか。",
                "q_reading": "しりょうはだれによういさせましたか。",
                "q_en": "Who did you have prepare the materials?",
                "a": "後輩に用意させました。",
                "a_reading": "こうはいによういさせました。",
                "a_en": "I had a junior prepare them.",
                "keywords": ["後輩", "用意"],
                "min_chars": 7,
            },
        ],
    },
    42: {
        "title": "今朝のニュース",
        "title_en": "This morning's news",
        "chunks": [
            (
                "今朝のニュースを見ました。",
                "けさのニュースをみました。",
                "I watched the news this morning.",
            ),
            (
                "ニュースによると、経済が少し良くなるそうです。",
                "ニュースによると、けいざいがすこしよくなるそうです。",
                "According to the news the economy will improve a little.",
            ),
            (
                "人口は減る一方だと思っていました。",
                "じんこうはへるいっぽうだとおもっていました。",
                "I had thought the population was only falling.",
            ),
            (
                "地方は減っていますが、都市は増えています。",
                "ちほうはへっていますが、としはふえています。",
                "The countryside is shrinking, but the cities are growing.",
            ),
            (
                "来月の選挙にも影響するでしょう。",
                "らいげつのせんきょにもえいきょうするでしょう。",
                "It will probably affect next month's election too.",
            ),
        ],
        "questions": [
            {
                "q": "人口はどうなっていますか。",
                "q_reading": "じんこうはどうなっていますか。",
                "q_en": "What is happening to the population?",
                "a": "地方は減っていますが、都市は増えています。",
                "a_reading": "ちほうはへっていますが、としはふえています。",
                "a_en": "The countryside is shrinking but the cities are growing.",
                "keywords": ["減って", "増えて"],
                "min_chars": 12,
            },
        ],
    },
    43: {
        "title": "なくなった財布",
        "title_en": "The missing wallet",
        "chunks": [
            (
                "会社で財布がなくなりました。",
                "かいしゃでさいふがなくなりました。",
                "A wallet went missing at the office.",
            ),
            (
                "犯人は社内にいた人に違いありません。",
                "はんにんはしゃないにいたひとにちがいありません。",
                "The culprit must be someone who was in the building.",
            ),
            (
                "鍵の記録があります。",
                "かぎのきろくがあります。",
                "There are records from the key system.",
            ),
            (
                "それを見れば、分かるはずです。",
                "それをみれば、わかるはずです。",
                "If we look at them we should be able to tell.",
            ),
            (
                "現場にいた人の顔は、少しだけ覚えています。",
                "げんばにいたひとのかおは、すこしだけおぼえています。",
                "I remember the faces of the people there, a little.",
            ),
            (
                "逃げる人はいなかったと思います。",
                "にげるひとはいなかったとおもいます。",
                "I do not think anyone ran away.",
            ),
        ],
        "questions": [
            {
                "q": "何の記録がありますか。",
                "q_reading": "なにのきろくがありますか。",
                "q_en": "What records are there?",
                "a": "鍵の記録があります。",
                "a_reading": "かぎのきろくがあります。",
                "a_en": "There are records from the key system.",
                "keywords": ["鍵", "記録"],
                "min_chars": 6,
            },
        ],
    },
    44: {
        "title": "田中さんの案",
        "title_en": "Tanaka's proposal",
        "chunks": [
            (
                "田中さんの案を読みました。",
                "たなかさんのあんをよみました。",
                "I have read Tanaka's proposal.",
            ),
            (
                "私は反対しているわけではありません。",
                "わたしははんたいしているわけではありません。",
                "It is not that I am against it.",
            ),
            (
                "賛成とも、簡単には言えません。",
                "さんせいとも、かんたんにはいえません。",
                "I cannot simply say I am for it either.",
            ),
            (
                "難しいところもあります。",
                "むずかしいところもあります。",
                "There are some difficult parts.",
            ),
            (
                "全部ではなく、一部でいいと思います。",
                "ぜんぶではなく、いちぶでいいとおもいます。",
                "Not all of it - I think part of it is enough.",
            ),
            (
                "明日、もう少し説明します。",
                "あした、もうすこしせつめいします。",
                "I will explain a little more tomorrow.",
            ),
        ],
        "questions": [
            {
                "q": "全部を直したほうがいいですか。",
                "q_reading": "ぜんぶをなおしたほうがいいですか。",
                "q_en": "Is it better to fix all of it?",
                "a": "いいえ、全部ではなく、一部でいいです。",
                "a_reading": "いいえ、ぜんぶではなく、いちぶでいいです。",
                "a_en": "No - not all of it, part of it is fine.",
                "keywords": ["全部", "一部"],
                "min_chars": 10,
            },
        ],
    },
    45: {
        "title": "昨日の発表",
        "title_en": "Yesterday's presentation",
        "chunks": [
            (
                "昨日、会社で発表をしました。",
                "きのう、かいしゃではっぴょうをしました。",
                "Yesterday I gave a presentation at work.",
            ),
            (
                "準備をしたおかげで、失敗しませんでした。",
                "じゅんびをしたおかげで、しっぱいしませんでした。",
                "Thanks to preparing, it did not go wrong.",
            ),
            (
                "少し緊張しました。",
                "すこしきんちょうしました。",
                "I was a little nervous.",
            ),
            (
                "睡眠が足りなかったせいか、声が小さかったです。",
                "すいみんがたりなかったせいか、こえがちいさかったです。",
                "Perhaps for lack of sleep, my voice was quiet.",
            ),
            (
                "体調は大丈夫です。",
                "たいちょうはだいじょうぶです。",
                "I am physically fine.",
            ),
            (
                "油断しないで、もう一度準備します。",
                "ゆだんしないで、もういちどじゅんびします。",
                "Without getting careless, I will prepare again.",
            ),
        ],
        "questions": [
            {
                "q": "どうして失敗しませんでしたか。",
                "q_reading": "どうしてしっぱいしませんでしたか。",
                "q_en": "Why did it not go wrong?",
                "a": "準備をしたおかげです。",
                "a_reading": "じゅんびをしたおかげです。",
                "a_en": "Because I prepared.",
                "keywords": ["準備", "おかげ"],
                "min_chars": 7,
            },
        ],
    },
    46: {
        "title": "明日の出発",
        "title_en": "Tomorrow's departure",
        "chunks": [
            (
                "明日の天気予報は、午後から雨です。",
                "あしたのてんきよほうは、ごごからあめです。",
                "Tomorrow's forecast is rain from the afternoon.",
            ),
            (
                "雨なら、旅行は中止します。",
                "あめなら、りょこうはちゅうしします。",
                "If it rains we will cancel the trip.",
            ),
            (
                "晴れたら、六時に出発します。",
                "はれたら、ろくじにしゅっぱつします。",
                "If it is clear we will leave at six.",
            ),
            (
                "傘を持って行けば、心配はいりません。",
                "かさをもっていけば、しんぱいはいりません。",
                "If you take an umbrella there is nothing to worry about.",
            ),
            (
                "早いほうが道が空いています。",
                "はやいほうがみちがあいています。",
                "The earlier we go, the emptier the roads.",
            ),
        ],
        "questions": [
            {
                "q": "雨なら、どうしますか。",
                "q_reading": "あめなら、どうしますか。",
                "q_en": "What will you do if it rains?",
                "a": "旅行は中止します。",
                "a_reading": "りょこうはちゅうしします。",
                "a_en": "We will cancel the trip.",
                "keywords": ["中止"],
                "min_chars": 6,
            },
        ],
    },
    47: {
        "title": "古いパソコン",
        "title_en": "An old computer",
        "chunks": [
            (
                "このパソコンは古いですが、性能はいいです。",
                "このパソコンはふるいですが、せいのうはいいです。",
                "This computer is old, but its performance is good.",
            ),
            (
                "修理すれば、まだ使えます。",
                "しゅうりすれば、まだつかえます。",
                "If you repair it, it can still be used.",
            ),
            (
                "修理しても、値段は安いです。",
                "しゅうりしても、ねだんはやすいです。",
                "Even with the repair, the price is low.",
            ),
            (
                "壊れても、すぐ直ると思います。",
                "こわれても、すぐなおるとおもいます。",
                "Even if it breaks, I think it can be fixed at once.",
            ),
            (
                "古いにもかかわらず、人気があります。",
                "ふるいにもかかわらず、にんきがあります。",
                "Old as it is, it is popular.",
            ),
            (
                "それで、買う決心がつきました。",
                "それで、かうけっしんがつきました。",
                "So I made up my mind to buy it.",
            ),
        ],
        "questions": [
            {
                "q": "このパソコンの値段はどうですか。",
                "q_reading": "このパソコンのねだんはどうですか。",
                "q_en": "What about the price of this computer?",
                "a": "修理しても、値段は安いです。",
                "a_reading": "しゅうりしても、ねだんはやすいです。",
                "a_en": "Even with the repair, the price is low.",
                "keywords": ["値段", "安い"],
                "min_chars": 8,
            },
        ],
    },
    48: {
        "title": "新しいシステム",
        "title_en": "The new system",
        "chunks": [
            (
                "締め切りは今週ですが、少し遅れてしまいました。",
                "しめきりはこんしゅうですが、すこしおくれてしまいました。",
                "The deadline is this week, but we have slipped a little.",
            ),
            (
                "新しいシステムは来週の水曜日に完成する予定です。",
                "あたらしいシステムはらいしゅうのすいようびにかんせいするよていです。",
                "The new system is due to be finished next Wednesday.",
            ),
            (
                "徹夜で直すのは無理です。",
                "てつやでなおすのはむりです。",
                "Fixing it by working all night is out of the question.",
            ),
            (
                "人員を増やすことになっています。",
                "じんいんをふやすことになっています。",
                "It has been decided to add more people.",
            ),
            (
                "金曜日までには終わらせます。",
                "きんようびまでにはおわらせます。",
                "We will get it finished by Friday.",
            ),
            (
                "それなら、間に合うと思います。",
                "それなら、まにあうとおもいます。",
                "In that case I think we will make it.",
            ),
        ],
        "questions": [
            {
                "q": "新しいシステムはいつ完成しますか。",
                "q_reading": "あたらしいシステムはいつかんせいしますか。",
                "q_en": "When will the new system be finished?",
                "a": "来週の水曜日に完成する予定です。",
                "a_reading": "らいしゅうのすいようびにかんせいするよていです。",
                "a_en": "It is due to be finished next Wednesday.",
                "keywords": ["水曜日", "完成"],
                "min_chars": 10,
            },
        ],
    },
    49: {
        "title": "納品が遅れます",
        "title_en": "The delivery will be late",
        "chunks": [
            (
                "部品が足りないため、納品が一週間遅れます。",
                "ぶひんがたりないため、のうひんがいっしゅうかんおくれます。",
                "Parts are short, so delivery will be a week late.",
            ),
            (
                "客には今日、電話で話しました。",
                "きゃくにはきょう、でんわではなしました。",
                "I spoke to the customer by phone today.",
            ),
            (
                "延期の交渉もしています。",
                "えんきのこうしょうもしています。",
                "We are also negotiating a postponement.",
            ),
            (
                "対応が早ければ、大丈夫だと思います。",
                "たいおうがはやければ、だいじょうぶだとおもいます。",
                "If we respond quickly I think it will be all right.",
            ),
            (
                "遅れたら、損害が大きくなるでしょう。",
                "おくれたら、そんがいがおおきくなるでしょう。",
                "If we are late the damage will probably be large.",
            ),
            (
                "午後までに回答します。",
                "ごごまでにかいとうします。",
                "I will reply by this afternoon.",
            ),
        ],
        "questions": [
            {
                "q": "どうして納品が遅れますか。",
                "q_reading": "どうしてのうひんがおくれますか。",
                "q_en": "Why will the delivery be late?",
                "a": "部品が足りないためです。",
                "a_reading": "ぶひんがたりないためです。",
                "a_en": "Because parts are short.",
                "keywords": ["部品", "足りない"],
                "min_chars": 8,
            },
        ],
    },
}

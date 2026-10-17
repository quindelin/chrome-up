# -*- coding: utf-8 -*-
"""Reading passages, lessons 50-73 (N2 through N1 and above).

Same contract as `readings.py` - read that docstring before writing. In
short:

    PASSAGES[lesson_id] = {
        "title": "…", "title_en": "…",
        "chunks": [("日本語。", "にほんご。", "English."), …],
        "questions": [{"q": "…", "q_reading": "…", "q_en": "…",
                       "a": "…", "a_reading": "…", "a_en": "…",
                       "keywords": ["…"], "min_chars": 6}],
    }

Five to seven chunks, one sentence each, each under 45 characters. These
read like real Japanese: editorial, business, and academic register as the
lesson demands. One or two questions, answerable from the text.

Verify with:  .venv/bin/python server/course/ja/readings.py
"""

PASSAGES: dict = {
    50: {
        "title": "自己紹介",
        "title_en": "Introducing yourself",
        "chunks": [
            (
                "初めまして。営業部の鈴木と申します。",
                "はじめまして。えいぎょうぶのすずきともうします。",
                "How do you do. I am Suzuki, from the sales division.",
            ),
            (
                "海外のお客様との契約を担当しております。",
                "かいがいのおきゃくさまとのけいやくをたんとうしております。",
                "I handle contracts with our overseas customers.",
            ),
            (
                "前職では、同じく契約の仕事をしておりました。",
                "ぜんしょくでは、おなじくけいやくのしごとをしておりました。",
                "At my previous company I did contract work as well.",
            ),
            (
                "三年ほど経験を重ね、今年の四月に来ました。",
                "さんねんほどけいけんをかさね、ことしのしがつにきました。",
                "After about three years of experience I came here this April.",
            ),
            (
                "部の皆さんには、明日あらためてご挨拶いたします。",
                "ぶのみなさんには、あしたあらためてごあいさついたします。",
                "I will greet everyone in the division properly tomorrow.",
            ),
            (
                "ご連絡は、いつでもこちらの番号までお願いします。",
                "ごれんらくは、いつでもこちらのばんごうまでおねがいします。",
                "Please reach me at this number at any time.",
            ),
            (
                "何とぞよろしくお願い申し上げます。",
                "なにとぞよろしくおねがいもうしあげます。",
                "I look forward to working with you.",
            ),
        ],
        "questions": [
            {
                "q": "鈴木さんは何を担当していますか。",
                "q_reading": "すずきさんはなにをたんとうしていますか。",
                "q_en": "What is Suzuki in charge of?",
                "a": "海外のお客様との契約を担当しています。",
                "a_reading": "かいがいのおきゃくさまとのけいやくをたんとうしています。",
                "a_en": "He handles contracts with overseas customers.",
                "keywords": ["契約", "担当"],
                "min_chars": 8,
            },
        ],
    },
    51: {
        "title": "至急のご確認",
        "title_en": "An urgent request",
        "chunks": [
            (
                "恐れ入りますが、資料のご確認をお願いいたします。",
                "おそれいりますが、しりょうのごかくにんをおねがいいたします。",
                "I am sorry to press, but please review the documents.",
            ),
            (
                "至急とは申しませんが、今日中にお願いします。",
                "しきゅうとはもうしませんが、きょうじゅうにおねがいします。",
                "I will not say urgent, but today would be best.",
            ),
            (
                "終わりましたら、お手数ですがご連絡ください。",
                "おわりましたら、おてすうですがごれんらくください。",
                "When you are done, please let me know - sorry for the trouble.",
            ),
            (
                "資料の送付も、承知いたしました。",
                "しりょうのそうふも、しょうちいたしました。",
                "Understood: I will send the documents too.",
            ),
            (
                "ご不明な点は、私までお知らせください。",
                "ごふめいなてんは、わたくしまでおしらせください。",
                "If anything is unclear, please tell me directly.",
            ),
            (
                "対応のほど、何とぞよろしくお願いいたします。",
                "たいおうのほど、なにとぞよろしくおねがいいたします。",
                "Thank you in advance for seeing to it.",
            ),
        ],
        "questions": [
            {
                "q": "確認が終わったら、どうしますか。",
                "q_reading": "かくにんがおわったら、どうしますか。",
                "q_en": "What happens once the review is finished?",
                "a": "終わり次第、連絡いたします。",
                "a_reading": "おわりしだい、れんらくいたします。",
                "a_en": "I will get in touch as soon as it is done.",
                "keywords": ["終わり", "連絡"],
                "min_chars": 6,
            },
        ],
    },
    52: {
        "title": "今回は見送り",
        "title_en": "Not this time",
        "chunks": [
            (
                "せっかくお誘いいただき、ありがとうございます。",
                "せっかくおさそいいただき、ありがとうございます。",
                "Thank you for thinking of me.",
            ),
            (
                "あいにく先約がありまして、今回は伺えません。",
                "あいにくせんやくがありまして、こんかいはうかがえません。",
                "Unfortunately I have a prior engagement, so not this time.",
            ),
            (
                "今回だけは、見送らせていただければと存じます。",
                "こんかいだけは、みおくらせていただければとぞんじます。",
                "I would like to pass on this occasion only.",
            ),
            (
                "次の機会に、改めてお声がけください。",
                "つぎのきかいに、あらためておこえがけください。",
                "Please ask me again next time.",
            ),
            (
                "来週でしたら、木曜の午後なら空いております。",
                "らいしゅうでしたら、もくようのごごならあいております。",
                "Next week I am free, Thursday afternoon.",
            ),
            (
                "ご都合に合わせて、こちらから伺います。",
                "ごつごうにあわせて、こちらからうかがいます。",
                "I will come to you, at a time that suits.",
            ),
        ],
        "questions": [
            {
                "q": "今回の誘いを断る理由は何ですか。",
                "q_reading": "こんかいのさそいをことわるりゆうはなんですか。",
                "q_en": "Why is the invitation refused this time?",
                "a": "あいにく先約があるからです。",
                "a_reading": "あいにくせんやくがあるからです。",
                "a_en": "Because there is a prior engagement.",
                "keywords": ["先約"],
                "min_chars": 6,
            },
        ],
    },
    53: {
        "title": "折り返しの電話",
        "title_en": "Returning a call",
        "chunks": [
            (
                "お電話ありがとうございます。山川商事でございます。",
                "おでんわありがとうございます。やまかわしょうじでございます。",
                "Thank you for calling. Yamakawa Trading.",
            ),
            (
                "恐れ入りますが、佐藤さんをお願いできますか。",
                "おそれいりますが、さとうさんをおねがいできますか。",
                "I am sorry to trouble you - may I speak to Sato?",
            ),
            (
                "佐藤は、ただ今席を外しております。",
                "さとうは、ただいませきをはずしております。",
                "Sato is away from his desk at the moment.",
            ),
            (
                "では、折り返しお願いできますでしょうか。",
                "では、おりかえしおねがいできますでしょうか。",
                "Then could you ask him to call me back?",
            ),
            (
                "ご要件を伺ってもよろしいでしょうか。",
                "ごようけんをうかがってもよろしいでしょうか。",
                "May I ask what it concerns?",
            ),
            (
                "資料の件です。確認の電話をいただけますか。",
                "しりょうのけんです。かくにんのでんわをいただけますか。",
                "It is about the documents. Could he call to confirm?",
            ),
            (
                "承知いたしました。佐藤から連絡いたします。",
                "しょうちいたしました。さとうかられんらくいたします。",
                "Understood. Sato will be in touch.",
            ),
        ],
        "questions": [
            {
                "q": "佐藤さんは今、どうしていますか。",
                "q_reading": "さとうさんはいま、どうしていますか。",
                "q_en": "What is Sato doing right now?",
                "a": "ただ今、席を外しております。",
                "a_reading": "ただいま、せきをはずしております。",
                "a_en": "He is away from his desk at the moment.",
                "keywords": ["席を外"],
                "min_chars": 6,
            },
        ],
    },
    54: {
        "title": "余白について",
        "title_en": "On leaving room",
        "chunks": [
            (
                "自由とは、選べる範囲が広いということです。",
                "じゆうとは、えらべるはんいがひろいということです。",
                "Freedom means that the range of choice is wide.",
            ),
            (
                "仕事でも、範囲が狭いほど自由がなくなります。",
                "しごとでも、はんいがせまいほどじゆうがなくなります。",
                "At work too, the narrower the range, the less freedom there is.",
            ),
            (
                "効率だけを追うと、余白は失われます。",
                "こうりつだけをおうと、よはくはうしなわれます。",
                "Chase efficiency alone and the spare room disappears.",
            ),
            (
                "余白とは、急がずに考える時間のことです。",
                "よはくとは、いそがずにかんがえるじかんのことです。",
                "Spare room means time to think without hurrying.",
            ),
            (
                "人と深く関わる時間も、そこに含まれます。",
                "ひととふかくかかわるじかんも、そこにふくまれます。",
                "Time spent deeply with others counts as part of it.",
            ),
            (
                "価値観は、人によって違います。",
                "かちかんは、ひとによってちがいます。",
                "Values differ from one person to another.",
            ),
            (
                "だからこそ、何を求めるかが問われます。",
                "だからこそ、なにをもとめるかがとわれます。",
                "Which is why what we ask for is the real question.",
            ),
        ],
        "questions": [
            {
                "q": "筆者は余白を何だと言っていますか。",
                "q_reading": "ひっしゃはよはくをなんだといっていますか。",
                "q_en": "What does the writer say spare room is?",
                "a": "急がずに考える時間のことだと言っています。",
                "a_reading": "いそがずにかんがえるじかんのことだといっています。",
                "a_en": "He says it is time to think without hurrying.",
                "keywords": ["考える", "時間"],
                "min_chars": 8,
            },
        ],
    },
    55: {
        "title": "三つの根拠",
        "title_en": "Three grounds",
        "chunks": [
            (
                "今回の主張の根拠は、三つございます。",
                "こんかいのしゅちょうのこんきょは、みっつございます。",
                "There are three grounds for the claim.",
            ),
            (
                "費用、時間、そして顧客の満足度です。",
                "ひよう、じかん、そしてこきゃくのまんぞくどです。",
                "Cost, time, and customer satisfaction.",
            ),
            (
                "費用の根拠は、数字を添えて示します。",
                "ひようのこんきょは、すうじをそえてしめします。",
                "I will set out the cost case with figures attached.",
            ),
            (
                "短期の効果と長期の効果は混ぜません。",
                "たんきのこうかとちょうきのこうかはまぜません。",
                "Short-term and long-term effects are not mixed.",
            ),
            (
                "分けて考えれば、結論が変わる場合もあります。",
                "わけてかんがえれば、けつろんがかわるばあいもあります。",
                "Kept apart, the conclusion sometimes changes.",
            ),
            (
                "三つの点に基づいて、判断いたします。",
                "みっつのてんにもとづいて、はんだんいたします。",
                "I will judge on the basis of the above.",
            ),
        ],
        "questions": [
            {
                "q": "三つの根拠は何ですか。",
                "q_reading": "みっつのこんきょはなんですか。",
                "q_en": "What are the three grounds?",
                "a": "費用、時間、顧客の満足度です。",
                "a_reading": "ひよう、じかん、こきゃくのまんぞくどです。",
                "a_en": "Cost, time, and customer satisfaction.",
                "keywords": ["費用", "満足度"],
                "min_chars": 8,
            },
        ],
    },
    56: {
        "title": "負担の偏り",
        "title_en": "An uneven burden",
        "chunks": [
            (
                "この問題の背景には、世代間の偏りがあります。",
                "このもんだいのはいけいには、せだいかんのかたよりがあります。",
                "Behind this problem lies an imbalance between generations.",
            ),
            (
                "その要因は、大きく二つあると考えます。",
                "そのよういんは、おおきくふたつあるとかんがえます。",
                "I take there to be two broad causes.",
            ),
            (
                "一つは人口の構成、もう一つは賃金です。",
                "ひとつはじんこうのこうせい、もうひとつはちんぎんです。",
                "One is the shape of the population, the other is wages.",
            ),
            (
                "賃金が伸びないことが、若い世代に響きます。",
                "ちんぎんがのびないことが、わかいせだいにひびきます。",
                "Wages that do not grow land hardest on the young.",
            ),
            (
                "社会には、将来への不安が広がります。",
                "しゃかいには、しょうらいへのふあんがひろがります。",
                "Anxiety about the future spreads through society.",
            ),
            (
                "だから、支え合う仕組みが要ります。",
                "だから、ささえあうしくみがいります。",
                "So a system of mutual support is needed.",
            ),
        ],
        "questions": [
            {
                "q": "偏りの要因は何だと言っていますか。",
                "q_reading": "かたよりのよういんはなんだといっていますか。",
                "q_en": "What does it say causes the imbalance?",
                "a": "人口の構成と、賃金が伸びないことです。",
                "a_reading": "じんこうのこうせいと、ちんぎんがのびないことです。",
                "a_en": "The shape of the population, and wages that do not grow.",
                "keywords": ["人口", "賃金"],
                "min_chars": 8,
            },
        ],
    },
    57: {
        "title": "便利さと安全",
        "title_en": "Convenience and safety",
        "chunks": [
            (
                "便利さと安全、どちらを優先すべきでしょうか。",
                "べんりさとあんぜん、どちらをゆうせんすべきでしょうか。",
                "Convenience and safety: which should come first?",
            ),
            (
                "私は、安全を優先すべきだと考えます。",
                "わたしは、あんぜんをゆうせんすべきだとかんがえます。",
                "I take the view that safety should come first.",
            ),
            (
                "便利さだけを求めれば、事故が増えます。",
                "べんりさだけをもとめれば、じこがふえます。",
                "Ask only for convenience and accidents multiply.",
            ),
            (
                "ただし、範囲を決めて妥協する形もあります。",
                "ただし、はんいをきめてだきょうするかたちもあります。",
                "Still, there is a version where we fix a range and compromise.",
            ),
            (
                "その判断で、不利になる人もいます。",
                "そのはんだんで、ふりになるひともいます。",
                "That decision leaves some people worse off.",
            ),
            (
                "高齢の方と、収入の少ない方です。",
                "こうれいのかたと、しゅうにゅうのすくないかたです。",
                "The elderly, and those on low incomes.",
            ),
            (
                "そこは、全体で支えるほかありません。",
                "そこは、ぜんたいでささえるほかありません。",
                "That part we can only carry together.",
            ),
        ],
        "questions": [
            {
                "q": "筆者は何を優先すべきだと言っていますか。",
                "q_reading": "ひっしゃはなにをゆうせんすべきだといっていますか。",
                "q_en": "What does the writer say should come first?",
                "a": "安全を優先すべきだと言っています。",
                "a_reading": "あんぜんをゆうせんすべきだといっています。",
                "a_en": "He says safety should come first.",
                "keywords": ["安全", "優先"],
                "min_chars": 8,
            },
        ],
    },
    58: {
        "title": "断定を避ける",
        "title_en": "Withholding a conclusion",
        "chunks": [
            (
                "この状況は、しばらく続くと思われます。",
                "このじょうきょうは、しばらくつづくとおもわれます。",
                "This situation is thought likely to continue a while.",
            ),
            (
                "ただし、数字は確実なものではありません。",
                "ただし、すうじはかくじつなものではありません。",
                "The figures, however, are not certain.",
            ),
            (
                "一時的な要因が、含まれているかもしれません。",
                "いちじてきなよういんが、ふくまれているかもしれません。",
                "Temporary factors may be folded into them.",
            ),
            (
                "ですから、解釈には幅を持たせるべきでしょう。",
                "ですから、かいしゃくにははばをもたせるべきでしょう。",
                "So the reading should be allowed some margin.",
            ),
            (
                "半年先の見通しは、まだ読めません。",
                "はんとしさきのみとおしは、まだよめません。",
                "Six months out, the outlook cannot yet be read.",
            ),
            (
                "傾向がはっきりするまでは、断定を避けたいです。",
                "けいこうがはっきりするまでは、だんていをさけたいです。",
                "Until the trend is clear I want to avoid concluding.",
            ),
        ],
        "questions": [
            {
                "q": "なぜ断定を避けたいのですか。",
                "q_reading": "なぜだんていをさけたいのですか。",
                "q_en": "Why does he want to avoid concluding?",
                "a": "数字に一時的な要因が含まれているからです。",
                "a_reading": "すうじにいちじてきなよういんがふくまれているからです。",
                "a_en": "Because temporary factors may be in the figures.",
                "keywords": ["一時的", "要因"],
                "min_chars": 8,
            },
        ],
    },
    59: {
        "title": "変えるべき一点",
        "title_en": "The one thing to change",
        "chunks": [
            (
                "今回こそ、変えるべき点があります。",
                "こんかいこそ、かえるべきてんがあります。",
                "This time there is something that must change.",
            ),
            (
                "それは、意思決定の速さです。",
                "それは、いしけっていのはやさです。",
                "It is the speed of decision-making.",
            ),
            (
                "速さこそが、今の課題だと考えます。",
                "はやさこそが、いまのかだいだとかんがえます。",
                "Speed is precisely the problem now.",
            ),
            (
                "ただし、最低限守るべきものもあります。",
                "ただし、さいていげんまもるべきものもあります。",
                "Even so, some things must be kept at a minimum.",
            ),
            (
                "お客様との信頼だけは、決して失いません。",
                "おきゃくさまとのしんらいだけは、けっしてうしないません。",
                "Trust with customers is the one thing we never lose.",
            ),
            (
                "回答の期限を決め、必ず守ります。",
                "かいとうのきげんをきめ、かならずまもります。",
                "We will set a deadline for replies and keep it.",
            ),
        ],
        "questions": [
            {
                "q": "筆者は、何が課題だと言っていますか。",
                "q_reading": "ひっしゃは、なにがかだいだといっていますか。",
                "q_en": "What does the writer say the problem is?",
                "a": "意思決定の速さこそが課題だと言っています。",
                "a_reading": "いしけっていのはやさこそがかだいだといっています。",
                "a_en": "He says the speed of decision-making is the problem.",
                "keywords": ["速さ", "課題"],
                "min_chars": 8,
            },
        ],
    },
    60: {
        "title": "教わってきたこと",
        "title_en": "What I was taught",
        "chunks": [
            (
                "約束は守るものだと、教わってきました。",
                "やくそくはまもるものだと、おそわってきました。",
                "I was taught that promises are things you keep.",
            ),
            (
                "失敗は、恐れるものではないとも言われます。",
                "しっぱいは、おそれるものではないともいわれます。",
                "I was also told failure is not something to fear.",
            ),
            (
                "若い人には、まず形を覚えさせます。",
                "わかいひとには、まずかたちをおぼえさせます。",
                "With young people I make them learn the form first.",
            ),
            (
                "意味は、後から分かるものです。",
                "いみは、あとからわかるものです。",
                "Meaning is something that arrives later.",
            ),
            (
                "経験は、すぐには力になりません。",
                "けいけんは、すぐにはちからになりません。",
                "Experience does not turn into strength straight away.",
            ),
            (
                "それでも、重ねていくしかないのです。",
                "それでも、かさねていくしかないのです。",
                "Even so, there is nothing to do but stack it up.",
            ),
        ],
        "questions": [
            {
                "q": "失敗について、筆者はどう言っていますか。",
                "q_reading": "しっぱいについて、ひっしゃはどういっていますか。",
                "q_en": "What does the writer say about failure?",
                "a": "失敗は恐れるものではないと言っています。",
                "a_reading": "しっぱいはおそれるものではないといっています。",
                "a_en": "He says failure is not something to fear.",
                "keywords": ["失敗", "恐れる"],
                "min_chars": 8,
            },
        ],
    },
    61: {
        "title": "持ち帰ります",
        "title_en": "I'll take it back with me",
        "chunks": [
            (
                "この提案、一度持ち帰らせていただけますか。",
                "このていあん、いちどもちかえらせていただけますか。",
                "May I take this proposal back with me once?",
            ),
            (
                "つまり、賛成できないということですか。",
                "つまり、さんせいできないということですか。",
                "In other words, you cannot agree to it.",
            ),
            (
                "いいえ、別の角度からも見たいのです。",
                "いいえ、べつのかくどからもみたいのです。",
                "No - I simply want to look at it from another angle.",
            ),
            (
                "遠回しに断られた気がしますが。",
                "とおまわしにことわられたきがしますが。",
                "It does feel as though I am being refused obliquely.",
            ),
            (
                "申し訳ありません。顔をつぶすつもりはありません。",
                "もうしわけありません。かおをつぶすつもりはありません。",
                "My apologies. I have no wish to embarrass you.",
            ),
            (
                "検討した上で、今週中に書面でお答えします。",
                "けんとうしたうえで、こんしゅうちゅうにしょめんでおこたえします。",
                "I will reply in writing this week, once I have considered it.",
            ),
        ],
        "questions": [
            {
                "q": "なぜ一度持ち帰りたいのですか。",
                "q_reading": "なぜいちどもちかえりたいのですか。",
                "q_en": "Why does he want to take it back once?",
                "a": "別の角度からも見たいからです。",
                "a_reading": "べつのかくどからもみたいからです。",
                "a_en": "Because he wants to look at it from another angle.",
                "keywords": ["別の", "角度"],
                "min_chars": 6,
            },
        ],
    },
    62: {
        "title": "見出しを読む",
        "title_en": "Reading the headline",
        "chunks": [
            (
                "今朝の見出しは、短く、省略が多い。",
                "けさのみだしは、みじかく、しょうりゃくがおおい。",
                "This morning's headline is short, and full of ellipsis.",
            ),
            (
                "助詞が省かれるため、慣れが要ります。",
                "じょしがはぶかれるため、なれがいります。",
                "Particles are dropped, so it takes practice.",
            ),
            (
                "本紙は、この件を独占で報じました。",
                "ほんしは、このけんをどくせんでほうじました。",
                "This paper reported the matter as an exclusive.",
            ),
            (
                "他紙も追随すれば、波紋は広がるでしょう。",
                "たしもついずいすれば、はもんはひろがるでしょう。",
                "If the other papers follow, the ripples will spread.",
            ),
            (
                "担当者は、事実を確認しています。",
                "たんとうしゃは、じじつをかくにんしています。",
                "Those handling it are checking the facts.",
            ),
            (
                "報道の姿勢も、問われることになります。",
                "ほうどうのしせいも、とわれることになります。",
                "The stance of the reporting will be called into question too.",
            ),
        ],
        "questions": [
            {
                "q": "見出しが読みにくい理由は何ですか。",
                "q_reading": "みだしがよみにくいりゆうはなんですか。",
                "q_en": "Why are headlines hard to read?",
                "a": "助詞が省かれているからです。",
                "a_reading": "じょしがはぶかれているからです。",
                "a_en": "Because particles are dropped.",
                "keywords": ["助詞", "省か"],
                "min_chars": 6,
            },
        ],
    },
    63: {
        "title": "今朝の社説",
        "title_en": "This morning's editorial",
        "chunks": [
            (
                "今朝の社説は、慎重な論調でした。",
                "けさのしゃせつは、しんちょうなろんちょうでした。",
                "This morning's editorial struck a cautious note.",
            ),
            (
                "人口減少に、警鐘を鳴らしています。",
                "じんこうげんしょうに、けいしょうをならしています。",
                "It sounds an alarm about the falling population.",
            ),
            (
                "提起されたのは、地域を維持する難問です。",
                "ていきされたのは、ちいきをいじするなんもんです。",
                "What it raises is the hard problem of keeping regions going.",
            ),
            (
                "提言は示されています。",
                "ていげんはしめされています。",
                "A recommendation is offered.",
            ),
            (
                "ただし、具体策には踏み込んでいません。",
                "ただし、ぐたいさくにはふみこんでいません。",
                "It does not, however, go into concrete measures.",
            ),
            (
                "解決は、次の機会に譲られた形です。",
                "かいけつは、つぎのきかいにゆずられたかたちです。",
                "The solution is left to a later occasion.",
            ),
            (
                "いかにも社説らしい終わり方でした。",
                "いかにもしゃせつらしいおわりかたでした。",
                "A quiet ending, very much an editorial's.",
            ),
        ],
        "questions": [
            {
                "q": "社説は何に警鐘を鳴らしていますか。",
                "q_reading": "しゃせつはなににけいしょうをならしていますか。",
                "q_en": "What does the editorial sound an alarm about?",
                "a": "人口減少に警鐘を鳴らしています。",
                "a_reading": "じんこうげんしょうにけいしょうをならしています。",
                "a_en": "It sounds an alarm about the falling population.",
                "keywords": ["人口減少", "警鐘"],
                "min_chars": 8,
            },
        ],
    },
    64: {
        "title": "取材に答える",
        "title_en": "Answering a reporter",
        "chunks": [
            (
                "計画は順調だという認識でよろしいですか。",
                "けいかくはじゅんちょうだというにんしきでよろしいですか。",
                "Is it fair to say the plan is going smoothly?",
            ),
            (
                "少し留保があります。全面的には順調ではありません。",
                "すこしりゅうほがあります。ぜんめんてきにはじゅんちょうではありません。",
                "With some reservation. Not smoothly across the board.",
            ),
            (
                "つまり、軌道修正の必要があるということですね。",
                "つまり、きどうしゅうせいのひつようがあるということですね。",
                "So a change of course will be needed.",
            ),
            (
                "その含みでお読みいただければ結構です。",
                "そのふくみでおよみいただければけっこうです。",
                "You may read it with that implication.",
            ),
            (
                "一部は、想定より遅れております。",
                "いちぶは、そうていよりおくれております。",
                "Parts of it are behind schedule.",
            ),
            (
                "今後の所見は、改めて書面でお示しします。",
                "こんごのしょけんは、あらためてしょめんでおしめしします。",
                "I will set out my views on the future in writing.",
            ),
        ],
        "questions": [
            {
                "q": "計画は全面的に順調ですか。",
                "q_reading": "けいかくはぜんめんてきにじゅんちょうですか。",
                "q_en": "Is the plan going smoothly across the board?",
                "a": "いいえ、少し留保があります。",
                "a_reading": "いいえ、すこしりゅうほがあります。",
                "a_en": "No - with some reservation.",
                "keywords": ["留保"],
                "min_chars": 6,
            },
        ],
    },
    65: {
        "title": "食い違う数字",
        "title_en": "Conflicting numbers",
        "chunks": [
            (
                "報道各社で、数字が食い違っています。",
                "ほうどうかくしゃで、すうじがくいちがっています。",
                "The figures differ from one outlet to another.",
            ),
            (
                "推測と、確認済みの事実が混ざっています。",
                "すいそくと、かくにんずみのじじつがまざっています。",
                "Guesswork and confirmed fact are mixed together.",
            ),
            (
                "現段階では、どちらとも断定できません。",
                "げんだんかいでは、どちらともだんていできません。",
                "At this stage neither can be asserted.",
            ),
            (
                "検証を待つべきだと考えます。",
                "けんしょうをまつべきだとかんがえます。",
                "I think we should wait for verification.",
            ),
            (
                "影響は今のところ、限定的だと見ています。",
                "えいきょうはいまのところ、げんていてきだとみています。",
                "For now I read the impact as limited.",
            ),
            (
                "ただ、注視は続けるつもりです。",
                "ただ、ちゅうしはつづけるつもりです。",
                "I intend, though, to keep watching.",
            ),
        ],
        "questions": [
            {
                "q": "現段階では何を避けるべきですか。",
                "q_reading": "げんだんかいではなにをさけるべきですか。",
                "q_en": "What should be avoided at this stage?",
                "a": "断定を避け、検証を待つべきです。",
                "a_reading": "だんていをさけ、けんしょうをまつべきです。",
                "a_en": "We should avoid asserting and wait for verification.",
                "keywords": ["断定", "検証"],
                "min_chars": 8,
            },
        ],
    },
    66: {
        "title": "用語の定義",
        "title_en": "Defining a term",
        "chunks": [
            (
                "この専門用語は、狭義と広義で意味が変わります。",
                "このせんもんようごは、きょうぎとこうぎでいみがかわります。",
                "This technical term changes meaning narrow vs. broad.",
            ),
            (
                "狭義では、装置そのものを指します。",
                "きょうぎでは、そうちそのものをさします。",
                "In the narrow sense it points to the device itself.",
            ),
            (
                "広義では、周辺の仕組み全体を含みます。",
                "こうぎでは、しゅうへんのしくみぜんたいをふくみます。",
                "In the broad sense it covers the whole surrounding system.",
            ),
            (
                "どちらかは、用例によって決まります。",
                "どちらかは、ようれいによってきまります。",
                "Which one applies is settled by usage.",
            ),
            (
                "今回の件は、厳密には該当しません。",
                "こんかいのけんは、げんみつにはがいとうしません。",
                "Strictly, this case does not fall under it.",
            ),
            (
                "類例として扱うのが、妥当でしょう。",
                "るいれいとしてあつかうのが、だとうでしょう。",
                "Treating it as a near example is probably right.",
            ),
        ],
        "questions": [
            {
                "q": "広義では何を含みますか。",
                "q_reading": "こうぎではなにをふくみますか。",
                "q_en": "In the broad sense, what does it include?",
                "a": "周辺の仕組み全体を含みます。",
                "a_reading": "しゅうへんのしくみぜんたいをふくみます。",
                "a_en": "It includes the whole surrounding system.",
                "keywords": ["周辺", "仕組み"],
                "min_chars": 8,
            },
        ],
    },
    67: {
        "title": "論文の手法",
        "title_en": "The paper's method",
        "chunks": [
            (
                "この論文の手法は、手順が明快です。",
                "このろんぶんのしゅほうは、てじゅんがめいかいです。",
                "The method of this paper is clear in its steps.",
            ),
            (
                "ただ、標本がやや小さいのが難点です。",
                "ただ、ひょうほんがややちいさいのがなんてんです。",
                "The weak point is that the sample is rather small.",
            ),
            (
                "有意差は出ています。",
                "ゆういさはでています。",
                "A significant difference does appear.",
            ),
            (
                "しかし、結果の解釈には注意が要ります。",
                "しかし、けっかのかいしゃくにはちゅういがいります。",
                "Still, care is needed in reading the result.",
            ),
            (
                "妥当性は、追試で確かめるべきです。",
                "だとうせいは、ついしでたしかめるべきです。",
                "Its validity should be checked by replication.",
            ),
            (
                "別の機関で進める予定です。",
                "べつのきかんですすめるよていです。",
                "That is to be carried out at another institution.",
            ),
            (
                "制約となっているのは、時間です。",
                "せいやくとなっているのは、じかんです。",
                "What constrains it is time.",
            ),
        ],
        "questions": [
            {
                "q": "この論文の手法の難点は何ですか。",
                "q_reading": "このろんぶんのしゅほうのなんてんはなんですか。",
                "q_en": "What is the weak point of the paper's method?",
                "a": "標本がやや小さいことです。",
                "a_reading": "ひょうほんがややちいさいことです。",
                "a_en": "That the sample is rather small.",
                "keywords": ["標本", "小さい"],
                "min_chars": 8,
            },
        ],
    },
    68: {
        "title": "発表の構成",
        "title_en": "Structuring a talk",
        "chunks": [
            (
                "本日の発表は、三部構成でお話しします。",
                "ほんじつのはっぴょうは、さんぶこうせいでおはなしします。",
                "Today's talk is in three parts.",
            ),
            (
                "まず背景、次に要点、最後に今後の課題です。",
                "まずはいけい、つぎにようてん、さいごにこんごのかだいです。",
                "Background first, then the points, then open questions.",
            ),
            (
                "補足は、資料に譲ります。",
                "ほそくは、しりょうにゆずります。",
                "I leave the detail to the handout.",
            ),
            (
                "十五分あれば、十分足ります。",
                "じゅうごふんあれば、じゅうぶんたります。",
                "Fifteen minutes is quite enough.",
            ),
            (
                "質疑には、想定問答を用意しています。",
                "しつぎには、そうていもんどうをよういしています。",
                "I have answers ready for the likely questions.",
            ),
            (
                "時間も、あらかじめ確保しました。",
                "じかんも、あらかじめかくほしました。",
                "I have set time aside for it in advance.",
            ),
            (
                "結びは、次の一歩をお示しして締めます。",
                "むすびは、つぎのいっぽをおしめししてしめます。",
                "I close by pointing to the next step.",
            ),
        ],
        "questions": [
            {
                "q": "発表の三つの部分は何ですか。",
                "q_reading": "はっぴょうのみっつのぶぶんはなんですか。",
                "q_en": "What are the three parts of the talk?",
                "a": "背景、要点、今後の課題です。",
                "a_reading": "はいけい、ようてん、こんごのかだいです。",
                "a_en": "Background, the main points, and open questions.",
                "keywords": ["背景", "要点"],
                "min_chars": 8,
            },
            {
                "q": "補足はどう扱いますか。",
                "q_reading": "ほそくはどうあつかいますか。",
                "q_en": "How is the supporting detail handled?",
                "a": "資料に譲ります。",
                "a_reading": "しりょうにゆずります。",
                "a_en": "It is left to the handout.",
                "keywords": ["資料"],
                "min_chars": 4,
            },
        ],
    },
    69: {
        "title": "質疑応答",
        "title_en": "Questions and answers",
        "chunks": [
            (
                "一点、指摘させていただいてよろしいですか。",
                "いってん、してきさせていただいてよろしいですか。",
                "May I raise one point?",
            ),
            (
                "どうぞ。ご指摘はもっともだと思います。",
                "どうぞ。ごしてきはもっともだとおもいます。",
                "Please. I think your point is fair.",
            ),
            (
                "では、前提条件を再考されますか。",
                "では、ぜんていじょうけんをさいこうされますか。",
                "Then will you reconsider the assumptions?",
            ),
            (
                "はい、精査した上で報告します。",
                "はい、せいさしたうえでほうこくします。",
                "Yes - I will examine it and report back.",
            ),
            (
                "ご指摘には反論いたしません。",
                "ごしてきにははんろんいたしません。",
                "I will not argue against the point.",
            ),
            (
                "それを宿題としてお受け取りください。",
                "それをしゅくだいとしておうけとりください。",
                "Please take that as homework.",
            ),
            (
                "承知しました。次の機会に必ず触れます。",
                "しょうちしました。つぎのきかいにかならずふれます。",
                "Understood. I will certainly address it next time.",
            ),
        ],
        "questions": [
            {
                "q": "指摘に対して、どう答えましたか。",
                "q_reading": "してきにたいして、どうこたえましたか。",
                "q_en": "How did he answer the objection?",
                "a": "ご指摘はもっともだと認めました。",
                "a_reading": "ごしてきはもっともだとみとめました。",
                "a_en": "He accepted that the point was fair.",
                "keywords": ["指摘", "もっとも"],
                "min_chars": 8,
            },
        ],
    },
    70: {
        "title": "三つの言い方",
        "title_en": "Three ways to say it",
        "chunks": [
            (
                "同じ内容でも、場面によって言い方が変わります。",
                "おなじないようでも、ばめんによっていいかたがかわります。",
                "The same content changes phrasing with the setting.",
            ),
            (
                "砕けた場では、「明日でいいよ」と言います。",
                "くだけたばでは、「あしたでいいよ」といいます。",
                "Among friends: 'tomorrow's fine'.",
            ),
            (
                "ふだんは、「明日で大丈夫です」でしょう。",
                "ふだんは、「あしたでだいじょうぶです」でしょう。",
                "Ordinarily it is 'tomorrow will be all right'.",
            ),
            (
                "改まった場では、語彙も変わります。",
                "あらたまったばでは、ごいもかわります。",
                "In a formal setting the vocabulary changes too.",
            ),
            (
                "「明日でよろしいでしょうか」と申し上げます。",
                "「あしたでよろしいでしょうか」ともうしあげます。",
                "One says 'might tomorrow be acceptable'.",
            ),
            (
                "最上級の敬語は、長くなる傾向があります。",
                "さいじょうきゅうのけいごは、ながくなるけいこうがあります。",
                "The most formal honorifics tend to get longer.",
            ),
            (
                "使い分けは、相手との距離で決まります。",
                "つかいわけは、あいてとのきょりできまります。",
                "Which you use is decided by your distance from the other.",
            ),
        ],
        "questions": [
            {
                "q": "砕けた場では、何と言いますか。",
                "q_reading": "くだけたばでは、なんといいますか。",
                "q_en": "What do you say in a casual setting?",
                "a": "「明日でいいよ」と言います。",
                "a_reading": "「あしたでいいよ」といいます。",
                "a_en": "You say 'tomorrow's fine'.",
                "keywords": ["いいよ"],
                "min_chars": 6,
            },
            {
                "q": "何によって言い方が変わりますか。",
                "q_reading": "なにによっていいかたがかわりますか。",
                "q_en": "What does the phrasing depend on?",
                "a": "場面と、相手との距離です。",
                "a_reading": "ばめんと、あいてとのきょりです。",
                "a_en": "The setting, and your distance from the other person.",
                "keywords": ["場面", "距離"],
                "min_chars": 6,
            },
        ],
    },
    71: {
        "title": "拍子抜け",
        "title_en": "Let down",
        "chunks": [
            (
                "気にかかっていたので、現地に足を運びました。",
                "きにかかっていたので、げんちにあしをはこびました。",
                "It was on my mind, so I went there in person.",
            ),
            (
                "結果は期待外れで、拍子抜けでした。",
                "けっかはきたいはずれで、ひょうしぬけでした。",
                "The result fell short and I was let down.",
            ),
            (
                "早めに手を打たなかったのが悔やまれます。",
                "はやめにてをうたなかったのがくやまれます。",
                "I regret not having acted sooner.",
            ),
            (
                "同僚は「まだ取り戻せる」と言いました。",
                "どうりょうは「まだとりもどせる」といいました。",
                "A colleague said there is still time to recover it.",
            ),
            (
                "肩の力を抜いて、考え直すことにしました。",
                "かたのちからをぬいて、かんがえなおすことにしました。",
                "I decided to relax and think it through again.",
            ),
            (
                "慣用句は、気持ちを短く伝えます。",
                "かんようくは、きもちをみじかくつたえます。",
                "Idioms carry a feeling in a short space.",
            ),
        ],
        "questions": [
            {
                "q": "なぜ現地に足を運びましたか。",
                "q_reading": "なぜげんちにあしをはこびましたか。",
                "q_en": "Why did he go there in person?",
                "a": "気にかかっていたからです。",
                "a_reading": "きにかかっていたからです。",
                "a_en": "Because it was on his mind.",
                "keywords": ["気にかかっ"],
                "min_chars": 6,
            },
            {
                "q": "拍子抜けした理由は何ですか。",
                "q_reading": "ひょうしぬけしたりゆうはなんですか。",
                "q_en": "Why was he let down?",
                "a": "結果が期待外れだったからです。",
                "a_reading": "けっかがきたいはずれだったからです。",
                "a_en": "Because the result fell short of what he expected.",
                "keywords": ["期待外れ"],
                "min_chars": 6,
            },
        ],
    },
    72: {
        "title": "前提を疑う",
        "title_en": "Questioning the premise",
        "chunks": [
            (
                "議論が、同じ枠組みの中で回っています。",
                "ぎろんが、おなじわくぐみのなかでまわっています。",
                "The debate is turning inside one frame.",
            ),
            (
                "そこで、前提を疑う必要があります。",
                "そこで、ぜんていをうたがうひつようがあります。",
                "So we need to doubt the premise.",
            ),
            (
                "成長が続くという前提自体が、仮説です。",
                "せいちょうがつづくというぜんていじたいが、かせつです。",
                "That growth continues is itself a hypothesis.",
            ),
            (
                "二つの案を天秤にかけるだけでは、足りません。",
                "ふたつのあんをてんびんにかけるだけでは、たりません。",
                "Merely weighing two plans is not enough.",
            ),
            (
                "単純な折衷では、どちらの弱さも残ります。",
                "たんじゅんなせっちゅうでは、どちらのよわさものこります。",
                "A simple compromise leaves both weaknesses in place.",
            ),
            (
                "土台から組み直す統合が必要です。",
                "どだいからくみなおすとうごうがひつようです。",
                "What is needed is a synthesis rebuilt from the ground.",
            ),
        ],
        "questions": [
            {
                "q": "疑うべきだと言っているのは何ですか。",
                "q_reading": "うたがうべきだといっているのはなんですか。",
                "q_en": "What does he say should be doubted?",
                "a": "成長が続くという前提です。",
                "a_reading": "せいちょうがつづくというぜんていです。",
                "a_en": "The premise that growth will continue.",
                "keywords": ["成長", "前提"],
                "min_chars": 8,
            },
        ],
    },
    73: {
        "title": "所信の一端",
        "title_en": "A short address",
        "chunks": [
            (
                "本日は、一言ご挨拶申し上げます。",
                "ほんじつは、ひとことごあいさつもうしあげます。",
                "I offer a few words of greeting today.",
            ),
            (
                "所信の一端を、述べさせていただきます。",
                "しょしんのいったんを、のべさせていただきます。",
                "Let me state a part of what I believe.",
            ),
            (
                "人づくりが、最も肝要だと考えます。",
                "ひとづくりが、もっともかんようだとかんがえます。",
                "I hold that developing people matters most.",
            ),
            (
                "所期の目標には、時間が要ります。",
                "しょきのもくひょうには、じかんがいります。",
                "The goals we first set will take time.",
            ),
            (
                "地道に、段階を踏んで進みます。",
                "じみちに、だんかいをふんですすみます。",
                "We will go steadily, one stage at a time.",
            ),
            (
                "微力ながら、全力で務めさせていただきます。",
                "びりょくながら、ぜんりょくでつとめさせていただきます。",
                "My powers are small, but I will serve with all of them.",
            ),
            (
                "結びに、どうかよろしくお願いいたします。",
                "むすびに、どうかよろしくおねがいいたします。",
                "In closing, I ask for your kind support.",
            ),
        ],
        "questions": [
            {
                "q": "何が最も肝要だと言っていますか。",
                "q_reading": "なにがもっともかんようだといっていますか。",
                "q_en": "What does he say matters most?",
                "a": "人づくりが最も肝要だと言っています。",
                "a_reading": "ひとづくりがもっともかんようだといっています。",
                "a_en": "He says developing people matters most.",
                "keywords": ["人づくり", "肝要"],
                "min_chars": 8,
            },
        ],
    },
}

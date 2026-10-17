# -*- coding: utf-8 -*-
"""HSK 3 — daily life in detail: routine, weather, health, people, plans,
comparisons, and 过 (experience)."""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    {
        "id": 6,
        "title": "Daily Life",
        "focus": "Talk about your routine, your home, the weather and your health.",
        "lessons": [
            {
                "id": 26,
                "title": "My day",
                "goal": "Describe a daily routine and say when you do things.",
                "vocab": [
                    ("起床", "qǐ chuáng", "to get up"),
                    ("睡觉", "shuì jiào", "to sleep"),
                    ("洗澡", "xǐ zǎo", "to shower"),
                    ("上班", "shàng bān", "to go to work"),
                    ("下班", "xià bān", "to finish work"),
                    ("一般", "yìbān", "usually"),
                ],
                "dialogue": [
                    ("them", "你每天几点起床？", "nǐ měitiān jǐ diǎn qǐchuáng?", "What time do you get up every day?"),
                    ("you", "我一般七点起床。", "wǒ yìbān qī diǎn qǐchuáng.", "I usually get up at seven."),
                    ("them", "这么早？你几点睡觉？", "zhème zǎo? nǐ jǐ diǎn shuìjiào?", "That early? When do you go to bed?"),
                    ("you", "十一点左右。我先洗澡，再睡觉。", "shíyī diǎn zuǒyòu. wǒ xiān xǐzǎo, zài shuìjiào.", "Around eleven. I shower first, then sleep."),
                    ("them", "你周末也起得这么早吗？", "nǐ zhōumò yě qǐ de zhème zǎo ma?", "Do you get up that early at the weekend too?"),
                    ("you", "不，周末我睡到九点。", "bù, zhōumò wǒ shuì dào jiǔ diǎn.", "No, at the weekend I sleep until nine."),
                ],
                "patterns": [
                    {
                        "text": "我每天{x}起床",
                        "reading": "wǒ měitiān {x} qǐchuáng",
                        "en": "I get up at {x} every day",
                        "kind": "clock",
                        "values": [("七点", "qī diǎn", "seven"), ("六点半", "liù diǎn bàn", "half past six"), ("八点", "bā diǎn", "eight")],
                    }
                ],
                "notes": ["先…再… = first …, then … (先洗澡，再睡觉)."],
            },
            {
                "id": 27,
                "title": "At home",
                "goal": "Describe your home and say what you do around the house.",
                "vocab": [
                    ("打扫", "dǎsǎo", "to clean"),
                    ("房间", "fángjiān", "room"),
                    ("做饭", "zuò fàn", "to cook"),
                    ("洗衣服", "xǐ yīfu", "to wash clothes"),
                    ("干净", "gānjìng", "clean"),
                    ("常常", "chángcháng", "often"),
                ],
                "dialogue": [
                    ("them", "你的房间大吗？", "nǐ de fángjiān dà ma?", "Is your room big?"),
                    ("you", "不大，但是很干净。", "bù dà, dànshì hěn gānjìng.", "Not big, but very clean."),
                    ("them", "你常常打扫吗？", "nǐ chángcháng dǎsǎo ma?", "Do you clean often?"),
                    ("you", "我每天打扫，周末洗衣服。", "wǒ měitiān dǎsǎo, zhōumò xǐ yīfu.", "I clean every day and do laundry at the weekend."),
                    ("them", "你会做饭吗？", "nǐ huì zuò fàn ma?", "Can you cook?"),
                    ("you", "会一点。我常常自己做。", "huì yìdiǎn. wǒ chángcháng zìjǐ zuò.", "A little. I often cook for myself."),
                ],
                "patterns": [
                    {
                        "text": "我会{x}",
                        "reading": "wǒ huì {x}",
                        "en": "I can {x}",
                        "values": [("做饭", "zuò fàn", "cook"), ("开车", "kāi chē", "drive"), ("游泳", "yóuyǒng", "swim")],
                    }
                ],
                "notes": ["会 = learned ability. 能 = ability/permission in the moment."],
            },
            {
                "id": 28,
                "title": "Weather",
                "goal": "Ask about and describe the weather and seasons.",
                "vocab": [
                    ("天气", "tiānqì", "weather"),
                    ("下雨", "xià yǔ", "to rain"),
                    ("冷", "lěng", "cold"),
                    ("热", "rè", "hot"),
                    ("季节", "jìjié", "season"),
                    ("最喜欢", "zuì xǐhuan", "like most"),
                ],
                "dialogue": [
                    ("them", "今天天气怎么样？", "jīntiān tiānqì zěnmeyàng?", "How's the weather today?"),
                    ("you", "今天很热。", "jīntiān hěn rè.", "It's very hot today."),
                    ("them", "明天会下雨吗？", "míngtiān huì xià yǔ ma?", "Will it rain tomorrow?"),
                    ("you", "会的，你带把伞吧。", "huì de, nǐ dài bǎ sǎn ba.", "Yes, take an umbrella."),
                    ("them", "你最喜欢哪个季节？", "nǐ zuì xǐhuan nǎge jìjié?", "Which season do you like most?"),
                    ("you", "我最喜欢秋天，不太冷也不太热。", "wǒ zuì xǐhuan qiūtiān, bú tài lěng yě bú tài rè.", "Autumn - not too cold, not too hot."),
                ],
                "patterns": [
                    {
                        "text": "今天很{x}",
                        "reading": "jīntiān hěn {x}",
                        "en": "Today is very {x}",
                        "kind": "weather",
                        "values": [("热", "rè", "hot"), ("冷", "lěng", "cold"), ("凉快", "liángkuai", "cool")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 29,
                "title": "Not feeling well",
                "goal": "Describe symptoms and understand simple medical advice.",
                "vocab": [
                    ("不舒服", "bù shūfu", "not feeling well"),
                    ("感冒", "gǎnmào", "to have a cold"),
                    ("发烧", "fā shāo", "to have a fever"),
                    ("头疼", "tóu téng", "headache"),
                    ("休息", "xiūxi", "to rest"),
                    ("医院", "yīyuàn", "hospital"),
                ],
                "dialogue": [
                    ("them", "你怎么了？", "nǐ zěnme le?", "What's wrong with you?"),
                    ("you", "我不舒服，可能感冒了。", "wǒ bù shūfu, kěnéng gǎnmào le.", "I feel unwell, maybe I caught a cold."),
                    ("them", "你发烧吗？", "nǐ fā shāo ma?", "Do you have a fever?"),
                    ("you", "不发烧，但是头疼。", "bù fā shāo, dànshì tóu téng.", "No fever, but a headache."),
                    ("them", "你要去医院吗？", "nǐ yào qù yīyuàn ma?", "Do you want to go to the hospital?"),
                    ("you", "不用，我多喝水，好好休息。", "bú yòng, wǒ duō hē shuǐ, hǎohǎo xiūxi.", "No need, I'll drink plenty of water and rest well."),
                ],
                "patterns": [
                    {
                        "text": "我有点{x}",
                        "reading": "wǒ yǒudiǎn {x}",
                        "en": "I'm a bit {x}",
                        "values": [("头疼", "tóu téng", "headachy"), ("累", "lèi", "tired"), ("咳嗽", "ké sou", "coughy")],
                    }
                ],
                "notes": ["有点 = 'a bit', usually for something unpleasant."],
            },
        ],
    },
    {
        "id": 7,
        "title": "People & Plans",
        "focus": "Describe people, arrange to meet, talk hobbies, make comparisons.",
        "lessons": [
            {
                "id": 30,
                "title": "My family",
                "goal": "Talk about your family and compare people.",
                "vocab": [
                    ("几口人", "jǐ kǒu rén", "how many people (in the family)"),
                    ("哥哥", "gēge", "older brother"),
                    ("比", "bǐ", "compared with"),
                    ("高", "gāo", "tall"),
                    ("长得像", "zhǎng de xiàng", "to look like"),
                    ("性格", "xìnggé", "personality"),
                ],
                "dialogue": [
                    ("them", "你家有几口人？", "nǐ jiā yǒu jǐ kǒu rén?", "How many people are in your family?"),
                    ("you", "四口人：爸爸、妈妈、哥哥和我。", "sì kǒu rén: bàba, māma, gēge hé wǒ.", "Four: dad, mum, my brother and me."),
                    ("them", "你哥哥比你高吗？", "nǐ gēge bǐ nǐ gāo ma?", "Is your brother taller than you?"),
                    ("you", "他比我高一点。", "tā bǐ wǒ gāo yìdiǎn.", "He's a bit taller than me."),
                    ("them", "你长得像谁？", "nǐ zhǎng de xiàng shéi?", "Who do you look like?"),
                    ("you", "大家都说我像我妈妈。", "dàjiā dōu shuō wǒ xiàng wǒ māma.", "Everyone says I look like my mother."),
                ],
                "patterns": [
                    {
                        "text": "他比我{x}",
                        "reading": "tā bǐ wǒ {x}",
                        "en": "He is {x} than me",
                        "values": [("高", "gāo", "taller"), ("大", "dà", "older"), ("忙", "máng", "busier")],
                    }
                ],
                "notes": ["比 pattern: A 比 B + adjective. No 很 before the adjective."],
            },
            {
                "id": 31,
                "title": "Let's meet",
                "goal": "Arrange a meeting and reschedule it.",
                "vocab": [
                    ("见面", "jiàn miàn", "to meet"),
                    ("改", "gǎi", "to change"),
                    ("有事", "yǒu shì", "to have something on"),
                    ("那天", "nà tiān", "that day"),
                    ("咖啡馆", "kāfēi guǎn", "café"),
                    ("等你", "děng nǐ", "wait for you"),
                ],
                "dialogue": [
                    ("you", "我们什么时候见面？", "wǒmen shénme shíhou jiànmiàn?", "When shall we meet?"),
                    ("them", "这周六可以吗？", "zhè zhōuliù kěyǐ ma?", "Is this Saturday OK?"),
                    ("you", "抱歉，我那天有事。改到周日吧。", "bàoqiàn, wǒ nà tiān yǒu shì. gǎi dào zhōurì ba.", "Sorry, I have something that day. Let's move it to Sunday."),
                    ("them", "好，周日几点？", "hǎo, zhōurì jǐ diǎn?", "OK, what time on Sunday?"),
                    ("you", "下午三点，在咖啡馆，好吗？", "xiàwǔ sān diǎn, zài kāfēi guǎn, hǎo ma?", "Three in the afternoon, at the café, OK?"),
                    ("them", "好，我等你。", "hǎo, wǒ děng nǐ.", "Good, I'll wait for you."),
                ],
                "patterns": [
                    {
                        "text": "我们{x}见面",
                        "reading": "wǒmen {x} jiànmiàn",
                        "en": "We'll meet {x}",
                        "kind": "day",
                        "values": [("明天", "míngtiān", "tomorrow"), ("周日", "zhōurì", "Sunday"), ("下午三点", "xiàwǔ sān diǎn", "at 3 pm")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 32,
                "title": "Hobbies",
                "goal": "Say what you like doing and how often.",
                "vocab": [
                    ("爱好", "àihào", "hobby"),
                    ("跑步", "pǎo bù", "to run"),
                    ("多久一次", "duō jiǔ yí cì", "how often"),
                    ("一个星期三次", "yí ge xīngqī sān cì", "three times a week"),
                    ("一起", "yìqǐ", "together"),
                    ("想学", "xiǎng xué", "want to learn"),
                ],
                "dialogue": [
                    ("them", "你有什么爱好？", "nǐ yǒu shénme àihào?", "What are your hobbies?"),
                    ("you", "我喜欢跑步。", "wǒ xǐhuan pǎobù.", "I like running."),
                    ("them", "你多久跑一次？", "nǐ duō jiǔ pǎo yí cì?", "How often do you run?"),
                    ("you", "一个星期三次。", "yí ge xīngqī sān cì.", "Three times a week."),
                    ("them", "我也想学。", "wǒ yě xiǎng xué.", "I'd like to learn too."),
                    ("you", "那我们一起去吧。", "nà wǒmen yìqǐ qù ba.", "Then let's go together."),
                ],
                "patterns": [
                    {
                        "text": "我喜欢{x}",
                        "reading": "wǒ xǐhuan {x}",
                        "en": "I like to {x}",
                        "values": [("跑步", "pǎo bù", "run"), ("游泳", "yóuyǒng", "swim"), ("看书", "kàn shū", "read"), ("听音乐", "tīng yīnyuè", "listen to music")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 33,
                "title": "Comparing",
                "goal": "Compare two options and give a preference.",
                "vocab": [
                    ("更", "gèng", "more / -er"),
                    ("方便", "fāngbiàn", "convenient"),
                    ("不过", "bùguò", "however"),
                    ("哪个", "nǎge", "which one"),
                    ("还是", "háishì", "still / or (in questions)"),
                    ("而且", "érqiě", "moreover"),
                ],
                "dialogue": [
                    ("them", "你觉得这家怎么样？", "nǐ juéde zhè jiā zěnmeyàng?", "What do you think of this place?"),
                    ("you", "这家比那家好吃，不过贵一点。", "zhè jiā bǐ nà jiā hǎochī, bùguò guì yìdiǎn.", "It's better than that one, but a bit pricier."),
                    ("them", "坐地铁是不是更方便？", "zuò dìtiě shì bú shì gèng fāngbiàn?", "Is the subway more convenient?"),
                    ("you", "对，而且更快。", "duì, érqiě gèng kuài.", "Yes, and faster too."),
                    ("them", "你更喜欢哪个？", "nǐ gèng xǐhuan nǎge?", "Which do you prefer?"),
                    ("you", "我还是喜欢坐地铁。", "wǒ háishì xǐhuan zuò dìtiě.", "I still prefer the subway."),
                ],
                "patterns": [
                    {
                        "text": "{x}更方便",
                        "reading": "{x} gèng fāngbiàn",
                        "en": "{x} is more convenient",
                        "values": [("坐地铁", "zuò dìtiě", "taking the subway"), ("骑车", "qí chē", "cycling"), ("打车", "dǎ chē", "taking a taxi")],
                    }
                ],
                "notes": ["还是 = 'still' in statements, 'or' in questions (你喝茶还是咖啡？)."],
            },
        ],
    },
    {
        "id": 8,
        "title": "Getting Things Done",
        "focus": "Phone calls, returns, admin, and talking about experiences with 过.",
        "lessons": [
            {
                "id": 34,
                "title": "On the phone",
                "goal": "Ask for someone, leave a message, give your number.",
                "vocab": [
                    ("请问", "qǐng wèn", "excuse me, may I ask"),
                    ("留言", "liú yán", "leave a message"),
                    ("回电话", "huí diànhuà", "call back"),
                    ("号码", "hàomǎ", "number"),
                    ("记一下", "jì yíxià", "note it down"),
                    ("现在不在", "xiànzài bú zài", "not here right now"),
                ],
                "dialogue": [
                    ("you", "请问，王先生在吗？", "qǐng wèn, Wáng xiānsheng zài ma?", "Is Mr Wang there, please?"),
                    ("them", "他现在不在。你是哪位？", "tā xiànzài bú zài. nǐ shì něi wèi?", "He's not here. Who's calling?"),
                    ("you", "我是李明的朋友。我可以留言吗？", "wǒ shì Lǐ Míng de péngyou. wǒ kěyǐ liúyán ma?", "I'm Li Ming's friend. May I leave a message?"),
                    ("them", "可以。请说。", "kěyǐ. qǐng shuō.", "Of course. Go ahead."),
                    ("you", "请他给我回电话。我的号码是……", "qǐng tā gěi wǒ huí diànhuà. wǒ de hàomǎ shì……", "Please ask him to call me back. My number is…"),
                    ("them", "好，我记一下。", "hǎo, wǒ jì yíxià.", "OK, let me write it down."),
                ],
                "patterns": [
                    {
                        "text": "请{x}给我回电话",
                        "reading": "qǐng {x} gěi wǒ huí diànhuà",
                        "en": "Please ask {x} to call me back",
                        "kind": "person",
                        "values": [("他", "tā", "him"), ("她", "tā", "her"), ("王先生", "Wáng xiānsheng", "Mr Wang")],
                    }
                ],
                "notes": ["你是哪位？ is the polite 'who is calling?'."],
            },
            {
                "id": 35,
                "title": "Returning something",
                "goal": "Return or exchange a purchase.",
                "vocab": [
                    ("退", "tuì", "to return (goods)"),
                    ("换", "huàn", "to exchange"),
                    ("坏了", "huài le", "broken"),
                    ("发票", "fāpiào", "receipt"),
                    ("昨天买的", "zuótiān mǎi de", "bought yesterday"),
                    ("修", "xiū", "to repair"),
                ],
                "dialogue": [
                    ("you", "我想退这个。", "wǒ xiǎng tuì zhège.", "I'd like to return this."),
                    ("them", "为什么？坏了吗？", "wèishénme? huài le ma?", "Why? Is it broken?"),
                    ("you", "对，昨天买的就坏了。", "duì, zuótiān mǎi de jiù huài le.", "Yes, it broke the day after I bought it."),
                    ("them", "有发票吗？", "yǒu fāpiào ma?", "Do you have the receipt?"),
                    ("you", "有，在这儿。可以换一个吗？", "yǒu, zài zhèr. kěyǐ huàn yí ge ma?", "Yes, here. Can I exchange it?"),
                    ("them", "可以。", "kěyǐ.", "You can."),
                ],
                "patterns": [
                    {
                        "text": "我想{x}这个",
                        "reading": "wǒ xiǎng {x} zhège",
                        "en": "I want to {x} this",
                        "values": [("退", "tuì", "return"), ("换", "huàn", "exchange"), ("修", "xiū", "repair")],
                    }
                ],
                "notes": ["就 here means 'already / as early as': 昨天买的就坏了."],
            },
            {
                "id": 36,
                "title": "At the bank",
                "goal": "Handle simple admin: forms, documents, waiting.",
                "vocab": [
                    ("开一个账户", "kāi yí ge zhànghù", "open an account"),
                    ("填表", "tián biǎo", "fill in a form"),
                    ("护照", "hùzhào", "passport"),
                    ("大概", "dàgài", "about / roughly"),
                    ("分钟", "fēnzhōng", "minute"),
                    ("身份证", "shēnfènzhèng", "ID card"),
                ],
                "dialogue": [
                    ("you", "我想开一个账户。", "wǒ xiǎng kāi yí ge zhànghù.", "I'd like to open an account."),
                    ("them", "请填一下这张表。", "qǐng tián yíxià zhè zhāng biǎo.", "Please fill in this form."),
                    ("you", "需要护照吗？", "xūyào hùzhào ma?", "Do you need my passport?"),
                    ("them", "需要。大概要二十分钟。", "xūyào. dàgài yào èrshí fēnzhōng.", "Yes. It takes about twenty minutes."),
                    ("you", "好的，我等一下。", "hǎo de, wǒ děng yíxià.", "OK, I'll wait."),
                    ("them", "好了，这是你的卡。", "hǎo le, zhè shì nǐ de kǎ.", "Done, here's your card."),
                ],
                "patterns": [
                    {
                        "text": "需要{x}吗？",
                        "reading": "xūyào {x} ma?",
                        "en": "Do you need {x}?",
                        "kind": "object",
                        "values": [("护照", "hùzhào", "a passport"), ("身份证", "shēnfènzhèng", "an ID card"), ("照片", "zhàopiàn", "a photo")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 37,
                "title": "Have you ever...?",
                "goal": "Talk about experiences with 过.",
                "vocab": [
                    ("去过", "qù guo", "have been to"),
                    ("两次", "liǎng cì", "twice"),
                    ("烤鸭", "kǎoyā", "roast duck"),
                    ("没吃过", "méi chī guo", "have never eaten"),
                    ("学过", "xué guo", "have studied"),
                    ("忘了", "wàng le", "forgotten"),
                ],
                "dialogue": [
                    ("them", "你去过中国吗？", "nǐ qù guo Zhōngguó ma?", "Have you been to China?"),
                    ("you", "去过两次。", "qù guo liǎng cì.", "Twice."),
                    ("them", "你吃过北京烤鸭吗？", "nǐ chī guo Běijīng kǎoyā ma?", "Have you eaten Peking duck?"),
                    ("you", "没吃过。下次一定要试试。", "méi chī guo. xià cì yídìng yào shìshi.", "Not yet. I must try it next time."),
                    ("them", "你学过中文吗？", "nǐ xué guo Zhōngwén ma?", "Have you studied Chinese?"),
                    ("you", "学过一年，但是忘了不少。", "xué guo yì nián, dànshì wàng le bùshǎo.", "For a year, but I've forgotten a lot."),
                ],
                "patterns": [
                    {
                        "text": "我去过{x}",
                        "reading": "wǒ qù guo {x}",
                        "en": "I have been to {x}",
                        "kind": "place",
                        "values": [("北京", "Běijīng", "Beijing"), ("上海", "Shànghǎi", "Shanghai"), ("长城", "Chángchéng", "the Great Wall")],
                    }
                ],
                "notes": ["Verb + 过 = experience. Negation is 没 + verb + 过 (not 不)."],
            },
        ],
    },
]

LEVEL = {
    "band": 3,
    "id": 3,
    "title": "HSK 3 · Real life",
    "focus": "Routines, weather, health, family, plans, comparisons and experience (过).",
    "gate": {"min_pron_score": 72.0, "min_accuracy": 72.0, "min_completeness": 85.0, "min_tone_score": 66.0},
    "units": UNITS,
}

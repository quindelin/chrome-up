# -*- coding: utf-8 -*-
"""HSK 4 — the grammar that makes you precise: 把, complements, conditionals,
passive 被, and formal connectives."""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    {
        "id": 9,
        "title": "Saying It Precisely",
        "focus": "把-sentences, result / potential / directional complements.",
        "lessons": [
            {
                "id": 38,
                "title": "The 把 sentence",
                "goal": "Say what you did to something: 把 + object + verb.",
                "vocab": [
                    ("把", "bǎ", "object marker: 把 + O + V"),
                    ("关", "guān", "to close"),
                    ("打开", "dǎkāi", "to open"),
                    ("打破", "dǎ pò", "to break"),
                    ("放在", "fàng zài", "to put at/on"),
                    ("忘", "wàng", "to forget"),
                    ("本", "běn", "measure word: books"),
                    ("门", "mén", "door"),
                ],
                "dialogue": [
                    ("them", "请把书给我。", "qǐng bǎ shū gěi wǒ.", "Please give me the book."),
                    ("you", "给你。你要哪本？", "gěi nǐ. nǐ yào něi běn?", "Here. Which one do you want?"),
                    ("them", "那本红色的。", "nà běn hóngsè de.", "The red one."),
                    ("you", "好。我把门关了，可以吗？", "hǎo. wǒ bǎ mén guān le, kěyǐ ma?", "OK. I've closed the door, is that alright?"),
                    ("them", "可以，屋里有点冷。", "kěyǐ, wū lǐ yǒudiǎn lěng.", "Yes, it's a bit cold in here."),
                    ("you", "对了，我把杯子打破了，对不起。", "duì le, wǒ bǎ bēizi dǎ pò le, duìbuqǐ.", "By the way, I broke the cup, sorry."),
                ],
                "patterns": [
                    {
                        "text": "请把{x}给我",
                        "reading": "qǐng bǎ {x} gěi wǒ",
                        "en": "Please give me the {x}",
                        "kind": "object",
                        "values": [("书", "shū", "book"), ("杯子", "bēizi", "cup"), ("钥匙", "yàoshi", "keys")],
                    }
                ],
                "notes": ["把 moves the object before the verb: 我把门关了 (I closed the door)."],
            },
            {
                "id": 39,
                "title": "Result complements",
                "goal": "Say whether an action succeeded: 听懂, 找到, 做完.",
                "vocab": [
                    ("听懂", "tīng dǒng", "understand (by listening)"),
                    ("看清楚", "kàn qīngchu", "see clearly"),
                    ("找到", "zhǎo dào", "to find"),
                    ("做完", "zuò wán", "to finish doing"),
                    ("记住", "jì zhù", "to memorise"),
                    ("打通", "dǎ tōng", "to get through (on the phone)"),
                ],
                "dialogue": [
                    ("them", "我说的话你听懂了吗？", "wǒ shuō de huà nǐ tīng dǒng le ma?", "Did you understand what I said?"),
                    ("you", "听懂了。", "tīng dǒng le.", "Yes, I understood."),
                    ("them", "黑板上的字你看清楚了吗？", "hēibǎn shàng de zì nǐ kàn qīngchu le ma?", "Can you see the characters on the board clearly?"),
                    ("you", "看清楚了。", "kàn qīngchu le.", "Yes, clearly."),
                    ("them", "你的钱包找到了吗？", "nǐ de qiánbāo zhǎo dào le ma?", "Did you find your wallet?"),
                    ("you", "找到了，在车里。", "zhǎo dào le, zài chē lǐ.", "Found it, in the car."),
                ],
                "patterns": [
                    {
                        "text": "我{x}了",
                        "reading": "wǒ {x} le",
                        "en": "I managed to {x}",
                        "values": [("听懂", "tīng dǒng", "understand by listening"), ("找到", "zhǎo dào", "find it"), ("做完", "zuò wán", "finish it")],
                    }
                ],
                "notes": ["Negative: 没听懂 / 没找到. 不 is wrong with a result complement."],
            },
            {
                "id": 40,
                "title": "Potential complements",
                "goal": "Say what you can or cannot manage: 吃得完 / 看不懂.",
                "vocab": [
                    ("吃得完", "chī de wán", "able to finish eating"),
                    ("看不懂", "kàn bù dǒng", "unable to understand by reading"),
                    ("走得到", "zǒu de dào", "able to walk there"),
                    ("听得见", "tīng de jiàn", "able to hear"),
                    ("拿得动", "ná de dòng", "able to lift"),
                    ("这么多", "zhème duō", "so much"),
                    ("大部分", "dàbùfen", "most, the majority"),
                ],
                "dialogue": [
                    ("them", "这么多，你吃得完吗？", "zhème duō, nǐ chī de wán ma?", "This much - can you finish it?"),
                    ("you", "吃不完，太多了。", "chī bu wán, tài duō le.", "I can't, it's too much."),
                    ("them", "这本书你看得懂吗？", "zhè běn shū nǐ kàn de dǒng ma?", "Can you read this book?"),
                    ("you", "大部分看得懂。", "dàbùfen kàn de dǒng.", "I can follow most of it."),
                    ("them", "从这里走得到吗？", "cóng zhèlǐ zǒu de dào ma?", "Can we walk there from here?"),
                    ("you", "走不到，太远了，我们坐车吧。", "zǒu bu dào, tài yuǎn le, wǒmen zuò chē ba.", "No, too far - let's take a bus."),
                ],
                "patterns": [
                    {
                        "text": "我{x}",
                        "reading": "wǒ {x}",
                        "en": "I can {x}",
                        "values": [("吃得完", "chī de wán", "finish eating it"), ("拿得动", "ná de dòng", "lift it"), ("听得见", "tīng de jiàn", "hear it")],
                    }
                ],
                "notes": ["Structure: verb + 得/不 + result. 吃得完 vs 吃不完."],
            },
            {
                "id": 41,
                "title": "Direction complements",
                "goal": "Add direction and state change: 进来, 坐下来, 想起来.",
                "vocab": [
                    ("进来", "jìn lái", "to come in"),
                    ("坐下来", "zuò xià lái", "to sit down"),
                    ("拿上来", "ná shàng lái", "to bring up"),
                    ("想起来", "xiǎng qǐ lái", "to recall"),
                    ("跑出去", "pǎo chū qù", "to run out"),
                    ("黑下来", "hēi xià lái", "to get dark"),
                    ("桌子", "zhuōzi", "table, desk"),
                ],
                "dialogue": [
                    ("them", "请进，外面冷。", "qǐng jìn, wàimiàn lěng.", "Come in, it's cold outside."),
                    ("you", "谢谢，我坐下来了。", "xièxie, wǒ zuò xià lái le.", "Thanks, I've sat down."),
                    ("them", "你能把包拿上来吗？", "nǐ néng bǎ bāo ná shàng lái ma?", "Can you bring the bag up?"),
                    ("you", "可以，给你。", "kěyǐ, gěi nǐ.", "Sure, here."),
                    ("them", "天黑下来了，我们走吧。", "tiān hēi xià lái le, wǒmen zǒu ba.", "It's getting dark, let's go."),
                    ("you", "好，我想起来了，钥匙在桌上。", "hǎo, wǒ xiǎng qǐ lái le, yàoshi zài zhuō shàng.", "OK - I remember now, the keys are on the table."),
                ],
                "patterns": [
                    {
                        "text": "请你{x}",
                        "reading": "qǐng nǐ {x}",
                        "en": "Please {x}",
                        "values": [("进来", "jìn lái", "come in"), ("坐下来", "zuò xià lái", "sit down"), ("拿上来", "ná shàng lái", "bring it up")],
                    }
                ],
                "notes": ["下来/起来 also mark state change: 天黑下来了, 我想起来了."],
            },
        ],
    },
    {
        "id": 10,
        "title": "Cause & Condition",
        "focus": "越来越, 一…就, 只要…就, 虽然…但是, 即使, 不管.",
        "lessons": [
            {
                "id": 42,
                "title": "More and more",
                "goal": "Describe a trend with 越来越.",
                "vocab": [
                    ("越来越", "yuè lái yuè", "more and more"),
                    ("难", "nán", "difficult"),
                    ("人多", "rén duō", "crowded"),
                    ("贵", "guì", "expensive"),
                    ("忙", "máng", "busy"),
                    ("严重", "yánzhòng", "serious"),
                    ("东西", "dōngxi", "thing, stuff"),
                    ("工作", "gōngzuò", "to work; job"),
                    ("连…都", "lián…dōu", "even …"),
                ],
                "dialogue": [
                    ("them", "你觉得中文难吗？", "nǐ juéde Zhōngwén nán ma?", "Do you find Chinese difficult?"),
                    ("you", "越来越难了，但是很有意思。", "yuè lái yuè nán le, dànshì hěn yǒu yìsi.", "More and more difficult, but very interesting."),
                    ("them", "这里的人是不是越来越多了？", "zhèlǐ de rén shì bú shì yuè lái yuè duō le?", "Are there more and more people here?"),
                    ("you", "对，而且东西也越来越贵。", "duì, érqiě dōngxi yě yuè lái yuè guì.", "Yes, and things are getting more expensive too."),
                    ("them", "你最近忙吗？", "nǐ zuìjìn máng ma?", "Have you been busy lately?"),
                    ("you", "越来越忙，连周末都要工作。", "yuè lái yuè máng, lián zhōumò dōu yào gōngzuò.", "Busier and busier - I even work at weekends."),
                ],
                "patterns": [
                    {
                        "text": "天气越来越{x}",
                        "reading": "tiānqì yuè lái yuè {x}",
                        "en": "The weather is getting {x}",
                        "kind": "weather",
                        "values": [("热", "rè", "hotter"), ("冷", "lěng", "colder"), ("好", "hǎo", "better")],
                    }
                ],
                "notes": ["越来越 + adjective. No 很 after it."],
            },
            {
                "id": 43,
                "title": "As soon as / as long as",
                "goal": "Use 一…就 and 只要…就.",
                "vocab": [
                    ("一…就", "yī…jiù", "as soon as"),
                    ("只要", "zhǐyào", "as long as"),
                    ("努力", "nǔlì", "to make an effort"),
                    ("来得及", "lái de jí", "there is still time"),
                    ("出门", "chū mén", "to go out"),
                    ("坚持", "jiānchí", "to persist"),
                ],
                "dialogue": [
                    ("them", "你一般什么时候吃饭？", "nǐ yìbān shénme shíhou chī fàn?", "When do you usually eat?"),
                    ("you", "我一到家就吃饭。", "wǒ yí dào jiā jiù chī fàn.", "I eat as soon as I get home."),
                    ("them", "那学习呢？", "nà xuéxí ne?", "And studying?"),
                    ("you", "只要有时间，我就看一会儿书。", "zhǐyào yǒu shíjiān, wǒ jiù kàn yíhuìr shū.", "I read a bit whenever I have time."),
                    ("them", "明天下雨你还去吗？", "míngtiān xià yǔ nǐ hái qù ma?", "Will you still go if it rains tomorrow?"),
                    ("you", "只要不下雨，我就去。", "zhǐyào bú xià yǔ, wǒ jiù qù.", "As long as it doesn't rain, I'll go."),
                ],
                "patterns": [
                    {
                        "text": "我一到家就{x}",
                        "reading": "wǒ yí dào jiā jiù {x}",
                        "en": "As soon as I get home I {x}",
                        "values": [("吃饭", "chī fàn", "eat"), ("睡觉", "shuì jiào", "sleep"), ("看书", "kàn shū", "read")],
                    }
                ],
                "notes": ["一 is pronounced yí / yì depending on the following tone."],
            },
            {
                "id": 44,
                "title": "Not only / although",
                "goal": "Combine ideas with 不但…而且 and 虽然…但是.",
                "vocab": [
                    ("不但", "búdàn", "not only"),
                    ("而且", "érqiě", "but also"),
                    ("虽然", "suīrán", "although"),
                    ("值得", "zhíde", "worth it"),
                    ("聪明", "cōngmíng", "clever"),
                    ("排队", "pái duì", "to queue"),
                ],
                "dialogue": [
                    ("them", "你觉得小王怎么样？", "nǐ juéde Xiǎo Wáng zěnmeyàng?", "What do you think of Xiao Wang?"),
                    ("you", "他不但聪明，而且很努力。", "tā búdàn cōngmíng, érqiě hěn nǔlì.", "He's not only clever but also hard-working."),
                    ("them", "这家餐厅呢？", "zhè jiā cāntīng ne?", "What about this restaurant?"),
                    ("you", "不但好吃，而且不贵。", "búdàn hǎochī, érqiě bú guì.", "Not only tasty, but also cheap."),
                    ("them", "但是排队要很久。", "dànshì páiduì yào hěn jiǔ.", "But the queue is very long."),
                    ("you", "虽然要等，但是值得。", "suīrán yào děng, dànshì zhíde.", "Although you wait, it's worth it."),
                ],
                "patterns": [
                    {
                        "text": "这道菜不但{x}",
                        "reading": "zhè dào cài búdàn {x}",
                        "en": "This dish is not only {x}",
                        "kind": "food",
                        "values": [("好吃", "hǎochī", "tasty"), ("便宜", "piányi", "cheap"), ("新鲜", "xīnxiān", "fresh")],
                    }
                ],
                "notes": ["虽然 and 但是 belong together in Chinese - you normally use both."],
            },
            {
                "id": 45,
                "title": "Since / even if / no matter",
                "goal": "Use 既然, 即使 and 不管.",
                "vocab": [
                    ("既然", "jìrán", "since / given that"),
                    ("即使", "jíshǐ", "even if"),
                    ("不管", "bùguǎn", "no matter"),
                    ("试一试", "shì yi shì", "to have a try"),
                    ("多待一会儿", "duō dāi yíhuìr", "stay a while longer"),
                    ("例外", "lìwài", "exception"),
                ],
                "dialogue": [
                    ("them", "明天爬山，你去吗？", "míngtiān pá shān, nǐ qù ma?", "We're hiking tomorrow - are you going?"),
                    ("you", "即使下雨，我也要去。", "jíshǐ xià yǔ, wǒ yě yào qù.", "Even if it rains, I'll go."),
                    ("them", "你身体不太舒服吧？", "nǐ shēntǐ bú tài shūfu ba?", "You're not feeling well, aren't you?"),
                    ("you", "既然来了，就多待一会儿。", "jìrán lái le, jiù duō dāi yíhuìr.", "Since I'm here, I'll stay a bit longer."),
                    ("them", "你总是这么坚持吗？", "nǐ zǒngshì zhème jiānchí ma?", "Are you always this persistent?"),
                    ("you", "不管多难，我都要试一试。", "bùguǎn duō nán, wǒ dōu yào shì yi shì.", "No matter how hard, I'll give it a go."),
                ],
                "patterns": [
                    {
                        "text": "即使{x}，我也要去",
                        "reading": "jíshǐ {x}, wǒ yě yào qù",
                        "en": "Even if {x}, I'm still going",
                        "values": [("下雨", "xià yǔ", "it rains"), ("很累", "hěn lèi", "I'm tired"), ("没人陪", "méi rén péi", "nobody comes along")],
                    }
                ],
                "notes": ["不管 + question word (多难 / 谁 / 什么时候) + 都/也."],
            },
        ],
    },
    {
        "id": 11,
        "title": "Formal Structures",
        "focus": "Passive 被, 关于 / 对于 / 通过, 一方面…另一方面, and a review.",
        "lessons": [
            {
                "id": 46,
                "title": "Things that happened to me",
                "goal": "Use the passive with 被.",
                "vocab": [
                    ("被", "bèi", "by (passive marker)"),
                    ("偷", "tōu", "to steal"),
                    ("批评", "pīpíng", "to criticise"),
                    ("选为", "xuǎn wéi", "to be elected as"),
                    ("钱包", "qiánbāo", "wallet"),
                    ("小心", "xiǎoxīn", "to be careful"),
                ],
                "dialogue": [
                    ("them", "你怎么了？", "nǐ zěnme le?", "What happened to you?"),
                    ("you", "我的手机被偷了。", "wǒ de shǒujī bèi tōu le.", "My phone was stolen."),
                    ("them", "真的吗？在哪儿？", "zhēn de ma? zài nǎr?", "Really? Where?"),
                    ("you", "在地铁上。钱包也被偷了。", "zài dìtiě shàng. qiánbāo yě bèi tōu le.", "On the subway. My wallet too."),
                    ("them", "太糟糕了。报警了吗？", "tài zāogāo le. bàojǐng le ma?", "That's awful. Did you call the police?"),
                    ("you", "报了。以后我一定小心。", "bào le. yǐhòu wǒ yídìng xiǎoxīn.", "Yes. I'll be careful from now on."),
                ],
                "patterns": [
                    {
                        "text": "我的{x}被偷了",
                        "reading": "wǒ de {x} bèi tōu le",
                        "en": "My {x} was stolen",
                        "kind": "object",
                        "values": [("手机", "shǒujī", "phone"), ("钱包", "qiánbāo", "wallet"), ("自行车", "zìxíngchē", "bicycle")],
                    }
                ],
                "notes": ["被 is mostly used for unpleasant events."],
            },
            {
                "id": 47,
                "title": "Regarding / as for / through",
                "goal": "Frame a topic with 关于, 对于, 通过.",
                "vocab": [
                    ("关于", "guānyú", "regarding"),
                    ("对于", "duìyú", "as for / to"),
                    ("通过", "tōngguò", "via / through"),
                    ("了解", "liǎojiě", "to understand (a subject)"),
                    ("感兴趣", "gǎn xìngqù", "to be interested in"),
                    ("介绍", "jièshào", "to introduce"),
                    ("敢", "gǎn", "to dare"),
                    ("非常", "fēicháng", "very, extremely"),
                ],
                "dialogue": [
                    ("them", "关于这个问题，你怎么看？", "guānyú zhè ge wèntí, nǐ zěnme kàn?", "What's your view on this issue?"),
                    ("you", "我不太了解，不敢说。", "wǒ bú tài liǎojiě, bù gǎn shuō.", "I don't know much about it, I'd rather not say."),
                    ("them", "对于中文，你感兴趣吗？", "duìyú Zhōngwén, nǐ gǎn xìngqù ma?", "Are you interested in Chinese?"),
                    ("you", "非常感兴趣。", "fēicháng gǎn xìngqù.", "Very much so."),
                    ("them", "你是怎么找到这份工作的？", "nǐ shì zěnme zhǎodào zhè fèn gōngzuò de?", "How did you find this job?"),
                    ("you", "通过一个朋友介绍的。", "tōngguò yí ge péngyou jièshào de.", "A friend introduced me."),
                ],
                "patterns": [
                    {
                        "text": "对于{x}，我很感兴趣",
                        "reading": "duìyú {x}, wǒ hěn gǎn xìngqù",
                        "en": "I'm very interested in {x}",
                        "values": [("中文", "Zhōngwén", "Chinese"), ("历史", "lìshǐ", "history"), ("音乐", "yīnyuè", "music")],
                    }
                ],
                "notes": ["通过 = by means of / via; 经过 = to pass by or after a process."],
            },
            {
                "id": 48,
                "title": "On the one hand...",
                "goal": "Weigh two sides with 一方面…另一方面 and 不仅.",
                "vocab": [
                    ("一方面", "yì fāngmiàn", "on the one hand"),
                    ("另一方面", "lìng yì fāngmiàn", "on the other hand"),
                    ("不仅", "bùjǐn", "not only"),
                    ("质量", "zhìliàng", "quality"),
                    ("影响", "yǐngxiǎng", "to affect"),
                    ("反而", "fǎn'ér", "on the contrary"),
                    ("省钱", "shěng qián", "to save money"),
                    ("健康", "jiànkāng", "health; healthy"),
                ],
                "dialogue": [
                    ("them", "你为什么骑车上班？", "nǐ wèishénme qí chē shàngbān?", "Why do you cycle to work?"),
                    ("you", "一方面方便，另一方面省钱。", "yì fāngmiàn fāngbiàn, lìng yì fāngmiàn shěng qián.", "It's convenient, and it saves money."),
                    ("them", "只有你这样吗？", "zhǐyǒu nǐ zhèyàng ma?", "Are you the only one?"),
                    ("you", "不仅是我，很多同事也骑车。", "bùjǐn shì wǒ, hěn duō tóngshì yě qí chē.", "Not just me, many colleagues cycle too."),
                    ("them", "这对环境也有好处吧？", "zhè duì huánjìng yě yǒu hǎochù ba?", "It's good for the environment too?"),
                    ("you", "对，不但不影响健康，反而更好。", "duì, búdàn bù yǐngxiǎng jiànkāng, fǎn'ér gèng hǎo.", "Yes, it doesn't harm your health - on the contrary, it helps."),
                ],
                "patterns": [
                    {
                        "text": "骑车一方面很{x}",
                        "reading": "qí chē yì fāngmiàn hěn {x}",
                        "en": "Cycling is, on one hand, very {x}",
                        "values": [("方便", "fāngbiàn", "convenient"), ("健康", "jiànkāng", "healthy"), ("省钱", "shěng qián", "money-saving")],
                    }
                ],
                "notes": ["反而 = contrary to what you'd expect. It follows a negative clause."],
            },
            {
                "id": 49,
                "title": "Review: asking for leave",
                "goal": "A full HSK 4 exchange at work, mixing 把 and complements.",
                "vocab": [
                    ("请假", "qǐng jià", "to ask for leave"),
                    ("请假条", "qǐngjià tiáo", "leave request note"),
                    ("厉害", "lìhài", "severe / formidable"),
                    ("养好", "yǎng hǎo", "to nurse back to health"),
                    ("安排", "ānpái", "to arrange"),
                    ("发", "fā", "to send"),
                    ("药", "yào", "medicine"),
                    ("您", "nín", "you (polite)"),
                ],
                "dialogue": [
                    ("you", "王经理，我想请一天假。", "Wáng jīnglǐ, wǒ xiǎng qǐng yì tiān jià.", "Manager Wang, I'd like a day off."),
                    ("them", "怎么了？身体不舒服吗？", "zěnme le? shēntǐ bù shūfu ma?", "What's up? Are you unwell?"),
                    ("you", "我感冒了，头疼得厉害。", "wǒ gǎnmào le, tóu téng de lìhài.", "I have a cold and a bad headache."),
                    ("them", "去医院了吗？", "qù yīyuàn le ma?", "Did you go to the hospital?"),
                    ("you", "去了，医生说要把药吃完，还要多休息。", "qù le, yīshēng shuō yào bǎ yào chī wán, hái yào duō xiūxi.", "Yes - the doctor said to finish the medicine and rest a lot."),
                    ("them", "好，工作我先帮你安排。", "hǎo, gōngzuò wǒ xiān bāng nǐ ānpái.", "OK, I'll arrange your work for now."),
                    ("you", "谢谢。我会把请假条发给您。", "xièxie. wǒ huì bǎ qǐngjià tiáo fā gěi nín.", "Thanks. I'll send you the leave form."),
                    ("them", "不急，先养好身体。", "bù jí, xiān yǎng hǎo shēntǐ.", "No rush - get better first."),
                ],
                "patterns": [
                    {
                        "text": "我把{x}发给您",
                        "reading": "wǒ bǎ {x} fā gěi nín",
                        "en": "I'll send you the {x}",
                        "kind": "object",
                        "values": [("请假条", "qǐngjià tiáo", "leave form"), ("文件", "wénjiàn", "document"), ("照片", "zhàopiàn", "photo")],
                    }
                ],
                "notes": ["得厉害 = to a severe degree: 疼得厉害, 忙得厉害."],
            },
        ],
    },
]

LEVEL = {
    "band": 4,
    "id": 4,
    "title": "HSK 4 · Precision",
    "focus": "把, complements, 越来越, conditionals, 被, formal connectives.",
    "gate": {"min_pron_score": 75.0, "min_accuracy": 75.0, "min_completeness": 88.0, "min_tone_score": 70.0},
    "units": UNITS,
}

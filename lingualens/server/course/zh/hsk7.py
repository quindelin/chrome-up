# -*- coding: utf-8 -*-
"""HSK 7-9 — beyond the exam: native register and the domains you actually
need it in.

The old HSK topped out at 6, so the course did too, and "HSK 6" quietly
became the goal. It is not the goal. The 2021 standard adds 7-9 on top of
HSK 6 and roughly doubles the word count again (11,092 words across the
whole ladder); more to the point, the difference between 6 and 7-9 is not
more vocabulary, it is *register and domain*. At HSK 6 you can hold a
conversation. At 7-9 you can follow the news, read a contract, sit in a
meeting about 合规, and tell 内卷 from 竞争.

So this band is deliberately not "HSK 6 again with harder words":

* lessons 74-79 are **native register** - what real speech and real text
  sound like when nobody is grading it: news formulae, internet slang,
  regional accents, 成语 with their stories, poetry, and the connected
  speech that makes "every character you know" still incomprehensible.
* lessons 80-85 are **domains** - the vocabulary of economics, technology
  and ethics, law, energy, and research. Nobody needs these to buy
  dumplings; everybody needs them the first time they are in a room where
  Chinese is the working language.

Two deliberate choices worth knowing about:

1. Slang and accent are taught as *comprehension*, not as production. The
   notes say so. A learner who uses 内卷 in a job interview is fine; one
   who uses it in a report is not, and the lesson says which.
2. Band 7 turns the pinyin off entirely (`ui.reading_by_level`). By here
   the characters are the text, and a pinyin line above them is a crutch
   that has outlived its use.
"""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    {
        "id": 16,
        "title": "Native Register",
        "focus": "News formulae, internet slang, accents, 成语 with their stories, poetry, connected speech.",
        "lessons": [
            {
                "id": 74,
                "title": "The news",
                "goal": "Follow a Chinese news report and say what it said.",
                "vocab": [
                    ("据报道", "jù bàodào", "according to reports"),
                    ("数据显示", "shùjù xiǎnshì", "the figures show"),
                    ("引发", "yǐnfā", "to give rise to"),
                    ("广泛关注", "guǎngfàn guānzhù", "widespread attention"),
                    ("官方", "guānfāng", "official"),
                    ("回应", "huíyìng", "to respond (officially)"),
                ],
                "dialogue": [
                    ("them", "你看今天的新闻了吗？", "nǐ kàn jīntiān de xīnwén le ma?", "Have you seen today's news?"),
                    ("you", "看了。据报道，今年毕业生的数量又创新高。", "kàn le. jù bàodào, jīnnián bìyèshēng de shùliàng yòu chuàng xīn gāo.", "Yes. Reports say the number of graduates hit a new high again."),
                    ("them", "官方有回应吗？", "guānfāng yǒu huíyìng ma?", "Has there been an official response?"),
                    ("you", "有，相关部门已经回应，说会加大支持力度。", "yǒu, xiāngguān bùmén yǐjīng huíyìng, shuō huì jiādà zhīchí lìdù.", "Yes - the departments concerned have responded, saying they will increase support."),
                    ("them", "网上讨论得厉害吗？", "wǎngshang tǎolùn de lìhai ma?", "Is there much discussion online?"),
                    ("you", "很厉害，这件事引发了广泛关注。", "hěn lìhai, zhè jiàn shì yǐnfā le guǎngfàn guānzhù.", "A great deal - it has drawn widespread attention."),
                ],
                "patterns": [
                    {
                        "text": "据{x}",
                        "reading": "jù {x}",
                        "en": "According to {x}",
                        "values": [("报道", "bàodào", "reports"), ("统计", "tǒngjì", "the statistics"), ("官方消息", "guānfāng xiāoxi", "official sources")],
                    }
                ],
                "notes": ["据 is written register. Out loud you would say 听说 or 新闻上说."],
            },
            {
                "id": 75,
                "title": "Internet slang",
                "goal": "Understand 内卷, 躺平 and friends - and know where not to use them.",
                "vocab": [
                    ("内卷", "nèijuǎn", "cut-throat competition with no gain"),
                    ("躺平", "tǎng píng", "to opt out; to lie flat"),
                    ("出圈", "chū quān", "to break out of one's niche"),
                    ("刷屏", "shuā píng", "to flood the feed"),
                    ("给力", "gěi lì", "impressive; does the job"),
                    ("土豪", "tǔháo", "flashy rich person"),
                ],
                "dialogue": [
                    ("them", "最近老看到一个词，内卷。", "zuìjìn lǎo kàn dào yí ge cí, nèijuǎn.", "I keep seeing the word 内卷 lately."),
                    ("you", "就是大家过度竞争，付出越来越多，收获却没变多。", "jiùshì dàjiā guòdù jìngzhēng, fùchū yuè lái yuè duō, shōuhuò què méi biàn duō.", "It means everyone competing harder and harder for no extra gain."),
                    ("them", "那躺平呢？", "nà tǎng píng ne?", "And 躺平?"),
                    ("you", "躺平就是干脆不争了，两个词经常一起出现。", "tǎng píng jiùshì gāncuì bù zhēng le, liǎng ge cí jīngcháng yìqǐ chūxiàn.", "It means just opting out. The two words usually travel together."),
                    ("them", "这些词正式吗？", "zhèxiē cí zhèngshì ma?", "Are these words formal?"),
                    ("you", "不算正式。聊天可以用，写报告千万别用。", "bú suàn zhèngshì. liáotiān kěyǐ yòng, xiě bàogào qiānwàn bié yòng.", "Not formal. Fine in chat; never in a report."),
                ],
                "patterns": [
                    {
                        "text": "这件事{x}",
                        "reading": "zhè jiàn shì {x}",
                        "en": "This is {x}",
                        "values": [("太内卷了", "tài nèijuǎn le", "far too cut-throat"), ("挺给力的", "tǐng gěi lì de", "pretty impressive"), ("已经出圈了", "yǐjīng chū quān le", "already gone mainstream")],
                    }
                ],
                "notes": [
                    "These are comprehension targets first: you need to understand them, and you may use them with friends.",
                    "None of them belong in writing, in an interview, or with someone older than you. 内卷 in a report reads as careless.",
                ],
            },
            {
                "id": 76,
                "title": "Accents",
                "goal": "Talk about accents and understand why you still can't follow people.",
                "vocab": [
                    ("口音", "kǒuyīn", "accent"),
                    ("方言", "fāngyán", "dialect"),
                    ("普通话", "pǔtōnghuà", "Standard Mandarin"),
                    ("标准", "biāozhǔn", "standard"),
                    ("听得出来", "tīng de chū lái", "can tell by listening"),
                    ("字正腔圆", "zì zhèng qiāng yuán", "perfectly enunciated"),
                ],
                "dialogue": [
                    ("them", "你听得出来我是哪里人吗？", "nǐ tīng de chū lái wǒ shì nǎlǐ rén ma?", "Can you tell where I'm from?"),
                    ("you", "听得出来，你有一点南方口音，但是很轻。", "tīng de chū lái, nǐ yǒu yìdiǎn nánfāng kǒuyīn, dànshì hěn qīng.", "Yes - a slight southern accent, but very slight."),
                    ("them", "我担心说得不够标准。", "wǒ dānxīn shuō de bú gòu biāozhǔn.", "I worry I don't sound standard enough."),
                    ("you", "没关系，带一点口音很正常，本地人也有方言。", "méi guānxi, dài yìdiǎn kǒuyīn hěn zhèngcháng, běndì rén yě yǒu fāngyán.", "It doesn't matter. A slight accent is normal - locals have dialects too."),
                    ("them", "那我还要改吗？", "nà wǒ hái yào gǎi ma?", "So should I still fix it?"),
                    ("you", "只要别人听得懂就不用改。字正腔圆是播音员的事。", "zhǐyào biérén tīng de dǒng jiù bú yòng gǎi. zì zhèng qiāng yuán shì bōyīn yuán de shì.", "If people understand you, there's nothing to fix. Perfect enunciation is for announcers."),
                ],
                "patterns": [
                    {
                        "text": "听得{x}",
                        "reading": "tīng de {x}",
                        "en": "Can tell by listening: {x}",
                        "values": [("出来", "chū lái", "can make it out"), ("懂", "dǒng", "can understand it"), ("不太懂", "bú tài dǒng", "can barely follow it")],
                    }
                ],
                "notes": ["听得出来 vs 听得懂: the first is 'I can tell', the second 'I can understand'."],
            },
            {
                "id": 77,
                "title": "Where idioms come from",
                "goal": "Know the stories behind the 成语 you already use.",
                "vocab": [
                    ("掩耳盗铃", "yǎn ěr dào líng", "to deceive oneself"),
                    ("刻舟求剑", "kè zhōu qiú jiàn", "to ignore how things have changed"),
                    ("守株待兔", "shǒu zhū dài tù", "to wait for luck to repeat"),
                    ("画蛇添足", "huà shé tiān zú", "to ruin it by overdoing it"),
                    ("亡羊补牢", "wáng yáng bǔ láo", "better late than never"),
                    ("寓意", "yùyì", "the moral of it"),
                ],
                "dialogue": [
                    ("them", "掩耳盗铃到底是什么意思？", "yǎn ěr dào líng dàodǐ shì shénme yìsi?", "What does 掩耳盗铃 actually mean?"),
                    ("you", "捂着自己的耳朵去偷铃铛，以为别人也听不见。比喻自己骗自己。", "wǔ zhe zìjǐ de ěrduo qù tōu língdang, yǐwéi biérén yě tīng bu jiàn. bǐyù zìjǐ piàn zìjǐ.", "Covering your own ears to steal a bell, as if nobody else could hear. It means deceiving yourself."),
                    ("them", "那刻舟求剑呢？", "nà kè zhōu qiú jiàn ne?", "And 刻舟求剑?"),
                    ("you", "剑掉进水里，在船上刻个记号，船走了还按记号找。说的是不知变通。", "jiàn diào jìn shuǐ lǐ, zài chuán shang kè ge jìhao, chuán zǒu le hái àn jìhao zhǎo. shuō de shì bù zhī biàntōng.", "A sword falls in the water, he marks the boat, and looks for it there after the boat has moved. It means refusing to adapt."),
                    ("them", "这些故事都有出处吗？", "zhèxiē gùshi dōu yǒu chūchù ma?", "Do these stories all have a source?"),
                    ("you", "几乎每个成语背后都有一个故事，这就是它们的寓意所在。", "jīhū měi ge chéngyǔ bèihòu dōu yǒu yí ge gùshi, zhè jiùshì tāmen de yùyì suǒ zài.", "Almost every idiom has a story behind it - that's where the moral comes from."),
                ],
                "patterns": [
                    {
                        "text": "这真是{x}",
                        "reading": "zhè zhēn shì {x}",
                        "en": "This is really {x}",
                        "values": [("掩耳盗铃", "yǎn ěr dào líng", "pure self-deception"), ("画蛇添足", "huà shé tiān zú", "gilding the lily"), ("亡羊补牢", "wáng yáng bǔ láo", "late but not too late")],
                    }
                ],
                "notes": ["亡羊补牢 is usually followed by 为时未晚 - 'mending the fold after the sheep is gone is not too late'."],
            },
            {
                "id": 78,
                "title": "Poetry",
                "goal": "Talk about the poems every Chinese person knows by heart.",
                "vocab": [
                    ("古诗", "gǔshī", "classical poetry"),
                    ("背诵", "bèisòng", "to recite from memory"),
                    ("名句", "míngjù", "a famous line"),
                    ("意境", "yìjìng", "mood; the picture a poem paints"),
                    ("唐诗", "Táng shī", "Tang poetry"),
                    ("流传千古", "liúchuán qiāngǔ", "to be handed down for millennia"),
                ],
                "dialogue": [
                    ("them", "中国人真的会背古诗吗？", "Zhōngguó rén zhēn de huì bèi gǔshī ma?", "Do Chinese people really recite classical poetry?"),
                    ("you", "小时候都背过，很多名句到现在还记得。", "xiǎoshíhou dōu bèi guo, hěn duō míngjù dào xiànzài hái jìde.", "Everyone memorised some as a child, and many of the famous lines stick."),
                    ("them", "比如呢？", "bǐrú ne?", "Such as?"),
                    ("you", "“床前明月光”，几乎人人都会。", "“chuáng qián míng yuè guāng”, jīhū rén rén dōu huì.", "“Before my bed the moonlight glows” - almost everyone knows that one."),
                    ("them", "为什么这些诗能流传千古？", "wèishénme zhèxiē shī néng liúchuán qiāngǔ?", "Why have these poems lasted so long?"),
                    ("you", "因为意境好，短短几个字就能画出一幅画。", "yīnwèi yìjìng hǎo, duǎnduǎn jǐ ge zì jiù néng huà chū yì fú huà.", "Because of the mood - a few characters and you can see the picture."),
                ],
                "patterns": [
                    {
                        "text": "{x}几乎人人都会",
                        "reading": "{x} jīhū rén rén dōu huì",
                        "en": "Almost everyone knows {x}",
                        "values": [("这首诗", "zhè shǒu shī", "this poem"), ("这句", "zhè jù", "this line"), ("这个故事", "zhè ge gùshi", "this story")],
                    }
                ],
                "notes": ["意境 has no clean English equivalent: it is the picture-and-feeling a poem leaves you with."],
            },
            {
                "id": 79,
                "title": "Why you still can't follow it",
                "goal": "Understand connected speech: 连读, 吞音, 省略.",
                "vocab": [
                    ("连读", "liándú", "liaison; running words together"),
                    ("吞音", "tūn yīn", "swallowing a sound"),
                    ("省略", "shěnglüè", "to omit"),
                    ("语气词", "yǔqì cí", "sentence-final particle"),
                    ("节奏", "jiézòu", "rhythm; pace"),
                    ("听起来", "tīng qǐ lái", "sounds (like)"),
                ],
                "dialogue": [
                    ("them", "为什么中国人说话我听不懂，明明每个字都学过？", "wèishénme Zhōngguó rén shuō huà wǒ tīng bu dǒng, míngmíng měi ge zì dōu xué guo?", "Why can't I follow Chinese people when I know every character?"),
                    ("you", "因为口语会连读、会吞音，还会省略。", "yīnwèi kǒuyǔ huì liándú, huì tūn yīn, hái huì shěnglüè.", "Because speech runs words together, swallows sounds, and drops things."),
                    ("them", "比如说？", "bǐrú shuō?", "For instance?"),
                    ("you", "比如 “不知道” 常常说成两个字的音，“这样子” 听起来像 “酱紫”。", "bǐrú “bù zhīdào” chángcháng shuō chéng liǎng ge zì de yīn, “zhèyàngzi” tīng qǐ lái xiàng “jiàng zǐ”.", "For instance, 不知道 often comes out as two syllables, and 这样子 sounds like 酱紫."),
                    ("them", "那我该怎么办？", "nà wǒ gāi zěnme bàn?", "So what should I do?"),
                    ("you", "先抓节奏和语气词，别一个字一个字地听。", "xiān zhuā jiézòu hé yǔqì cí, bié yí ge zì yí ge zì de tīng.", "Catch the rhythm and the particles first. Don't listen character by character."),
                ],
                "patterns": [
                    {
                        "text": "听起来像{x}",
                        "reading": "tīng qǐ lái xiàng {x}",
                        "en": "Sounds like {x}",
                        "values": [("另一个词", "lìng yí ge cí", "a different word"), ("方言", "fāngyán", "a dialect"), ("没说完", "méi shuō wán", "they haven't finished")],
                    }
                ],
                "notes": ["This is a listening lesson, not a speaking one: you are learning to hear these, not to say them."],
            },
        ],
    },
    {
        "id": 17,
        "title": "Domains",
        "focus": "The working vocabulary of economics, technology, law, energy and research.",
        "lessons": [
            {
                "id": 80,
                "title": "Figures",
                "goal": "Read a quarterly figure out loud and say what it means.",
                "vocab": [
                    ("增长率", "zēngzhǎng lǜ", "growth rate"),
                    ("同比", "tóngbǐ", "year on year"),
                    ("环比", "huánbǐ", "quarter on quarter; period on period"),
                    ("增幅", "zēngfú", "amount of increase"),
                    ("回落", "huíluò", "to fall back"),
                    ("稳健", "wěnjiàn", "steady; sound"),
                ],
                "dialogue": [
                    ("them", "今年第一季度的数据怎么样？", "jīnnián dì-yī jìdù de shùjù zěnmeyàng?", "How are this year's first-quarter figures?"),
                    ("you", "增长 5.2%，同比提高 0.4 个百分点。", "zēngzhǎng 5.2%, tóngbǐ tígāo 0.4 ge bǎifēndiǎn.", "Growth of 5.2%, up 0.4 percentage points year on year."),
                    ("them", "和上季度比呢？", "hé shàng jìdù bǐ ne?", "Compared with last quarter?"),
                    ("you", "环比略有回落，但整体还算稳健。", "huánbǐ lüè yǒu huíluò, dàn zhěngtǐ hái suàn wěnjiàn.", "Slightly down on the previous quarter, but sound overall."),
                    ("them", "增幅主要在哪些行业？", "zēngfú zhǔyào zài nǎxiē hángyè?", "Where is the increase concentrated?"),
                    ("you", "主要在服务和制造，投资方面增幅不大。", "zhǔyào zài fúwù hé zhìzào, tóuzī fāngmiàn zēngfú bú dà.", "Mainly services and manufacturing; investment hasn't grown much."),
                ],
                "patterns": [
                    {
                        "text": "{x}增长百分之五",
                        "reading": "{x} zēngzhǎng bǎi fēn zhī wǔ",
                        "en": "Up five percent {x}",
                        "values": [("同比", "tóngbǐ", "year on year"), ("环比", "huánbǐ", "period on period"), ("整体", "zhěngtǐ", "overall")],
                    }
                ],
                "notes": ["同比 = against the same period last year. 环比 = against the previous period. Mixing them up is the commonest mistake in a Chinese business meeting."],
            },
            {
                "id": 81,
                "title": "Technology & ethics",
                "goal": "Argue about algorithms, data and regulation.",
                "vocab": [
                    ("算法", "suànfǎ", "algorithm"),
                    ("隐私", "yǐnsī", "privacy"),
                    ("监管", "jiānguǎn", "regulation; oversight"),
                    ("滥用", "lànyòng", "to misuse"),
                    ("边界", "biānjiè", "boundary; limit"),
                    ("透明", "tòumíng", "transparent"),
                ],
                "dialogue": [
                    ("them", "你觉得算法推荐有问题吗？", "nǐ juéde suànfǎ tuījiàn yǒu wèntí ma?", "Do you think algorithmic recommendation is a problem?"),
                    ("you", "有。它让人只看自己想看的，视野越来越窄。", "yǒu. tā ràng rén zhǐ kàn zìjǐ xiǎng kàn de, shìyě yuè lái yuè zhǎi.", "Yes. It keeps people seeing only what they already want, so their view narrows."),
                    ("them", "隐私方面呢？", "yǐnsī fāngmiàn ne?", "What about privacy?"),
                    ("you", "更严重。数据怎么用，用户往往不知道。", "gèng yánzhòng. shùjù zěnme yòng, yònghù wǎngwǎng bù zhīdào.", "More serious. Users often have no idea how their data is used."),
                    ("them", "那该怎么管？", "nà gāi zěnme guǎn?", "So how should it be governed?"),
                    ("you", "监管要跟上，规则要透明，不能等滥用之后再说。", "jiānguǎn yào gēn shàng, guīzé yào tòumíng, bù néng děng lànyòng zhīhòu zài shuō.", "Oversight has to keep up and the rules have to be transparent. You can't wait until after the misuse."),
                ],
                "patterns": [
                    {
                        "text": "不能等{x}再处理",
                        "reading": "bù néng děng {x} zài chǔlǐ",
                        "en": "We can't wait for {x} before dealing with it",
                        "values": [("出事", "chū shì", "something going wrong"), ("有人投诉", "yǒu rén tóusù", "someone complaining"), ("上了新闻", "shàng le xīnwén", "it making the news")],
                    }
                ],
                "notes": ["跟上 means 'keep up with', not 'follow' - 监管要跟上 is 'regulation needs to catch up'."],
            },
            {
                "id": 82,
                "title": "Law",
                "goal": "Talk about rights, compliance and what happens next.",
                "vocab": [
                    ("立法", "lìfǎ", "to legislate"),
                    ("执法", "zhífǎ", "to enforce the law"),
                    ("维权", "wéi quán", "to defend one's rights"),
                    ("合规", "hé guī", "compliant"),
                    ("判决", "pànjué", "judgment; verdict"),
                    ("上诉", "shàngsù", "to appeal"),
                ],
                "dialogue": [
                    ("them", "遇到这种情况，普通人怎么维权？", "yù dào zhè zhǒng qíngkuàng, pǔtōng rén zěnme wéi quán?", "In a case like this, how does an ordinary person defend their rights?"),
                    ("you", "先保留证据，再找律师，必要的时候可以起诉。", "xiān bǎoliú zhèngjù, zài zhǎo lǜshī, bìyào de shíhou kěyǐ qǐsù.", "Keep the evidence, then find a lawyer, and sue if it comes to that."),
                    ("them", "判决下来还能改吗？", "pànjué xià lái hái néng gǎi ma?", "Once judgment is given, can it still change?"),
                    ("you", "可以上诉，但是要有新的理由。", "kěyǐ shàngsù, dànshì yào yǒu xīn de lǐyóu.", "You can appeal, but you need new grounds."),
                    ("them", "公司这边要注意什么？", "gōngsī zhè biān yào zhùyì shénme?", "What should the company watch out for?"),
                    ("you", "最重要的是合规，别等出事才查。", "zuì zhòngyào de shì hé guī, bié děng chū shì cái chá.", "Compliance above all - don't wait for an incident to start checking."),
                ],
                "patterns": [
                    {
                        "text": "别等{x}才后悔",
                        "reading": "bié děng {x} cái hòuhuǐ",
                        "en": "Don't wait for {x} to start regretting it",
                        "values": [("出事", "chū shì", "something going wrong"), ("被罚", "bèi fá", "being fined"), ("有人举报", "yǒu rén jǔbào", "someone reporting it")],
                    }
                ],
                "notes": ["维权 is a verb-object: 维 (defend) + 权 (rights). You 维权, you don't 保护权."],
            },
            {
                "id": 83,
                "title": "Energy",
                "goal": "Discuss targets, transition and what it costs.",
                "vocab": [
                    ("碳排放", "tàn páifàng", "carbon emissions"),
                    ("可再生能源", "kě zàishēng néngyuán", "renewable energy"),
                    ("减排", "jiǎn pái", "to cut emissions"),
                    ("达标", "dá biāo", "to meet the standard"),
                    ("转型", "zhuǎnxíng", "to transition"),
                    ("可持续", "kě chíxù", "sustainable"),
                ],
                "dialogue": [
                    ("them", "你们今年的减排目标完成了吗？", "nǐmen jīnnián de jiǎn pái mùbiāo wánchéng le ma?", "Did you hit this year's emissions target?"),
                    ("you", "碳排放已经达标，但是还没到行业先进水平。", "tàn páifàng yǐjīng dá biāo, dànshì hái méi dào hángyè xiānjìn shuǐpíng.", "Emissions meet the standard, but we're not at the industry's leading level yet."),
                    ("them", "下一步呢？", "xià yí bù ne?", "What's next?"),
                    ("you", "加大可再生能源的比例，逐步完成转型。", "jiādà kě zàishēng néngyuán de bǐlì, zhúbù wánchéng zhuǎnxíng.", "Raise the share of renewables and complete the transition step by step."),
                    ("them", "成本高吗？", "chéngběn gāo ma?", "Is it expensive?"),
                    ("you", "短期高。长期看是可持续的，而且越来越便宜。", "duǎnqī gāo. chángqī kàn shì kě chíxù de, érqiě yuè lái yuè piányi.", "In the short term yes. Long term it's sustainable, and getting cheaper."),
                ],
                "patterns": [
                    {
                        "text": "短期{x}，长期划算",
                        "reading": "duǎnqī {x}, chángqī huásuàn",
                        "en": "In the short term {x}; in the long term it pays off",
                        "values": [("成本高", "chéngběn gāo", "costs are high"), ("看不出来", "kàn bu chū lái", "you can't tell"), ("有压力", "yǒu yālì", "there is pressure")],
                    }
                ],
                "notes": ["达标 is a fixed verb-object: 达 (reach) + 标 (the standard). You cannot say 达标了标准."],
            },
            {
                "id": 84,
                "title": "Research",
                "goal": "Talk about a paper, its evidence and where it's going.",
                "vocab": [
                    ("论文", "lùnwén", "paper; thesis"),
                    ("期刊", "qíkān", "academic journal"),
                    ("引用", "yǐnyòng", "to cite"),
                    ("综述", "zōngshù", "literature review"),
                    ("实证", "shízhèng", "empirical"),
                    ("假设", "jiǎshè", "hypothesis"),
                ],
                "dialogue": [
                    ("them", "你的论文写到哪一步了？", "nǐ de lùnwén xiě dào nǎ yí bù le?", "How far along is your paper?"),
                    ("you", "综述写完了，正在做实证部分。", "zōngshù xiě wán le, zhèngzài zuò shízhèng bùfen.", "The review is done; I'm on the empirical part."),
                    ("them", "假设验证了吗？", "jiǎshè yànzhèng le ma?", "Has the hypothesis been tested?"),
                    ("you", "初步结果支持假设，但是样本还不够大。", "chūbù jiéguǒ zhīchí jiǎshè, dànshì yàngběn hái bú gòu dà.", "Preliminary results support it, but the sample isn't big enough yet."),
                    ("them", "准备投哪个期刊？", "zhǔnbèi tóu nǎ ge qíkān?", "Which journal will you submit to?"),
                    ("you", "先投国内的，引用的文献也以中文为主。", "xiān tóu guónèi de, yǐnyòng de wénxiàn yě yǐ Zhōngwén wéizhǔ.", "A domestic one first; the cited literature is mostly Chinese too."),
                ],
                "patterns": [
                    {
                        "text": "{x}还不够充分",
                        "reading": "{x} hái bú gòu chōngfèn",
                        "en": "{x} is not sufficient yet",
                        "values": [("样本", "yàngběn", "the sample"), ("数据", "shùjù", "the data"), ("证据", "zhèngjù", "the evidence")],
                    }
                ],
                "notes": ["投 (tóu) is the verb for submitting to a journal: 投稿, 投期刊."],
            },
            {
                "id": 85,
                "title": "Taking a position",
                "goal": "Hold a side in an argument: 立场, 前提, 共识.",
                "vocab": [
                    ("立场", "lìchǎng", "position; stance"),
                    ("前提", "qiántí", "precondition"),
                    ("证据", "zhèngjù", "evidence"),
                    ("反驳", "fǎnbó", "to rebut"),
                    ("共识", "gòngshí", "common ground; consensus"),
                    ("小结", "xiǎojué", "to sum up briefly"),
                ],
                "dialogue": [
                    ("them", "那我们到底该不该支持？", "nà wǒmen dàodǐ gāi bu gāi zhīchí?", "So should we support it or not?"),
                    ("you", "我的立场是支持，但有三个前提。", "wǒ de lìchǎng shì zhīchí, dàn yǒu sān ge qiántí.", "My position is yes, on three conditions."),
                    ("them", "说说看。", "shuōshuo kàn.", "Go on."),
                    ("you", "第一，证据要公开；第二，要有退出机制；第三，责任要清楚。", "dì-yī, zhèngjù yào gōngkāi; dì-èr, yào yǒu tuìchū jīzhì; dì-sān, zérèn yào qīngchu.", "One, the evidence is public. Two, there's a way out. Three, responsibility is clear."),
                    ("them", "如果这三条做不到呢？", "rúguǒ zhè sān tiáo zuò bu dào ne?", "And if those three can't be met?"),
                    ("you", "那我就不支持。在这之前，我们至少有一个共识：不能没有规则。", "nà wǒ jiù bù zhīchí. zài zhè zhīqián, wǒmen zhìshǎo yǒu yí ge gòngshí: bù néng méiyou guīzé.", "Then I'm against it. Before that, we at least have one thing in common: there have to be rules."),
                ],
                "patterns": [
                    {
                        "text": "我的立场是{x}，但有保留",
                        "reading": "wǒ de lìchǎng shì {x}, dàn yǒu bǎoliú",
                        "en": "My position is {x}, but with reservations",
                        "values": [("支持", "zhīchí", "support"), ("反对", "fǎnduì", "opposition"), ("暂时支持", "zànshí zhīchí", "qualified support")],
                    }
                ],
                "notes": ["You have finished the ladder: 你好 to 不能没有规则. The next step is not another level - it is using it."],
            },
        ],
    },
]

LEVEL = {
    "band": 7,
    "id": 7,
    "title": "HSK 7-9 · Native",
    "focus": "News, slang, accents, 成语 with their stories, and the working vocabulary of economics, law, technology and research.",
    "gate": {"min_pron_score": 82.0, "min_accuracy": 82.0, "min_completeness": 94.0, "min_tone_score": 78.0},
    "units": UNITS,
}

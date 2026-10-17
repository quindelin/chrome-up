# -*- coding: utf-8 -*-
"""HSK 6 — near-native: 成语, written register, abstract argument, and the
set phrases that make you sound educated rather than merely fluent."""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    {
        "id": 15,
        "title": "Idioms & Register",
        "focus": "成语, formal written Chinese, and high-level concession markers.",
        "lessons": [
            {
                "id": 62,
                "title": "Idioms I",
                "goal": "Use common 成语 to describe people and work.",
                "vocab": [
                    ("一丝不苟", "yì sī bù gǒu", "meticulous"),
                    ("举足轻重", "jǔ zú qīng zhòng", "pivotal"),
                    ("得不偿失", "dé bù cháng shī", "the gain doesn't repay the loss"),
                    ("事半功倍", "shì bàn gōng bèi", "half the effort, twice the result"),
                    ("小题大做", "xiǎo tí dà zuò", "make a mountain of a molehill"),
                    ("齐心协力", "qí xīn xié lì", "to work as one"),
                ],
                "dialogue": [
                    ("them", "你觉得张经理这个人怎么样？", "nǐ juéde Zhāng jīnglǐ zhè ge rén zěnmeyàng?", "What do you make of Manager Zhang?"),
                    ("you", "他做事一丝不苟，在团队里举足轻重。", "tā zuòshì yì sī bù gǒu, zài tuánduì lǐ jǔ zú qīng zhòng.", "He's meticulous and carries real weight in the team."),
                    ("them", "但是不是太严格了？", "dànshì bú shì tài yángé le?", "But isn't he too strict?"),
                    ("you", "严格不等于苛刻。方法对了，往往事半功倍。", "yángé bù děngyú kēkè. fāngfǎ duì le, wǎngwǎng shì bàn gōng bèi.", "Strict isn't harsh. With the right method you get twice the result for half the work."),
                    ("them", "上次那个小问题，他批评了半天。", "shàng cì nà ge xiǎo wèntí, tā pīpíng le bàntiān.", "Last time, over a small problem, he criticised us for ages."),
                    ("you", "那确实有点小题大做。只要大家齐心协力，问题就好解决。", "nà quèshí yǒudiǎn xiǎo tí dà zuò. zhǐyào dàjiā qí xīn xié lì, wèntí jiù hǎo jiějué.", "That was rather overblown. If everyone pulls together, problems get solved."),
                ],
                "patterns": [
                    {
                        "text": "这件事{x}",
                        "reading": "zhè jiàn shì {x}",
                        "en": "This matter is {x}",
                        "values": [("举足轻重", "jǔ zú qīng zhòng", "pivotal"), ("得不偿失", "dé bù cháng shī", "not worth the cost"), ("大有可为", "dà yǒu kě wéi", "full of promise")],
                    }
                ],
                "notes": ["事半功倍 (half effort, double result) vs 事倍功半 (double effort, half result)."],
            },
            {
                "id": 63,
                "title": "Idioms II",
                "goal": "Evaluate ideas and work with 成语.",
                "vocab": [
                    ("显而易见", "xiǎn'ér yì jiàn", "obvious"),
                    ("别出心裁", "bié chū xīn cái", "original, ingenious"),
                    ("差强人意", "chā qiáng rén yì", "barely satisfactory"),
                    ("半途而废", "bàn tú ér fèi", "to give up halfway"),
                    ("言简意赅", "yán jiǎn yì gāi", "concise and complete"),
                    ("各抒己见", "gè shū jǐ jiàn", "each states their view"),
                ],
                "dialogue": [
                    ("them", "这次的方案你看过了吗？", "zhè cì de fāng'àn nǐ kàn guò le ma?", "Have you looked at this proposal?"),
                    ("you", "看了。想法别出心裁，不过效果差强人意。", "kàn le. xiǎngfǎ bié chū xīn cái, bùguò xiàoguǒ chā qiáng rén yì.", "Yes. The idea is original, though the result is only passable."),
                    ("them", "问题出在哪儿？", "wèntí chū zài nǎr?", "Where's the problem?"),
                    ("you", "显而易见，执行不到位。", "xiǎn'ér yì jiàn, zhíxíng bú dào wèi.", "Obviously, execution fell short."),
                    ("them", "要不要换方向？", "yào bú yào huàn fāngxiàng?", "Should we change direction?"),
                    ("you", "别半途而废。大家各抒己见，再改一版。", "bié bàn tú ér fèi. dàjiā gè shū jǐ jiàn, zài gǎi yí bǎn.", "Don't give up halfway. Everyone air their view and we'll revise it."),
                ],
                "patterns": [
                    {
                        "text": "他的话{x}",
                        "reading": "tā de huà {x}",
                        "en": "His words are {x}",
                        "values": [("言简意赅", "yán jiǎn yì gāi", "concise and complete"), ("耐人寻味", "nài rén xún wèi", "thought-provoking"), ("意味深长", "yì wèi shēn cháng", "full of meaning")],
                    }
                ],
                "notes": ["差强人意 is often misused - it means 'barely acceptable', not 'very satisfying'."],
            },
            {
                "id": 64,
                "title": "Formal register",
                "goal": "Read and say written-style notices.",
                "vocab": [
                    ("鉴于", "jiànyú", "in view of"),
                    ("旨在", "zhǐ zài", "aimed at"),
                    ("予以", "yǔyǐ", "to grant / to give"),
                    ("相关人员", "xiāngguān rényuán", "relevant personnel"),
                    ("深表遗憾", "shēn biǎo yíhàn", "to deeply regret"),
                    ("特此通知", "tè cǐ tōngzhī", "hereby notify"),
                ],
                # Spoken, not written. 鉴于 / 旨在 / 予以 / 特此通知 are 书面语:
                # a notice says them, a person does not. This lesson used to
                # drill them as dialogue, which teaches you to answer
                # "会议为什么改期？" with "特此通知" and sound like a government
                # circular in a conversation. The written forms are learned
                # where they belong - in the reading passage - and here you
                # learn what you would actually say out loud for the same
                # situation, which is the harder half of register: knowing
                # that the two exist and are not interchangeable.
                "dialogue": [
                    ("them", "会议为什么改期了？", "huìyì wèishénme gǎiqī le?", "Why has the meeting been moved?"),
                    ("you", "现在情况有变化，改到下周一了。", "xiànzài qíngkuàng yǒu biànhuà, gǎi dào xià zhōuyī le.", "Things have changed, so it's next Monday now."),
                    ("them", "为什么要改呢？", "wèishénme yào gǎi ne?", "Why change it?"),
                    ("you", "主要是想提高效率，让大家准备得更充分。", "zhǔyào shì xiǎng tígāo xiàolǜ, ràng dàjiā zhǔnbèi de gèng chōngfèn.", "Mainly to be more efficient and let people prepare properly."),
                    ("them", "那之前安排好的事怎么办？", "nà zhīqián ānpái hǎo de shì zěnme bàn?", "What about what was already arranged?"),
                    ("you", "不好意思，只能麻烦大家调整一下了。", "bù hǎoyìsi, zhǐ néng máfan dàjiā tiáozhěng yíxià le.", "Sorry - everyone will just have to rearrange a bit."),
                ],
                "patterns": [
                    {
                        "text": "鉴于{x}",
                        "reading": "jiànyú {x}",
                        "en": "In view of {x}",
                        "values": [("目前的情况", "mùqián de qíngkuàng", "the present situation"), ("天气原因", "tiānqì yuányīn", "the weather"), ("大家的意见", "dàjiā de yìjiàn", "everyone's feedback")],
                    }
                ],
                "notes": [
                    "This vocabulary is 书面语 - written Chinese for notices and emails. Nobody says 特此通知 out loud; in conversation you would say 改到下周一了.",
                    "The written forms are in the reading passage for this lesson. Learn both: knowing which one the situation wants is the whole skill.",
                ],
            },
            {
                "id": 65,
                "title": "Conceding like a native",
                "goal": "Argue with 尽管如此 / 诚然 / 换言之 / 综上所述.",
                "vocab": [
                    ("尽管如此", "jǐn guǎn rú cǐ", "nevertheless"),
                    ("无可厚非", "wú kě hòu fēi", "perfectly understandable"),
                    ("诚然", "chéngrán", "admittedly"),
                    ("然而", "rán'ér", "however"),
                    ("换言之", "huàn yán zhī", "in other words"),
                    ("综上所述", "zōng shàng suǒ shù", "to sum up"),
                ],
                "dialogue": [
                    ("them", "年轻人换工作越来越频繁。", "niánqīngrén huàn gōngzuò yuè lái yuè pínfán.", "Young people change jobs more and more often."),
                    ("you", "诚然，这不无道理；然而，事实并非完全如此。", "chéngrán, zhè bù wú dàoli; rán'ér, shìshí bìngfēi wánquán rúcǐ.", "Admittedly that's not without reason; however, reality isn't quite so."),
                    ("them", "可是他们不够稳定。", "kěshì tāmen bú gòu wěndìng.", "But they lack stability."),
                    ("you", "尽管如此，这种选择也无可厚非。", "jǐn guǎn rú cǐ, zhè zhǒng xuǎnzé yě wú kě hòu fēi.", "Even so, that choice is perfectly understandable."),
                    ("them", "你的意思是？", "nǐ de yìsi shì?", "What do you mean?"),
                    ("you", "换言之，稳定不再是唯一标准。综上所述，这是时代的产物。", "huàn yán zhī, wěndìng bú zài shì wéiyī biāozhǔn. zōng shàng suǒ shù, zhè shì shídài de chǎnwù.", "In other words, stability is no longer the only criterion. To sum up, it's a product of the times."),
                ],
                "patterns": [
                    {
                        "text": "尽管如此，{x}",
                        "reading": "jǐn guǎn rú cǐ, {x}",
                        "en": "Even so, {x}",
                        "values": [("问题依然存在", "wèntí yīrán cúnzài", "the problem remains"), ("我们仍要努力", "wǒmen réng yào nǔlì", "we must keep trying"), ("我并不后悔", "wǒ bìng bù hòuhuǐ", "I don't regret it")],
                    }
                ],
                "notes": ["诚然 concedes a point before 然而/但是 turns it: a very Chinese move."],
            },
        ],
    },
    {
        "id": 16,
        "title": "Abstract Domains",
        "focus": "Literature, history and philosophy, technology, globalisation.",
        "lessons": [
            {
                "id": 66,
                "title": "Literature",
                "goal": "Talk about books with literary vocabulary.",
                "vocab": [
                    ("耐人寻味", "nài rén xún wèi", "thought-provoking"),
                    ("笔触", "bǐ chù", "style of writing"),
                    ("字里行间", "zì lǐ háng jiān", "between the lines"),
                    ("跌宕起伏", "diē dàng qǐ fú", "full of ups and downs"),
                    ("回味无穷", "huí wèi wú qióng", "leaving an endless aftertaste"),
                    ("不失为", "bù shī wéi", "can be considered"),
                ],
                "dialogue": [
                    ("them", "这本小说怎么样？", "zhè běn xiǎoshuō zěnmeyàng?", "How is this novel?"),
                    ("you", "很耐人寻味。作者笔触细腻，字里行间流露出淡淡的忧伤。", "hěn nài rén xún wèi. zuòzhě bǐchù xìnì, zì lǐ háng jiān liúlù chū dàndàn de yōushāng.", "Very thought-provoking. The writing is delicate, with a faint sadness between the lines."),
                    ("them", "情节呢？", "qíngjié ne?", "And the plot?"),
                    ("you", "跌宕起伏，读来令人回味无穷。", "diē dàng qǐ fú, dú lái lìng rén huí wèi wú qióng.", "Full of twists - it stays with you."),
                    ("them", "值得推荐吗？", "zhíde tuījiàn ma?", "Worth recommending?"),
                    ("you", "不失为一部佳作。", "bù shī wéi yí bù jiāzuò.", "It can fairly be called a fine work."),
                ],
                "patterns": [
                    {
                        "text": "这部作品{x}",
                        "reading": "zhè bù zuòpǐn {x}",
                        "en": "This work is {x}",
                        "values": [("耐人寻味", "nài rén xún wèi", "thought-provoking"), ("引人入胜", "yǐn rén rù shèng", "captivating"), ("发人深省", "fā rén shēn xǐng", "prompting deep reflection")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 67,
                "title": "History & philosophy",
                "goal": "Discuss patterns in history and Chinese thought.",
                "vocab": [
                    ("惊人的相似", "jīngrén de xiāngsì", "strikingly similar"),
                    ("盛极而衰", "shèng jí ér shuāi", "prosperity turns to decline"),
                    ("中庸之道", "zhōngyōng zhī dào", "the middle way"),
                    ("不以人的意志为转移", "bù yǐ rén de yìzhì wéi zhuǎnyí", "independent of human will"),
                    ("由此可见", "yóu cǐ kě jiàn", "thus it can be seen"),
                    ("顺势而为", "shùn shì ér wéi", "to act with the current"),
                ],
                "dialogue": [
                    ("them", "你为什么喜欢历史？", "nǐ wèishénme xǐhuan lìshǐ?", "Why do you like history?"),
                    ("you", "因为历史往往惊人的相似。", "yīnwèi lìshǐ wǎngwǎng jīngrén de xiāngsì.", "Because history is often strikingly similar."),
                    ("them", "能举个例子吗？", "néng jǔ ge lìzi ma?", "Can you give an example?"),
                    ("you", "盛极而衰几乎是常态。古人讲究中庸之道，这在某种意义上是一种智慧。", "shèng jí ér shuāi jīhū shì chángtài. gǔrén jiǎngjiu zhōngyōng zhī dào, zhè zài mǒu zhǒng yìyì shang shì yì zhǒng zhìhuì.", "Decline after peak is almost the norm. The ancients prized the middle way - a kind of wisdom, in a sense."),
                    ("them", "那我们能改变什么？", "nà wǒmen néng gǎibiàn shénme?", "So what can we change?"),
                    ("you", "事物的发展不以人的意志为转移。由此可见，顺势而为比逆流而上更明智。", "shìwù de fāzhǎn bù yǐ rén de yìzhì wéi zhuǎnyí. yóu cǐ kě jiàn, shùn shì ér wéi bǐ nì liú ér shàng gèng míngzhì.", "Development doesn't bend to human will. Thus, going with the current beats swimming against it."),
                ],
                "patterns": [
                    {
                        "text": "由此可见，{x}",
                        "reading": "yóu cǐ kě jiàn, {x}",
                        "en": "Thus it can be seen that {x}",
                        "values": [("顺势而为更重要", "shùn shì ér wéi gèng zhòngyào", "going with the flow matters more"), ("教育至关重要", "jiàoyù zhì guān zhòngyào", "education is crucial"), ("改革势在必行", "gǎigé shì zài bì xíng", "reform is imperative")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 68,
                "title": "Technology & the future",
                "goal": "Discuss AI and its consequences.",
                "vocab": [
                    ("突飞猛进", "tū fēi měng jìn", "advance by leaps and bounds"),
                    ("格局", "géjú", "landscape / structure"),
                    ("利弊兼而有之", "lì bì jiān ér yǒu zhī", "both pros and cons"),
                    ("不可限量", "bù kě xiànliàng", "boundless"),
                    ("引发", "yǐnfā", "to give rise to"),
                    ("机遇与挑战并存", "jīyù yǔ tiǎozhàn bìngcún", "opportunity and challenge coexist"),
                ],
                "dialogue": [
                    ("them", "人工智能发展得太快了。", "réngōng zhìnéng fāzhǎn de tài kuài le.", "AI is developing so fast."),
                    ("you", "确实突飞猛进。这在某种程度上改变了整个格局。", "quèshí tū fēi měng jìn. zhè zài mǒu zhǒng chéngdù shang gǎibiàn le zhěnggè géjú.", "It truly is leaping forward. It has reshaped the whole landscape to some extent."),
                    ("them", "是好事吗？", "shì hǎoshì ma?", "Is that good?"),
                    ("you", "利弊兼而有之。前景不可限量，同时也引发了担忧。", "lì bì jiān ér yǒu zhī. qiánjǐng bù kě xiànliàng, tóngshí yě yǐnfā le dānyōu.", "Both. The prospects are boundless, and it has also raised concerns."),
                    ("them", "那你怎么看未来？", "nà nǐ zěnme kàn wèilái?", "How do you see the future?"),
                    ("you", "换言之，机遇与挑战并存。", "huàn yán zhī, jīyù yǔ tiǎozhàn bìngcún.", "In other words, opportunity and challenge go hand in hand."),
                ],
                "patterns": [
                    {
                        "text": "这项技术{x}",
                        "reading": "zhè xiàng jìshù {x}",
                        "en": "This technology is {x}",
                        "values": [("突飞猛进", "tū fēi měng jìn", "advancing by leaps"), ("利弊兼而有之", "lì bì jiān ér yǒu zhī", "a mix of good and harm"), ("前景不可限量", "qiánjǐng bù kě xiànliàng", "of boundless promise")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 69,
                "title": "Globalisation",
                "goal": "Discuss globalisation and cultural difference.",
                "vocab": [
                    ("大势所趋", "dà shì suǒ qū", "the general trend"),
                    ("休戚与共", "xiū qī yǔ gòng", "to share weal and woe"),
                    ("求同存异", "qiú tóng cún yì", "seek common ground, keep differences"),
                    ("在一定程度上", "zài yídìng chéngdù shang", "to a certain extent"),
                    ("促进", "cùjìn", "to promote"),
                    ("差异", "chāyì", "difference"),
                ],
                "dialogue": [
                    ("them", "你怎么看全球化？", "nǐ zěnme kàn quánqiúhuà?", "What's your view on globalisation?"),
                    ("you", "全球化是大势所趋，各国休戚与共。", "quánqiúhuà shì dà shì suǒ qū, gè guó xiū qī yǔ gòng.", "It's the general trend; nations share weal and woe."),
                    ("them", "但文化差异显而易见。", "dàn wénhuà chāyì xiǎn'ér yì jiàn.", "But cultural differences are obvious."),
                    ("you", "对，所以求同存异才是上策。", "duì, suǒyǐ qiú tóng cún yì cái shì shàngcè.", "Yes - seeking common ground while keeping differences is the better policy."),
                    ("them", "这能促进交流吗？", "zhè néng cùjìn jiāoliú ma?", "Does that promote exchange?"),
                    ("you", "在一定程度上促进了交流。综上所述，开放比封闭更有利。", "zài yídìng chéngdù shang cùjìn le jiāoliú. zōng shàng suǒ shù, kāifàng bǐ fēngbì gèng yǒulì.", "It promotes exchange to a degree. To sum up, openness beats closure."),
                ],
                "patterns": [
                    {
                        "text": "在一定程度上{x}",
                        "reading": "zài yídìng chéngdù shang {x}",
                        "en": "To a certain extent it {x}",
                        "values": [("促进了交流", "cùjìn le jiāoliú", "promoted exchange"), ("缓解了矛盾", "huǎnjiě le máodùn", "eased tensions"), ("影响了决策", "yǐngxiǎng le juécè", "influenced decisions")],
                    }
                ],
                "notes": [],
            },
        ],
    },
    {
        "id": 17,
        "title": "Mastery",
        "focus": "Media, law and ethics, identity in the city, and a final deep conversation.",
        "lessons": [
            {
                "id": 70,
                "title": "Media & information",
                "goal": "Talk about information overload and responsibility.",
                "vocab": [
                    ("铺天盖地", "pū tiān gài dì", "overwhelming (information)"),
                    ("真假难辨", "zhēn jiǎ nán biàn", "hard to tell true from false"),
                    ("恪守", "kèshǒu", "to strictly observe"),
                    ("舆论导向", "yúlùn dǎoxiàng", "direction of public opinion"),
                    ("切忌", "qièjì", "must absolutely avoid"),
                    ("人云亦云", "rén yún yì yún", "to parrot what others say"),
                ],
                "dialogue": [
                    ("them", "现在的信息太多了。", "xiànzài de xìnxī tài duō le.", "There's too much information now."),
                    ("you", "是啊，铺天盖地，真假难辨。", "shì a, pū tiān gài dì, zhēn jiǎ nán biàn.", "Yes - overwhelming, and hard to tell what's true."),
                    ("them", "媒体应该做什么？", "méitǐ yīnggāi zuò shénme?", "What should the media do?"),
                    ("you", "应当恪守底线，舆论导向至关重要。", "yīngdāng kèshǒu dǐxiàn, yúlùn dǎoxiàng zhì guān zhòngyào.", "Hold the line; the direction of public opinion is crucial."),
                    ("them", "我们呢？", "wǒmen ne?", "And us?"),
                    ("you", "保持理性，切忌人云亦云。", "bǎochí lǐxìng, qièjì rén yún yì yún.", "Stay rational, and never just echo others."),
                ],
                "patterns": [
                    {
                        "text": "切忌{x}",
                        "reading": "qièjì {x}",
                        "en": "Absolutely avoid {x}",
                        "values": [("人云亦云", "rén yún yì yún", "parroting others"), ("盲目跟风", "mángmù gēn fēng", "blindly following trends"), ("断章取义", "duàn zhāng qǔ yì", "quoting out of context")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 71,
                "title": "Law & ethics",
                "goal": "Discuss fairness, feeling and law.",
                "vocab": [
                    ("人人平等", "rén rén píngděng", "everyone is equal"),
                    ("底线", "dǐxiàn", "bottom line"),
                    ("情理", "qínglǐ", "human reason / sentiment"),
                    ("法理", "fǎlǐ", "legal principle"),
                    ("以暴制暴", "yǐ bào zhì bào", "meeting violence with violence"),
                    ("不言而喻", "bù yán ér yù", "self-evident"),
                ],
                "dialogue": [
                    ("them", "你觉得法律面前人人平等吗？", "nǐ juéde fǎlǜ miànqián rén rén píngděng ma?", "Do you think all are equal before the law?"),
                    ("you", "这是原则。这起案件涉及道德底线。", "zhè shì yuánzé. zhè qǐ ànjiàn shèjí dàodé dǐxiàn.", "It's a principle. This case touches the moral bottom line."),
                    ("them", "可是情理和法理常常冲突。", "kěshì qínglǐ hé fǎlǐ chángcháng chōngtū.", "But sentiment and legal principle often clash."),
                    ("you", "确实，情理与法理并存。无论如何，不能以暴制暴。", "quèshí, qínglǐ yǔ fǎlǐ bìngcún. wúlùn rúhé, bù néng yǐ bào zhì bào.", "True, both exist. Whatever happens, violence must not answer violence."),
                    ("them", "那该怎么办？", "nà gāi zěnme bàn?", "So what should be done?"),
                    ("you", "应当依法行事。这是不言而喻的。", "yīngdāng yīfǎ xíngshì. zhè shì bù yán ér yù de.", "Act according to law. That goes without saying."),
                ],
                "patterns": [
                    {
                        "text": "无论如何，不能{x}",
                        "reading": "wúlùn rúhé, bù néng {x}",
                        "en": "Whatever happens, you must not {x}",
                        "values": [("以暴制暴", "yǐ bào zhì bào", "meet violence with violence"), ("轻言放弃", "qīng yán fàngqì", "give up lightly"), ("违背底线", "wéibèi dǐxiàn", "cross the bottom line")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 72,
                "title": "City & identity",
                "goal": "Talk about belonging and identity in modern cities.",
                "vocab": [
                    ("喘不过气", "chuǎn bu guò qì", "unable to catch one's breath"),
                    ("归属感", "guīshǔ gǎn", "sense of belonging"),
                    ("油然而生", "yóu rán ér shēng", "to arise spontaneously"),
                    ("荡然无存", "dàng rán wú cún", "to vanish completely"),
                    ("喧嚣", "xuānxiāo", "hustle and bustle"),
                    ("重构", "chónggòu", "to reconstruct"),
                ],
                "dialogue": [
                    ("them", "大城市的节奏怎么样？", "dà chéngshì de jiézòu zěnmeyàng?", "What's the pace of big cities like?"),
                    ("you", "快得让人喘不过气。", "kuài de ràng rén chuǎn bu guò qì.", "Fast enough to take your breath away."),
                    ("them", "有归属感吗？", "yǒu guīshǔ gǎn ma?", "Is there a sense of belonging?"),
                    ("you", "有时油然而生，有时又荡然无存。", "yǒushí yóu rán ér shēng, yǒushí yòu dàng rán wú cún.", "Sometimes it wells up, sometimes it vanishes entirely."),
                    ("them", "为什么？", "wèishénme?", "Why?"),
                    ("you", "人们在喧嚣中寻找宁静，故乡的概念愈发模糊。", "rénmen zài xuānxiāo zhōng xúnzhǎo níngjìng, gùxiāng de gàiniàn yùfā móhu.", "People seek quiet amid the noise, and the idea of home grows vaguer."),
                    ("them", "这说明了什么？", "zhè shuōmíng le shénme?", "What does that show?"),
                    ("you", "换言之，身份在重构。这值得深思。", "huàn yán zhī, shēnfèn zài chónggòu. zhè zhíde shēnsī.", "In other words, identity is being rebuilt. That's worth thinking about."),
                ],
                "patterns": [
                    {
                        "text": "这值得{x}",
                        "reading": "zhè zhíde {x}",
                        "en": "This deserves {x}",
                        "values": [("深思", "shēnsī", "deep thought"), ("反思", "fǎnsī", "reflection"), ("关注", "guānzhù", "attention")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 73,
                "title": "Review: why Chinese is hard",
                "goal": "A final deep conversation mixing idioms, concession and advice.",
                "vocab": [
                    ("归根结底", "guī gēn jié dǐ", "in the final analysis"),
                    ("一蹴而就", "yī cù ér jiù", "to succeed overnight"),
                    ("循序渐进", "xún xù jiàn jìn", "step by step"),
                    ("相辅相成", "xiāng fǔ xiāng chéng", "to complement each other"),
                    ("任重道远", "rèn zhòng dào yuǎn", "a heavy task and a long road"),
                    ("半途而废", "bàn tú ér fèi", "to give up halfway"),
                ],
                "dialogue": [
                    ("them", "学中文到底难在哪儿？", "xué Zhōngwén dàodǐ nán zài nǎr?", "What exactly is hard about learning Chinese?"),
                    ("you", "归根结底，难在声调和文化。", "guī gēn jié dǐ, nán zài shēngdiào hé wénhuà.", "In the final analysis: tones and culture."),
                    ("them", "有没有捷径？", "yǒu méiyǒu jiéjìng?", "Is there a shortcut?"),
                    ("you", "没有。语言学习不可能一蹴而就，只能循序渐进。", "méiyǒu. yǔyán xuéxí bù kěnéng yī cù ér jiù, zhǐ néng xún xù jiàn jìn.", "No. Language learning can't happen overnight - only step by step."),
                    ("them", "那听说和读写呢？", "nà tīngshuō hé dúxiě ne?", "What about listening/speaking versus reading/writing?"),
                    ("you", "二者相辅相成。", "èr zhě xiāng fǔ xiāng chéng.", "The two complement each other."),
                    ("them", "你说得很有道理。", "nǐ shuō de hěn yǒu dàoli.", "That's very reasonable."),
                    ("you", "诚然。学习这件事任重道远。", "chéngrán. xuéxí zhè jiàn shì rèn zhòng dào yuǎn.", "Indeed. Learning is a long road with a heavy load."),
                    ("them", "你会坚持下去吗？", "nǐ huì jiānchí xiàqù ma?", "Will you keep going?"),
                    ("you", "当然。既然选择了，就别半途而废。", "dāngrán. jìrán xuǎnzé le, jiù bié bàn tú ér fèi.", "Of course. Having chosen, don't stop halfway."),
                ],
                "patterns": [
                    {
                        "text": "学习这件事{x}",
                        "reading": "xuéxí zhè jiàn shì {x}",
                        "en": "Learning is {x}",
                        "values": [("任重道远", "rèn zhòng dào yuǎn", "a long, heavy road"), ("循序渐进", "xún xù jiàn jìn", "a step-by-step matter"), ("不可一蹴而就", "bù kě yī cù ér jiù", "not an overnight success")],
                    }
                ],
                "notes": ["你 finished every level - from 你好 to 任重道远. 恭喜。"],
            },
        ],
    },
]

LEVEL = {
    "band": 6,
    "id": 6,
    "title": "HSK 6 · Mastery",
    "focus": "成语, formal register, literary and abstract argument, near-native fluency.",
    "gate": {"min_pron_score": 80.0, "min_accuracy": 80.0, "min_completeness": 92.0, "min_tone_score": 75.0},
    "units": UNITS,
}

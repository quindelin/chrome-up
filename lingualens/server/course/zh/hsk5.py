# -*- coding: utf-8 -*-
"""HSK 5 — opinions, abstract topics and formal connectives:
与其…不如, 宁可, 难免, 未必, 换句话说, 在我看来, 见仁见智."""
from typing import Any, Dict, List

UNITS: List[Dict[str, Any]] = [
    {
        "id": 12,
        "title": "Work & Society",
        "focus": "Talk about work pressure, education, the environment and technology.",
        "lessons": [
            {
                "id": 50,
                "title": "Work pressure",
                "goal": "Discuss overtime and career choices with 与其…不如 / 宁可.",
                "vocab": [
                    ("加班", "jiā bān", "to work overtime"),
                    ("受不了", "shòu bu liǎo", "cannot stand"),
                    ("效率", "xiàolǜ", "efficiency"),
                    ("与其…不如", "yǔqí…bùrú", "rather than … better to"),
                    ("宁可", "nìngkě", "would rather"),
                    ("换工作", "huàn gōngzuò", "to change jobs"),
                    ("没办法", "méi bànfǎ", "there's no way; can't be helped"),
                    ("提高", "tígāo", "to raise, improve"),
                    ("暂时", "zànshí", "for the time being"),
                    ("考虑", "kǎolǜ", "to consider"),
                    ("赚", "zhuàn", "to earn"),
                ],
                "dialogue": [
                    ("them", "你最近怎么总是加班？", "nǐ zuìjìn zěnme zǒngshì jiā bān?", "Why are you working overtime all the time lately?"),
                    ("you", "项目太多了，没办法。", "xiàngmù tài duō le, méi bànfǎ.", "Too many projects, nothing I can do."),
                    ("them", "这样下去身体会受不了的。", "zhèyàng xiàqù shēntǐ huì shòu bu liǎo de.", "Your body won't cope if you keep this up."),
                    ("you", "我也知道。与其加班，不如提高效率。", "wǒ yě zhīdào. yǔqí jiā bān, bùrú tígāo xiàolǜ.", "I know. Better to raise efficiency than to work overtime."),
                    ("them", "你打算换工作吗？", "nǐ dǎsuàn huàn gōngzuò ma?", "Are you planning to change jobs?"),
                    ("you", "暂时不考虑。我宁可少赚一点，也不想天天加班。", "zànshí bù kǎolǜ. wǒ nìngkě shǎo zhuàn yìdiǎn, yě bù xiǎng tiāntiān jiā bān.", "Not for now. I'd rather earn less than work overtime every day."),
                ],
                "patterns": [
                    {
                        "text": "与其{x}，不如提高效率",
                        "reading": "yǔqí {x}, bùrú tígāo xiàolǜ",
                        "en": "Rather than {x}, better to raise efficiency",
                        "values": [("加班", "jiā bān", "working overtime"), ("抱怨", "bàoyuàn", "complaining"), ("着急", "zháojí", "getting anxious")],
                    }
                ],
                "notes": ["宁可 A，也不 B = would rather A than B. Both clauses are unwanted; you pick A."],
            },
            {
                "id": 51,
                "title": "Education",
                "goal": "Discuss how people learn, with 难免 and 减轻.",
                "vocab": [
                    ("死记硬背", "sǐ jì yìng bèi", "rote learning"),
                    ("理解", "lǐjiě", "to understand"),
                    ("减轻", "jiǎnqīng", "to lighten"),
                    ("负担", "fùdān", "burden"),
                    ("难免", "nánmiǎn", "hard to avoid"),
                    ("从某种意义上说", "cóng mǒu zhǒng yìyì shang shuō", "in a sense"),
                    ("重视", "zhòngshì", "to value, take seriously"),
                    ("压力", "yālì", "pressure"),
                    ("希望", "xīwàng", "to hope"),
                    ("学校", "xuéxiào", "school"),
                    ("应该", "yīnggāi", "should"),
                ],
                "dialogue": [
                    ("them", "你觉得这里的教育怎么样？", "nǐ juéde zhèlǐ de jiàoyù zěnmeyàng?", "What do you think of education here?"),
                    ("you", "很受重视，但是压力也很大。", "hěn shòu zhòngshì, dànshì yālì yě hěn dà.", "It's highly valued, but the pressure is big too."),
                    ("them", "孩子们怎么学？", "háizimen zěnme xué?", "How do the children study?"),
                    ("you", "有的死记硬背，我更希望他们理解。", "yǒude sǐ jì yìng bèi, wǒ gèng xīwàng tāmen lǐjiě.", "Some learn by rote; I'd rather they understood."),
                    ("them", "家长不着急吗？", "jiāzhǎng bù zháojí ma?", "Aren't parents anxious?"),
                    ("you", "难免着急。学校应该减轻负担。", "nánmiǎn zháojí. xuéxiào yīnggāi jiǎnqīng fùdān.", "Understandably so. Schools should lighten the load."),
                ],
                "patterns": [
                    {
                        "text": "与其死记硬背，不如{x}",
                        "reading": "yǔqí sǐ jì yìng bèi, bùrú {x}",
                        "en": "Rather than rote learning, better to {x}",
                        "values": [("多理解", "duō lǐjiě", "understand more"), ("多思考", "duō sīkǎo", "think more"), ("多练习", "duō liànxí", "practise more")],
                    }
                ],
                "notes": ["难免 + verb/adj = 'it's hard to avoid' (难免着急 / 难免出错)."],
            },
            {
                "id": 52,
                "title": "The environment",
                "goal": "Discuss problems and measures with 大有影响 / 重视.",
                "vocab": [
                    ("污染", "wūrǎn", "pollution"),
                    ("采取措施", "cǎiqǔ cuòshī", "to take measures"),
                    ("垃圾分类", "lājī fēnlèi", "waste sorting"),
                    ("大有影响", "dà yǒu yǐngxiǎng", "to have a big impact"),
                    ("重视", "zhòngshì", "to attach importance to"),
                    ("随着", "suízhe", "along with"),
                    ("尤其", "yóuqí", "especially"),
                    ("政府", "zhèngfǔ", "government"),
                    ("公交", "gōngjiāo", "public bus"),
                ],
                "dialogue": [
                    ("them", "你觉得环境污染严重吗？", "nǐ juéde huánjìng wūrǎn yánzhòng ma?", "Do you think pollution is serious?"),
                    ("you", "越来越严重，尤其在城市。", "yuè lái yuè yánzhòng, yóuqí zài chéngshì.", "More and more serious, especially in cities."),
                    ("them", "应该怎么办？", "yīnggāi zěnme bàn?", "What should be done?"),
                    ("you", "政府应该采取措施，比如垃圾分类。", "zhèngfǔ yīnggāi cǎiqǔ cuòshī, bǐrú lājī fēnlèi.", "The government should take measures, for instance waste sorting."),
                    ("them", "普通人能做什么？", "pǔtōng rén néng zuò shénme?", "What can ordinary people do?"),
                    ("you", "少开车，多坐公交。这对健康也大有影响。", "shǎo kāi chē, duō zuò gōngjiāo. zhè duì jiànkāng yě dà yǒu yǐngxiǎng.", "Drive less, take the bus more. It also has a big impact on health."),
                ],
                "patterns": [
                    {
                        "text": "这对{x}大有影响",
                        "reading": "zhè duì {x} dà yǒu yǐngxiǎng",
                        "en": "This has a big impact on {x}",
                        "values": [("健康", "jiànkāng", "health"), ("环境", "huánjìng", "the environment"), ("孩子", "háizi", "children")],
                    }
                ],
                "notes": ["随着 + phrase = 'as … develops': 随着生活水平的提高."],
            },
            {
                "id": 53,
                "title": "Technology",
                "goal": "Weigh convenience against cost with 换句话说.",
                "vocab": [
                    ("必不可少", "bì bù kě shǎo", "indispensable"),
                    ("离不开", "lí bu kāi", "unable to do without"),
                    ("隐私", "yǐnsī", "privacy"),
                    ("焦虑", "jiāolǜ", "anxious"),
                    ("换句话说", "huàn jù huà shuō", "in other words"),
                    ("代价", "dàijià", "price / cost"),
                    ("当然", "dāngrán", "of course"),
                    ("智能手机", "zhìnéng shǒujī", "smartphone"),
                    ("让", "ràng", "to make, to let"),
                ],
                "dialogue": [
                    ("them", "你觉得网络改变了生活吗？", "nǐ juéde wǎngluò gǎibiàn le shēnghuó ma?", "Do you think the internet has changed life?"),
                    ("you", "当然。智能手机已经必不可少。", "dāngrán. zhìnéng shǒujī yǐjīng bì bù kě shǎo.", "Of course. Smartphones are already indispensable."),
                    ("them", "可是人们离不开手机了。", "kěshì rénmen lí bu kāi shǒujī le.", "But people can't put their phones down."),
                    ("you", "一方面方便，一方面也让人焦虑。", "yì fāngmiàn fāngbiàn, yì fāngmiàn yě ràng rén jiāolǜ.", "On one hand convenient, on the other it makes people anxious."),
                    ("them", "你担心隐私吗？", "nǐ dānxīn yǐnsī ma?", "Do you worry about privacy?"),
                    ("you", "难免担心。换句话说，便利是有代价的。", "nánmiǎn dānxīn. huàn jù huà shuō, biànlì shì yǒu dàijià de.", "It's hard not to. In other words, convenience has a price."),
                ],
                "patterns": [
                    {
                        "text": "随着{x}的发展",
                        "reading": "suízhe {x} de fāzhǎn",
                        "en": "With the development of {x}",
                        "values": [("科技", "kējì", "technology"), ("网络", "wǎngluò", "the internet"), ("社会", "shèhuì", "society")],
                    }
                ],
                "notes": ["换句话说 = 'in other words' - the classic HSK 5 reformulation marker."],
            },
        ],
    },
    {
        "id": 13,
        "title": "Culture & Debate",
        "focus": "Festivals, food culture, film, and agreeing/disagreeing politely.",
        "lessons": [
            {
                "id": 54,
                "title": "Festivals",
                "goal": "Compare traditions with 无论 / 相比之下 / 在我看来.",
                "vocab": [
                    ("无论", "wúlùn", "no matter"),
                    ("体现", "tǐxiàn", "to embody"),
                    ("相比之下", "xiāng bǐ zhī xià", "by comparison"),
                    ("并存", "bìngcún", "to coexist"),
                    ("在我看来", "zài wǒ kàn lái", "in my view"),
                    ("观念", "guānniàn", "concept / values"),
                    ("春节", "Chūnjié", "Spring Festival"),
                    ("它", "tā", "it"),
                    ("传统", "chuántǒng", "tradition; traditional"),
                ],
                "dialogue": [
                    ("them", "中国最重要的节日是什么？", "Zhōngguó zuì zhòngyào de jiérì shì shénme?", "What is the most important Chinese festival?"),
                    ("you", "春节。无论多远，人们都要回家。", "Chūnjié. wúlùn duō yuǎn, rénmen dōu yào huí jiā.", "Spring Festival. No matter how far, people go home."),
                    ("them", "为什么这么重要？", "wèishénme zhème zhòngyào?", "Why is it so important?"),
                    ("you", "它体现了家庭观念。", "tā tǐxiàn le jiātíng guānniàn.", "It embodies the idea of family."),
                    ("them", "和西方一样吗？", "hé xīfāng yíyàng ma?", "Is it the same in the West?"),
                    ("you", "相比之下，西方更重视个人。传统和现代并存，在我看来很有意义。", "xiāng bǐ zhī xià, xīfāng gèng zhòngshì gèrén. chuántǒng hé xiàndài bìngcún, zài wǒ kàn lái hěn yǒu yìyì.", "By comparison, the West values the individual more. Tradition and modernity coexist - meaningful, in my view."),
                ],
                "patterns": [
                    {
                        "text": "无论{x}，我都要去",
                        "reading": "wúlùn {x}, wǒ dōu yào qù",
                        "en": "No matter {x}, I'm going",
                        "values": [("多远", "duō yuǎn", "how far"), ("多忙", "duō máng", "how busy"), ("多贵", "duō guì", "how expensive")],
                    }
                ],
                "notes": ["无论 + question word + 都/也. Never 无论…但是."],
            },
            {
                "id": 55,
                "title": "Food culture",
                "goal": "Describe regional differences with 以…闻名 / 与其说…不如说.",
                "vocab": [
                    ("讲究", "jiǎngjiu", "to pay attention to"),
                    ("色香味俱全", "sè xiāng wèi jù quán", "colour, aroma and taste all present"),
                    ("以…闻名", "yǐ…wénmíng", "famous for"),
                    ("清淡", "qīngdàn", "light (food)"),
                    ("大开眼界", "dà kāi yǎnjiè", "eye-opening"),
                    ("与其说…不如说", "yǔqí shuō…bùrú shuō", "not so much … as …"),
                    ("差别", "chābié", "difference"),
                    ("四川", "Sìchuān", "Sichuan"),
                    ("广东", "Guǎngdōng", "Guangdong"),
                    ("比较", "bǐjiào", "fairly, relatively"),
                    ("文化", "wénhuà", "culture"),
                ],
                "dialogue": [
                    ("them", "中国菜有什么特点？", "Zhōngguó cài yǒu shénme tèdiǎn?", "What characterises Chinese food?"),
                    ("you", "讲究色香味俱全。", "jiǎngjiu sè xiāng wèi jù quán.", "It values colour, aroma and taste together."),
                    ("them", "各地一样吗？", "gè dì yíyàng ma?", "Is it the same everywhere?"),
                    ("you", "差别很大。四川菜以辣闻名，相比之下广东菜比较清淡。", "chābié hěn dà. Sìchuān cài yǐ là wénmíng, xiāng bǐ zhī xià Guǎngdōng cài bǐjiào qīngdàn.", "Very different. Sichuan food is famous for heat; by contrast Cantonese food is lighter."),
                    ("them", "你来中国后最喜欢什么？", "nǐ lái Zhōngguó hòu zuì xǐhuan shénme?", "What have you liked most since coming to China?"),
                    ("you", "与其说喜欢某道菜，不如说喜欢这种文化。这让我大开眼界。", "yǔqí shuō xǐhuan mǒu dào cài, bùrú shuō xǐhuan zhè zhǒng wénhuà. zhè ràng wǒ dà kāi yǎnjiè.", "Not so much a particular dish as the culture itself. It's been eye-opening."),
                ],
                "patterns": [
                    {
                        "text": "四川菜以{x}闻名",
                        "reading": "Sìchuān cài yǐ {x} wénmíng",
                        "en": "Sichuan food is famous for being {x}",
                        "kind": "food",
                        "values": [("辣", "là", "spicy"), ("麻", "má", "numbing"), ("香", "xiāng", "aromatic")],
                    }
                ],
                "notes": ["与其说 A，不如说 B = 'not so much A as B'."],
            },
            {
                "id": 56,
                "title": "Film & art",
                "goal": "Review a film with 未必 / 反映 / 总的来说.",
                "vocab": [
                    ("值得一看", "zhíde yí kàn", "worth watching"),
                    ("剧情", "jùqíng", "plot"),
                    ("未必", "wèibì", "not necessarily"),
                    ("反映", "fǎnyìng", "to reflect"),
                    ("反响", "fǎnxiǎng", "reception"),
                    ("总的来说", "zǒng de lái shuō", "on the whole"),
                    ("真实", "zhēnshí", "true to life, real"),
                    ("讨论", "tǎolùn", "discussion; to discuss"),
                    ("仓促", "cāngcù", "hasty, rushed"),
                    ("不错", "búcuò", "not bad, pretty good"),
                ],
                "dialogue": [
                    ("them", "这部电影值得一看吗？", "zhè bù diànyǐng zhíde yí kàn ma?", "Is this film worth watching?"),
                    ("you", "值得。剧情未必真实，但反映了社会现实。", "zhíde. jùqíng wèibì zhēnshí, dàn fǎnyìng le shèhuì xiànshí.", "Yes. The plot isn't necessarily true, but it reflects social reality."),
                    ("them", "观众的反响怎么样？", "guānzhòng de fǎnxiǎng zěnmeyàng?", "How was it received?"),
                    ("you", "很好，讨论很多。", "hěn hǎo, tǎolùn hěn duō.", "Very well - a lot of discussion."),
                    ("them", "你觉得结局呢？", "nǐ juéde jiéjú ne?", "What about the ending?"),
                    ("you", "在我看来有点仓促。总的来说，还是不错的。", "zài wǒ kàn lái yǒudiǎn cāngcù. zǒng de lái shuō, háishì búcuò de.", "In my view it's a bit rushed. On the whole, still good."),
                ],
                "patterns": [
                    {
                        "text": "在我看来有点{x}",
                        "reading": "zài wǒ kàn lái yǒudiǎn {x}",
                        "en": "In my view it's a bit {x}",
                        "values": [("仓促", "cāngcù", "rushed"), ("复杂", "fùzá", "complicated"), ("夸张", "kuāzhāng", "exaggerated")],
                    }
                ],
                "notes": ["未必 = not necessarily. It softens a disagreement."],
            },
            {
                "id": 57,
                "title": "Agreeing to disagree",
                "goal": "Disagree politely with 一概而论 / 见仁见智.",
                "vocab": [
                    ("一概而论", "yígài'érlùn", "to generalise"),
                    ("见仁见智", "jiàn rén jiàn zhì", "a matter of opinion"),
                    ("有道理", "yǒu dàoli", "to have a point"),
                    ("上瘾", "shàngyǐn", "to be addictive"),
                    ("例外", "lìwài", "exception"),
                    ("某种程度上", "mǒu zhǒng chéngdù shang", "to some extent"),
                ],
                "dialogue": [
                    ("them", "我觉得年轻人不该花太多时间上网。", "wǒ juéde niánqīngrén bù gāi huā tài duō shíjiān shàngwǎng.", "I think young people shouldn't spend so much time online."),
                    ("you", "我不同意。从某种程度上说，上网也是学习。", "wǒ bù tóngyì. cóng mǒu zhǒng chéngdù shang shuō, shàngwǎng yě shì xuéxí.", "I disagree. To some extent, being online is also learning."),
                    ("them", "但是容易上瘾。", "dànshì róngyì shàngyǐn.", "But it's easy to get addicted."),
                    ("you", "你说得有道理，不过难免有例外。", "nǐ shuō de yǒu dàoli, bùguò nánmiǎn yǒu lìwài.", "You have a point, though there are bound to be exceptions."),
                    ("them", "那你的意思是？", "nà nǐ de yìsi shì?", "So what do you mean?"),
                    ("you", "我们不能一概而论。这个问题见仁见智。", "wǒmen bù néng yígài'érlùn. zhè ge wèntí jiàn rén jiàn zhì.", "We can't generalise. It's a matter of opinion."),
                ],
                "patterns": [
                    {
                        "text": "从{x}上说",
                        "reading": "cóng {x} shang shuō",
                        "en": "Speaking in terms of {x}",
                        "values": [("某种程度", "mǒu zhǒng chéngdù", "some extent"), ("某种意义", "mǒu zhǒng yìyì", "some sense"), ("这个角度", "zhè ge jiǎodù", "this angle")],
                    }
                ],
                "notes": ["见仁见智 comes from 易经: 'the benevolent see benevolence, the wise see wisdom'."],
            },
        ],
    },
    {
        "id": 14,
        "title": "Advanced Expression",
        "focus": "Economy, health, travel, and a full discussion of city life.",
        "lessons": [
            {
                "id": 58,
                "title": "Spending habits",
                "goal": "Talk about consumption with 从长远来看 / 未必.",
                "vocab": [
                    ("消费观念", "xiāofèi guānniàn", "attitude to consumption"),
                    ("注重", "zhùzhòng", "to emphasise"),
                    ("品质", "pǐnzhì", "quality"),
                    ("从长远来看", "cóng chángyuǎn lái kàn", "in the long run"),
                    ("需求", "xūqiú", "demand"),
                    ("升级", "shēngjí", "to upgrade"),
                    ("决定", "juédìng", "to decide"),
                    ("一切", "yíqiè", "everything"),
                ],
                "dialogue": [
                    ("them", "人们的消费观念变了吗？", "rénmen de xiāofèi guānniàn biàn le ma?", "Have people's spending attitudes changed?"),
                    ("you", "变了。人们越来越注重品质。", "biàn le. rénmen yuè lái yuè zhùzhòng pǐnzhì.", "Yes. People care more and more about quality."),
                    ("them", "价格还重要吗？", "jiàgé hái zhòngyào ma?", "Does price still matter?"),
                    ("you", "价格未必决定一切。", "jiàgé wèibì juédìng yíqiè.", "Price doesn't necessarily decide everything."),
                    ("them", "从长远来看呢？", "cóng chángyuǎn lái kàn ne?", "And in the long run?"),
                    ("you", "从长远来看，需求在升级。换句话说，市场也在变。", "cóng chángyuǎn lái kàn, xūqiú zài shēngjí. huàn jù huà shuō, shìchǎng yě zài biàn.", "In the long run, demand is upgrading. In other words, the market is changing too."),
                ],
                "patterns": [
                    {
                        "text": "从长远来看，{x}",
                        "reading": "cóng chángyuǎn lái kàn, {x}",
                        "en": "In the long run, {x}",
                        "values": [("需求在升级", "xūqiú zài shēngjí", "demand is upgrading"), ("价格会下降", "jiàgé huì xiàjiàng", "prices will fall"), ("品质更重要", "pǐnzhì gèng zhòngyào", "quality matters more")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 59,
                "title": "Health",
                "goal": "Give advice with 与其…不如 / 至关重要.",
                "vocab": [
                    ("熬夜", "áo yè", "to stay up late"),
                    ("有害", "yǒu hài", "harmful"),
                    ("锻炼", "duànliàn", "to exercise"),
                    ("至关重要", "zhì guān zhòngyào", "crucial"),
                    ("引起重视", "yǐnqǐ zhòngshì", "to draw attention to"),
                    ("从医学角度看", "cóng yīxué jiǎodù kàn", "from a medical point of view"),
                    ("良好", "liánghǎo", "good, sound"),
                    ("睡眠", "shuìmián", "sleep"),
                ],
                "dialogue": [
                    ("them", "你常熬夜吗？", "nǐ cháng áo yè ma?", "Do you often stay up late?"),
                    ("you", "以前常，现在不了。熬夜对身体有害。", "yǐqián cháng, xiànzài bù le. áo yè duì shēntǐ yǒu hài.", "I used to, not any more. Staying up late is harmful."),
                    ("them", "那怎么保持健康？", "nà zěnme bǎochí jiànkāng?", "So how do you stay healthy?"),
                    ("you", "与其吃药，不如锻炼。", "yǔqí chī yào, bùrú duànliàn.", "Better to exercise than to take medicine."),
                    ("them", "你说得对，可是我没时间。", "nǐ shuō de duì, kěshì wǒ méi shíjiān.", "You're right, but I have no time."),
                    ("you", "良好的习惯至关重要。从医学角度看，睡眠也很重要。", "liánghǎo de xíguàn zhì guān zhòngyào. cóng yīxué jiǎodù kàn, shuìmián yě hěn zhòngyào.", "Good habits are crucial. From a medical standpoint, sleep matters a lot too."),
                ],
                "patterns": [
                    {
                        "text": "与其{x}，不如锻炼",
                        "reading": "yǔqí {x}, bùrú duànliàn",
                        "en": "Rather than {x}, better to exercise",
                        "values": [("吃药", "chī yào", "take medicine"), ("发愁", "fā chóu", "worry"), ("久坐", "jiǔ zuò", "sit for hours")],
                    }
                ],
                "notes": [],
            },
            {
                "id": 60,
                "title": "Travel",
                "goal": "Talk about travel with 受益匪浅 / 相比之下.",
                "vocab": [
                    ("受益匪浅", "shòu yì fěi qiǎn", "to benefit greatly"),
                    ("途中", "tú zhōng", "en route"),
                    ("跟团", "gēn tuán", "to join a tour group"),
                    ("省心", "shěng xīn", "worry-free"),
                    ("当地", "dāngdì", "local"),
                    ("自由行", "zìyóuxíng", "independent travel"),
                    ("遇到", "yùdào", "to run into, encounter"),
                    ("困难", "kùnnan", "difficulty"),
                ],
                "dialogue": [
                    ("them", "这次旅行怎么样？", "zhè cì lǚxíng zěnmeyàng?", "How was the trip?"),
                    ("you", "让我受益匪浅。途中难免遇到困难。", "ràng wǒ shòu yì fěi qiǎn. tú zhōng nánmiǎn yùdào kùnnan.", "I learned a lot. There were bound to be difficulties on the way."),
                    ("them", "自由行还是跟团？", "zìyóuxíng háishì gēn tuán?", "Independent travel or a tour group?"),
                    ("you", "自由行。相比之下，跟团更省心，但我不喜欢被安排。", "zìyóuxíng. xiāng bǐ zhī xià, gēn tuán gèng shěng xīn, dàn wǒ bù xǐhuan bèi ānpái.", "Independent. A tour is less hassle by comparison, but I don't like being scheduled."),
                    ("them", "你最喜欢什么？", "nǐ zuì xǐhuan shénme?", "What did you like most?"),
                    ("you", "无论去哪儿，我都喜欢了解当地文化。", "wúlùn qù nǎr, wǒ dōu xǐhuan liǎojiě dāngdì wénhuà.", "Wherever I go, I like to learn about local culture."),
                ],
                "patterns": [
                    {
                        "text": "无论{x}，我都喜欢旅行",
                        "reading": "wúlùn {x}, wǒ dōu xǐhuan lǚxíng",
                        "en": "No matter {x}, I like travelling",
                        "values": [("去哪儿", "qù nǎr", "where I go"), ("多远", "duō yuǎn", "how far"), ("多忙", "duō máng", "how busy")],
                    }
                ],
                "notes": ["受益匪浅 = 'benefited no little' - a set HSK 5-6 phrase."],
            },
            {
                "id": 61,
                "title": "Review: city life",
                "goal": "A full HSK 5 discussion weighing pros and cons.",
                "vocab": [
                    ("节奏", "jiézòu", "pace / rhythm"),
                    ("与此同时", "yǔ cǐ tóngshí", "at the same time"),
                    ("权衡", "quánhéng", "to weigh up"),
                    ("归根结底", "guī gēn jié dǐ", "in the final analysis"),
                    ("冲动", "chōngdòng", "impulsive"),
                    ("理性", "lǐxìng", "rational"),
                    ("又…又", "yòu…yòu", "both … and …"),
                    ("怕", "pà", "to be afraid"),
                    ("资源", "zīyuán", "resources"),
                    ("安静", "ānjìng", "quiet"),
                ],
                "dialogue": [
                    ("them", "你喜欢大城市的生活吗？", "nǐ xǐhuan dà chéngshì de shēnghuó ma?", "Do you like life in a big city?"),
                    ("you", "又喜欢又怕。节奏快，机会多，但是压力也大。", "yòu xǐhuan yòu pà. jiézòu kuài, jīhuì duō, dànshì yālì yě dà.", "Both. The pace is fast and there are opportunities, but the pressure is big too."),
                    ("them", "那你为什么留下？", "nà nǐ wèishénme liú xià?", "Then why do you stay?"),
                    ("you", "因为这里的人和资源。与此同时，我也想念小城市的安静。", "yīnwèi zhèlǐ de rén hé zīyuán. yǔ cǐ tóngshí, wǒ yě xiǎngniàn xiǎo chéngshì de ānjìng.", "For the people and the resources. At the same time, I miss the quiet of small cities."),
                    ("them", "你打算一直待下去吗？", "nǐ dǎsuàn yìzhí dāi xiàqù ma?", "Do you plan to stay for good?"),
                    ("you", "还在权衡。归根结底，要看家人和工作。", "hái zài quánhéng. guī gēn jié dǐ, yào kàn jiārén hé gōngzuò.", "Still weighing it up. In the final analysis it depends on family and work."),
                    ("them", "听起来你很理性。", "tīng qǐlái nǐ hěn lǐxìng.", "That sounds very rational."),
                    ("you", "与其冲动决定，不如想清楚。", "yǔqí chōngdòng juédìng, bùrú xiǎng qīngchu.", "Better to think it through than to decide on impulse."),
                ],
                "patterns": [
                    {
                        "text": "与其{x}，不如想清楚",
                        "reading": "yǔqí {x}, bùrú xiǎng qīngchu",
                        "en": "Rather than {x}, better to think it through",
                        "values": [("冲动决定", "chōngdòng juédìng", "deciding on impulse"), ("急着离开", "jí zhe líkāi", "rushing to leave"), ("一直犹豫", "yìzhí yóuyù", "hesitating forever")],
                    }
                ],
                "notes": ["归根结底 / 归根到底 = 'when all is said and done'."],
            },
        ],
    },
]

LEVEL = {
    "band": 5,
    "id": 5,
    "title": "HSK 5 · Opinions",
    "focus": "Abstract topics and formal connectives: 与其…不如, 难免, 未必, 换句话说, 见仁见智.",
    "gate": {"min_pron_score": 78.0, "min_accuracy": 78.0, "min_completeness": 90.0, "min_tone_score": 72.0},
    "units": UNITS,
}

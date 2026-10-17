# -*- coding: utf-8 -*-
"""HSK 6-7 缩写 — summarise the passage you just read, out loud.

HSK 6 写作 is a timed 缩写: read ~1,000 characters, produce ~400, in ten
minutes. There is no way to build that by speaking memorised lines, and
there is no way to *type* it on a pair of glasses either - so this is the
part of the exam skill that fits this app: read the passage, then say a
condensed version of it in your own words.

It is still the same exam task and it is still hard in the same way. The
difficulty of 缩写 is not handwriting, it is deciding what to leave out
while keeping the point, under time pressure, in the target language.
Speaking it keeps that and drops the part that needs a keyboard.

One entry per passage, lessons 62-85. `keywords` are the points a summary
has to keep - grading checks coverage of these, not wording, which is why
the sample is offered as "one possible summary" and never as a reference
answer to be matched.
"""

# lesson_id -> {prompt, sample, keywords, min_chars}
SUMMARIES = {
    62: {
        "prompt": "用两三句话说说张经理是个什么样的人。",
        "prompt_reading": "yòng liǎng sān jù huà shuōshuo Zhāng jīnglǐ shì ge shénmeyàng de rén.",
        "prompt_en": "In two or three sentences: what sort of person is Manager Zhang?",
        "sample": "张经理做事一丝不苟，在团队里举足轻重。他虽然严格，但并不苛刻，只要大家齐心协力，再难的问题也能解决。",
        "sample_reading": "Zhāng jīnglǐ zuòshì yì sī bù gǒu, zài tuánduì lǐ jǔ zú qīng zhòng. tā suīrán yángé, dàn bìng bù kēkè, zhǐyào dàjiā qí xīn xié lì, zài nán de wèntí yě néng jiějué.",
        "sample_en": "He is meticulous and carries weight. Strict, but not harsh; with everyone pulling together, even hard problems get solved.",
        "keywords": ["一丝不苟", "严格", "齐心协力"], "min_chars": 35,
    },
    63: {
        "prompt": "用两三句话评价这个方案。",
        "prompt_reading": "yòng liǎng sān jù huà píngjià zhè ge fāng'àn.",
        "prompt_en": "In two or three sentences, assess this proposal.",
        "sample": "这个方案想法别出心裁，但效果差强人意，问题出在执行不到位。大家各抒己见，再改一版。",
        "sample_reading": "zhè ge fāng'àn xiǎngfǎ bié chū xīn cái, dàn xiàoguǒ chā qiáng rén yì, wèntí chū zài zhíxíng bú dào wèi. dàjiā gè shū jǐ jiàn, zài gǎi yì bǎn.",
        "sample_en": "The idea is original but the result only passable; execution fell short. Everyone should air their view and revise it.",
        "keywords": ["别出心裁", "差强人意", "各抒己见"], "min_chars": 32,
    },
    64: {
        "prompt": "口头通知一下：会议改期了，怎么回事？",
        "prompt_reading": "kǒutóu tōngzhī yíxià: huìyì gǎiqī le, zěnme huí shì?",
        "prompt_en": "Announce it out loud: the meeting has moved, what happened?",
        "sample": "因为情况有变化，原定本周五的会议改到下周一了。由此带来的不便，请大家谅解。",
        "sample_reading": "yīnwèi qíngkuàng yǒu biànhuà, yuándìng běn zhōuwǔ de huìyì gǎi dào xià zhōuyī le. yóucǐ dàilái de bùbiàn, qǐng dàjiā liàngjiě.",
        "sample_en": "Things have changed, so Friday's meeting is now next Monday. Sorry for the inconvenience.",
        "keywords": ["会议", "下周一", "不便"], "min_chars": 28,
    },
    65: {
        "prompt": "说说你对年轻人换工作的看法。",
        "prompt_reading": "shuōshuo nǐ duì niánqīngrén huàn gōngzuò de kànfǎ.",
        "prompt_en": "Give your view on young people changing jobs.",
        "sample": "诚然，这种选择不无道理；然而事实并非完全如此。尽管如此，也无可厚非，稳定已不再是唯一标准。",
        "sample_reading": "chéngrán, zhè zhǒng xuǎnzé bù wú dàoli; rán'ér shìshí bìngfēi wánquán rúcǐ. jǐn guǎn rú cǐ, yě wú kě hòu fēi, wěndìng yǐ bú zài shì wéiyī biāozhǔn.",
        "sample_en": "There is something in it, but the reality is not quite so. Even so it is understandable: stability is no longer the only criterion.",
        "keywords": ["诚然", "然而", "稳定"], "min_chars": 35,
    },
    66: {
        "prompt": "用几句话推荐这本小说。",
        "prompt_reading": "yòng jǐ jù huà tuījiàn zhè běn xiǎoshuō.",
        "prompt_en": "Recommend this novel in a few sentences.",
        "sample": "这本小说很耐人寻味，作者笔触细腻，情节跌宕起伏，不失为一部佳作，值得推荐。",
        "sample_reading": "zhè běn xiǎoshuō hěn nài rén xún wèi, zuòzhě bǐchù xìnì, qíngjié diē dàng qǐ fú, bù shī wéi yí bù jiāzuò, zhíde tuījiàn.",
        "sample_en": "Thought-provoking, delicately written, full of twists - it can fairly be called a fine work.",
        "keywords": ["耐人寻味", "细腻", "值得推荐"], "min_chars": 32,
    },
    67: {
        "prompt": "为什么历史值得读？",
        "prompt_reading": "wèishénme lìshǐ zhíde dú?",
        "prompt_en": "Why is history worth reading?",
        "sample": "因为历史往往惊人的相似，盛极而衰几乎是常态。古人讲究中庸之道，顺势而为比逆流而上更明智。",
        "sample_reading": "yīnwèi lìshǐ wǎngwǎng jīngrén de xiāngsì, shèng jí ér shuāi jīhū shì chángtài. gǔrén jiǎngjiu zhōngyōng zhī dào, shùn shì ér wéi bǐ nì liú ér shàng gèng míngzhì.",
        "sample_en": "Because it rhymes: decline after the peak is the norm. The ancients prized the middle way, and going with the current beats fighting it.",
        "keywords": ["相似", "盛极而衰", "顺势而为"], "min_chars": 35,
    },
    68: {
        "prompt": "说说人工智能的发展。",
        "prompt_reading": "shuōshuo réngōng zhìnéng de fāzhǎn.",
        "prompt_en": "Talk about the development of AI.",
        "sample": "人工智能这几年发展得突飞猛进，改变了整个行业的格局。前景不可限量，但也引发了担忧，机遇与挑战并存。",
        "sample_reading": "réngōng zhìnéng zhè jǐ nián fāzhǎn de tū fēi měng jìn, gǎibiàn le zhěnggè hángyè de géjú. qiánjǐng bù kě xiànliàng, dàn yě yǐnfā le dānyōu, jīyù yǔ tiǎozhàn bìngcún.",
        "sample_en": "AI has advanced by leaps and bounds and reshaped the industry. Boundless prospects, real concerns - opportunity and challenge together.",
        "keywords": ["突飞猛进", "格局", "机遇"], "min_chars": 35,
    },
    69: {
        "prompt": "全球化带来什么问题？该怎么看？",
        "prompt_reading": "quánqiúhuà dàilái shénme wèntí? gāi zěnme kàn?",
        "prompt_en": "What problems does globalisation bring, and how do you see it?",
        "sample": "全球化是大势所趋，各国休戚与共；但文化差异也显而易见，所以求同存异才是上策。",
        "sample_reading": "quánqiúhuà shì dà shì suǒ qū, gè guó xiū qī yǔ gòng; dàn wénhuà chāyì yě xiǎn'ér yì jiàn, suǒyǐ qiú tóng cún yì cái shì shàngcè.",
        "sample_en": "It is the general trend and nations are in it together; but differences are obvious, so common ground while keeping differences is the better course.",
        "keywords": ["大势所趋", "文化差异", "求同存异"], "min_chars": 33,
    },
    70: {
        "prompt": "信息太多，我们该怎么办？",
        "prompt_reading": "xìnxī tài duō, wǒmen gāi zěnme bàn?",
        "prompt_en": "There is too much information. What should we do?",
        "sample": "现在的信息铺天盖地，真假难辨。媒体应当恪守底线，我们自己也要保持理性，切忌人云亦云。",
        "sample_reading": "xiànzài de xìnxī pū tiān gài dì, zhēn jiǎ nán biàn. méitǐ yīngdāng kèshǒu dǐxiàn, wǒmen zìjǐ yě yào bǎochí lǐxìng, qièjì rén yún yì yún.",
        "sample_en": "Information swamps us and truth is hard to tell. Media must hold the line; we must stay rational and not just echo others.",
        "keywords": ["铺天盖地", "恪守", "人云亦云"], "min_chars": 33,
    },
    71: {
        "prompt": "情理和法理冲突的时候，应该怎么办？",
        "prompt_reading": "qínglǐ hé fǎlǐ chōngtū de shíhou, yīnggāi zěnme bàn?",
        "prompt_en": "When sentiment and legal principle clash, what should be done?",
        "sample": "情理和法理常常冲突，但无论如何不能以暴制暴，应当依法行事。",
        "sample_reading": "qínglǐ hé fǎlǐ chángcháng chōngtū, dàn wúlùn rúhé bù néng yǐ bào zhì bào, yīngdāng yīfǎ xíngshì.",
        "sample_en": "They often clash, but whatever happens, violence must not answer violence; act according to law.",
        "keywords": ["冲突", "以暴制暴", "依法"], "min_chars": 28,
    },
    72: {
        "prompt": "大城市给人什么样的感觉？",
        "prompt_reading": "dà chéngshì gěi rén shénmeyàng de gǎnjué?",
        "prompt_en": "What does the big city feel like?",
        "sample": "大城市的节奏快得让人喘不过气，归属感时有时无。人们在喧嚣中寻找宁静，身份也在重构。",
        "sample_reading": "dà chéngshì de jiézòu kuài de ràng rén chuǎn bu guò qì, guīshǔ gǎn shí yǒu shí wú. rénmen zài xuānxiāo zhōng xúnzhǎo níngjìng, shēnfèn yě zài chónggòu.",
        "sample_en": "The pace takes your breath away and belonging comes and goes. People look for quiet in the noise; identity is being rebuilt.",
        "keywords": ["喘不过气", "归属感", "喧嚣"], "min_chars": 32,
    },
    73: {
        "prompt": "学中文到底难在哪儿？",
        "prompt_reading": "xué Zhōngwén dàodǐ nán zài nǎr?",
        "prompt_en": "What exactly is hard about learning Chinese?",
        "sample": "归根结底，难在声调和文化。没有捷径，语言学习不可能一蹴而就，听说和读写相辅相成。",
        "sample_reading": "guī gēn jié dǐ, nán zài shēngdiào hé wénhuà. méiyou jiéjìng, yǔyán xuéxí bù kěnéng yī cù ér jiù, tīngshuō hé dúxiě xiāng fǔ xiāng chéng.",
        "sample_en": "In the end, tones and culture. No shortcut, no overnight result; listening-speaking and reading-writing feed each other.",
        "keywords": ["归根结底", "声调", "一蹴而就"], "min_chars": 33,
    },
    74: {
        "prompt": "用两三句话概括这则新闻。",
        "prompt_reading": "yòng liǎng sān jù huà gàikuò zhè zé xīnwén.",
        "prompt_en": "Summarise this news item in two or three sentences.",
        "sample": "据报道，今年毕业生数量再创新高，就业压力主要集中在服务业和制造业。官方已经回应，说会加大支持力度。",
        "sample_reading": "jù bàodào, jīnnián bìyèshēng shùliàng zài chuàng xīn gāo, jiùyè yālì zhǔyào jízhōng zài fúwùyè hé zhìzàoyè. guānfāng yǐjīng huíyìng, shuō huì jiādà zhīchí lìdù.",
        "sample_en": "Reports say graduate numbers hit a new high, with pressure in services and manufacturing. The authorities have promised more support.",
        "keywords": ["毕业生", "服务业", "官方"], "min_chars": 33,
    },
    75: {
        "prompt": "解释一下“内卷”和“躺平”这两个词。",
        "prompt_reading": "jiěshì yíxià “nèijuǎn” hé “tǎng píng” zhè liǎng ge cí.",
        "prompt_en": "Explain the two words 内卷 and 躺平.",
        "sample": "内卷是过度竞争，付出越来越多，收获却没变多；躺平是干脆不争了。这些词只适合聊天，不能用在正式文件里。",
        "sample_reading": "nèijuǎn shì guòdù jìngzhēng, fùchū yuè lái yuè duō, shōuhuò què méi biàn duō; tǎng píng shì gāncuì bù zhēng le. zhèxiē cí zhǐ shìhé liáotiān, bù néng yòng zài zhèngshì wénjiàn lǐ.",
        "sample_en": "内卷 is competing harder for no extra gain; 躺平 is opting out. They are for chat, not for formal documents.",
        "keywords": ["内卷", "躺平", "正式"], "min_chars": 35,
    },
    76: {
        "prompt": "带口音是问题吗？为什么？",
        "prompt_reading": "dài kǒuyīn shì wèntí ma? wèishénme?",
        "prompt_en": "Is having an accent a problem? Why?",
        "sample": "不是问题。带一点口音很正常，本地人之间也讲方言。真正的困难在语速，因为口语会连读、吞音和省略。",
        "sample_reading": "bú shì wèntí. dài yìdiǎn kǒuyīn hěn zhèngcháng, běndì rén zhī jiān yě jiǎng fāngyán. zhēnzhèng de kùnnan zài yǔsù, yīnwèi kǒuyǔ huì liándú, tūn yīn hé shěnglüè.",
        "sample_en": "No. A slight accent is normal - locals speak dialect too. The real difficulty is speed: speech runs together and drops sounds.",
        "keywords": ["口音", "方言", "连读"], "min_chars": 33,
    },
    77: {
        "prompt": "讲讲“掩耳盗铃”这个故事。",
        "prompt_reading": "jiǎngjiang “yǎn ěr dào líng” zhè ge gùshi.",
        "prompt_en": "Tell the story of 掩耳盗铃.",
        "sample": "有个人捂住自己的耳朵去偷铃铛，以为这样别人也就听不见了。这个故事的寓意是：骗自己最容易。",
        "sample_reading": "yǒu ge rén wǔ zhù zìjǐ de ěrduo qù tōu língdang, yǐwéi zhèyàng biérén yě jiù tīng bu jiàn le. zhè ge gùshi de yùyì shì: piàn zìjǐ zuì róngyì.",
        "sample_en": "A man covered his own ears to steal a bell, thinking nobody else could hear. The moral: deceiving yourself is easiest.",
        "keywords": ["耳朵", "偷", "骗"], "min_chars": 30,
    },
    78: {
        "prompt": "为什么古诗能流传千古？",
        "prompt_reading": "wèishénme gǔshī néng liúchuán qiāngǔ?",
        "prompt_en": "Why have these poems lasted so long?",
        "sample": "因为意境好，短短几个字就能画出一幅画。孩子们从小背诵唐诗，很多名句一辈子都忘不掉。",
        "sample_reading": "yīnwèi yìjìng hǎo, duǎnduǎn jǐ ge zì jiù néng huà chū yì fú huà. háizimen cóng xiǎo bèisòng Táng shī, hěn duō míngjù yí bèizi dōu wàng bu diào.",
        "sample_en": "Because of the mood: a few characters paint a picture. Children memorise Tang poems young and the lines stay for life.",
        "keywords": ["意境", "背诵", "名句"], "min_chars": 32,
    },
    79: {
        "prompt": "为什么每个字都学过，还是听不懂？",
        "prompt_reading": "wèishénme měi ge zì dōu xué guo, háishì tīng bu dǒng?",
        "prompt_en": "Why can't you follow it when you know every character?",
        "sample": "因为口语会连读、吞音和省略。所以听不懂的时候，先抓节奏和语气词，别一个字一个字地听。",
        "sample_reading": "yīnwèi kǒuyǔ huì liándú, tūn yīn hé shěnglüè. suǒyǐ tīng bu dǒng de shíhou, xiān zhuā jiézòu hé yǔqì cí, bié yí ge zì yí ge zì de tīng.",
        "sample_en": "Because speech runs together, swallows sounds and omits. So catch the rhythm and particles, not each character.",
        "keywords": ["连读", "吞音", "节奏"], "min_chars": 33,
    },
    80: {
        "prompt": "用几句话说说这组数据。",
        "prompt_reading": "yòng jǐ jù huà shuōshuo zhè zǔ shùjù.",
        "prompt_en": "Describe these figures in a few sentences.",
        "sample": "第一季度同比增长 5.2%，环比略有回落，但整体仍然稳健。增幅主要在服务业和制造业，投资增幅不大。",
        "sample_reading": "dì-yī jìdù tóngbǐ zēngzhǎng 5.2%, huánbǐ lüè yǒu huíluò, dàn zhěngtǐ réngrán wěnjiàn. zēngfú zhǔyào zài fúwùyè hé zhìzàoyè, tóuzī zēngfú bú dà.",
        "sample_en": "Q1 grew 5.2% year on year, slightly down on the quarter but sound. Growth is in services and manufacturing, not investment.",
        "keywords": ["同比", "环比", "增幅"], "min_chars": 35,
    },
    81: {
        "prompt": "算法推荐有什么问题？该怎么管？",
        "prompt_reading": "suànfǎ tuījiàn yǒu shénme wèntí? gāi zěnme guǎn?",
        "prompt_en": "What is wrong with algorithmic recommendation, and how should it be governed?",
        "sample": "一是让人只看自己想看的，视野越来越窄；二是数据怎么用，用户往往不知道。所以监管要跟上，规则必须透明。",
        "sample_reading": "yī shì ràng rén zhǐ kàn zìjǐ xiǎng kàn de, shìyě yuè lái yuè zhǎi; èr shì shùjù zěnme yòng, yònghù wǎngwǎng bù zhīdào. suǒyǐ jiānguǎn yào gēn shàng, guīzé bìxū tòumíng.",
        "sample_en": "It narrows what you see, and users don't know how their data is used. Oversight must keep up and the rules be transparent.",
        "keywords": ["视野", "隐私", "透明"], "min_chars": 35,
    },
    82: {
        "prompt": "普通人该怎么维权？对企业来说什么最重要？",
        "prompt_reading": "pǔtōng rén gāi zěnme wéi quán? duì qǐyè lái shuō shénme zuì zhòngyào?",
        "prompt_en": "How does an ordinary person defend their rights, and what matters most to a company?",
        "sample": "先保留证据，再找律师，必要的时候可以起诉。对企业来说，最重要的不是打官司，而是日常合规。",
        "sample_reading": "xiān bǎoliú zhèngjù, zài zhǎo lǜshī, bìyào de shíhou kěyǐ qǐsù. duì qǐyè lái shuō, zuì zhòngyào de bú shì dǎ guānsi, ér shì rìcháng hé guī.",
        "sample_en": "Preserve evidence, find a lawyer, sue if need be. For a company it is not litigation but everyday compliance.",
        "keywords": ["证据", "律师", "合规"], "min_chars": 33,
    },
    83: {
        "prompt": "减排到底值不值得？",
        "prompt_reading": "jiǎn pái dàodǐ zhí bu zhíde?",
        "prompt_en": "Is cutting emissions really worth it?",
        "sample": "碳排放已经达标，但距离先进水平还有差距。短期成本高一些，长期看是可持续的，而且越来越便宜。",
        "sample_reading": "tàn páifàng yǐjīng dá biāo, dàn jùlí xiānjìn shuǐpíng hái yǒu chājù. duǎnqī chéngběn gāo yìxiē, chángqī kàn shì kě chíxù de, érqiě yuè lái yuè piányi.",
        "sample_en": "Emissions meet the standard but there's still a gap. Costlier short term, sustainable and cheaper long term.",
        "keywords": ["达标", "成本", "可持续"], "min_chars": 33,
    },
    84: {
        "prompt": "论文进展得怎么样了？",
        "prompt_reading": "lùnwén jìnzhǎn de zěnmeyàng le?",
        "prompt_en": "How is the paper coming along?",
        "sample": "综述已经写完，正在做实证研究。初步结果支持假设，但样本还不够大，所以还不能急着下结论。",
        "sample_reading": "zōngshù yǐjīng xiě wán, zhèngzài zuò shízhèng yánjiū. chūbù jiéguǒ zhīchí jiǎshè, dàn yàngběn hái bú gòu dà, suǒyǐ hái bù néng jí zhe xià jiélùn.",
        "sample_en": "The review is done and the empirical work is under way. Initial results support the hypothesis but the sample is too small to conclude.",
        "keywords": ["综述", "实证", "样本"], "min_chars": 33,
    },
    85: {
        "prompt": "你的立场是什么？有什么前提？",
        "prompt_reading": "nǐ de lìchǎng shì shénme? yǒu shénme qiántí?",
        "prompt_en": "What is your position, and on what conditions?",
        "sample": "我的立场是支持，但有三个前提：证据要公开，要有退出机制，责任要清楚。做不到我就反对。",
        "sample_reading": "wǒ de lìchǎng shì zhīchí, dàn yǒu sān ge qiántí: zhèngjù yào gōngkāi, yào yǒu tuìchū jīzhì, zérèn yào qīngchu. zuò bu dào wǒ jiù fǎnduì.",
        "sample_en": "I am in favour on three conditions: public evidence, an exit mechanism, clear responsibility. Otherwise I oppose it.",
        "keywords": ["立场", "前提", "支持"], "min_chars": 33,
    },
}


def get(lesson_id: int) -> dict:
    return SUMMARIES.get(int(lesson_id)) or {}

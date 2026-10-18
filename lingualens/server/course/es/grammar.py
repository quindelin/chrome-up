# -*- coding: utf-8 -*-
"""A grammar page per lesson - same contract as `course.ja.grammar`:

    GRAMMAR[lesson_id] = [{"point", "en", "formula", "examples": [(text, reading, en)],
                           "contrast", "watch"}]

The page is reference, not a lecture: the learner meets the structure in the
dialogue first and comes here to see it laid out. `watch` is the mistake an
English speaker actually makes with it.
"""
E = ""

GRAMMAR = {
    1: [{
        "point": "estar + how you are",
        "en": "how someone is right now",
        "formula": "(yo) estoy · (tú) estás · (usted) está + bien / mal / cansado",
        "examples": [("Estoy bien, gracias.", E, "I'm fine, thanks."),
                     ("¿Estás bien?", E, "Are you OK?")],
        "contrast": "¿Qué tal? needs no verb at all, which is why it is the easiest "
                    "greeting to answer.",
        "watch": "Not 'soy bien'. How you are today is estar, always.",
    }],
    2: [{
        "point": "tú or usted",
        "en": "two ways to say 'you'",
        "formula": "tú te llamas · usted se llama  (usted takes the él/ella verb form)",
        "examples": [("¿Cómo te llamas?", E, "What's your name? (friend)"),
                     ("¿Cómo se llama usted?", E, "What is your name? (stranger, elder)")],
        "contrast": "Usted is grammatically third person: '¿cómo se llama?' could "
                    "mean 'what's his name?' too, which is why usted is often said "
                    "out loud.",
        "watch": "Pick one per person and keep it. Switching tú and usted with "
                 "the same person mid-conversation sounds odd.",
    }, {
        "point": "llamarse",
        "en": "to be called (literally 'to call oneself')",
        "formula": "me llamo · te llamas · se llama",
        "examples": [("Me llamo Sam.", E, "My name is Sam.")],
        "contrast": "'Mi nombre es Sam' is correct but stiff - like 'my name is' on a form.",
        "watch": "Not 'me llamo es Sam'. Llamo is already the verb.",
    }],
    3: [{
        "point": "ser de",
        "en": "where someone is from",
        "formula": "soy · eres · es · somos + de + place",
        "examples": [("Soy de Chicago.", E, "I'm from Chicago."),
                     ("¿De dónde eres?", E, "Where are you from?")],
        "contrast": "The question word goes first and takes its preposition with it: "
                    "¿de dónde...?, never '¿dónde eres de?'.",
        "watch": "Drop yo unless you are contrasting yourself with someone.",
    }],
    4: [{
        "point": "present tense, -ar verbs",
        "en": "regular verbs: the ending says who",
        "formula": "hablar → hablo · hablas · habla · hablamos · habláis · hablan",
        "examples": [("Hablo un poco de español.", E, "I speak a little Spanish."),
                     ("¿Habla usted inglés?", E, "Do you speak English?")],
        "contrast": "Questions do not need 'do': the same words with rising "
                    "intonation are a question.",
        "watch": "-o is always 'I'. Hablo, trabajo, estudio - you can say a lot "
                 "about yourself with one ending.",
    }],
    5: [{
        "point": "-ar, -er, -ir together",
        "en": "the three verb families in the present",
        "formula": "trabajo / trabajas · como / comes · vivo / vives",
        "examples": [("¿Trabajas o estudias?", E, "Do you work or study?"),
                     ("Vivo aquí.", E, "I live here.")],
        "contrast": "Yo is -o in all three families. Only the tú ending changes: "
                    "-as for -ar, -es for -er and -ir.",
        "watch": "Ser and estar, ir and tener are irregular - learn them as words.",
    }],
    6: [{
        "point": "estar for location",
        "en": "where something is",
        "formula": "N + está + place word · ¿dónde está + el/la N?",
        "examples": [("La estación está cerca.", E, "The station is near."),
                     ("¿Dónde está el baño?", E, "Where is the bathroom?")],
        "contrast": "Ser tells you what a place is (es un banco); estar tells you "
                    "where it is (está aquí).",
        "watch": "de + el → del (al lado del banco). Never 'de el'.",
    }],
    7: [{
        "point": "hay vs está",
        "en": "is there one? vs where is it?",
        "formula": "hay + un/una/dos/nothing + N  ·  el/la + N + está",
        "examples": [("¿Hay una farmacia por aquí?", E, "Is there a pharmacy around here?"),
                     ("La farmacia está en la calle Sol.", E, "The pharmacy is on Sol Street.")],
        "contrast": "Hay introduces something new; está locates something already "
                    "known. The article follows: un/una with hay, el/la with está.",
        "watch": "×Hay el banco. ×¿Dónde hay la farmacia?",
    }],
    8: [{
        "point": "ir a",
        "en": "going somewhere",
        "formula": "voy · vas · va · vamos + a + place   (a + el → al)",
        "examples": [("Voy al centro.", E, "I'm going to the centre."),
                     ("¿Adónde vas?", E, "Where are you going?")],
        "contrast": "Movement takes a: voy a Madrid. Being somewhere takes en: estoy "
                    "en Madrid. Transport takes en: en autobús - except andando.",
        "watch": "×Voy a el centro. ×Voy en la playa.",
    }],
    9: [{
        "point": "numbers 0-20, and telling the time",
        "en": "counting, prices, departure times",
        "formula": "a la una · a las dos · a las diez y media",
        "examples": [("Son doce euros.", E, "It's twelve euros."),
                     ("Sale a las diez.", E, "It leaves at ten.")],
        "contrast": "Times are feminine plural (las horas are understood): a las "
                    "tres. One o'clock is singular: a la una.",
        "watch": "Seis and siete, doce and dos are the pairs learners mishear - "
                 "listen for the end of the word.",
    }],
    10: [{
        "point": "review: ser, estar, hay, ir",
        "en": "four verbs, four jobs",
        "formula": "ser = what · estar = where/how · hay = there is · ir = going",
        "examples": [("¿Este tren va a Sevilla?", E, "Does this train go to Seville?"),
                     ("¿Hay una taquilla por aquí?", E, "Is there a ticket office around here?")],
        "contrast": "This lesson needs all four in one minute. If one is slow, go "
                    "back to its lesson before A1 ends.",
        "watch": "",
    }],
    11: [{
        "point": "tener + noun for states",
        "en": "hunger, thirst, cold, heat, age",
        "formula": "tengo · tienes · tiene + hambre / sed / frío / calor / N años",
        "examples": [("Tengo hambre.", E, "I'm hungry."),
                     ("¿Tienes frío?", E, "Are you cold?")],
        "contrast": "English 'be' + adjective; Spanish 'have' + noun. Tired, happy "
                    "and ill are adjectives and take estar: estoy cansado.",
        "watch": "Muy goes with adjectives, mucho/mucha with nouns: tengo mucha "
                 "hambre, estoy muy cansado.",
    }, {
        "point": "querer + infinitive",
        "en": "wanting to do something",
        "formula": "quiero · quieres · quiere + infinitive / noun",
        "examples": [("Quiero comer.", E, "I want to eat.")],
        "contrast": "Quiero un café is fine at a bar, but 'me pone un café' or "
                    "'¿me pones...?' is what you will hear in Spain.",
        "watch": "The stem changes: querer → quiero, not 'quero'.",
    }],
    12: [{
        "point": "gender and articles",
        "en": "every noun is masculine or feminine",
        "formula": "un / el + masculine  ·  una / la + feminine",
        "examples": [("un café con leche", E, "a white coffee"),
                     ("una tostada", E, "a piece of toast")],
        "contrast": "-o is usually masculine, -a usually feminine, but not always: "
                    "el día, la mano, el idioma. That is why the bank always shows "
                    "the article.",
        "watch": "Adjectives agree too: una cerveza fría, un café frío.",
    }],
    13: [{
        "point": "gustar",
        "en": "liking - the thing liked is the subject",
        "formula": "me / te / le gusta + singular · me / te / le gustan + plural",
        "examples": [("Me gusta el pescado.", E, "I like fish."),
                     ("Me gustan las verduras.", E, "I like vegetables.")],
        "contrast": "'A mí' and 'a ti' add emphasis or contrast: ¿y a ti? = and "
                    "you? It is never '¿y tú?' after gustar.",
        "watch": "×Yo gusto el café. ×Me gusta las verduras.",
    }],
    14: [{
        "point": "numbers 30-100",
        "en": "prices",
        "formula": "treinta y uno ... noventa y nueve · cien",
        "examples": [("Son treinta y cinco euros.", E, "It's thirty-five euros.")],
        "contrast": "Up to 29 it is one word (veintiocho); from 31 it is three "
                    "(treinta y ocho). Exactly 100 is cien.",
        "watch": "Sesenta and setenta are the pair everyone confuses.",
    }, {
        "point": "poder + infinitive",
        "en": "asking if you can",
        "formula": "¿puedo + infinitive?",
        "examples": [("¿Puedo pagar con tarjeta?", E, "Can I pay by card?")],
        "contrast": "Puedo is from poder (o → ue), the same kind of change as "
                    "querer → quiero.",
        "watch": "",
    }],
    15: [{
        "point": "review: ordering",
        "en": "the restaurant sequence",
        "formula": "una mesa para N · de primero... · de segundo... · ¿me trae la cuenta?",
        "examples": [("De primero, una sopa.", E, "For starter, a soup.")],
        "contrast": "Rico/rica is delicious and agrees with the food: la sopa está "
                    "muy rica, el pollo está muy rico.",
        "watch": "",
    }],
}


def for_lesson(lesson_id: int) -> list:
    """The grammar page for one lesson, or an empty list."""
    return list(GRAMMAR.get(int(lesson_id)) or [])

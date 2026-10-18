# -*- coding: utf-8 -*-
"""CEFR A1 — first contact: people, getting around, food.

Data layout is the Japanese course's, with the reading slot left empty:
Spanish is spelled the way it is said, so there is no second script to put
above the line. Where a line has a real pronunciation trap, the trap goes in
the vocab `note`, not in the reading.

    vocab     (text, reading, english, note)
    dialogue  (speaker, text, reading, english)
    patterns  {"text", "reading", "en", "kind", "values": [(text, reading, en)]}

Authoring rules this file keeps (see docs/COURSE_AUDIT.md for why):
  1. The learner ("you") says the lesson's target structure at least twice.
     Listening to it in "them" lines is input, not practice.
  2. Every lesson has at least two patterns, and every pattern has a `kind`,
     so drills.recombine can bring words from earlier lessons back.
     Slot values carry their own article - the frame never has to guess
     a gender.
  3. Register is a choice the learner makes: lessons with strangers and staff
     use usted, lessons with peers use tú, and lessons 2 and 5 make you
     produce both.
  4. One variety: Peninsular Spanish, to match the es-ES voice and scorer.
     Latin American alternatives go in the vocab note, never mixed into a
     line.
  5. Lines stay under ~60 characters: the gate allows 15 seconds and the
     glasses show about three lines.
"""

E = ""  # the empty reading slot, so the tables below stay readable

# ---------------------------------------------------------------------------
# Unit 1 - Saludos y presentaciones
# ---------------------------------------------------------------------------
UNIT_1 = {
    "id": 1,
    "title": "Greetings & Introductions",
    "focus": "Say hello, give your name and where you are from, and keep a "
             "conversation going when you do not understand.",
    "gate": {"min_pron_score": 62.0, "min_accuracy": 62.0, "min_completeness": 75.0},
    "lessons": [
        {
            "id": 1,
            "title": "Hola",
            "goal": "Greet someone at any time of day, say how you are, and say goodbye.",
            "vocab": [
                ("hola", E, "hello", "the h is silent: 'ola'"),
                ("buenos días", E, "good morning", ""),
                ("buenas tardes", E, "good afternoon / evening", "from lunch until dark"),
                ("¿qué tal?", E, "how are things?", ""),
                ("bien", E, "well, fine", ""),
                ("hasta luego", E, "see you later", "the h is silent again"),
            ],
            "dialogue": [
                ("them", "¡Hola! Buenos días.", E, "Hi! Good morning."),
                ("you", "Hola, buenos días.", E, "Hi, good morning."),
                ("them", "¿Qué tal?", E, "How are things?"),
                ("you", "Bien, gracias. ¿Y tú?", E, "Fine, thanks. And you?"),
                ("them", "Muy bien. Oye, ¿vas al trabajo?", E, "Very well. Hey, are you off to work?"),
                ("you", "Sí. ¡Hasta luego!", E, "Yes. See you later!"),
                ("them", "¡Hasta luego! Buenas tardes, ¿eh?", E, "See you! Have a good afternoon."),
                ("you", "Gracias, igualmente.", E, "Thanks, you too."),
            ],
            "patterns": [
                {"text": "{x}, ¿qué tal?", "reading": E, "en": "{x}, how are things?",
                 "kind": "es-greeting",
                 "values": [("Hola", E, "Hi"), ("Buenos días", E, "Good morning"),
                            ("Buenas tardes", E, "Good afternoon")]},
                {"text": "Estoy {x}, gracias.", "reading": E, "en": "I'm {x}, thanks.",
                 "kind": "es-state",
                 "values": [("bien", E, "fine"), ("muy bien", E, "very well"),
                            ("regular", E, "so-so")]},
            ],
            "notes": [
                "Spanish has five vowels and they never change: a e i o u, short "
                "and clean. 'Bien' is one syllable, bjen.",
                "¿Y tú? turns any answer back on the other person. It is the "
                "single cheapest way to keep a conversation alive.",
            ],
        },
        {
            "id": 2,
            "title": "¿Cómo te llamas?",
            "goal": "Give your name and ask someone else's, informally and politely.",
            "vocab": [
                ("me llamo", E, "my name is", "ll is a 'y' sound in most of the world"),
                ("¿cómo te llamas?", E, "what's your name? (tú)", ""),
                ("¿cómo se llama usted?", E, "what's your name? (usted)", ""),
                ("mucho gusto", E, "nice to meet you", ""),
                ("encantado / encantada", E, "delighted (to meet you)",
                 "-o if you are a man, -a if you are a woman"),
                ("señora", E, "madam, Mrs", "ñ is 'ny', as in canyon"),
            ],
            "dialogue": [
                ("them", "Hola, me llamo Lucía. ¿Cómo te llamas?", E, "Hi, I'm Lucía. What's your name?"),
                ("you", "Me llamo Sam. Mucho gusto.", E, "I'm Sam. Nice to meet you."),
                ("them", "Igualmente. Mira, esta es la señora Ruiz.", E, "Likewise. Look, this is Mrs Ruiz."),
                ("you", "Buenas tardes, señora. ¿Cómo se llama usted?", E,
                 "Good afternoon, madam. What is your name?"),
                ("them", "Me llamo Carmen Ruiz. Encantada.", E, "My name is Carmen Ruiz. Delighted."),
                ("you", "Encantado. Me llamo Sam.", E, "Delighted. I'm Sam."),
                ("them", "¿Y usted es amigo de Lucía?", E, "And are you a friend of Lucía's?"),
                ("you", "Sí, soy amigo de Lucía.", E, "Yes, I'm a friend of Lucía's."),
            ],
            "patterns": [
                {"text": "Me llamo {x}.", "reading": E, "en": "My name is {x}.",
                 "kind": "es-name",
                 "values": [("Sam", E, "Sam"), ("Ana", E, "Ana"), ("Daniel", E, "Daniel")]},
                {"text": "Buenas tardes, {x}.", "reading": E, "en": "Good afternoon, {x}.",
                 "kind": "es-title",
                 "values": [("señora", E, "madam"), ("señor", E, "sir"),
                            ("señorita", E, "miss")]},
            ],
            "notes": [
                "Tú is for people your age, friends, children. Usted is for "
                "strangers older than you, staff, anyone you would call sir or "
                "madam. When in doubt with an adult stranger, start with usted - "
                "they will tell you to use tú.",
                "Say your own name in the pattern drill, not Sam's. The line is "
                "yours to change.",
            ],
        },
        {
            "id": 3,
            "title": "¿De dónde eres?",
            "goal": "Say where you are from and ask the same, with ser.",
            "vocab": [
                ("soy de", E, "I'm from", ""),
                ("¿de dónde eres?", E, "where are you from? (tú)", ""),
                ("¿de dónde es usted?", E, "where are you from? (usted)", ""),
                ("Estados Unidos", E, "the United States", ""),
                ("Inglaterra", E, "England", ""),
                ("también", E, "also, too", "stress on the last syllable: tam-BIEN"),
            ],
            "dialogue": [
                ("them", "Tú no eres de aquí, ¿verdad?", E, "You're not from here, are you?"),
                ("you", "No, soy de Estados Unidos. ¿Y tú?", E, "No, I'm from the United States. And you?"),
                ("them", "Yo soy de Guadalajara. ¿De qué ciudad eres?", E,
                 "I'm from Guadalajara. Which city are you from?"),
                ("you", "Soy de Chicago. Es una ciudad grande.", E, "I'm from Chicago. It's a big city."),
                ("them", "¡Qué bien! Mi hermano vive en Chicago.", E, "How nice! My brother lives in Chicago."),
                ("you", "¿En serio? ¿Tu hermano es de Guadalajara también?", E,
                 "Really? Is your brother from Guadalajara too?"),
                ("them", "Sí, somos de Guadalajara.", E, "Yes, we're from Guadalajara."),
                ("you", "Yo soy de Chicago, pero vivo aquí.", E, "I'm from Chicago, but I live here."),
            ],
            "patterns": [
                {"text": "Soy de {x}.", "reading": E, "en": "I'm from {x}.",
                 "kind": "es-origin",
                 "values": [("Estados Unidos", E, "the United States"), ("Inglaterra", E, "England"),
                            ("Canadá", E, "Canada")]},
                {"text": "Vivo en {x}.", "reading": E, "en": "I live in {x}.",
                 "kind": "es-city",
                 "values": [("Chicago", E, "Chicago"), ("Madrid", E, "Madrid"),
                            ("Ciudad de México", E, "Mexico City")]},
            ],
            "notes": [
                "Spanish drops the subject: 'soy de Chicago', not 'yo soy de "
                "Chicago'. Saying yo is emphasis - 'I, on the other hand, am from "
                "Chicago' - which is exactly how the last line uses it.",
                "Ser is for what something is: origin, identity, nationality. "
                "Estar (lesson 6) is for where and how something is right now.",
            ],
        },
        {
            "id": 4,
            "title": "No entiendo",
            "goal": "Slow a conversation down, ask for a word, and keep going in Spanish.",
            "vocab": [
                ("no entiendo", E, "I don't understand", ""),
                ("más despacio", E, "more slowly", ""),
                ("otra vez", E, "again", ""),
                ("¿cómo se dice...?", E, "how do you say...?", ""),
                ("un poco", E, "a little", ""),
                ("¿habla inglés?", E, "do you speak English? (usted)", "the h is silent: 'abla'"),
            ],
            "dialogue": [
                ("them", "Disculpe, ¿sabe dónde está la calle Mayor?", E,
                 "Excuse me, do you know where Mayor Street is?"),
                ("you", "Perdón, no entiendo. Más despacio, por favor.", E,
                 "Sorry, I don't understand. More slowly, please."),
                ("them", "¿Sabe... dónde... está... la calle Mayor?", E,
                 "Do you know... where... Mayor Street... is?"),
                ("you", "Ah, la calle Mayor. Lo siento, no sé.", E, "Ah, Mayor Street. Sorry, I don't know."),
                ("them", "No pasa nada. ¿Usted habla inglés?", E, "No problem. Do you speak English?"),
                ("you", "Sí, pero hablo un poco de español.", E, "Yes, but I speak a little Spanish."),
                ("them", "¡Muy bien! Habla muy bien.", E, "Very good! You speak very well."),
                ("you", "Gracias. ¿Cómo se dice 'map' en español?", E,
                 "Thanks. How do you say 'map' in Spanish?"),
                ("them", "Se dice 'mapa'.", E, "You say 'mapa'."),
                ("you", "Mapa. Gracias, muy amable.", E, "Mapa. Thank you, that's very kind."),
            ],
            "patterns": [
                {"text": "{x}, por favor.", "reading": E, "en": "{x}, please.",
                 "kind": "es-repair",
                 "values": [("Más despacio", E, "More slowly"), ("Otra vez", E, "Again"),
                            ("Más alto", E, "Louder")]},
                {"text": "Hablo {x} de español.", "reading": E, "en": "I speak {x} Spanish.",
                 "kind": "es-amount",
                 "values": [("un poco", E, "a little"), ("muy poco", E, "very little"),
                            ("bastante", E, "quite a bit")]},
            ],
            "notes": [
                "Más despacio, por favor is worth more than any other line in this "
                "band: it keeps the conversation in Spanish instead of ending it.",
                "Disculpe (usted) and perdón both get attention politely. Lo "
                "siento is a real apology - 'I'm sorry that...'.",
            ],
        },
        {
            "id": 5,
            "title": "Repaso: en una fiesta",
            "goal": "Hold a whole first conversation: greet, names, origin, and a graceful exit.",
            "vocab": [
                ("¿y usted?", E, "and you? (usted)", ""),
                ("amigo / amiga", E, "friend", ""),
                ("trabajo en", E, "I work in / at", ""),
                ("estudio", E, "I study", ""),
                ("me tengo que ir", E, "I have to go", ""),
                ("nos vemos", E, "see you", ""),
            ],
            "dialogue": [
                ("them", "Hola, soy Diego, el amigo de Lucía. ¿Y tú?", E, "Hi, I'm Diego, Lucía's friend. And you?"),
                ("you", "Hola, Diego. Me llamo Sam. Mucho gusto.", E, "Hi, Diego. I'm Sam. Nice to meet you."),
                ("them", "¿De dónde eres, Sam?", E, "Where are you from, Sam?"),
                ("you", "Soy de Estados Unidos, pero vivo aquí.", E, "I'm from the US, but I live here."),
                ("them", "¿Y trabajas o estudias?", E, "And do you work or study?"),
                ("you", "Trabajo en un hotel. ¿Y tú?", E, "I work in a hotel. And you?"),
                ("them", "Yo estudio. Mira, el padre de Lucía.", E, "I study. Look, Lucía's father."),
                ("you", "Buenas noches, señor. ¿Cómo está usted?", E, "Good evening, sir. How are you?"),
                ("them", "Muy bien, gracias. ¿Y usted?", E, "Very well, thank you. And you?"),
                ("you", "Bien, gracias. Bueno, me tengo que ir. ¡Nos vemos!", E,
                 "Fine, thanks. Well, I have to go. See you!"),
            ],
            "patterns": [
                {"text": "Trabajo en {x}.", "reading": E, "en": "I work in {x}.",
                 "kind": "es-workplace",
                 "values": [("un hotel", E, "a hotel"), ("una oficina", E, "an office"),
                            ("un hospital", E, "a hospital"), ("una escuela", E, "a school")]},
                {"text": "¿Cómo {x}?", "reading": E, "en": "How are you? ({x})",
                 "kind": "es-howareyou",
                 "values": [("estás", E, "tú - to a friend"), ("está usted", E, "usted - to an elder"),
                            ("están ustedes", E, "to a group, formally - and any group in Latin America")]},
            ],
            "notes": [
                "The register switch in the middle is the point of this lesson: "
                "tú with Diego, usted with Lucía's father, in the same minute.",
                "Buenas noches is both 'good evening' and 'good night' - after dark "
                "it is the greeting, not only the goodbye.",
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Unit 2 - Moverse por la ciudad
# ---------------------------------------------------------------------------
UNIT_2 = {
    "id": 2,
    "title": "Getting Around",
    "focus": "Find places, ask what there is, say where you are going, and buy a ticket.",
    "gate": {"min_pron_score": 64.0, "min_accuracy": 64.0, "min_completeness": 78.0},
    "lessons": [
        {
            "id": 6,
            "title": "¿Dónde está...?",
            "goal": "Ask where a place is and understand left, right and straight on.",
            "vocab": [
                ("¿dónde está...?", E, "where is...?", ""),
                ("a la derecha", E, "on the right", "a single r between vowels is one tap"),
                ("a la izquierda", E, "on the left", ""),
                ("todo recto", E, "straight ahead", "Mexico also says 'derecho'"),
                ("cerca", E, "near", ""),
                ("lejos", E, "far", "j is a breathy h, from the throat"),
            ],
            "dialogue": [
                ("you", "Perdone, ¿dónde está la estación?", E, "Excuse me, where is the station?"),
                ("them", "Está cerca. Siga todo recto.", E, "It's near. Go straight on."),
                ("you", "¿Todo recto? ¿Y después?", E, "Straight on? And then?"),
                ("them", "Después, a la derecha. Está al lado del banco.", E,
                 "Then right. It's next to the bank."),
                ("you", "A la derecha, al lado del banco. ¿Está lejos?", E,
                 "Right, next to the bank. Is it far?"),
                ("them", "No, está a cinco minutos.", E, "No, it's five minutes away."),
                ("you", "Perfecto. ¿Y dónde está el baño, por favor?", E,
                 "Perfect. And where's the bathroom, please?"),
                ("them", "Allí, a la izquierda.", E, "Over there, on the left."),
            ],
            "patterns": [
                {"text": "¿Dónde está {x}?", "reading": E, "en": "Where is {x}?",
                 "kind": "es-place",
                 "values": [("la estación", E, "the station"), ("el banco", E, "the bank"),
                            ("el baño", E, "the bathroom")]},
                {"text": "Está {x}.", "reading": E, "en": "It's {x}.",
                 "kind": "es-direction",
                 "values": [("a la derecha", E, "on the right"), ("a la izquierda", E, "on the left"),
                            ("todo recto", E, "straight ahead"), ("cerca", E, "near")]},
            ],
            "notes": [
                "Estar is for location: la estación está cerca. Even a building "
                "that has not moved in a century 'está' somewhere.",
                "de + el contracts to del: al lado del banco. de + la does not: "
                "al lado de la farmacia.",
            ],
        },
        {
            "id": 7,
            "title": "¿Hay un... por aquí?",
            "goal": "Ask whether there is something nearby, and tell hay from está.",
            "vocab": [
                ("¿hay...?", E, "is there / are there...?", "the h is silent: 'ai'"),
                ("por aquí", E, "around here", ""),
                ("una farmacia", E, "a pharmacy", ""),
                ("un cajero", E, "a cash machine", ""),
                ("un supermercado", E, "a supermarket", ""),
                ("la calle", E, "the street", ""),
            ],
            "dialogue": [
                ("you", "Disculpe, ¿hay una farmacia por aquí?", E, "Excuse me, is there a pharmacy around here?"),
                ("them", "Sí, hay una en la calle Sol.", E, "Yes, there's one on Sol Street."),
                ("you", "¿Y dónde está la calle Sol?", E, "And where is Sol Street?"),
                ("them", "Es la segunda a la izquierda.", E, "It's the second on the left."),
                ("you", "Gracias. ¿Hay un cajero también?", E, "Thanks. Is there a cash machine too?"),
                ("them", "Hay dos, enfrente del supermercado.", E, "There are two, opposite the supermarket."),
                ("you", "¿El supermercado está en la calle Sol?", E, "Is the supermarket on Sol Street?"),
                ("them", "No, está aquí, en esta calle.", E, "No, it's here, on this street."),
            ],
            "patterns": [
                {"text": "¿Hay {x} por aquí?", "reading": E, "en": "Is there {x} around here?",
                 "kind": "es-indef-place",
                 "values": [("una farmacia", E, "a pharmacy"), ("un cajero", E, "a cash machine"),
                            ("un supermercado", E, "a supermarket"), ("un hotel", E, "a hotel")]},
                {"text": "¿Dónde está {x}?", "reading": E, "en": "Where is {x}?",
                 "kind": "es-place",
                 "values": [("la farmacia", E, "the pharmacy"), ("la calle Sol", E, "Sol Street"),
                            ("el supermercado", E, "the supermarket")]},
            ],
            "notes": [
                "Hay + un/una: is there a...? Está + el/la: where is the...? "
                "You ask with hay when you do not know one exists, with está when "
                "you do. 'Hay el banco' is the classic beginner slip.",
                "Hay never changes: hay una farmacia, hay dos cajeros.",
            ],
        },
        {
            "id": 8,
            "title": "Voy a...",
            "goal": "Say where you are going and ask how to get there.",
            "vocab": [
                ("voy a", E, "I'm going to", ""),
                ("¿adónde vas?", E, "where are you going? (tú)", ""),
                ("el centro", E, "the town centre", ""),
                ("la playa", E, "the beach", ""),
                ("en autobús", E, "by bus", "b and v sound the same in Spanish"),
                ("andando", E, "on foot", "Mexico also says 'caminando'"),
            ],
            "dialogue": [
                ("them", "¡Hola! ¿Adónde vas?", E, "Hi! Where are you going?"),
                ("you", "Voy al centro. ¿Y tú?", E, "I'm going to the centre. And you?"),
                ("them", "Voy a la playa con mi hermana.", E, "I'm going to the beach with my sister."),
                ("you", "¡Qué bien! ¿Vas en autobús?", E, "Nice! Are you going by bus?"),
                ("them", "No, vamos andando. Está cerca. ¿Y tú, cómo vas?", E,
                 "No, we're walking. It's close. And you, how are you getting there?"),
                ("you", "Voy en metro. El centro está lejos.", E, "I'm going by metro. The centre is far."),
                ("them", "La parada de metro está allí.", E, "The metro stop is over there."),
                ("you", "Gracias. ¡Que te vaya bien en la playa!", E, "Thanks. Have a good time at the beach!"),
            ],
            "patterns": [
                {"text": "Voy {x}.", "reading": E, "en": "I'm going {x}.",
                 "kind": "es-to-place",
                 "values": [("al centro", E, "to the centre"), ("a la playa", E, "to the beach"),
                            ("al banco", E, "to the bank"), ("a la estación", E, "to the station")]},
                {"text": "Voy {x}.", "reading": E, "en": "I'm going {x}.",
                 "kind": "es-transport",
                 "values": [("en autobús", E, "by bus"), ("en metro", E, "by metro"),
                            ("en taxi", E, "by taxi"), ("andando", E, "on foot")]},
            ],
            "notes": [
                "a + el contracts to al: voy al centro. a + la does not: voy a la "
                "playa. Same rule as del in lesson 6.",
                "Voy, vas, va, vamos: ir is irregular and too common to avoid. "
                "Learn the four forms as four words.",
            ],
        },
        {
            "id": 9,
            "title": "Un billete, por favor",
            "goal": "Buy a ticket: numbers to twenty, one-way or return, and the price.",
            "vocab": [
                ("un billete", E, "a ticket", "Latin America mostly says 'un boleto'"),
                ("de ida", E, "one-way", ""),
                ("de ida y vuelta", E, "return", ""),
                ("¿cuánto cuesta?", E, "how much is it?", ""),
                ("euros / pesos", E, "euros / pesos", ""),
                ("¿a qué hora sale?", E, "what time does it leave?", ""),
            ],
            "dialogue": [
                ("them", "Buenos días, ¿qué desea?", E, "Good morning, what would you like?"),
                ("you", "Un billete para Toledo, por favor.", E, "A ticket to Toledo, please."),
                ("them", "¿De ida o de ida y vuelta?", E, "One-way or return?"),
                ("you", "De ida y vuelta. ¿Cuánto cuesta?", E, "Return. How much is it?"),
                ("them", "Son doce euros.", E, "That's twelve euros."),
                ("you", "Doce euros. ¿A qué hora sale el tren?", E, "Twelve euros. What time does the train leave?"),
                ("them", "Sale a las diez, del andén tres.", E, "It leaves at ten, from platform three."),
                ("you", "A las diez, andén tres. Muchas gracias.", E, "At ten, platform three. Thank you very much."),
            ],
            "patterns": [
                {"text": "Un billete para {x}, por favor.", "reading": E, "en": "A ticket to {x}, please.",
                 "kind": "es-city",
                 "values": [("Toledo", E, "Toledo"), ("Sevilla", E, "Seville"),
                            ("Salamanca", E, "Salamanca")]},
                {"text": "Son {x} euros.", "reading": E, "en": "It's {x} euros.",
                 "kind": "es-number",
                 "values": [("cinco", E, "five"), ("doce", E, "twelve"), ("quince", E, "fifteen"),
                            ("veinte", E, "twenty")]},
            ],
            "notes": [
                "Uno to quince are one word each and have to be learned: uno, dos, "
                "tres, cuatro, cinco, seis, siete, ocho, nueve, diez, once, doce, "
                "trece, catorce, quince. From sixteen they build: dieciséis.",
                "Times use la/las: a la una, a las dos, a las diez.",
            ],
        },
        {
            "id": 10,
            "title": "Repaso: en la estación",
            "goal": "Find the station, buy a ticket, and find your platform without English.",
            "vocab": [
                ("el andén", E, "the platform", ""),
                ("el tren", E, "the train", ""),
                ("la taquilla", E, "the ticket office", ""),
                ("¿este tren va a...?", E, "does this train go to...?", ""),
                ("ahora", E, "now", "the h is silent: a-o-ra"),
                ("tarde", E, "late", ""),
            ],
            "dialogue": [
                ("you", "Perdone, ¿hay una taquilla por aquí?", E, "Excuse me, is there a ticket office around here?"),
                ("them", "Sí, está allí, a la derecha.", E, "Yes, it's over there, on the right."),
                ("you", "Gracias. Un billete de ida para Sevilla, por favor.", E,
                 "Thanks. A one-way ticket to Seville, please."),
                ("them", "Son veinte euros. Sale del andén dos.", E, "Twenty euros. It leaves from platform two."),
                ("you", "¿Dónde está el andén dos?", E, "Where is platform two?"),
                ("them", "Todo recto y a la izquierda. Pero sale ahora.", E,
                 "Straight on and left. But it's leaving now."),
                ("you", "¡Uy, voy tarde! ¿Este tren va a Sevilla?", E, "Oh, I'm late! Does this train go to Seville?"),
                ("them", "Sí, sí, ¡suba!", E, "Yes, yes, get on!"),
            ],
            "patterns": [
                {"text": "¿Este tren va a {x}?", "reading": E, "en": "Does this train go to {x}?",
                 "kind": "es-city",
                 "values": [("Sevilla", E, "Seville"), ("Madrid", E, "Madrid"),
                            ("Valencia", E, "Valencia")]},
                {"text": "¿Dónde está {x}?", "reading": E, "en": "Where is {x}?",
                 "kind": "es-place",
                 "values": [("el andén dos", E, "platform two"), ("la taquilla", E, "the ticket office"),
                            ("el tren", E, "the train")]},
            ],
            "notes": [
                "Nothing new to learn here except four words. Everything else is "
                "lessons 6 to 9, in a different order - which is the test.",
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Unit 3 - Comer y beber
# ---------------------------------------------------------------------------
UNIT_3 = {
    "id": 3,
    "title": "Food & Drink",
    "focus": "Say what you want, order in a café and a restaurant, say what you like, and pay.",
    "gate": {"min_pron_score": 66.0, "min_accuracy": 66.0, "min_completeness": 80.0},
    "lessons": [
        {
            "id": 11,
            "title": "Tengo hambre",
            "goal": "Say you are hungry, thirsty or tired, and what you want to do about it.",
            "vocab": [
                ("tengo hambre", E, "I'm hungry", "literally 'I have hunger'"),
                ("tengo sed", E, "I'm thirsty", ""),
                ("estoy cansado / cansada", E, "I'm tired", ""),
                ("quiero", E, "I want", ""),
                ("comer", E, "to eat", ""),
                ("beber / tomar", E, "to drink / to have", ""),
            ],
            "dialogue": [
                ("them", "¿Qué te pasa? ¿Estás bien?", E, "What's up? Are you OK?"),
                ("you", "Estoy cansado y tengo hambre.", E, "I'm tired and I'm hungry."),
                ("them", "Yo también. ¿Quieres comer algo?", E, "Me too. Do you want to eat something?"),
                ("you", "Sí, quiero comer. Y tengo sed.", E, "Yes, I want to eat. And I'm thirsty."),
                ("them", "Hay un café aquí al lado.", E, "There's a café right next door."),
                ("you", "Perfecto. Quiero tomar un café.", E, "Perfect. I want to have a coffee."),
                ("them", "¿No tienes hambre? ¡Es la una!", E, "Aren't you hungry? It's one o'clock!"),
                ("you", "Sí, tengo mucha hambre. Vamos.", E, "Yes, I'm very hungry. Let's go."),
            ],
            "patterns": [
                {"text": "Tengo {x}.", "reading": E, "en": "I'm {x}.",
                 "kind": "es-tener-state",
                 "values": [("hambre", E, "hungry"), ("sed", E, "thirsty"), ("frío", E, "cold"),
                            ("calor", E, "hot")]},
                {"text": "Quiero {x}.", "reading": E, "en": "I want {x}.",
                 "kind": "es-infinitive",
                 "values": [("comer", E, "to eat"), ("tomar un café", E, "to have a coffee"),
                            ("ir al centro", E, "to go to the centre")]},
            ],
            "notes": [
                "Hunger, thirst, cold, heat and age are things you have in Spanish: "
                "tengo hambre, tengo frío, tengo treinta años. Tired is a state "
                "you are in: estoy cansado.",
                "Mucha hambre, not mucho: hambre is feminine even though it takes "
                "'el' in front (el hambre). That is a quirk worth one note, no more.",
            ],
        },
        {
            "id": 12,
            "title": "En el café",
            "goal": "Order a drink and something to eat, with un and una.",
            "vocab": [
                ("para mí", E, "for me", ""),
                ("un café con leche", E, "a white coffee", ""),
                ("una tostada", E, "a piece of toast", ""),
                ("un zumo de naranja", E, "an orange juice", "Latin America: 'un jugo'"),
                ("¿algo más?", E, "anything else?", ""),
                ("nada más", E, "nothing else", ""),
            ],
            "dialogue": [
                ("them", "Buenos días. ¿Qué le pongo?", E, "Good morning. What can I get you?"),
                ("you", "Para mí, un café con leche, por favor.", E, "For me, a white coffee, please."),
                ("them", "Muy bien. ¿Algo para comer?", E, "Very good. Anything to eat?"),
                ("you", "Sí, una tostada con tomate.", E, "Yes, a piece of toast with tomato."),
                ("them", "¿Y para su amiga?", E, "And for your friend?"),
                ("you", "Para ella, un zumo de naranja.", E, "For her, an orange juice."),
                ("them", "¿Algo más?", E, "Anything else?"),
                ("you", "No, nada más, gracias.", E, "No, nothing else, thanks."),
            ],
            "patterns": [
                {"text": "Para mí, {x}, por favor.", "reading": E, "en": "For me, {x}, please.",
                 "kind": "es-order",
                 "values": [("un café", E, "a coffee"), ("una cerveza", E, "a beer"),
                            ("un té", E, "a tea"), ("una tostada", E, "a piece of toast")]},
                {"text": "Quiero {x}, por favor.", "reading": E, "en": "I'd like {x}, please.",
                 "kind": "es-order",
                 "values": [("un zumo de naranja", E, "an orange juice"), ("agua", E, "water"),
                            ("un croissant", E, "a croissant")]},
            ],
            "notes": [
                "Every noun is masculine or feminine and the article tells you "
                "which: un café, una cerveza. Learn the article with the noun, "
                "always - 'café' alone is half a word.",
                "Ella (her) after para: para ella, para él, para mí. Mí takes an "
                "accent; mi (my) does not.",
            ],
        },
        {
            "id": 13,
            "title": "Me gusta",
            "goal": "Say what you like and do not like, with gusta and gustan.",
            "vocab": [
                ("me gusta", E, "I like (one thing)", ""),
                ("me gustan", E, "I like (several things)", ""),
                ("no me gusta", E, "I don't like", ""),
                ("¿te gusta...?", E, "do you like...? (tú)", ""),
                ("el pescado", E, "fish (as food)", ""),
                ("las verduras", E, "vegetables", ""),
            ],
            "dialogue": [
                ("them", "¿Te gusta la comida mexicana?", E, "Do you like Mexican food?"),
                ("you", "Sí, me gusta mucho. ¿Y a ti?", E, "Yes, I like it a lot. And you?"),
                ("them", "Me encanta. ¿Te gustan los tacos de pescado?", E, "I love it. Do you like fish tacos?"),
                ("you", "No, no me gusta el pescado.", E, "No, I don't like fish."),
                ("them", "¿Y las verduras?", E, "And vegetables?"),
                ("you", "Sí, me gustan las verduras. Y me gusta el picante.", E,
                 "Yes, I like vegetables. And I like spicy food."),
                ("them", "Entonces, tacos de verduras con salsa verde.", E,
                 "Then vegetable tacos with green salsa."),
                ("you", "¡Me gustan los tacos de verduras!", E, "I like vegetable tacos!"),
            ],
            "patterns": [
                {"text": "Me gusta {x}.", "reading": E, "en": "I like {x}.",
                 "kind": "es-like-one",
                 "values": [("el café", E, "coffee"), ("la música", E, "music"),
                            ("el pescado", E, "fish"), ("la playa", E, "the beach")]},
                {"text": "Me gustan {x}.", "reading": E, "en": "I like {x}.",
                 "kind": "es-like-many",
                 "values": [("las verduras", E, "vegetables"), ("los tacos", E, "tacos"),
                            ("los perros", E, "dogs")]},
            ],
            "notes": [
                "Gustar works backwards: the thing liked is the subject. 'Me gusta "
                "el café' is 'coffee pleases me', so more than one thing pleases "
                "you in the plural: me gustan las verduras.",
                "Things you like in general take the article: me gusta el café, not "
                "'me gusta café'.",
            ],
        },
        {
            "id": 14,
            "title": "La cuenta, por favor",
            "goal": "Ask for the bill, understand prices to a hundred, and pay.",
            "vocab": [
                ("la cuenta", E, "the bill", ""),
                ("¿me trae la cuenta?", E, "could you bring me the bill? (usted)", ""),
                ("con tarjeta", E, "by card", ""),
                ("en efectivo", E, "in cash", ""),
                ("la propina", E, "the tip", ""),
                ("treinta, cuarenta, cincuenta", E, "thirty, forty, fifty", ""),
            ],
            "dialogue": [
                ("you", "Perdone, ¿me trae la cuenta, por favor?", E, "Excuse me, could you bring the bill, please?"),
                ("them", "Ahora mismo.", E, "Right away."),
                ("them", "Son treinta y cinco euros.", E, "That's thirty-five euros."),
                ("you", "¿Treinta y cinco? ¿Puedo pagar con tarjeta?", E, "Thirty-five? Can I pay by card?"),
                ("them", "Sí, claro. ¿Juntos o separados?", E, "Yes, of course. Together or separately?"),
                ("you", "Juntos, por favor. Pago yo.", E, "Together, please. I'm paying."),
                ("them", "Muy bien. Aquí tiene.", E, "Very good. Here you are."),
                ("you", "Gracias. Y esto es para usted, la propina.", E, "Thank you. And this is for you, the tip."),
            ],
            "patterns": [
                {"text": "¿Puedo pagar {x}?", "reading": E, "en": "Can I pay {x}?",
                 "kind": "es-payment",
                 "values": [("con tarjeta", E, "by card"), ("en efectivo", E, "in cash"),
                            ("con el móvil", E, "with my phone")]},
                {"text": "Son {x} euros.", "reading": E, "en": "It's {x} euros.",
                 "kind": "es-number",
                 "values": [("treinta y cinco", E, "thirty-five"), ("cuarenta", E, "forty"),
                            ("cincuenta y dos", E, "fifty-two"), ("cien", E, "a hundred")]},
            ],
            "notes": [
                "From thirty on, numbers are tens + y + units, written apart: "
                "treinta y cinco. Below thirty they are one word: veinticinco.",
                "¿Me trae...? (usted) is the polite ask to staff. ¿Me traes...? "
                "is the same to a friend.",
            ],
        },
        {
            "id": 15,
            "title": "Repaso: en el restaurante",
            "goal": "A whole meal: a table, order for two, say what you like, and pay.",
            "vocab": [
                ("una mesa para dos", E, "a table for two", ""),
                ("de primero", E, "as a starter", ""),
                ("de segundo", E, "as a main course", ""),
                ("el postre", E, "dessert", ""),
                ("¿qué me recomienda?", E, "what do you recommend? (usted)", ""),
                ("está muy rico", E, "it's delicious", ""),
            ],
            "dialogue": [
                ("you", "Buenas noches. Una mesa para dos, por favor.", E, "Good evening. A table for two, please."),
                ("them", "Por aquí. ¿Qué van a tomar?", E, "This way. What will you have?"),
                ("you", "¿Qué me recomienda?", E, "What do you recommend?"),
                ("them", "El pescado está muy bueno hoy.", E, "The fish is very good today."),
                ("you", "No me gusta el pescado. De primero, una sopa.", E,
                 "I don't like fish. For starter, a soup."),
                ("them", "¿Y de segundo?", E, "And for the main course?"),
                ("you", "De segundo, pollo con verduras. Y para ella, el pescado.", E,
                 "For main, chicken with vegetables. And for her, the fish."),
                ("them", "¿Qué tal todo?", E, "How is everything?"),
                ("you", "Está muy rico, gracias. ¿Me trae la cuenta?", E,
                 "It's delicious, thank you. Could you bring the bill?"),
            ],
            "patterns": [
                {"text": "De primero, {x}.", "reading": E, "en": "As a starter, {x}.",
                 "kind": "es-order",
                 "values": [("una sopa", E, "a soup"), ("una ensalada", E, "a salad"),
                            ("un gazpacho", E, "a gazpacho")]},
                {"text": "Una mesa para {x}, por favor.", "reading": E, "en": "A table for {x}, please.",
                 "kind": "es-number",
                 "values": [("dos", E, "two"), ("cuatro", E, "four"), ("seis", E, "six")]},
            ],
            "notes": [
                "Rico for food is 'delicious', not 'rich'. Está muy rico is what "
                "you say to the waiter, and they will be pleased.",
            ],
        },
    ],
}

UNITS = [UNIT_1, UNIT_2, UNIT_3]

LEVEL = {
    "band": 1,
    "id": 1,
    "code": "A1",
    "title": "CEFR A1 · First contact",
    "focus": "Meet people in both registers, find your way, buy a ticket, order, say what you like, pay.",
    "gate": {"min_pron_score": 62.0, "min_accuracy": 62.0, "min_completeness": 78.0},
    "units": [dict(u, band=1) for u in UNITS],
}

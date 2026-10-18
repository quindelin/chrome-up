# -*- coding: utf-8 -*-
"""CEFR A1 word bank: 96 words in six topics (people has twenty-one).

Sized to the lessons, on purpose. `Course.vocab_for_lesson` hands each lesson
the next `vocab.inject_per_lesson` words of the band (6 in config.es.yaml),
so 16 lessons x 6 = 96: walking A1 in order meets every word here exactly
once inside a lesson, and the topic order follows the units - people for
unit 1, places and numbers for unit 2, food and verbs for unit 3. The
Japanese N5 bank is 341 words fed four at a time to 15 lessons; 60 of them
are ever reached.

People has six more than the other topics: lesson 5 (describing people)
made A1 sixteen lessons, and those six are the words for looks.

Nouns carry their article. A Spanish noun without el/la is half a word, and
the drills never have to guess a gender.

No word here repeats a lesson's own vocab list (smoke test checks it).
"""
E = ""

TOPICS = [
    {
        "id": "a1-people",
        "title": "People & Family",
        "title_native": "Personas y familia",
        "words": [
            ("el padre", E, "father"),
            ("la madre", E, "mother"),
            ("el hermano", E, "brother"),
            ("la hermana", E, "sister"),
            ("el hijo", E, "son"),
            ("la hija", E, "daughter"),
            ("el marido", E, "husband"),
            ("la mujer", E, "wife; woman"),
            ("el novio / la novia", E, "boyfriend / girlfriend"),
            ("el niño / la niña", E, "boy / girl, child"),
            ("la gente", E, "people (singular in Spanish)"),
            ("el vecino / la vecina", E, "neighbour"),
            ("el compañero de trabajo", E, "colleague"),
            ("simpático / simpática", E, "nice, friendly"),
            ("joven", E, "young"),
            ("rubio / rubia", E, "blond, fair-haired"),
            ("moreno / morena", E, "dark-haired; tanned", "in Spain mostly hair, not skin"),
            ("guapo / guapa", E, "good-looking", "Spain also uses it as a friendly 'love': ¡hola, guapa!"),
            ("delgado / delgada", E, "slim, thin"),
            ("las gafas", E, "glasses", "Latin America: los lentes / los anteojos"),
            ("la barba", E, "beard"),
        ],
    },
    {
        "id": "a1-work-world",
        "title": "Jobs & Countries",
        "title_native": "Trabajos y países",
        "words": [
            ("el profesor / la profesora", E, "teacher"),
            ("el médico / la médica", E, "doctor"),
            ("el camarero / la camarera", E, "waiter / waitress"),
            ("el estudiante", E, "student"),
            ("el ingeniero / la ingeniera", E, "engineer"),
            ("la oficina", E, "office"),
            ("la empresa", E, "company"),
            ("España", E, "Spain"),
            ("México", E, "Mexico", "the x is a j sound: Méjico"),
            ("estadounidense", E, "American (from the US)", "same form for men and women"),
            ("inglés / inglesa", E, "English"),
            ("el idioma", E, "language", "masculine despite the -a"),
            ("hablar", E, "to speak"),
            ("vivir", E, "to live"),
            ("trabajar", E, "to work"),
        ],
    },
    {
        "id": "a1-town",
        "title": "Around Town",
        "title_native": "En la ciudad",
        "words": [
            ("la plaza", E, "square"),
            ("el parque", E, "park"),
            ("el museo", E, "museum"),
            ("la iglesia", E, "church"),
            ("el mercado", E, "market"),
            ("la tienda", E, "shop"),
            ("el hospital", E, "hospital", "silent h: ospital"),
            ("el aeropuerto", E, "airport"),
            ("la parada de autobús", E, "bus stop"),
            ("el semáforo", E, "traffic lights"),
            ("la esquina", E, "corner"),
            ("enfrente de", E, "opposite"),
            ("al lado de", E, "next to"),
            ("allí", E, "over there"),
            ("aquí", E, "here"),
        ],
    },
    {
        "id": "a1-numbers-time",
        "title": "Numbers & Time",
        "title_native": "Números y horas",
        "words": [
            ("cero", E, "zero"),
            ("dieciséis", E, "sixteen"),
            ("veintiuno", E, "twenty-one"),
            ("sesenta", E, "sixty"),
            ("setenta", E, "seventy"),
            ("ochenta", E, "eighty"),
            ("noventa", E, "ninety"),
            ("la hora", E, "hour; the time", "silent h"),
            ("y media", E, "half past"),
            ("y cuarto", E, "quarter past"),
            ("menos cuarto", E, "quarter to"),
            ("hoy", E, "today"),
            ("mañana", E, "tomorrow; morning"),
            ("la semana", E, "week"),
            ("el fin de semana", E, "weekend"),
        ],
    },
    {
        "id": "a1-food",
        "title": "Food & Drink",
        "title_native": "Comida y bebida",
        "words": [
            ("el agua", E, "water", "feminine - el only to avoid 'la a-'"),
            ("el vino", E, "wine"),
            ("la cerveza", E, "beer"),
            ("el pan", E, "bread"),
            ("el queso", E, "cheese"),
            ("el jamón", E, "ham"),
            ("el pollo", E, "chicken"),
            ("la carne", E, "meat"),
            ("el arroz", E, "rice"),
            ("la fruta", E, "fruit"),
            ("la ensalada", E, "salad"),
            ("los huevos", E, "eggs", "silent h: uevos"),
            ("el azúcar", E, "sugar"),
            ("caliente", E, "hot (temperature)"),
            ("frío / fría", E, "cold"),
        ],
    },
    {
        "id": "a1-verbs",
        "title": "Everyday Verbs",
        "title_native": "Verbos de todos los días",
        "words": [
            ("necesito", E, "I need"),
            ("puedo", E, "I can"),
            ("tengo", E, "I have"),
            ("hago", E, "I do / I make"),
            ("salgo", E, "I go out / I leave"),
            ("vengo", E, "I come"),
            ("conozco", E, "I know (a person, a place)"),
            ("sé", E, "I know (a fact)", "the accent tells it from se"),
            ("busco", E, "I'm looking for"),
            ("compro", E, "I buy"),
            ("pago", E, "I pay"),
            ("llego", E, "I arrive"),
            ("abre", E, "it opens"),
            ("cierra", E, "it closes", "rr is a trill: roll it"),
            ("me gustaría", E, "I would like"),
        ],
    },
]

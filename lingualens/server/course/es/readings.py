# -*- coding: utf-8 -*-
"""Graded reading and listening for the Spanish course.

Same contract as `course.ja.readings`:

    PASSAGES[lesson_id] = {"title", "title_en",
                           "chunks": [(text, reading, en), ...],
                           "questions": [{"q", "q_reading", "q_en", "a", "a_reading",
                                          "a_en", "keywords", "min_chars"}, ...]}

Two rules that the engine depends on, checked by `check()`:
  * questions[0] is answered from the passage you just READ.
  * questions[1] is answered from the LAST chunk alone, because the listening
    step plays only chunks[-1] with the screen blank and then asks it.

Passages use only the lesson's words and earlier ones, plus at most one new
word you can guess. Each chunk is one sentence, under ~70 characters.

A1 passages live here; A2-C2 passages live in their band files and are
merged in below.

Verify with:  .venv/bin/python -m server.course.es.readings
"""
E = ""


def _q(q, q_en, a, a_en, keywords, min_chars=8):
    return {"q": q, "q_reading": E, "q_en": q_en, "a": a, "a_reading": E,
            "a_en": a_en, "keywords": keywords, "min_chars": min_chars}


PASSAGES = {
    1: {"title": "Por la mañana", "title_en": "In the morning",
        "chunks": [("Ana sale de casa a las ocho.", E, "Ana leaves home at eight."),
                   ("En la escalera ve a su vecino Pablo.", E, "On the stairs she sees her neighbour Pablo."),
                   ("—¡Hola, Pablo! ¿Qué tal?", E, "'Hi, Pablo! How are things?'"),
                   ("—Bien, pero estoy un poco cansado. ¡Hasta luego!", E,
                    "'Fine, but I'm a little tired. See you later!'")],
        "questions": [_q("¿A quién ve Ana en la escalera?", "Who does Ana see on the stairs?",
                         "Ve a su vecino Pablo.", "She sees her neighbour Pablo.", ["vecino", "Pablo"]),
                      _q("¿Cómo está Pablo?", "How is Pablo?",
                         "Está un poco cansado.", "He's a little tired.", ["cansado"])]},
    2: {"title": "En la fiesta", "title_en": "At the party",
        "chunks": [("Lucía tiene una fiesta en su casa.", E, "Lucía is having a party at her house."),
                   ("Sam no conoce a nadie.", E, "Sam doesn't know anyone."),
                   ("Lucía dice: «Sam, esta es la señora Ruiz».", E, "Lucía says: 'Sam, this is Mrs Ruiz.'"),
                   ("Sam dice: «Encantado, señora. Me llamo Sam».", E,
                    "Sam says: 'Delighted, madam. My name is Sam.'")],
        "questions": [_q("¿Dónde es la fiesta?", "Where is the party?",
                         "Es en la casa de Lucía.", "It's at Lucía's house.", ["casa", "Lucía"]),
                      _q("¿Qué dice Sam a la señora?", "What does Sam say to the lady?",
                         "Dice encantado, me llamo Sam.", "He says delighted, my name is Sam.",
                         ["encantado", "llamo"])]},
    3: {"title": "Dos ciudades", "title_en": "Two cities",
        "chunks": [("Marta es de Guadalajara, en México.", E, "Marta is from Guadalajara, in Mexico."),
                   ("Ahora vive en Madrid y estudia inglés.", E, "Now she lives in Madrid and studies English."),
                   ("Su hermano Luis vive en Chicago.", E, "Her brother Luis lives in Chicago."),
                   ("Luis trabaja en un hotel muy grande.", E, "Luis works in a very big hotel.")],
        "questions": [_q("¿De dónde es Marta?", "Where is Marta from?",
                         "Es de Guadalajara, en México.", "She's from Guadalajara, in Mexico.",
                         ["Guadalajara", "México"]),
                      _q("¿Dónde trabaja Luis?", "Where does Luis work?",
                         "Trabaja en un hotel.", "He works in a hotel.", ["hotel"])]},
    4: {"title": "Un poco de español", "title_en": "A little Spanish",
        "chunks": [("Tom es inglés y habla un poco de español.", E, "Tom is English and speaks a little Spanish."),
                   ("Un señor le pregunta por una calle.", E, "A man asks him about a street."),
                   ("Tom no entiende y dice: «Más despacio, por favor».", E,
                    "Tom doesn't understand and says: 'More slowly, please.'"),
                   ("El señor repite la pregunta otra vez, muy despacio.", E,
                    "The man repeats the question again, very slowly.")],
        "questions": [_q("¿Qué idioma habla Tom un poco?", "Which language does Tom speak a little?",
                         "Habla un poco de español.", "He speaks a little Spanish.", ["español", "poco"]),
                      _q("¿Cómo repite el señor la pregunta?", "How does the man repeat the question?",
                         "La repite muy despacio.", "He repeats it very slowly.", ["despacio"])]},
    6: {"title": "Nuevos amigos", "title_en": "New friends",
        "chunks": [("En la fiesta, Sam habla con Diego.", E, "At the party, Sam talks with Diego."),
                   ("Diego es estudiante y Sam trabaja en un hotel.", E, "Diego is a student and Sam works in a hotel."),
                   ("Después, Sam habla con el padre de Lucía.", E, "Afterwards, Sam talks with Lucía's father."),
                   ("A las once, Sam dice: «Me tengo que ir».", E, "At eleven, Sam says: 'I have to go.'")],
        "questions": [_q("¿Qué hace Diego?", "What does Diego do?",
                         "Diego es estudiante.", "Diego is a student.", ["estudiante"]),
                      _q("¿Qué dice Sam a las once?", "What does Sam say at eleven?",
                         "Dice que se tiene que ir.", "He says he has to go.", ["tengo", "ir"])]},
    5: {"title": "La foto de la boda", "title_en": "The wedding photo",
        "chunks": [("En la foto hay tres personas.", E, "There are three people in the photo."),
                   ("Mi primo Andrés es alto y tiene barba.", E, "My cousin Andrés is tall and has a beard."),
                   ("Su novia, Clara, es baja y tiene el pelo rizado.", E,
                    "His girlfriend Clara is short and has curly hair."),
                   ("Mi tía Rosa está bailando con un niño.", E, "My aunt Rosa is dancing with a little boy.")],
        "questions": [_q("¿Cómo es Andrés?", "What is Andrés like?",
                         "Es alto y tiene barba.", "He's tall and has a beard.", ["alto", "barba"]),
                      _q("¿Qué está haciendo Rosa?", "What is Rosa doing?",
                         "Está bailando con un niño.", "She's dancing with a little boy.", ["bailando"])]},
    7: {"title": "La estación", "title_en": "The station",
        "chunks": [("Estoy en una ciudad nueva y busco la estación.", E,
                    "I'm in a new city and I'm looking for the station."),
                   ("Una señora me dice: «Siga todo recto y gire a la derecha».", E,
                    "A woman tells me: 'Go straight on and turn right.'"),
                   ("La estación está al lado de un banco.", E, "The station is next to a bank."),
                   ("No está lejos: está a cinco minutos.", E, "It isn't far: it's five minutes away.")],
        "questions": [_q("¿Qué hay al lado de la estación?", "What is next to the station?",
                         "Hay un banco.", "There's a bank.", ["banco"], 6),
                      _q("¿Está lejos la estación?", "Is the station far?",
                         "No, está a cinco minutos.", "No, it's five minutes away.", ["cinco", "minutos"])]},
    8: {"title": "Mi calle", "title_en": "My street",
        "chunks": [("En mi calle hay muchas tiendas.", E, "On my street there are lots of shops."),
                   ("Hay una farmacia, un supermercado y dos cafés.", E,
                    "There's a pharmacy, a supermarket and two cafés."),
                   ("El supermercado está enfrente de mi casa.", E, "The supermarket is opposite my house."),
                   ("Los domingos, la farmacia está de guardia.", E, "On Sundays, the pharmacy is on duty."),
                   ("Pero no hay un cajero; está en la calle Sol.", E,
                    "But there's no cash machine; it's on Sol Street.")],
        "questions": [_q("¿Cuántos cafés hay en la calle?", "How many cafés are there on the street?",
                         "Hay dos cafés.", "There are two cafés.", ["dos", "cafés"], 6),
                      _q("¿Dónde está el cajero?", "Where is the cash machine?",
                         "Está en la calle Sol.", "It's on Sol Street.", ["calle", "Sol"])]},
    9: {"title": "El sábado", "title_en": "On Saturday",
        "chunks": [("El sábado, Clara va a la playa con su hermana.", E,
                    "On Saturday, Clara goes to the beach with her sister."),
                   ("Van andando porque la playa está cerca.", E, "They walk because the beach is close."),
                   ("Su amigo Jorge no va a la playa.", E, "Her friend Jorge isn't going to the beach."),
                   ("Jorge va al centro en metro.", E, "Jorge goes to the centre by metro.")],
        "questions": [_q("¿Con quién va Clara a la playa?", "Who does Clara go to the beach with?",
                         "Va con su hermana.", "She goes with her sister.", ["hermana"]),
                      _q("¿Cómo va Jorge al centro?", "How does Jorge get to the centre?",
                         "Va en metro.", "He goes by metro.", ["metro"], 6)]},
    10: {"title": "Un viaje a Toledo", "title_en": "A trip to Toledo",
        "chunks": [("Quiero ir a Toledo el domingo.", E, "I want to go to Toledo on Sunday."),
                   ("En la taquilla compro un billete de ida y vuelta.", E,
                    "At the ticket office I buy a return ticket."),
                   ("Cuesta doce euros.", E, "It costs twelve euros."),
                   ("El tren sale a las diez del andén tres.", E, "The train leaves at ten from platform three.")],
        "questions": [_q("¿Cuánto cuesta el billete?", "How much is the ticket?",
                         "Cuesta doce euros.", "It costs twelve euros.", ["doce", "euros"]),
                      _q("¿A qué hora sale el tren?", "What time does the train leave?",
                         "Sale a las diez.", "It leaves at ten.", ["diez"], 6)]},
    11: {"title": "¡Tarde!", "title_en": "Late!",
         "chunks": [("Llego a la estación a las nueve menos cinco.", E,
                     "I arrive at the station at five to nine."),
                    ("Mi tren a Sevilla sale a las nueve.", E, "My train to Seville leaves at nine."),
                    ("Compro el billete y busco el andén dos.", E, "I buy the ticket and look for platform two."),
                    ("Un señor me dice: «¡Rápido, el tren sale ahora!»", E,
                     "A man tells me: 'Quick, the train is leaving now!'")],
         "questions": [_q("¿Adónde va el tren?", "Where does the train go?",
                          "Va a Sevilla.", "It goes to Seville.", ["Sevilla"], 6),
                       _q("¿Qué dice el señor?", "What does the man say?",
                          "Dice que el tren sale ahora.", "He says the train is leaving now.",
                          ["sale", "ahora"])]},
    12: {"title": "La hora de comer", "title_en": "Lunchtime",
         "chunks": [("Es la una y media y tengo mucha hambre.", E, "It's half past one and I'm very hungry."),
                    ("Mi amiga Eva tiene sed y está cansada.", E, "My friend Eva is thirsty and tired."),
                    ("Hay un café aquí al lado.", E, "There's a café right next door."),
                    ("Eva quiere tomar un agua y yo quiero comer.", E, "Eva wants to have a water and I want to eat.")],
         "questions": [_q("¿Qué hora es?", "What time is it?",
                          "Es la una y media.", "It's half past one.", ["una", "media"]),
                       _q("¿Qué quiere tomar Eva?", "What does Eva want to have?",
                          "Quiere tomar un agua.", "She wants a water.", ["agua"])]},
    13: {"title": "El desayuno", "title_en": "Breakfast",
         "chunks": [("Cada mañana desayuno en el café de la esquina.", E,
                     "Every morning I have breakfast in the café on the corner."),
                    ("El camarero se llama Paco y es muy simpático.", E,
                     "The waiter is called Paco and he's very friendly."),
                    ("Para mí, un café con leche y una tostada.", E, "For me, a white coffee and a piece of toast."),
                    ("Mi amiga siempre pide un zumo de naranja.", E, "My friend always orders an orange juice.")],
         "questions": [_q("¿Cómo se llama el camarero?", "What is the waiter called?",
                          "Se llama Paco.", "He's called Paco.", ["Paco"], 6),
                       _q("¿Qué pide la amiga?", "What does the friend order?",
                          "Pide un zumo de naranja.", "She orders an orange juice.", ["zumo", "naranja"])]},
    14: {"title": "Gustos", "title_en": "Tastes",
         "chunks": [("A Raúl le gusta mucho la comida mexicana.", E, "Raúl really likes Mexican food."),
                    ("Le gustan los tacos y le gusta el picante.", E, "He likes tacos and he likes spicy food."),
                    ("A su novia no le gusta el picante.", E, "His girlfriend doesn't like spicy food."),
                    ("A ella le gustan las verduras y el pescado.", E, "She likes vegetables and fish.")],
         "questions": [_q("¿Qué comida le gusta a Raúl?", "What food does Raúl like?",
                          "Le gusta la comida mexicana.", "He likes Mexican food.", ["mexicana"]),
                       _q("¿Qué le gusta a la novia?", "What does the girlfriend like?",
                          "Le gustan las verduras y el pescado.", "She likes vegetables and fish.",
                          ["verduras", "pescado"])]},
    15: {"title": "El mercado", "title_en": "The market",
         "chunks": [("Los sábados compro en el mercado del barrio.", E, "On Saturdays I shop at the local market."),
                    ("Pido un kilo de tomates y media docena de huevos.", E,
                     "I ask for a kilo of tomatoes and half a dozen eggs."),
                    ("El jamón ibérico está a noventa euros el kilo.", E, "Iberian ham is ninety euros a kilo."),
                    ("Por eso solo compro cien gramos.", E, "That's why I only buy a hundred grams.")],
         "questions": [_q("¿Qué pide en el mercado?", "What does he ask for at the market?",
                          "Un kilo de tomates y media docena de huevos.", "A kilo of tomatoes and half a dozen eggs.",
                          ["tomates", "huevos"]),
                       _q("¿Cuánto jamón compra?", "How much ham does he buy?",
                          "Compra cien gramos.", "He buys a hundred grams.", ["cien", "gramos"], 6)]},
    16: {"title": "Una cena", "title_en": "A dinner",
         "chunks": [("El viernes ceno con Eva en un restaurante.", E, "On Friday I have dinner with Eva in a restaurant."),
                    ("Pedimos una mesa para dos.", E, "We ask for a table for two."),
                    ("De primero, Eva pide una sopa y yo una ensalada.", E,
                     "For starter, Eva orders a soup and I order a salad."),
                    ("De segundo, pedimos pollo, y está muy rico.", E,
                     "For main, we order chicken, and it's delicious.")],
         "questions": [_q("¿Qué pide Eva de primero?", "What does Eva order as a starter?",
                          "Pide una sopa.", "She orders a soup.", ["sopa"], 6),
                       _q("¿Qué piden de segundo?", "What do they order for the main course?",
                          "Piden pollo.", "They order chicken.", ["pollo"], 5)]},
}


# later bands keep their passages in their own band file
from . import merged as _merged  # noqa: E402
PASSAGES = _merged("PASSAGES", PASSAGES)


def get(lesson_id: int) -> dict:
    """The passage for one lesson, or {} if there isn't one yet."""
    return PASSAGES.get(int(lesson_id)) or {}


def check() -> list:
    """Mechanical rules, so the passages cannot quietly rot."""
    problems = []
    for lid, p in sorted(PASSAGES.items()):
        chunks = p.get("chunks") or []
        qs = p.get("questions") or []
        if not 3 <= len(chunks) <= 7:
            problems.append(f"{lid}: {len(chunks)} chunks (want 3-7)")
        limit = 70 if lid <= 28 else 110   # one breath at A1-A2, one sentence after
        for text, _r, en in chunks:
            if len(text) > limit:
                problems.append(f"{lid}: chunk over {limit} chars: {text}")
            if not en:
                problems.append(f"{lid}: chunk without English: {text}")
        if len(qs) < 2:
            problems.append(f"{lid}: needs 2 questions (read + hear), has {len(qs)}")
            continue
        last = chunks[-1][0].casefold() if chunks else ""
        for kw in qs[1].get("keywords") or []:
            if kw.casefold() not in last:
                problems.append(f"{lid}: hear-question keyword '{kw}' not in the last chunk")
        body = " ".join(c[0] for c in chunks).casefold()
        for kw in qs[0].get("keywords") or []:
            if kw.casefold() not in body:
                problems.append(f"{lid}: read-question keyword '{kw}' not in the passage")
    return problems


if __name__ == "__main__":
    issues = check()
    print(f"{len(PASSAGES)} passages, {len(issues)} issues")
    for line in issues:
        print("  ", line)
    raise SystemExit(1 if issues else 0)

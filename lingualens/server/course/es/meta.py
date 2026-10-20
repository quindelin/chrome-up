# -*- coding: utf-8 -*-
"""Spanish: what the engine needs to know about this course's language.

This is the reference meta.py: a new course copies its shape (see
docs/NEW_COURSE.md). Loaded on its own by server/course/__init__.py - no
package import, so keep it to plain data and pure functions with no imports
from the server.
"""
import re

CODE = "es"
NAME = "Spanish"
NATIVE = "Español"
ALIASES = ["spanish", "es-mx", "es-es", "es_mx", "es_es", "espanol", "español", "castellano"]
BAND_LABEL = "CEFR"
TOKENS = "spaced"        # matched by word, not by character
SPEECH_LANG = "es-ES"

# Words that carry no meaning for "did you answer the question?": articles,
# clitics, common prepositions, courtesy words. Space-separated.
FUNCTION_WORDS = 'a al bien buena bueno como con de del e el ella ellas ellos en entonces eso esta este esto favor gracias hay hola la las le les lo los me mi mis muy más ni no nos nosotras nosotros o os para pero por pues que qué se si sin su sus sí también te tu tus tú u un una unas unos usted ustedes vale vosotros y ya yo él'

# Verb forms a question and its answer share in different persons
# ("¿de dónde eres?" - "soy de Canadá"): lemma -> forms. Anything else is cut
# to a three-letter stem.
LEMMAS = {'ser': 'soy eres es somos sois son era',
 'estar': 'estoy estás está estamos estáis están',
 'ir': 'voy vas va vamos vais van',
 'tener': 'tengo tienes tiene tenemos tenéis tienen',
 'hacer': 'hago haces hace hacemos hacéis hacen'}

# Hesitation sounds for the fluency check. Matched against text with the
# spaces removed, so nothing that can hide inside a real word.
FILLERS = ('ehh', 'emm', 'mmm', 'osea', 'estee')

# Labels for the lesson steps and the two notes the engine prints.
UI = {'read': 'Leer',
 'literacy': 'Letras',
 'hearing': 'Escuchar',
 'writing': 'Resumen',
 'vocab': 'Vocabulario'}
NOTES = {'hear': 'Solo escucha, no mires',
 'write': 'Con tus propias palabras, no hace falta copiar el texto'}

# The free-answer grader and the 'think in Spanish' translator (OpenAI-compatible LLM).
GRADER_PROMPT = (
    'You are grading a spoken answer in Spanish for a language learner. You are given the que'
    "stion and the learner's answer as transcribed by speech recognition, so minor transcript"
    "ion errors (a missing accent, a dropped article, ¿ or ¡) are not the learner's fault - j"
    'udge the language, not the ASR.\nDecide: (a) does it actually answer the question, (b) is'
    ' the grammar acceptable Spanish - agreement of gender and number, the right person on th'
    'e verb, ser vs estar - and (c) is the register consistent: tú or usted, whichever the qu'
    'estion used. Latin American and Peninsular usage are both correct; vosotros is fine, so '
    'is ustedes.\nBe strict on agreement, verb person and actually answering the question. Do '
    'not penalise a dropped subject pronoun - Spanish drops them.\nReply with JSON only: {"ok"'
    ': true|false, "reason": one short sentence in English, "better": a corrected version in '
    'Spanish}. If it is acceptable, "reason" is empty and "better" is empty.'
)
THINK_PROMPT = (
    "You are a Spanish coach inside a hands-free glasses app. Turn the user's English thought"
    ' into natural SPOKEN Spanish a beginner can repeat out loud.\nRules: CEFR A1-A2 vocabular'
    'y only; keep it short; drop subject pronouns the way Spanish does; use tú unless the tho'
    'ught is clearly to a stranger or official, then usted; get gender and number agreement r'
    'ight; Peninsular (Spain) usage to match the course - billete, zumo, móvil - unless the u'
    'ser writes Latin American forms; produce what a waiter in Madrid would say.\nReply with J'
    'SON only: {"text": str, "reading": "" (Spanish needs no reading line), "literal": short '
    'English gloss, "tips": one short pronunciation tip - stress, r/rr, the soft d, linking}.'
)

# Offline 'think' phrasebook (used when no LLM key is set). Optional.
PHRASEBOOK = {
    "lexicon": {'coffee': ('un café', ''),
     'tea': ('un té', ''),
     'water': ('agua', ''),
     'beer': ('una cerveza', ''),
     'wine': ('vino', ''),
     'bread': ('pan', ''),
     'bathroom': ('el baño', ''),
     'restroom': ('el baño', ''),
     'toilet': ('el baño', ''),
     'station': ('la estación', ''),
     'train station': ('la estación de tren', ''),
     'bus stop': ('la parada de autobús', ''),
     'airport': ('el aeropuerto', ''),
     'hotel': ('el hotel', ''),
     'bank': ('el banco', ''),
     'pharmacy': ('la farmacia', ''),
     'hospital': ('el hospital', ''),
     'market': ('el mercado', ''),
     'beach': ('la playa', ''),
     'museum': ('el museo', ''),
     'restaurant': ('el restaurante', ''),
     'ticket': ('el billete', ''),
     'menu': ('la carta', ''),
     'bill': ('la cuenta', ''),
     'check': ('la cuenta', ''),
     'help': ('ayuda', ''),
     'taxi': ('un taxi', ''),
     'this': ('esto', ''),
     'that': ('eso', '')},
    "phrases": {'hello': ('Hola.', ''),
     'good morning': ('Buenos días.', ''),
     'good afternoon': ('Buenas tardes.', ''),
     'good evening': ('Buenas noches.', ''),
     'good night': ('Buenas noches.', ''),
     'goodbye': ('Adiós.', ''),
     'see you later': ('Hasta luego.', ''),
     'see you tomorrow': ('Hasta mañana.', ''),
     'thank you': ('Gracias.', ''),
     'thanks': ('Gracias.', ''),
     'thank you very much': ('Muchas gracias.', ''),
     'you are welcome': ('De nada.', ''),
     'please': ('Por favor.', ''),
     'excuse me': ('Perdón.', ''),
     'sorry': ('Lo siento.', ''),
     'yes': ('Sí.', ''),
     'no': ('No.', ''),
     'ok': ('Vale.', ''),
     'okay': ('Vale.', ''),
     'i do not understand': ('No entiendo.', ''),
     'i do not know': ('No sé.', ''),
     'slowly please': ('Más despacio, por favor.', ''),
     'more slowly please': ('Más despacio, por favor.', ''),
     'again please': ('Otra vez, por favor.', ''),
     'one more time': ('Otra vez, por favor.', ''),
     'do you speak english': ('¿Habla inglés?', ''),
     'how are you': ('¿Qué tal?', ''),
     'i am fine': ('Estoy bien, gracias.', ''),
     'what is your name': ('¿Cómo te llamas?', ''),
     'nice to meet you': ('Mucho gusto.', ''),
     'how much is it': ('¿Cuánto cuesta?', ''),
     'the check please': ('La cuenta, por favor.', ''),
     'the bill please': ('La cuenta, por favor.', ''),
     'cheers': ('¡Salud!', ''),
     'i am hungry': ('Tengo hambre.', ''),
     'i am thirsty': ('Tengo sed.', ''),
     'i am tired': ('Estoy cansado.', ''),
     'really': ('¿En serio?', ''),
     'what time is it': ('¿Qué hora es?', '')},
    "patterns": [('^i (?:would like|want) (?:a |an |some )?(?P<x>.+)$',
      'Quiero {x}, por favor.',
      '',
      "I'd like {x}, please."),
     ('^where is (?:the )?(?P<x>.+)$', '¿Dónde está {x}?', '', 'Where is {x}?'),
     ('^how much is (?:the )?(?P<x>.+)$', '¿Cuánto cuesta {x}?', '', 'How much is {x}?'),
     ('^i am looking for (?:the |a |an )?(?P<x>.+)$', 'Busco {x}.', '', "I'm looking for {x}."),
     ('^is there (?:a |an )?(?P<x>.+?)(?: near here| nearby)?$',
      '¿Hay {x} por aquí?',
      '',
      'Is there {x} around here?')],
}

# Config defaults for this course (merged under config.<code>.yaml).
DEFAULTS = {'pronunciation': {'prefer': 'azure', 'language': 'es-ES', 'iflytek': {'enabled': False}},
 'gate': {'min_tone_score': 0.0},
 'ui': {'reading_by_level': {1: 'always',
                             2: 'fade',
                             3: 'reveal',
                             4: 'never',
                             5: 'never',
                             6: 'never'},
        'scene_by_level': {1: 'always',
                           2: 'always',
                           3: 'first',
                           4: 'first',
                           5: 'tip',
                           6: 'tip'},
        'vocab_label': 'Vocabulario'},
 'audio': {'seconds_per_char': 0.075},
 'writing': {'min_band': 5, 'min_chars': 80},
 'fluency': {'min_chars_per_second': 9.0, 'min_band': 4},
 'reading': {'per_lesson': 1, 'read_aloud': True, 'comprehension': True},
 'listening': {'natural_bands': [4, 5, 6]},
 'free': {'per_lesson': 4},
 'storage': {'path': 'state.es.json'}}


# -- spoken-text normalisation -------------------------------------------------
# Dictation writes "son doce euros" back as "Son 12 €". The word check counts
# letters, so digits are spelled out first; and forms that differ only in
# agreement (un / una / uno) count as one word. Both are optional hooks:
#   normalize_spoken(text) -> text      word_key(word) -> word
_ES_UNITS = ['cero',
 'uno',
 'dos',
 'tres',
 'cuatro',
 'cinco',
 'seis',
 'siete',
 'ocho',
 'nueve',
 'diez',
 'once',
 'doce',
 'trece',
 'catorce',
 'quince',
 'dieciséis',
 'diecisiete',
 'dieciocho',
 'diecinueve',
 'veinte',
 'veintiuno',
 'veintidós',
 'veintitrés',
 'veinticuatro',
 'veinticinco',
 'veintiséis',
 'veintisiete',
 'veintiocho',
 'veintinueve']
_ES_TENS = {3: 'treinta',
 4: 'cuarenta',
 5: 'cincuenta',
 6: 'sesenta',
 7: 'setenta',
 8: 'ochenta',
 9: 'noventa'}
_ES_HUNDREDS = {2: 'doscientos',
 3: 'trescientos',
 4: 'cuatrocientos',
 5: 'quinientos',
 6: 'seiscientos',
 7: 'setecientos',
 8: 'ochocientos',
 9: 'novecientos'}
_ES_ORDINALS = {1: 'primero',
 2: 'segundo',
 3: 'tercero',
 4: 'cuarto',
 5: 'quinto',
 6: 'sexto',
 7: 'séptimo',
 8: 'octavo',
 9: 'noveno',
 10: 'décimo'}
_ES_SAME = {'un': 'uno',
 'una': 'uno',
 'veintiun': 'veintiuno',
 'veintiuna': 'veintiuno',
 'primer': 'primero',
 'primera': 'primero',
 'tercer': 'tercero',
 'tercera': 'tercero'}
_ES_NUMERAL = re.compile(
    '(\\d{1,3}(?:\\.\\d{3})+|\\d+)(?::(\\d{2}))?(?:,(\\d+))?(\\.?º|\\.?ª|er\\b)?'
)

def _es_number(n: int) -> str:
    """Spanish words for 0 <= n < 10**9, the way a learner says it."""
    if n < 30:
        return _ES_UNITS[n]
    if n < 100:
        tens, unit = divmod(n, 10)
        return _ES_TENS[tens] + (f" y {_ES_UNITS[unit]}" if unit else "")
    if n < 1000:
        hund, rest = divmod(n, 100)
        head = ("cien" if not rest else "ciento") if hund == 1 else _ES_HUNDREDS[hund]
        return head + (f" {_es_number(rest)}" if rest else "")
    if n < 10 ** 6:
        thou, rest = divmod(n, 1000)
        head = "mil" if thou == 1 else f"{_es_number(thou)} mil"
        return head + (f" {_es_number(rest)}" if rest else "")
    mill, rest = divmod(n, 10 ** 6)
    head = "un millón" if mill == 1 else f"{_es_number(mill)} millones"
    return head + (f" {_es_number(rest)}" if rest else "")


def _es_spell_numerals(text: str) -> str:
    """Write dictation's digits back as the words the learner actually said.

    Azure (and phone dictation) apply inverse text normalisation: "son doce
    euros" comes back as "Son 12 €". The word check below only counts
    letters, so without this every price, time and date line fails on the
    number the learner said correctly.
    """
    def one(m: "re.Match") -> str:
        whole, minutes, decimals, ordinal = m.groups()
        n = int(whole.replace(".", ""))
        if ordinal and 1 <= n <= 10:
            return _ES_ORDINALS[n]
        if n >= 10 ** 9:
            return m.group(0)
        out = _es_number(n)
        if minutes is not None:
            mm = int(minutes)
            out += {0: "", 15: " y cuarto", 30: " y media"}.get(mm, f" y {_es_number(mm)}")
        if decimals:
            out += " coma " + _es_number(int(decimals)) if len(decimals) < 10 else ""
        return f" {out} "

    text = text.replace("%", " por ciento ").replace("€", " euros ").replace("$", " dólares ")
    return _ES_NUMERAL.sub(one, text)


def _es_word_key(word: str) -> str:
    word = _ES_SAME.get(word, word)
    return word[:-6] + "ientos" if word.endswith("ientas") else word


normalize_spoken = _es_spell_numerals
word_key = _es_word_key

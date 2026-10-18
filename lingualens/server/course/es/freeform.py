# -*- coding: utf-8 -*-
"""Free-response prompts: the model asks, you answer about YOURSELF.

Same six-string contract as the Japanese file:
    q_text, q_reading, q_en, a_text, a_reading, a_en

The difference is deliberate: every question here is about the learner -
your name, your city, your job, what you like - not about a character in the
dialogue. Personal relevance is the cheapest retention lever there is, and
"Mike is from America" in the Japanese course spends it on Mike. The sample
answer is one possible answer, never the only one.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

Prompt = Tuple[str, str, str, str, str, str]
E = ""

PROMPTS: Dict[int, List[Prompt]] = {
    1: [
        ("¡Hola! ¿Qué tal?", E, "Hi! How are things?",
         "Muy bien, gracias. ¿Y tú?", E, "Very well, thanks. And you?"),
        ("Buenas tardes. ¿Cómo estás hoy?", E, "Good afternoon. How are you today?",
         "Estoy bien, pero un poco cansado.", E, "I'm fine, but a little tired."),
    ],
    2: [
        ("Hola, ¿cómo te llamas?", E, "Hi, what's your name?",
         "Me llamo Alex. ¿Y tú?", E, "My name is Alex. And you?"),
        ("Buenas tardes. ¿Cómo se llama usted?", E, "Good afternoon. What is your name?",
         "Me llamo Alex Smith. Mucho gusto.", E, "My name is Alex Smith. Nice to meet you."),
    ],
    3: [
        ("¿De dónde eres?", E, "Where are you from?",
         "Soy de Estados Unidos, de Boston.", E, "I'm from the United States, from Boston."),
        ("¿Y dónde vives ahora?", E, "And where do you live now?",
         "Ahora vivo en Madrid.", E, "Now I live in Madrid."),
    ],
    4: [
        ("¿Usted habla español?", E, "Do you speak Spanish?",
         "Sí, hablo un poco de español.", E, "Yes, I speak a little Spanish."),
        ("¿Qué idiomas hablas?", E, "Which languages do you speak?",
         "Hablo inglés y un poco de español.", E, "I speak English and a little Spanish."),
    ],
    5: [
        ("¿Cómo eres tú?", E, "What are you like?",
         "Soy alto y tengo el pelo corto.", E, "I'm tall and I have short hair."),
        ("¿Cómo es tu mejor amigo o amiga?", E, "What is your best friend like?",
         "Es baja, tiene los ojos marrones y es muy simpática.", E,
         "She's short, has brown eyes and is really nice."),
        ("¿Qué estás haciendo ahora?", E, "What are you doing right now?",
         "Estoy estudiando español.", E, "I'm studying Spanish."),
    ],
    6: [
        ("¿Trabajas o estudias?", E, "Do you work or study?",
         "Trabajo en una oficina en el centro.", E, "I work in an office in the centre."),
        ("¿Y de dónde es usted?", E, "And where are you from?",
         "Soy de Inglaterra, pero vivo aquí.", E, "I'm from England, but I live here."),
    ],
    7: [
        ("Perdone, ¿dónde está el banco?", E, "Excuse me, where is the bank?",
         "Siga todo recto y gire a la derecha.", E, "Go straight on and turn right."),
        ("¿Tu casa está cerca o lejos de aquí?", E, "Is your home near here or far?",
         "Mi casa está cerca, a diez minutos.", E, "My home is close, ten minutes away."),
    ],
    8: [
        ("¿Qué hay cerca de tu casa?", E, "What is there near your home?",
         "Hay un supermercado y una farmacia.", E, "There's a supermarket and a pharmacy."),
        ("¿Hay un cajero por aquí?", E, "Is there a cash machine around here?",
         "Sí, hay uno enfrente del banco.", E, "Yes, there's one opposite the bank."),
    ],
    9: [
        ("¿Adónde vas este fin de semana?", E, "Where are you going this weekend?",
         "Voy a la playa con mis amigos.", E, "I'm going to the beach with my friends."),
        ("¿Cómo vas al trabajo?", E, "How do you get to work?",
         "Voy en metro. Está un poco lejos.", E, "I go by metro. It's a little far."),
    ],
    10: [
        ("Buenos días, ¿qué desea?", E, "Good morning, what would you like?",
         "Un billete de ida y vuelta para Toledo.", E, "A return ticket to Toledo."),
        ("¿A qué hora sale tu tren?", E, "What time does your train leave?",
         "Sale a las diez y media.", E, "It leaves at half past ten."),
    ],
    11: [
        ("¿Adónde va usted?", E, "Where are you going?",
         "Voy a Sevilla. ¿Este tren va a Sevilla?", E, "I'm going to Seville. Does this train go to Seville?"),
        ("¿Qué necesita?", E, "What do you need?",
         "Necesito un billete y el número del andén.", E, "I need a ticket and the platform number."),
    ],
    12: [
        ("¿Tienes hambre?", E, "Are you hungry?",
         "Sí, tengo mucha hambre. ¿Comemos?", E, "Yes, I'm very hungry. Shall we eat?"),
        ("¿Qué quieres hacer ahora?", E, "What do you want to do now?",
         "Quiero tomar un café y descansar.", E, "I want to have a coffee and rest."),
    ],
    13: [
        ("Buenos días, ¿qué le pongo?", E, "Good morning, what can I get you?",
         "Un café con leche y una tostada, por favor.", E, "A white coffee and a piece of toast, please."),
        ("¿Algo más?", E, "Anything else?",
         "Sí, un zumo de naranja para mi amiga.", E, "Yes, an orange juice for my friend."),
    ],
    14: [
        ("¿Qué comida te gusta?", E, "What food do you like?",
         "Me gusta mucho la comida italiana.", E, "I really like Italian food."),
        ("¿Qué no te gusta?", E, "What don't you like?",
         "No me gustan las verduras.", E, "I don't like vegetables."),
    ],
    15: [
        ("Buenos días. ¿Qué le pongo?", E, "Good morning. What can I get you?",
         "¿Me pone un kilo de naranjas y media docena de huevos?", E,
         "Could I have a kilo of oranges and half a dozen eggs?"),
        ("¿Qué compras en el mercado o en el súper?", E, "What do you buy at the market or the supermarket?",
         "Compro fruta, pan y cien gramos de queso.", E, "I buy fruit, bread and a hundred grams of cheese."),
        ("Son cuarenta y dos euros. ¿Cómo quiere pagar?", E, "That's forty-two euros. How would you like to pay?",
         "Con tarjeta, por favor.", E, "By card, please."),
    ],
    16: [
        ("¿Qué van a tomar de primero?", E, "What will you have as a starter?",
         "De primero, una ensalada para mí.", E, "As a starter, a salad for me."),
        ("¿Qué tal la comida?", E, "How is the food?",
         "Está muy rica, gracias.", E, "It's delicious, thank you."),
    ],
}

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
        ("Hola, buenos días. ¿Estás bien?", E, "Hello, good morning. Are you well?",
         "Sí, estoy muy bien, gracias.", E, "Yes, I'm very well, thanks."),
        ("¿Cómo estás esta noche?", E, "How are you this evening?",
         "Estoy cansado, pero contento. ¡Buenas noches!", E, "I'm tired, but happy. Good night!"),
    ],
    2: [
        ("Hola, ¿cómo te llamas?", E, "Hi, what's your name?",
         "Me llamo Alex. ¿Y tú?", E, "My name is Alex. And you?"),
        ("Buenas tardes. ¿Cómo se llama usted?", E, "Good afternoon. What is your name?",
         "Me llamo Alex Smith. Mucho gusto.", E, "My name is Alex Smith. Nice to meet you."),
        ("¿Cómo se llama tu mejor amigo?", E, "What's your best friend's name?",
         "Mi mejor amigo se llama Sam.", E, "My best friend's name is Sam."),
        ("Y usted, ¿cómo se llama? ¿Y su apellido?", E, "And you, what's your name? And your surname?",
         "Me llamo Alex y mi apellido es Smith.", E, "My name is Alex and my surname is Smith."),
    ],
    3: [
        ("¿De dónde eres?", E, "Where are you from?",
         "Soy de Estados Unidos, de Boston.", E, "I'm from the United States, from Boston."),
        ("¿Y dónde vives ahora?", E, "And where do you live now?",
         "Ahora vivo en Madrid.", E, "Now I live in Madrid."),
        ("¿Eres de una ciudad grande o pequeña?", E, "Are you from a big city or a small one?",
         "Soy de una ciudad pequeña, cerca de Chicago.", E, "I'm from a small city, near Chicago."),
        ("¿De dónde es tu familia?", E, "Where is your family from?",
         "Mi familia es de Irlanda y de México.", E, "My family is from Ireland and Mexico."),
    ],
    4: [
        ("¿Usted habla español?", E, "Do you speak Spanish?",
         "Sí, hablo un poco de español.", E, "Yes, I speak a little Spanish."),
        ("¿Qué idiomas hablas?", E, "Which languages do you speak?",
         "Hablo inglés y un poco de español.", E, "I speak English and a little Spanish."),
        ("¿Estudias español en casa o en una clase?", E, "Do you study Spanish at home or in a class?",
         "Estudio español en casa, con el móvil.", E, "I study Spanish at home, on my phone."),
        ("¿Hablas español en el trabajo?", E, "Do you speak Spanish at work?",
         "No, en el trabajo hablo inglés.", E, "No, at work I speak English."),
    ],
    5: [
        ("¿Trabajas o estudias?", E, "Do you work or study?",
         "Trabajo en una oficina en el centro.", E, "I work in an office in the centre."),
        ("¿Y de dónde es usted?", E, "And where are you from?",
         "Soy de Inglaterra, pero vivo aquí.", E, "I'm from England, but I live here."),
        ("¿Qué estudias o en qué trabajas?", E, "What do you study, or what do you work as?",
         "Estudio economía y trabajo en un café.", E, "I study economics and I work in a café."),
        ("¿Vives cerca de aquí?", E, "Do you live near here?",
         "Sí, vivo en esta calle, en el número diez.", E, "Yes, I live on this street, at number ten."),
    ],
    6: [
        ("Perdone, ¿dónde está el banco?", E, "Excuse me, where is the bank?",
         "Está todo recto, a la derecha.", E, "It's straight ahead, on the right."),
        ("¿Tu casa está cerca o lejos de aquí?", E, "Is your home near here or far?",
         "Mi casa está cerca, a diez minutos.", E, "My home is close, ten minutes away."),
        ("¿Dónde está tu trabajo?", E, "Where is your work?",
         "Mi trabajo está en el centro, cerca de la estación.", E, "My work is in the centre, near the station."),
        ("¿Dónde estás ahora mismo?", E, "Where are you right now?",
         "Estoy en casa, en la cocina.", E, "I'm at home, in the kitchen."),
    ],
    7: [
        ("¿Qué hay cerca de tu casa?", E, "What is there near your home?",
         "Hay un supermercado y una farmacia.", E, "There's a supermarket and a pharmacy."),
        ("¿Hay un cajero por aquí?", E, "Is there a cash machine around here?",
         "Sí, hay uno enfrente del banco.", E, "Yes, there's one opposite the bank."),
        ("¿Hay un parque en tu barrio?", E, "Is there a park in your neighbourhood?",
         "Sí, hay un parque grande al lado de mi casa.", E, "Yes, there's a big park next to my house."),
        ("¿Dónde está el supermercado más cerca de tu casa?", E, "Where is the nearest supermarket to your home?",
         "Está a cinco minutos, en la plaza.", E, "It's five minutes away, in the square."),
    ],
    8: [
        ("¿Adónde vas este fin de semana?", E, "Where are you going this weekend?",
         "Voy a la playa con mis amigos.", E, "I'm going to the beach with my friends."),
        ("¿Cómo vas al trabajo?", E, "How do you get to work?",
         "Voy en metro. Está un poco lejos.", E, "I go by metro. It's a little far."),
        ("¿Adónde vas mañana?", E, "Where are you going tomorrow?",
         "Mañana voy a la universidad y luego al gimnasio.", E, "Tomorrow I'm going to the university and then the gym."),
        ("¿Vas a viajar este año? ¿Adónde?", E, "Are you going to travel this year? Where?",
         "Sí, voy a ir a España en verano.", E, "Yes, I'm going to go to Spain in summer."),
    ],
    9: [
        ("Buenos días, ¿qué desea?", E, "Good morning, what would you like?",
         "Un billete de ida y vuelta para Toledo.", E, "A return ticket to Toledo."),
        ("¿A qué hora sale tu tren?", E, "What time does your train leave?",
         "Sale a las diez y media.", E, "It leaves at half past ten."),
        ("¿A qué hora empiezas a trabajar?", E, "What time do you start work?",
         "Empiezo a las nueve de la mañana.", E, "I start at nine in the morning."),
        ("¿Cuánto cuesta un billete de autobús en tu ciudad?", E, "How much is a bus ticket in your city?",
         "Cuesta dos euros, más o menos.", E, "It costs about two euros."),
    ],
    10: [
        ("¿Adónde va usted?", E, "Where are you going?",
         "Voy a Sevilla. ¿Este tren va a Sevilla?", E, "I'm going to Seville. Does this train go to Seville?"),
        ("¿Qué necesita?", E, "What do you need?",
         "Necesito un billete y el número del andén.", E, "I need a ticket and the platform number."),
        ("¿Hay estación de tren en tu ciudad? ¿Dónde está?", E, "Is there a train station in your city? Where is it?",
         "Sí, hay una estación. Está en el centro.", E, "Yes, there's a station. It's in the centre."),
        ("¿Cómo vas a casa hoy?", E, "How are you going home today?",
         "Voy a casa en metro y luego a pie.", E, "I'm going home by metro and then on foot."),
    ],
    11: [
        ("¿Tienes hambre?", E, "Are you hungry?",
         "Sí, tengo mucha hambre. ¿Comemos?", E, "Yes, I'm very hungry. Shall we eat?"),
        ("¿Qué quieres hacer ahora?", E, "What do you want to do now?",
         "Quiero tomar un café y descansar.", E, "I want to have a coffee and rest."),
        ("¿Tienes sueño ahora?", E, "Are you sleepy now?",
         "Sí, tengo sueño. Quiero dormir un poco.", E, "Yes, I'm sleepy. I want to sleep a bit."),
        ("¿Qué quieres comer esta noche?", E, "What do you want to eat tonight?",
         "Quiero comer una pizza en casa.", E, "I want to eat a pizza at home."),
    ],
    12: [
        ("Buenos días, ¿qué le pongo?", E, "Good morning, what can I get you?",
         "Un café con leche y una tostada, por favor.", E, "A white coffee and a piece of toast, please."),
        ("¿Algo más?", E, "Anything else?",
         "Sí, un zumo de naranja para mi amiga.", E, "Yes, an orange juice for my friend."),
        ("¿Qué tomas por la mañana?", E, "What do you have in the morning?",
         "Tomo un café con leche y una tostada.", E, "I have a white coffee and a piece of toast."),
        ("¿Hay un café bueno cerca de tu casa?", E, "Is there a good café near your home?",
         "Sí, hay un café pequeño con una terraza.", E, "Yes, there's a small café with a terrace."),
    ],
    13: [
        ("¿Qué comida te gusta?", E, "What food do you like?",
         "Me gusta mucho la comida italiana.", E, "I really like Italian food."),
        ("¿Qué no te gusta?", E, "What don't you like?",
         "No me gustan las verduras.", E, "I don't like vegetables."),
        ("¿Te gustan los deportes?", E, "Do you like sports?",
         "Me gusta el fútbol, pero no me gustan los deportes de invierno.", E, "I like football, but I don't like winter sports."),
        ("¿Qué te gusta hacer los domingos?", E, "What do you like doing on Sundays?",
         "Me gusta pasear y leer en el parque.", E, "I like going for walks and reading in the park."),
    ],
    14: [
        ("¿Cómo quiere pagar?", E, "How would you like to pay?",
         "Con tarjeta, por favor.", E, "By card, please."),
        ("Son cuarenta y dos euros. ¿Juntos o separados?", E, "That's forty-two euros. Together or separately?",
         "Separados, por favor. Pago yo el mío.", E, "Separately, please. I'll pay for mine."),
        ("¿Puedes pagar con el móvil en tu país?", E, "Can you pay by phone in your country?",
         "Sí, puedo pagar con el móvil en casi todas partes.", E, "Yes, I can pay by phone almost everywhere."),
        ("¿Cuánto cuesta una comida en tu ciudad?", E, "How much does a meal cost in your city?",
         "Una comida cuesta unos treinta dólares.", E, "A meal costs about thirty dollars."),
    ],
    15: [
        ("¿Qué van a tomar de primero?", E, "What will you have as a starter?",
         "De primero, una ensalada para mí.", E, "As a starter, a salad for me."),
        ("¿Qué tal la comida?", E, "How is the food?",
         "Está muy rica, gracias.", E, "It's delicious, thank you."),
        ("¿Qué pides normalmente en un restaurante?", E, "What do you usually order in a restaurant?",
         "Normalmente pido pescado y una ensalada.", E, "I usually order fish and a salad."),
        ("¿Cuál es tu restaurante favorito?", E, "What is your favourite restaurant?",
         "Mi favorito es un restaurante italiano. Me gusta mucho la pasta.", E, "My favourite is an Italian restaurant. I really like the pasta."),
    ],
}

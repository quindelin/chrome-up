# -*- coding: utf-8 -*-
"""English scene-setting for every Japanese lesson, keyed by lesson id.

Why this is a separate module: 73 hand-authored one-liners belong in one
reviewable place, not scattered through six level files. Nothing here is ever
spoken - this text is printed on the glasses before the conversation starts,
so 100% of the audio stays in Japanese.

Rules for authoring one:

  * one sentence, second person, present tense
  * name the two things a listener cannot guess: WHO they are talking to and
    WHERE they are standing
  * the politeness level of the dialogue depends on the scene, so the scene
    also tells you how formally to speak
  * never explain the grammar and never translate a word - the scene is a
    signpost, not the road
  * no more than about twenty words: it has to fit a 600x600 display

If a lesson id is missing here the course still loads; the engine falls back
to the lesson's goal line.
"""
from typing import Dict

SCENES: Dict[int, str] = {
    1: "You meet a neighbour in the hallway of your building at midday.",
    2: "You are shown into a colleague's office, ten minutes late.",
    3: "A stranger greets you and launches into fast Japanese.",
    4: "You are at a welcome party and someone is introducing you around.",
    5: "You are in a shop and the assistant has just greeted you.",
    6: "You are in a Tokyo department store and you need the restroom.",
    7: "You are at the kerb with a suitcase, and a taxi has stopped.",
    8: "You are at a station exit, trying to reach the airport.",
    9: "You are in the back of a taxi with a hotel card in your hand.",
    10: "You are at a station ticket machine with a train to catch.",
    11: "It is late, and a friend is reading a menu out loud.",
    12: "You are at an izakaya and the waiter is waiting.",
    13: "The plates are cleared. You want to pay and go.",
    14: "You want to take a new colleague out, and you need a time.",
    15: "You walk into a restaurant alone. From the door to the table, it is all on you.",
    16: "You are in a clothing shop and the jacket is nearly right.",
    17: "You are at a market stall holding something you want.",
    18: "You are in an electronics shop and your phone is dead.",
    19: "You are at the till. They ask how you will pay, and whether you want a bag.",
    20: "You are in a konbini buying a hot bento for dinner.",
    21: "You have no watch and a train to catch.",
    22: "You are trying to arrange something for this week.",
    23: "You arrive late, and you have to apologise properly.",
    24: "Someone asks what you think of Japanese food, and why.",
    25: "You are at a party and someone has just sat down next to you.",
    26: "A colleague is curious about what your ordinary day looks like.",
    27: "You are being asked about the flat you live in.",
    28: "Small talk at the door, the way every morning starts.",
    29: "You look unwell, and someone has said so.",
    30: "You are showing someone photographs of your family.",
    31: "You are trying to fix a time and a place to meet.",
    32: "Someone wants to know what you do in your free time.",
    33: "Japanese cars or German cars: you are asked to choose.",
    34: "You ring an office. The person you want is not there.",
    35: "You are back at the shop with something that does not fit.",
    36: "You are at a bank counter with your ID and a form.",
    37: "A friend is asking about the things you have done.",
    38: "There is news going round the office about your manager.",
    39: "You were late this morning, and your boss wants to know why.",
    40: "Things have been happening to you at work, and none of them by you.",
    41: "There is a new project and it needs an owner.",
    42: "You are discussing the morning's news with a colleague.",
    43: "A wallet has gone missing and everyone has a theory.",
    44: "You are being asked why you oppose a colleague's plan.",
    45: "You gave a presentation yesterday. It went well - or it did not.",
    46: "You are talking about tomorrow's weather and what you will do about it.",
    47: "The office computer is old, and you still prefer it.",
    48: "There is a new system, a deadline this week, and a client waiting.",
    49: "A delivery is a week late, and the client has not been told yet.",
    50: "You are meeting a client company for the first time.",
    51: "You need someone to check a document urgently.",
    52: "You have been invited to something you cannot attend.",
    53: "The phone is ringing, and you are the one who answers.",
    54: "You are asked what you think freedom actually is.",
    55: "You have made a claim, and you must give your grounds for it.",
    56: "You are asked what lies behind a problem.",
    57: "Convenience or safety, and you have to choose.",
    58: "You are asked what will happen, without being asked to promise it.",
    59: "Everyone agrees something must change, and you have to name what.",
    60: "You are asked what you value most at work.",
    61: "You have been handed a proposal you do not like.",
    62: "Someone is holding this morning's paper and wants your reading of it.",
    63: "You are asked what the editorial in this morning's paper was arguing.",
    64: "A journalist has asked you a question that assumes too much.",
    65: "Two outlets have reported the same story with different figures.",
    66: "You are in a specialist discussion and a term needs defining.",
    67: "You are asked to assess a paper's method.",
    68: "You are about to speak, and you have to structure it.",
    69: "You are on a panel and someone in the audience disagrees with you.",
    70: "You are asked to say the same thing three different ways.",
    71: "You are thanking someone who came a long way to see you.",
    72: "The discussion is going in circles and you want to break the frame.",
    73: "You have been asked to stand up and say a few words.",
}

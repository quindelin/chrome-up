# -*- coding: utf-8 -*-
"""English scene-setting for every Mandarin lesson, keyed by lesson id.

Why this is a separate module: 73 hand-authored one-liners belong in one
reviewable place, not scattered through six level files. Nothing here is ever
spoken - this text is printed on the glasses before the conversation starts,
so 100% of the audio stays in Chinese.

Rules for authoring one:

  * one sentence, second person, present tense
  * name the two things a listener cannot guess: WHO they are talking to and
    WHERE they are standing
  * never explain the grammar and never translate a word - the scene is a
    signpost, not the road
  * no more than about twenty words: it has to fit a 600x600 display

If a lesson id is missing here the course still loads; the engine falls back
to the lesson's goal line.
"""
from typing import Dict

SCENES: Dict[int, str] = {
    1: "You bump into a neighbour in the hallway of your building. She speaks no English.",
    2: "You are shown into a colleague's office, ten minutes late.",
    3: "A stranger greets you on the street and starts talking fast. You catch almost nothing.",
    4: "You are at a hostel welcome evening, sitting next to another traveller.",
    5: "You are at a street stall. The seller wants to know what you are after.",
    6: "You are in a Beijing shopping centre and you need the restroom, urgently.",
    7: "You are at the kerb with a suitcase, and a taxi has just pulled over.",
    8: "You are at a Shanghai metro exit, trying to reach the train station on time.",
    9: "You came out of the wrong subway exit and the map on your phone is useless.",
    10: "You are checking into a hotel. The receptionist needs your room number and address.",
    11: "It is late, you have not eaten, and a friend is standing in front of a menu.",
    12: "You are at a small Sichuan restaurant with someone who speaks only Chinese.",
    13: "The plates are cleared. You want the bill, and you want to pay.",
    14: "You want to take a new colleague to dinner, and you need to fix a time.",
    15: "You walk into a busy restaurant alone. From the door to the table, it is all on you.",
    16: "You are in a clothing shop. The jacket nearly fits, but you want another size.",
    17: "You are at a market stall holding something you want, and the price is far too high.",
    18: "You are in an electronics shop and your phone is dead.",
    19: "You are at the till. They ask how you intend to pay.",
    20: "You are at a wet market buying fruit by weight, with cash in your pocket.",
    21: "You have no watch and a train to catch.",
    22: "You are trying to arrange something for next week.",
    23: "You walk into the meeting twenty minutes late.",
    24: "Someone asks what you think of the food here, and they want a reason.",
    25: "You are at a party and someone has just sat down next to you.",
    26: "A friend wants to know what your ordinary weekday looks like.",
    27: "You are showing someone around your flat for the first time.",
    28: "Small talk at the office door, the way every morning starts.",
    29: "You look awful and a colleague has noticed.",
    30: "You are sharing photographs of your family with a friend.",
    31: "You are trying to fix a time and a place to meet.",
    32: "Someone wants to know what you do with your evenings.",
    33: "You are choosing between two things, and you must say which and why.",
    34: "You ring an office. The person you want is not at their desk.",
    35: "You are back at the shop with something that does not fit.",
    36: "You are at the bank counter with a form and your passport.",
    37: "A friend is asking about the places you have been.",
    38: "You are in the office and people keep asking you to move things.",
    39: "You are checking whether people actually managed to do the things they said.",
    40: "There is too much food, too much work, and not enough time.",
    41: "It is cold outside, and people keep coming in and sitting down.",
    42: "You are talking about things that keep changing.",
    43: "You are asked about your habits, and about the conditions on your promises.",
    44: "You are asked what you think of a mutual acquaintance.",
    45: "There is a hike tomorrow and you may not want to go.",
    46: "Things have been happening to you this week, and none of them by you.",
    47: "A colleague wants your view on a problem at work.",
    48: "You cycle to work, and someone wants to know why.",
    49: "You need a day off, and Manager Wang is at his desk.",
    50: "A friend has been working late every night for weeks.",
    51: "You are comparing how children learn in two countries.",
    52: "The sky is grey, and you are asked whether it worries you.",
    53: "You are asked whether the internet has actually improved anything.",
    54: "You are asked about the biggest festival of the year.",
    55: "You are at a table of regional dishes, asked what Chinese food is like.",
    56: "You have just come out of a film and someone is asking you about it.",
    57: "You disagree with someone at dinner and you want to say so politely.",
    58: "You are asked whether people your age spend their money differently now.",
    59: "You are asked for advice about sleep, and you are not a doctor.",
    60: "You have just come back from a trip.",
    61: "Someone is deciding whether to move to a big city, and they ask you.",
    62: "You are asked what sort of person your manager is.",
    63: "You are in a meeting, asked what you make of the new proposal.",
    64: "There is a notice on the wall, and a meeting that has been moved.",
    65: "You are arguing about something everyone has an opinion on.",
    66: "Someone hands you a novel and wants to know what you thought.",
    67: "You are asked why history matters to you.",
    68: "You are talking about what AI will do next.",
    69: "Two countries, one market, and you are asked to take a side.",
    70: "There is too much news, and nobody knows what is true.",
    71: "You are asked whether the law treats everyone the same.",
    72: "You have lived in three cities, and you are asked where you belong.",
    73: "You have been learning Chinese for a year, and someone asks what is hard.",
    # --- HSK 7-9: native register, then domains -----------------------------
    74: "You are reading the morning headline and someone asks what it says.",
    75: "A younger colleague uses a word you don't know, and you ask what it means.",
    76: "You are asked where you think someone is from, by their accent.",
    77: "Someone asks you what the story behind an idiom actually is.",
    78: "You are asked whether Chinese people really recite classical poetry.",
    79: "You admit you know every character and still can't follow the conversation.",
    80: "You are in a weekly meeting and have to read the quarterly figures out.",
    81: "You are asked whether algorithmic recommendation is a problem.",
    82: "A friend has been wronged and asks how ordinary people defend their rights.",
    83: "You are asked whether cutting emissions is worth the cost.",
    84: "A colleague asks how your paper is going.",
    85: "Everyone has an opinion, and you are asked which side you are on.",
}

from datetime import datetime
import re
import pytz
from decimal import *


def find_digits(num: str):
    res = re.findall("\d+\.\d+", num)
    if len(res) == 0:
        res = re.findall("\d+", num)
        if len(res) == 0:
            print(f"Error: Diffrent format of hand")
            return None
    return Decimal(res[-1])


def parse_hand(hand_id: int, hh: str):
    # Constants
    NAMES = "Seat \d{1,2}: (\S+) "
    BLINDS = " posts "
    ANTE = "posts dead blind"
    BET = " bets "
    CALL = " calls "
    RAISE = " raises "
    COLLECT = " collected "
    FLOP = "** Dealing flop **"
    DT = "\d\d \d\d \d{4} \d\d:\d\d:\d\d"
    DEALT = "Dealt to (\S+) \[ (.+?) ]"
    SHOWS = "(\S+) shows \[ (.+?) ]"
    LIMITS = "\$\d{1,3}\.*\d{0,2}/\$(\d{1,3}\.*\d{0,2})"
    PLO4 = "Pot Limit Omaha"
    NLHE = "No Limit Holdem"
    LOCAL_TZ = "Asia/Tbilisi"
    DT_FORMAT = "%d %m %Y %H:%M:%S"

    no_names = " posts"

    # vars
    players_bets = {}
    players_cards = {}
    wins = {}
    ante = {}
    timestamp = None
    game_limit = 0
    game_type = ""

    # Detecting game type
    if PLO4 in hh:
        game_type = "PLO4"
    elif NLHE in hh:
        game_type = "NLHE"
    else:
        print("Error: Unsopported game type")
        return None
    # Detect blinds level
    srch = re.findall(LIMITS, hh)
    if srch and len(srch) == 1:
        game_limit = 100 * Decimal(srch[0])

    # collect all players' names
    players = re.findall(NAMES, hh)
    for player in players:
        players_bets[player] = 0
    # collect dealt cards
    srch = re.findall(DEALT, hh)
    for res in srch:
        players_cards[res[0]] = " ".join(res[1].split(", "))
    # collect shown cards
    srch = re.findall(SHOWS, hh)
    for res in srch:
        players_cards[res[0]] = " ".join(res[1].split(", "))
    # find the datetime
    srch = re.findall(DT, hh)
    if srch:
        dt = datetime.strptime(srch[0], DT_FORMAT)
        timestamp = str(pytz.timezone(LOCAL_TZ).localize(dt))
    else:
        print(f"Hand doesn't contain datetime. Skipping hand# {hand_id} ...")
        return None

    # Extracting actions
    lines = re.split("\n", hh)
    for line in lines:
        if line.startswith(no_names):
            print(f"Hand doesn't contain Names. Skipping hand# {hand_id} ...")
            return None
        # search and extract bets for players in pot
        if BLINDS in line or CALL in line or BET in line or RAISE in line:
            words = line.split()
            player = words[0]
            bet = find_digits(words[-1])
            if bet is None:
                return None
            players_bets[player] += bet
            if ANTE in line:
                dead = find_digits(words[-3])
                if dead is None:
                    return None
                ante.update({player: find_digits(words[-3])})
        # search and extract hand result
        elif COLLECT in line:
            words = line.split()
            player = words[0]
            sidepot = find_digits(words[-2])
            if sidepot is None:
                return None
            won = sidepot + wins.get(player, 0)
            wins.update({player: won})

    # Calculating rake paid
    won = sum(wins.values())
    all_bets = sorted(players_bets.values())
    # detecting uncalled bets and fixing dict
    if all_bets[-1] != all_bets[-2]:
        for player, bet in players_bets.items():
            if bet == all_bets[-1]:
                players_bets[player] = all_bets[-2]
        all_bets[-1] = all_bets[-2]
    # adding ante (dead blinds)
    pot = sum(all_bets) + sum(ante.values())
    rake = pot - won

    # Cheking rake rules
    if rake < 0:
        print(
            f" ERROR: Negative Rake\n @ hand {hand_id}\n Rake={rake}\n Pot={pot}\n Won={won}\n players_bets{players_bets}\n Wins={wins}\n Ante={ante} "
        )
        return None
    if rake > 0 and not (FLOP in hh):
        print(
            f" ERROR Rake at No flop\n @ hand {hand_id}\n Rake={rake}\n Pot={pot}\n Won={won}\n players_bets{players_bets}\n Wins={wins}\n Ante={ante} "
        )
        return None

    # prepare outpup
    output = [
        int(hand_id),
        timestamp,
        hh,
        game_type,
        game_limit,
        len(players),
        pot,
        rake,
    ]
    for pl in players:
        output.extend(
            [
                pl,
                players_cards.get(pl, None),
                players_bets.get(pl, 0) + ante.get(pl, 0),
                wins.get(pl, 0),
            ]
        )
    return output


def parse_file(file: str, ids_in_db=None):
    NEW_HAND_TEXT = "888poker Hand History for Game (\d{7,12})"
    TOURNAMENT = "Tournament #"

    output = []
    hands_imported = 0

    # Skipping Tournaments
    if TOURNAMENT in file:
        return False

    hands = file.split("\n\n")
    for hand in hands:
        if len(hand) < 20:
            continue
        # looking fo ids in file
        id = re.findall(NEW_HAND_TEXT, hand)
        # skipping text w\o id
        if not id:
            print(f"Strange piece of text:\n{hand}")
            continue
        # check if more than one hand in text
        if len(id) != 1:
            print(f"More than one hand in text: ID: {id}\nHH:\n{hand}")
            continue
        id = int(id[0])
        # skipping hands that already exist in DB
        if id in ids_in_db:
            continue
        parsed_hand = parse_hand(id, hand)
        if parsed_hand is None:
            print(f"Empty hand returned: ID: {id}\nHH:\n{hand}")
            continue
        output.append(parsed_hand)
        hands_imported += 1
    return output


if __name__ == "__main__":
    # test parse_hand
    try:
        with open("./test_hh.txt", "r") as f:
            hh = f.read()
            id, dt, hh, *res = parse_hand("1234567890", hh, "PLO4")
            print(f"\n#{id}\n{dt}\n{res}\n\n{hh}")
    except IOError:
        print("Error: File does not appear to exist.")

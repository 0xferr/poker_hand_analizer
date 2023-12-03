from datetime import datetime
import re
import pytz
from decimal import Decimal

from tracker_utils.logger import logger

lg = logger(__name__)


def find_digits(num: str) -> Decimal:
    """
    It looks for digits in sting, and returns it as a Decimal
    """
    res = re.findall("\d+\.\d+", num)
    if len(res) == 0:
        res = re.findall("\d+", num)
        if len(res) == 0:
            lg.warning(f"Error: Diffrent format of hand")
            return None
    return Decimal(res[-1])


def parse_hand(hand_id: int, hh: str) -> list:
    """
    Parse single hand history for date, players names, their bets, dealt cards and result of the hand.
    Returns list containing [hand id, timestamp, hand history, game_type, game_limit, number of players, pot, rake,
    and for every player in hand: name, player cards, players bets incl. ante, wins
    """
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
        lg.warning(f"Error: Unsopported game type. Skipping hand# {hand_id}")
        return None
    # Detect blinds level
    srch = re.findall(LIMITS, hh)
    if srch and len(srch) == 1:
        game_limit = 100 * Decimal(srch[0])

    # collect all players' names
    players = re.findall(NAMES, hh)

    for player in players:
        # check player name is not empty
        if player == " ":
            lg.warning(f"Hand doesn't contain Names. Skipping hand# {hand_id} ...")
            return None
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
        lg.warning(f"Hand doesn't contain datetime. Skipping hand# {hand_id} ...")
        return None

    # Extracting actions
    lines = re.split("\n", hh)
    for line in lines:
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
    if won == 0:
        lg.warning(f"Hand #{hand_id} probably incomlete")
        return None
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
        lg.warning(f" ERROR: Negative Rake @ hand {hand_id}")
        lg.debug(
            f"ERROR: Negative Rake @ hand#{hand_id}\nRake={rake}\nPot={pot}\nWon={won}\nbets{players_bets}\nWins={wins}\nAnte={ante}"
        )
        return None
    if rake > 0 and not (FLOP in hh):
        lg.warning(f" ERROR Rake at No flop @ hand #{hand_id}")
        lg.debug(
            f"ERROR: Rake at No flop @ hand {hand_id}\nRake={rake}\nPot={pot}\nWon={won}\nbets{players_bets}\nWins={wins}\nAnte={ante}"
        )
        return None

    # prepare output
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
    # append betting history
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


# parse HH file. IDs can be designated to faster import
def parse_file(file: str, ids_in_db: set = None) -> list:
    """
    Parses hand history file. Collects their IDs. Checks if they are alredy imporded to database, and if not
    takes history of each hand and sends it to parse_hand func.
    Returns quantity of succesfully parsed hands.
    """
    NEW_HAND_TEXT = "888poker Hand History for Game (\d{7,12})"
    TOURNAMENT = "Tournament #"

    output = []
    hands_to_import = 0

    # Skipping Tournaments
    if TOURNAMENT in file:
        return output

    ids = re.findall(NEW_HAND_TEXT, file)
    ids_in_file = set(map(lambda x: int(x), ids))
    ids_in_file.difference_update(ids_in_db)
    if not ids_in_file:
        return output

    hands = file.split("\n\n")
    for hand in hands:
        if len(hand) < 20:
            continue
        # looking fo ids in file
        id = re.findall(NEW_HAND_TEXT, hand)
        # skipping text w\o id
        if not id:
            lg.warning(f"Strange piece of text:\n{hand}")
            lg.debug(f"Strange piece of text:\n{hand}")
            continue
        # check if more than one hand in text
        if len(id) != 1:
            lg.warning(f"More than one hand in text: ID: {id}")
            lg.debug(f"More than one hand in text: ID: {id}\nHH:\n{hand}")
            continue
        id = int(id[0])
        # skipping hands that already exist in DB
        if id in ids_in_db:
            continue
        parsed_hand = parse_hand(id, hand)
        if parsed_hand is None:
            lg.debug(f"Empty hand returned: ID: {id}\nHH:\n{hand}")
            continue
        output.append(parsed_hand)
        hands_to_import += 1
    return output

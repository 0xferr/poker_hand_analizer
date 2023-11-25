### This script works only with 888poker hand history.
### It compute your Contributed Rake in the same was
### as poker room did it.
### Formula:  Rake*(your_investmets_in_pot/total_pot_size)
### Also it shows your prifit according provided hand history.
### Months that it will ask to input is the name of folder
### in start folder (2023/8 or 2023/11) as Nand2Note store it.
### You can specify it to avoid importing entire HH.
### Or simply specify it in START_DIR.

import re
import os
from datetime import datetime, timedelta

# SETTINGS
HERO = "0xferr"  # save here YOUR NICKNAME
# save here your time difference to UTC for precise weekly/monthly rake calculation
GMT_DIFF = timedelta(hours=4)
START_DIR = "./test_hhs/"
SAVE_TO_FILE = True
PRINT_RESULT = True


# All internal calculations performs in cents for accuracy
def str_to_int(number):
    return round(float(number) * 100)


def int_to_str(number):
    temp = round(number / 100)
    return temp


def find_digits(str):
    res = re.findall("\d+\.\d+", str)
    if len(res) == 0:
        res = re.findall("\d+", str)
    return str_to_int(res[-1])


def analyze_hand(hand, lines):
    # Constants
    BLINDS = "posts"
    ANTE = "posts dead blind"
    BET = "bets"
    CALL = "calls"
    RAISE = "raises"
    COLLECT = "collected"
    FLOP = "** Dealing flop **"
    DT = "- *** "
    no_names = " posts"
    skip_hand = False

    # vars
    players_bets = {}
    wins = {}
    flop_is_dealed = False
    ante = {}

    # extracting values
    for line in lines:
        # search and extract bets for players in pot
        if line.startswith(no_names):
            print(f"Hands doesn't contain Names. Skipping hand# {hand} ...")
            skip_hand = True
            break
        if BLINDS in line or CALL in line or BET in line or RAISE in line:
            words = line.split()
            player = words[0]
            bet = find_digits(words[-1])
            if player in players_bets:
                players_bets[player] += bet
            else:
                players_bets.update({player: bet})
            if ANTE in line:
                ante.update({player: find_digits(words[-3])})
        # search and extract hand result
        elif COLLECT in line:
            words = line.split()
            player = words[0]
            won_sidepot = find_digits(words[-2])
            won = won_sidepot + wins.get(player, 0)
            wins.update({player: won})
        elif FLOP in line:
            flop_is_dealed = True
        elif DT in line:
            dt_string = re.findall("\d\d \d\d \d{4} \d\d:\d\d:\d\d", line)[0]
            timestamp = datetime.strptime(dt_string, "%d %m %Y %H:%M:%S") - GMT_DIFF
            date = timestamp.strftime("%d-%m-%Y")

    if skip_hand:
        return 0, 0, date

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
    if rake < 0:
        print(
            f" ERROR: Negative Rake\n @ hand {hand}\n Rake={rake}\n Pot={pot}\n Won={won}\n players_bets{players_bets}\n Wins={wins}\n Ante={ante} "
        )
        return 0, 0, date

    if rake > 0 and not (flop_is_dealed):
        print(
            f" ERROR Rake at No flop\n @ hand {hand}\n Rake={rake}\n Pot={pot}\n Won={won}\n players_bets{players_bets}\n Wins={wins}\n Ante={ante} "
        )
        rake = 0

    # calc player's profit
    profit = wins.get(HERO, 0) - players_bets.get(HERO, 0) - ante.get(HERO, 0)
    # calc player's rake share
    hero_bet = players_bets.get(HERO, 0) + ante.get(HERO, 0)
    hero_rake = hero_bet / pot * rake
    if rake > 400:
        print(
            f"High Rake,  @ hand {hand}\n Rake={rake}\n Pot={pot}\n Won={won}\n players_bets{players_bets}\n Wins={wins}\n Ante={ante} "
        )
    return hero_rake, profit, date


def analyze_file(name, daily_stats):
    NEW_HAND_TEXT = "***** 888poker"
    TOURNAMENT = "Tournament #"

    hand_start = 0
    hand_finish = 0
    hand_detected = False
    f = open(name, "r")
    lines = f.readlines()
    lines.append("\n")
    i = 0
    for line in lines:
        if NEW_HAND_TEXT in line:
            hand_n = re.findall("\d{7,12}", line)[0]
            hand_start = i
            hand_detected = True
        elif TOURNAMENT in line:
            print(f"Tournament HH. Skippig...")
            break
        elif line == "\n" and i > 5 and hand_detected:
            hand_finish = i
            hand_lines = lines[hand_start:hand_finish]
            hand_detected = False
            try:
                rake, profit, date = analyze_hand(hand_n, hand_lines)
            except:
                rake, profit, date = 0, 0, "err"
                with open("errors/" + hand_n + ".txt", "w") as log_hand:
                    for line in hand_lines:
                        log_hand.write(line)
            if date in daily_stats:
                daily_stats[date]["rake"].append(rake)
                daily_stats[date]["profit"].append(profit)
            elif date != "err":
                daily_stats.update({date: {"rake": [rake], "profit": [profit]}})
        i += 1
    f.close()
    return daily_stats


def analyze_dir(hh_dir, daily_stats={}):
    for subdir, dirs, files in os.walk(hh_dir):
        for file in files:
            filepath = subdir + os.sep + file
            if file.endswith(".txt") and not ("ID #" in file):
                daily_stats = analyze_file(filepath, daily_stats)
    return daily_stats


# START ANALYSIS
# input
input_months = input("Month to analyze:")
months = re.findall("\d{1,2}", input_months)


empty_stats = {"rake": 0, "profit": 0, "hands": 0}
total_hands = 0
total_rake = 0
total_profit = 0
daily_stats = {}
weekly_stats = {}
monthly_stats = {}
if not months:
    daily_stats = analyze_dir(START_DIR)
else:
    for m in months:
        hh_dir = START_DIR + m + "/"
        daily_stats = analyze_dir(hh_dir, daily_stats)


for day, result in daily_stats.items():
    # daily results
    d_hands = len(result["rake"])
    d_rake = sum(result["rake"])
    d_profit = sum(result["profit"])

    # all results
    total_hands += d_hands
    total_rake += d_rake
    total_profit += d_profit

    # weekly results
    iso_day = datetime.strptime(day, "%d-%m-%Y").isocalendar()
    iso_week = f"{iso_day[0]}-{iso_day[1]}"
    w_hands = weekly_stats.get(iso_week, empty_stats)["hands"] + d_hands
    w_rake = weekly_stats.get(iso_week, empty_stats)["rake"] + d_rake
    w_profit = weekly_stats.get(iso_week, empty_stats)["profit"] + d_profit
    weekly_stats.update(
        {iso_week: {"rake": w_rake, "profit": w_profit, "hands": w_hands}}
    )

    # monthly results
    month = day[3:5]
    m_hands = monthly_stats.get(month, empty_stats)["hands"] + d_hands
    m_rake = monthly_stats.get(month, empty_stats)["rake"] + d_rake
    m_profit = monthly_stats.get(month, empty_stats)["profit"] + d_profit
    monthly_stats.update(
        {month: {"rake": m_rake, "profit": m_profit, "hands": m_hands}}
    )


rake = int_to_str(total_rake)
profit = int_to_str(total_profit)

# OUTPUT
if PRINT_RESULT:
    print(f"\n{'-'*20}")
    print(f"Profit = ${profit}\n Rake earned ${rake}\nFor {total_hands} hands ")

    print(f"\n{'-'*20}")
    for key, val in sorted(weekly_stats.items()):
        print(
            f"Week {key}:\tProfit=${int_to_str(val['profit'])}\tRake=${int_to_str(val['rake'])}\tHands={val['hands']}"
        )

    print(f"\n{'-'*20}")
    for key, val in sorted(monthly_stats.items()):
        print(
            f"Month {key}:\tProfit=${int_to_str(val['profit'])}\tRake=${int_to_str(val['rake'])}\tHands={val['hands']}"
        )


if SAVE_TO_FILE:
    with open("results.log", "w") as f:
        f.write(f"Profit = ${profit}\nRake earned ${rake}\nFor {total_hands} hands ")
        f.write(f"\n{'-'*20}\n")
        for key, val in sorted(weekly_stats.items()):
            f.write(
                f"Week {key}:\tProfit=${int_to_str(val['profit'])}\tRake=${int_to_str(val['rake'])}\tHands={val['hands']}\n"
            )

        f.write(f"\n{'-'*20}\n")
        for key, val in sorted(monthly_stats.items()):
            f.write(
                f"Month {key}:\tProfit=${int_to_str(val['profit'])}\tRake=${int_to_str(val['rake'])}\tHands={val['hands']}\n"
            )

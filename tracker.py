import os
from tracker_utils import *
from functools import reduce
from decimal import *
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt

TEST_DIR = "./test_hhs"
START_DIR = r"C:\MyHandsArchive_H2N\Pacific\2023\11"
START_DIR2 = r"C:\MyHandsArchive_H2N\2023"
OUTPUT_DIR = r"./charts/"

CUR_WEEK = 1
PREV_WEEK = 2
CUR_MONTH = 3
PREV_MONTH = 4


def time_deco(func):
    def wrap_func(*args, **kwargs):
        start = datetime.now()
        func(*args, **kwargs)
        print(datetime.now() - start)

    return wrap_func


# import hand history files from the specified folder
@time_deco
def analyze_dir(trdb: tracker_db, hh_dir=TEST_DIR, ids=set()):
    hands_imported = 0
    for subdir, dirs, files in os.walk(hh_dir):
        print(f"importing {subdir + os.sep}")
        for file in files:
            filepath = subdir + os.sep + file
            if file.endswith(".txt") and not ("ID #" in file):
                with open(filepath, "r") as f:
                    hh = f.read()
                    res = parse_file(hh, ids)
                    if res:
                        hands_imported += trdb.import_hands(res)
    print(f"Hands imported: {hands_imported}")


# transforms predefined periods to datetime
def period_to_dates(period: str) -> tuple[datetime, datetime]:
    today = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if period == CUR_WEEK:
        shift = today.weekday()
        start_date = today - timedelta(days=shift)
        end_date = None
    elif period == PREV_WEEK:
        shift = today.weekday() + 7
        start_date = today - timedelta(days=shift)
        end_date = start_date + timedelta(days=7)
    elif period == CUR_MONTH:
        start_date = today.replace(day=1)
        end_date = None
    elif period == PREV_MONTH:
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1
        start_date = today.replace(year=year, month=month, day=1)
        end_date = today.replace(day=1)
    else:
        start_date, end_date = None, None

    return start_date, end_date


# calculate cumulative profit
def cumulate_profit(data: list[Decimal]) -> list[Decimal]:
    cumulative_values = []
    cumulative_sum = 0
    for value in data:
        cumulative_sum += value
        cumulative_values.append(cumulative_sum)
    return cumulative_values


# get the rake for selected player. Start date and end date can be specified
def get_rake(
    db: tracker_db,
    player: str,
    predefined_period: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
) -> Decimal:
    """
    predefined_period can be only one of these:
    CUR_WEEK = 1 PREV_WEEK = 2 CUR_MONTH = 3 PREV_MONTH = 4
    if predefined_period is set, it will owerwrite start and end dates
    """
    cent = Decimal("0.01")
    if predefined_period:
        start_date, end_date = period_to_dates(predefined_period)
    result = db.get_rake(player, start_date, end_date)
    total_rake = sum(map(lambda x: x[1], result))
    return total_rake.quantize(cent)


# get the profit for selected player. Start, end dates or period can be specified
def get_profit_summary(
    db: tracker_db,
    player: str,
    predefined_period: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
) -> Decimal:
    cent = Decimal("0.01")
    if predefined_period:
        start_date, end_date = period_to_dates(predefined_period)
    result = db.get_result(player, start_date, end_date)
    total_profit = sum(map(lambda x: x[1], result))
    return total_profit.quantize(cent)


# get the rake for selected player. Start, end dates or period can be specified
def get_profit_chart(
    db: tracker_db,
    player: str,
    predefined_period: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
) -> None:
    if predefined_period:
        start_date, end_date = period_to_dates(predefined_period)
    result = db.get_result(player, start_date, end_date)
    sorted_res = sorted(result, key=lambda x: x[0])
    dates, values = zip(*sorted_res)
    sum_profit = cumulate_profit(values)
    hands = [i for i in range(len(values))]
    plt.figure(figsize=(10, 6))
    plt.plot(hands, sum_profit, linestyle="-", color="b")
    plt.title("Profit")
    plt.xlabel("Date")
    plt.ylabel("$")
    plt.grid(True)
    file_name = (
        f"chart_{dates[0].year}-{dates[0].month}-{dates[0].day}"
        f"_to_{dates[-1].year}-{dates[-1].month}-{dates[-1].day}.png"
    )
    plt.show()
    plt.savefig(OUTPUT_DIR + file_name)
    plt.close()


# split list of tuples to several list for each week
def split_by_week(data: list[datetime, Decimal]) -> tuple[list, ...]:
    pass


# split list of tuples to several list for each week
def split_by_month(data: list[datetime, Decimal]) -> tuple[list, ...]:
    pass


# Test parse_hand + import_hand
if False:
    try:
        with open("./test_hh.txt", "r") as f:
            hh = f.read()
            (*res,) = parse_hand("1234567890", hh)
            # print(f"\n#{id}\n{dt}\n{res}\n\n{hh}")
            trdb = tracker_db()
            if False:
                trdb.clear_tables()
            trdb.import_hand(*res)
            trdb.close()

    except IOError:
        print("Error: File does not appear to exist.")

# Test parse_file + parse_hand + import_hand
if True:
    trdb = tracker_db(clear_tables=False)
    ids_in_db = trdb.get_all_ids()
    try:
        analyze_dir(trdb, hh_dir=START_DIR2, ids=ids_in_db)

    except IOError:
        print("Error: File does not appear to exist.")
    trdb.close()

# Test profit and rake calculation
if True:
    PLAYER = "0xferr"
    start = datetime(2023, 11, 1, tzinfo=timezone.utc)
    finish = datetime(2023, 12, 1, tzinfo=timezone.utc)
    trdb = tracker_db()

    rake_specified_dates = get_rake(trdb, PLAYER, start_date=start, end_date=finish)
    rake_this_week = get_rake(trdb, PLAYER, CUR_WEEK)
    rake_prev_week = get_rake(trdb, PLAYER, PREV_WEEK)
    rake_this_month = get_rake(trdb, PLAYER, CUR_MONTH)
    rake_prev_month = get_rake(trdb, PLAYER, PREV_MONTH)

    profit_specified_dates = get_profit_summary(
        trdb, PLAYER, start_date=start, end_date=finish
    )
    profit_this_week = get_profit_summary(trdb, PLAYER, CUR_WEEK)
    profit_prev_week = get_profit_summary(trdb, PLAYER, PREV_WEEK)
    profit_this_month = get_profit_summary(trdb, PLAYER, CUR_MONTH)
    profit_prev_month = get_profit_summary(trdb, PLAYER, PREV_MONTH)

    print("\t\tRake:\tProfit:")
    print(f"For period:\t{rake_specified_dates}\t{profit_specified_dates}")
    print(f"This week:\t{rake_this_week}\t{profit_this_week}")
    print(f"Previous week:\t{rake_prev_week}\t{profit_prev_week}")
    print(f"This month:\t{rake_this_month}\t{profit_this_month}")
    print(f"Previous month:\t{rake_prev_month}\t{profit_prev_month}")

    get_profit_chart(trdb, PLAYER, CUR_MONTH)

    trdb.close()

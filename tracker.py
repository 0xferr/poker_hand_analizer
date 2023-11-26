import os
from tracker_utils import *
from functools import reduce
from decimal import *
from datetime import datetime, timezone, timedelta

TEST_DIR = "./test_hhs"
START_DIR = r"C:\MyHandsArchive_H2N\Pacific\2023\11"
START_DIR2 = r"C:\MyHandsArchive_H2N\2023\10"

CUR_WEEK = 1
PREV_WEEK = 2
CUR_MONTH = 3
PREV_MONTH = 4


def analyze_dir(trdb: tracker_db, hh_dir=TEST_DIR, ids_in_db=set()):
    hands_imported = 0
    for subdir, dirs, files in os.walk(hh_dir):
        print(f"importing {subdir + os.sep}")
        for file in files:
            filepath = subdir + os.sep + file
            if file.endswith(".txt") and not ("ID #" in file):
                with open(filepath, "r") as f:
                    hh = f.read()
                    res = parse_file(hh, ids_in_db)
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


# get the rake for selected player. Start date and end date can be specified
# predefined_period can be only one of these:
#    CUR_WEEK = 1 PREV_WEEK = 2 CUR_MONTH = 3 PREV_MONTH = 4
# if predefined_period is set, it will owerwrite start and end dates
def get_rake(
    db: tracker_db,
    player: str,
    predefined_period: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
) -> Decimal:
    cent = Decimal("0.01")
    if predefined_period:
        start_date, end_date = period_to_dates(predefined_period)
    result = db.get_rake(player, start_date, end_date)
    total_rake = sum(map(lambda x: x[1], result))
    return total_rake.quantize(cent)


# split list of tuples to several list for each week
def split_by_week(data: list) -> tuple:
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
if False:
    trdb = tracker_db(clear_tables=False)
    ids_in_db = set()
    # trdb.hand_exist()
    try:
        analyze_dir(trdb, hh_dir=START_DIR2)

    except IOError:
        print("Error: File does not appear to exist.")
    trdb.close()

# Test rake calculation
if True:
    PLAYER = "0xferr"
    start = datetime(2023, 11, 4, tzinfo=timezone.utc)
    finish = datetime(2023, 11, 5, tzinfo=timezone.utc)
    trdb = tracker_db()
    rake_specified_dates = get_rake(trdb, PLAYER, start_date=start, end_date=finish)
    rake_this_week = get_rake(trdb, PLAYER, CUR_WEEK)
    rake_prev_week = get_rake(trdb, PLAYER, PREV_WEEK)
    rake_this_month = get_rake(trdb, PLAYER, CUR_MONTH)
    rake_prev_month = get_rake(trdb, PLAYER, PREV_MONTH)

    print("Rake:")
    print(f"For period:\t{rake_specified_dates}")
    print(f"This week:\t{rake_this_week}")
    print(f"Previous week:\t{rake_prev_week}")
    print(f"This month:\t{rake_this_month}")
    print(f"Previous month:\t{rake_prev_month}")

    trdb.close()

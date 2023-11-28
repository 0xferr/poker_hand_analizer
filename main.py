from datetime import datetime, timezone
from tracker_utils.logger import logger
from tracker_utils.tracker import Tracker

TEST_DIR = "./test_hhs"
START_DIR = r"C:\MyHandsArchive_H2N\Pacific\2023"
START_DIR2 = r"C:\MyHandsArchive_H2N\2023"

CUR_WEEK = 1
PREV_WEEK = 2
CUR_MONTH = 3
PREV_MONTH = 4
PERIODS_NAMES = {
    1: "Current Week",
    2: "Previous Week",
    3: "Current Month",
    4: "Previous Month",
}


def time_deco(func):
    def wrap_func(*args, **kwargs):
        start = datetime.now()
        func(*args, **kwargs)
        print(datetime.now() - start)

    return wrap_func


if __name__ == "__main__":
    tr = Tracker()
    logger(__name__)
    PLAYER = "0xferr"

    # Test parse_hand + import_hand
    if False:
        try:
            with open("./test_hh.txt", "r") as f:
                hh = f.read()
                (*res,) = parse_hand("1234567890", hh)
                # print(f"\n#{id}\n{dt}\n{res}\n\n{hh}")
                if False:
                    tr.db.clear_tables()
                tr.db.import_hand(*res)

        except IOError:
            print("Error: File does not appear to exist.")

    # Test parse_file + parse_hand + import_hand
    if True:
        try:
            tr.import_hh(TEST_DIR)
        except IOError:
            print("Error: File does not appear to exist.")

    # Test profit and rake calculation
    if False:
        start = datetime(2023, 11, 1, tzinfo=timezone.utc)
        finish = datetime(2023, 11, 5, tzinfo=timezone.utc)
        print("\t\tRake:\tProfit:")
        rake_specified_dates = tr.get_rake(PLAYER, start_date=start, end_date=finish)
        profit_specified_dates = tr.get_profit(
            PLAYER, start_date=start, end_date=finish
        )
        print(f"For period:\t{rake_specified_dates:.2f}\t{profit_specified_dates:.2f}")

    if False:
        for per in (1, 2, 3, 4):
            rake = tr.get_rake(PLAYER, per)
            profit = tr.get_profit(PLAYER, per)
            print(f"{PERIODS_NAMES[per]}\t{rake:.2f}\t{profit:.2f}")

    if False:
        print("\n\t\tRake\tProfit")
        rake, rake_w, rake_m = tr.get_rake_splited_by_periods(PLAYER)
        profit, profit_w, profit_m = tr.get_profit_splited_by_periods(PLAYER)
        print(f"All Time\t{rake:.2f}\t{profit:.2f}")
        print("\nWeekly\t\tRake\tProfit")
        for key in rake_w.keys():
            print(f"{key}\t\t{rake_w[key]:.2f}\t{profit_w[key]:.2f}")
        print("\nMonthly\t\tRake\tProfit")
        for key in rake_m.keys():
            print(f"{key}\t\t{rake_m[key]:.2f}\t{profit_m[key]:.2f}")

        tr.get_profit_chart(PLAYER, CUR_MONTH)

    if False:
        tr.get_profit_chart(PLAYER)

    tr.db.close()

import os
from tracker_utils import *
from functools import reduce
from decimal import *
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
from typing import Literal
from tracker_utils.calc import *

TEST_DIR = "./test_hhs"
START_DIR = r"C:\MyHandsArchive_H2N\Pacific\2023\11"
START_DIR2 = r"C:\MyHandsArchive_H2N\2023"
OUTPUT_DIR = r"./charts/"

CUR_WEEK = 1
PREV_WEEK = 2
CUR_MONTH = 3
PREV_MONTH = 4
PERIODS = Literal[1, 2, 3, 4]
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


class Tracker:
    def __init__(self, clear_tables=False) -> None:
        self.db = tracker_db(clear_tables=clear_tables)

    # import HH from path to DB
    @time_deco
    def import_hh(self, path: str) -> int:
        ids = self.db.get_all_ids()
        hands_imported = 0
        for subdir, dirs, files in os.walk(path):
            print(f"importing {subdir + os.sep}")
            for file in files:
                filepath = subdir + os.sep + file
                if file.endswith(".txt"):
                    with open(filepath, "r") as f:
                        hh = f.read()
                        res = parse_file(hh, ids)
                        if res:
                            hands_imported += self.db.import_hands(res)
        return hands_imported

    # get the rake for selected player. Start date and end date can be specified
    def get_rake(
        self,
        player: str,
        predefined_period: PERIODS = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Decimal:
        """
        predefined_period can be only one of these:
        CUR_WEEK = 1 PREV_WEEK = 2 CUR_MONTH = 3 PREV_MONTH = 4
        if predefined_period is set, it will owerwrite start and end dates
        """
        if predefined_period:
            start_date, end_date = period_to_dates(predefined_period)
        result = self.db.get_rake(player, start_date, end_date)
        total_rake = sum(map(lambda x: x[1], result))
        return total_rake

    def get_rake_splited_by_periods(
        self, player: str, start_date: datetime = None, end_date: datetime = None
    ) -> [Decimal, dict[Decimal], dict[Decimal]]:
        result = self.db.get_rake(player, start_date, end_date)
        total_rake = sum(map(lambda x: x[1], result))
        weekly = sum_by_weeks(result)
        monthly = sum_by_month(result)
        return total_rake, weekly, monthly

    # get the profit for selected player. Start, end dates or period can be specified
    def get_profit(
        self,
        player: str,
        predefined_period: PERIODS = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Decimal:
        if predefined_period:
            start_date, end_date = period_to_dates(predefined_period)
        result = self.db.get_result(player, start_date, end_date)
        total_profit = sum(map(lambda x: x[1], result))
        return total_profit

    def get_profit_splited_by_periods(
        self, player: str, start_date: datetime = None, end_date: datetime = None
    ) -> [Decimal, dict[Decimal], dict[Decimal]]:
        result = self.db.get_result(player, start_date, end_date)
        total_profit = sum(map(lambda x: x[1], result))
        weekly = sum_by_weeks(result)
        monthly = sum_by_month(result)
        return total_profit, weekly, monthly

    # get the rake for selected player. Start, end dates or period can be specified
    def get_profit_chart(
        self,
        player: str,
        predefined_period: PERIODS = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> None:
        if predefined_period:
            start_date, end_date = period_to_dates(predefined_period)
        result = self.db.get_result(player, start_date, end_date)
        sorted_res = sorted(result, key=lambda x: x[0])
        dates, values = zip(*sorted_res)
        sum_profit = cumulate_profit(values)
        hands = [i for i in range(len(values))]
        plt.figure(figsize=(19.2, 10.8))
        plt.plot(hands, sum_profit, linestyle="-", color="g")
        plt.title("Profit")
        plt.xlabel("Hands")
        plt.ylabel("$")
        plt.xlim(xmin=0)
        plt.grid(True)
        file_name = (
            f"chart_{dates[0].year}-{dates[0].month}-{dates[0].day}"
            f"_to_{dates[-1].year}-{dates[-1].month}-{dates[-1].day}.png"
        )
        plt.savefig(OUTPUT_DIR + file_name)
        plt.show()
        plt.close()


if __name__ == "__main__":
    tr = Tracker()

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
                tr.db.close()

        except IOError:
            print("Error: File does not appear to exist.")

    # Test parse_file + parse_hand + import_hand
    if False:
        tr = Tracker(clear_tables=False)
        try:
            tr.import_hh(START_DIR2)
        except IOError:
            print("Error: File does not appear to exist.")
        tr.db.close()

    # Test profit and rake calculation
    if True:
        PLAYER = "0xferr"
        start = datetime(2023, 11, 1, tzinfo=timezone.utc)
        finish = datetime(2023, 12, 1, tzinfo=timezone.utc)
        tr = Tracker()
        print("\t\tRake:\tProfit:")
        rake_specified_dates = tr.get_rake(PLAYER, start_date=start, end_date=finish)
        profit_specified_dates = tr.get_profit(
            PLAYER, start_date=start, end_date=finish
        )
        print(f"For period:\t{rake_specified_dates:.2f}\t{profit_specified_dates:.2f}")
        for per in (1, 2, 3, 4):
            rake = tr.get_rake(PLAYER, per)
            profit = tr.get_profit(PLAYER, per)
            print(f"{PERIODS_NAMES[per]}\t{rake:.2f}\t{profit:.2f}")
        tr.get_profit_chart(PLAYER, CUR_MONTH)

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

        tr.db.close()

    if False:
        PLAYER = "0xferr"
        tr = Tracker()
        tr.get_profit_chart(PLAYER)
        tr.db.close()

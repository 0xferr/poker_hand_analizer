import os
from decimal import Decimal
from datetime import datetime
import matplotlib.pyplot as plt
from typing import Literal
from tracker_utils.db import tracker_db
from tracker_utils.calc import (
    period_to_dates,
    cumulate_profit,
    sum_by_weeks,
    sum_by_month,
)
from tracker_utils.hand_parser import parse_file

from tracker_utils.logger import logger

PERIODS = Literal[1, 2, 3, 4]
OUTPUT_DIR = r"./charts/"


class Tracker:
    def __init__(self, clear_tables=False) -> None:
        self.lg = logger(__name__)
        self.db = tracker_db(clear_tables=clear_tables)

    # import HH from path to DB
    def import_hh(self, path: str) -> int:
        ids = self.db.get_all_ids()
        hands_imported = 0
        for subdir, dirs, files in os.walk(path):
            self.lg.info(f"importing {subdir + os.sep}")
            for file in files:
                filepath = subdir + os.sep + file
                if file.endswith(".txt"):
                    with open(filepath, "r") as f:
                        hh = f.read()
                        res = parse_file(hh, ids)
                        if res:
                            hands_imported += self.db.import_hands(res)
        self.lg.info(f"Hands imported {hands_imported}")
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
        result = self.db.get_profit(player, start_date, end_date)
        total_profit = sum(map(lambda x: x[1], result))
        return total_profit

    def get_profit_splited_by_periods(
        self, player: str, start_date: datetime = None, end_date: datetime = None
    ) -> [Decimal, dict[Decimal], dict[Decimal]]:
        result = self.db.get_profit(player, start_date, end_date)
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
        result = self.db.get_profit(player, start_date, end_date)
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

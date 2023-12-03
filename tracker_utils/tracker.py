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

PERIODS = Literal["cw", "pw", "cm", "pm"]
OUTPUT_DIR = r"./charts/"


class Tracker:
    """
    Tracker import hand history files to database. Calculate rake and profit using data stored in DB.
    Inputs:
        player: Player name, for whom rake and profit will be calculated.
        clear_tables: If True delete all records in database.
        chart: If True the Won/Loss graph will be shown and saved after calling get_profit.
    Methods:
        import_hh: Imports all Hand History files from specified path to database.
        get_rake: Calculate contributed rake.
        get_profit: Calculate profit.
    """

    def __init__(self, player="0xferr", clear_tables=False, chart=False) -> None:
        self.lg = logger(__name__)
        self.db = tracker_db(clear_tables=clear_tables)
        self.chart = chart
        self.player = player

    def import_hh(self, path: str) -> int:
        """
        imports all Hand History files from specified path to database.
        """
        ids = self.db.get_all_ids()
        hands_imported = 0
        for subdir, dirs, files in os.walk(path):
            self.lg.debug(f"importing {subdir + os.sep}")
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

    def get_rake(
        self,
        period: PERIODS = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> [Decimal, dict[Decimal], dict[Decimal]]:
        """
        Calculate contributed rake. Returns total rake, and rake separeted by weeks and months
        period: can be only one of these: cw, pw, cm, pm (means Current|Previos Week|Month)
        start_date: indicate from what date the rake is calculated
        end_date: indicate until what date the rake is calculated
        IMPORTANT! if predefined_period is set, start and end dates will be overwritten
        """
        if period:
            start_date, end_date = period_to_dates(period)
        result = self.db.get_rake(self.player, start_date, end_date)
        if not result:
            return 0, {}, {}
        total_rake = sum(map(lambda x: x[1], result))
        weekly = sum_by_weeks(result)
        monthly = sum_by_month(result)
        return total_rake, weekly, monthly

    def get_profit(
        self,
        period: PERIODS = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> [Decimal, dict[Decimal], dict[Decimal]]:
        """
        Calculate profit/loss. Returns total profit, and profit separeted by weeks and months
        period: can be only one of these: cw, pw, cm, pm (means Current|Previos Week|Month)
        start_date: indicate from what date the rake is calculated
        end_date: indicate until what date the rake is calculated
        IMPORTANT! if predefined_period is set, start and end dates will be overwritten
        """
        if period:
            start_date, end_date = period_to_dates(period)
        result = self.db.get_profit(self.player, start_date, end_date)
        if not result:
            return 0, {}, {}
        total_profit = sum(map(lambda x: x[1], result))
        weekly = sum_by_weeks(result)
        monthly = sum_by_month(result)
        if self.chart:
            self._draw_chart(result)
        return total_profit, weekly, monthly

    def _draw_chart(self, data) -> None:
        """
        It draws chart based on provided data, and saves it to file.
        """
        sorted_res = sorted(data, key=lambda x: x[0])
        dates, values = zip(*sorted_res)
        sum_profit = cumulate_profit(values)
        hands = [i for i in range(len(values))]
        plt.figure(figsize=(19.2, 10.8))
        plt.plot(hands, sum_profit, linestyle="-", color="g")
        plt.title("Profit")
        plt.xlabel("Hands")
        plt.ylabel("Profit, $")
        plt.xlim(xmin=0)
        plt.grid(True)
        file_name = (
            f"chart_{dates[0].year}-{dates[0].month}-{dates[0].day}"
            f"_to_{dates[-1].year}-{dates[-1].month}-{dates[-1].day}.png"
        )
        plt.savefig(OUTPUT_DIR + file_name)
        plt.show()
        plt.close()

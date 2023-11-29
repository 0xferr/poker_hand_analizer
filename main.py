from datetime import datetime
from tracker_utils.logger import logger
from tracker_utils.tracker import Tracker
from tracker_utils.config import read_config, update_config
from tracker_utils.io import parser, print_results


PERIODS_NAMES = {
    "cw": "Current Week",
    "pw": "Previous Week",
    "cm": "Current Month",
    "pm": "Previous Month",
}


def main():
    config = read_config(section="tracker")

    player = config["player_name"]
    folder = config["import_folder"]

    args = parser()
    lg.info(args)

    tr = Tracker(player=player, chart=bool(args.chart))
    # Import HH to DB
    if args.import_hh:
        if args.import_hh != "":
            folder = args.import_hh
        print(f"Importing HHs from folder: {folder}")
        tr.import_hh(folder)

    # setting player_name
    if args.player:
        tr.player = args.player
        player = args.player

    # display results
    if args.results:
        start_date = None
        end_date = None
        period = None
        parts = args.results.split("=")
        if len(parts) == 2:
            query_type, date_range = parts
            if query_type == "since":
                start_date = datetime.strptime(date_range, "%d/%m/%Y")
            elif query_type == "before":
                end_date = datetime.strptime(date_range, "%d/%m/%Y")
            elif query_type == "between":
                start_date, end_date = map(
                    lambda x: datetime.strptime(x, "%d/%m/%Y"),
                    date_range.split("-"),
                )
        elif args.results:
            if args.results in PERIODS_NAMES.keys():
                period = args.results
            elif args.results != "all":
                lg.error(
                    f"Wrong period '{args.results}'. Expecting one of these: {PERIODS_NAMES.keys}"
                )

        profit = tr.get_profit(period=period, start_date=start_date, end_date=end_date)
        rake = tr.get_rake(period=period, start_date=start_date, end_date=end_date)
        print_results(profit, rake)

    if args.save:
        update_config("player_name", player)
        update_config("import_folder", folder)
    tr.db.close()


if __name__ == "__main__":
    lg = logger(__name__)
    main()

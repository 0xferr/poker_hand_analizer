import argparse


def parser():
    """parse command line"""
    parser = argparse.ArgumentParser(description="CLI for tracker")
    parser.add_argument(
        "--import",
        dest="import_hh",
        const="",
        nargs="?",
        help="Import hand history from the specified folder",
    )
    parser.add_argument(
        "--results",
        dest="results",
        const="all",
        nargs="?",
        help="Profit/Rake query in the format 'since|before=01/11/2023' or 'between=01/10/2023-20/10/2023'.\
              Or 'cw'/'pw'/'cm'/'pm' for Current/Previous Week/Month",
    )
    parser.add_argument(
        "--player",
        dest="player",
        help="Specify Player name",
    )
    parser.add_argument(
        "--chart",
        dest="chart",
        nargs="?",
        const=True,
        help="Show Chart",
    )
    parser.add_argument(
        "--save",
        dest="save",
        nargs="?",
        const=True,
        help="Save Player name and import folder to config.ini",
    )
    return parser.parse_args()


def print_results(profit, rake):
    """print results"""
    print("\t\tProfit\t\tRake")
    print(f"For period:\t{profit[0]:.0f}\t\t{rake[0]:.0f}")
    print("Weekly")
    for key in rake[1].keys():
        print(f"{key}\t\t{profit[1][key]:.0f}\t\t{rake[1][key]:.0f}")
    print("\nMonthly\t\tProfit\t\tRake")
    for key in rake[2].keys():
        print(f"{key}\t\t{profit[2][key]:.0f}\t\t{rake[2][key]:.0f}")

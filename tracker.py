import os
from tracker_utils import *

TEST_DIR = "./test_hhs"
START_DIR = r"C:\MyHandsArchive_H2N\Pacific\2023"
START_DIR2 = r"C:\MyHandsArchive_H2N\2023\6\4"


def analyze_dir(trdb: tracker_db, hh_dir=TEST_DIR, ids_in_db=set()):
    # output = []
    for subdir, dirs, files in os.walk(hh_dir):
        print(f"importing {subdir + os.sep}")
        for file in files:
            filepath = subdir + os.sep + file
            if file.endswith(".txt") and not ("ID #" in file):
                with open(filepath, "r") as f:
                    # print(f"Importing file {filepath}")
                    hh = f.read()
                    res = parse_file(hh, ids_in_db)
                    if res:
                        trdb.import_hands(res)
                        # output.append(res)


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
    trdb = tracker_db(clear_tables=True)
    ids_in_db = set()
    trdb.hand_exist()
    try:
        analyze_dir(trdb, hh_dir=START_DIR2)

    except IOError:
        print("Error: File does not appear to exist.")
    trdb.close()

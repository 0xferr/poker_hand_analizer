import psycopg2
from tracker_utils.config import config
from psycopg2.extras import execute_values


class tracker_db:
    def __init__(self, clear_tables=False):
        self.params = config()
        self.conn = self._connect()
        self.MAIN_TABLE = "main"
        res = self._check_tables(clear_tables)
        print(res)

    ### Service methods:
    def _connect(self) -> None:
        """Connect to the PostgreSQL database server"""
        conn = None
        try:
            # connect to the PostgreSQL server
            print("Connecting to the PostgreSQL database...")
            conn = psycopg2.connect(**self.params)

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            return conn

    # close connection
    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()

    # it checks if table exists
    def _check_tables(self, clear_tables=False) -> None:
        cur = self.conn.cursor()
        cur.execute(
            f"""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_catalog='{self.params['database']}' AND
                    table_schema='public' AND
                    table_name='{self.MAIN_TABLE}'
                    )
            """
        )
        table_exists = cur.fetchone()[0]
        cur.close()
        if not table_exists:
            self._create_table()
            res = "Table is created now"
        elif clear_tables:
            self._drop_table()
            self._create_table()
            res = "Table is cleared"
        else:
            res = "Table already exists"
        print(res)

    # Create table
    def _create_table(self) -> None:
        command = f"""
                    CREATE TABLE {self.MAIN_TABLE} 
                    (
                        id INTEGER PRIMARY KEY,
                        datetime TIMESTAMP WITH TIME ZONE,
                        hh TEXT,
                        game VARCHAR(4),
                        blind_level INTEGER,
                        players_in_hand INTEGER,
                        total_pot DECIMAL(10, 2),
                        rake DECIMAL(10, 2),
                """
        command += (
            ",".join(
                f"p{x} VARCHAR(30), p{x}_cards VARCHAR(17), p{x}_bets DECIMAL(10, 2), p{x}_result DECIMAL(10, 2)"
                for x in range(1, 11)
            )
            + ")"
        )
        cur = self.conn.cursor()
        cur.execute(command)
        cur.close()
        self.conn.commit()

    def clear_table(self) -> None:
        cur = self.conn.cursor()
        cur.execute(f"DELETE FROM {self.MAIN_TABLE}")
        cur.close()
        self.conn.commit()

    def _drop_table(self) -> None:
        cur = self.conn.cursor()
        cur.execute(f"DROP TABLE {self.MAIN_TABLE}")
        cur.close()
        self.conn.commit()

    ### Data Methods:
    # Checks if hand is DB already
    def hand_exist(self, id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self.MAIN_TABLE}
                    WHERE 
                    id={id}                    
                    )
            """
        )
        hand_exists = cur.fetchone()[0]
        cur.close()
        return hand_exists

    # import one hand
    def import_hand(self, hand: tuple | list) -> bool:
        sql = f"INSERT INTO {self.MAIN_TABLE} VALUES %s"
        # check if hand has already been imported
        if self.hand_exist(hand[0]):
            return False
        cur = self.conn.cursor()
        # fill the table
        command = sql % hand
        cur.execute(command)
        cur.close()
        self.conn.commit()
        return True

    # import bunch of hands
    def import_hands(self, hands: tuple | list) -> int:
        # removing from list hands that already exist in DB
        hands_to_import = list(filter(lambda x: not self.hand_exist(x[0]), hands))
        # check if there hands to import
        if len(hands_to_import) == 0:
            return 0

        # bringing the all hands to the same size, otherwise psycopg2 won't work
        hands_to_import.sort(key=len, reverse=True)
        max_len = len(hands_to_import[0])
        unified_hands = tuple(
            map(lambda x: x + (max_len - len(x)) * [None], hands_to_import)
        )
        # fill the table
        try:
            cur = self.conn.cursor()
            sql = f"INSERT INTO {self.MAIN_TABLE} VALUES %s"
            execute_values(cur, sql, unified_hands)
            cur.close()
            self.conn.commit()
            return len(hands_to_import)
        except Exception as exc:
            print(exc)
            return False

    # provides contributed rake for specified player and period
    def get_rake(self, player: str, start_date=None, finish_date=None) -> list:
        date_fltr = ""
        if start_date and finish_date:
            date_fltr = f" AND datetime BETWEEN '{start_date}' and '{finish_date}'"
        elif start_date:
            date_fltr = f" AND datetime > '{start_date}'"
        elif finish_date:
            date_fltr = f" AND datetime < '{finish_date}'"

        output = []
        for i in range(1, 11):
            sql = (
                f"SELECT datetime, (rake * p{i}_bets / total_pot) FROM main"
                f" WHERE p{i}='{player}' AND p{i}_bets>0 AND rake>0"
            )
            sql = sql + date_fltr
            cur = self.conn.cursor()
            cur.execute(sql)
            output.extend(cur.fetchall())
        return output


if __name__ == "__main__":
    from config import config
    import datetime

    to_clear = False
    trdb = tracker_db()
    dt = datetime.datetime.now()
    trdb.import_hand(
        1234567,
        "long text",
        str(dt),
        4,
        73,
        12,
        "player",
        "As Ad Ts 9d",
        10,
        0,
    )
    if to_clear:
        trdb.clear_tables()
    trdb.close()

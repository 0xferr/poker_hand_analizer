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

    # it checks if table exists
    def _check_tables(self, clear_tables=False):
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
            return "Table is created now"
        elif clear_tables:
            self._drop_table()
            self._create_table()
            return "Table is cleared"
        return "Table already exists"

    def _connect(self):
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

    # Create table
    def _create_table(self):
        command = f"""
                    CREATE TABLE {self.MAIN_TABLE} 
                    (
                        id INTEGER PRIMARY KEY,
                        hh TEXT,
                        game VARCHAR(4),
                        blind_level INTEGER,
                        datetime TIMESTAMP WITH TIME ZONE,
                        players_in_hand INTEGER,
                        total_pot INTEGER,
                        rake INTEGER,
                """
        command += (
            ",".join(
                f"p{x} VARCHAR(30), p{x}_cards VARCHAR(17), p{x}_bets INTEGER, p{x}_result INTEGER"
                for x in range(1, 11)
            )
            + ")"
        )
        cur = self.conn.cursor()
        cur.execute(command)
        cur.close()
        self.conn.commit()

    # Checks if hand is DB already
    def hand_exist(self, id):
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
    def import_hand(self, id, *args):
        sql = f"INSERT INTO {self.MAIN_TABLE} VALUES %s"
        # check if hand already imported
        if self.hand_exist(id):
            return False
        cur = self.conn.cursor()
        # fill the table
        command = sql % (id, *args)
        cur.execute(command)
        cur.close()
        self.conn.commit()
        return True

    # import bunch of hands
    def import_hands(self, hand_list):
        # removing from list hands that already exist in DB
        hand_to_import = list(filter(lambda x: not self.hand_exist(x[0]), hand_list))
        # check if there hands to import
        if len(hand_to_import) == 0:
            return False

        # bringing the lists of the hands_list to the same size, because psycopg2 is a piece of shit
        hand_list.sort(key=len, reverse=True)
        max_len = len(hand_list[0])
        unified_hands = tuple(
            map(lambda x: x + (max_len - len(x)) * [None], hand_to_import)
        )

        # fill the table
        try:
            cur = self.conn.cursor()
            sql = f"INSERT INTO {self.MAIN_TABLE} VALUES %s"
            execute_values(cur, sql, unified_hands)
            cur.close()
            self.conn.commit()
            return True
        except Exception as exc:
            print(exc)
            return False

    # close connection
    def close(self):
        if self.conn is not None:
            self.conn.close()

    def clear_table(self):
        cur = self.conn.cursor()
        cur.execute(f"DELETE FROM {self.MAIN_TABLE}")
        cur.close()
        self.conn.commit()

    def _drop_table(self):
        cur = self.conn.cursor()
        cur.execute(f"DROP TABLE {self.MAIN_TABLE}")
        cur.close()
        self.conn.commit()


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

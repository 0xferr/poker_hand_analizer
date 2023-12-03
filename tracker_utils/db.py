import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from decimal import Decimal
from tracker_utils.config import read_config
from tracker_utils.logger import logger

lg = logger("DB")


class tracker_db:
    """
    Connects to PostgreSQL Database. It can creates, drop, clear table.
    Import parsed Hand history. Returns rake and profit data.
    Input:
        clear_tables: if True delete all data in main table.
    Methods:
        close: close connection with DB
        import_hand: imports single parsed hand in DB
        import_hands: imports multiple hands
        get_rake: returns rake for each hand for the indicated period
        get_profit: returns profit/loss for each hand for the indicated period
        get_all_ids: returns all IDs for hands stored in DB
    """

    def __init__(self, clear_tables=False):
        self.params = read_config(section="postgresql")
        self.conn = self._connect()
        self.MAIN_TABLE = "main"
        self._check_tables(clear_tables)

    ### Service methods:
    def _connect(self) -> None:
        """Connect to the PostgreSQL database server"""
        conn = None
        try:
            # connect to the PostgreSQL server
            lg.debug("Connecting to the PostgreSQL database...")
            conn = psycopg2.connect(**self.params)
        except (Exception, psycopg2.DatabaseError) as error:
            lg.error(error)
        finally:
            return conn

    def close(self) -> None:
        """Close the connection to the PostgreSQL database server"""
        if self.conn is not None:
            self.conn.close()

    def _check_tables(self, clear_tables=False) -> None:
        """Checks the existance of main table. If clear_tables=True drops and create main table"""
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
        lg.debug(res)

    def _create_table(self) -> None:
        """Create the main table"""
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
        """Delete all data in main table"""
        cur = self.conn.cursor()
        cur.execute(f"DELETE FROM {self.MAIN_TABLE}")
        cur.close()
        self.conn.commit()

    def _drop_table(self) -> None:
        """Delete the main table"""
        cur = self.conn.cursor()
        cur.execute(f"DROP TABLE {self.MAIN_TABLE}")
        cur.close()
        self.conn.commit()

    ### Data Methods:
    def hand_exist(self, id: int) -> bool:
        """Check if hand with ID is already exist"""
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

    def import_hand(self, hand: tuple | list) -> bool:
        """Import sigle parsed hand to database"""
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

    def import_hands(self, hands: tuple | list) -> int:
        """Import multiple parsed hand to database"""
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
            return 0

    def get_rake(
        self, player: str, start_date=None, finish_date=None
    ) -> list[tuple[datetime, Decimal]]:
        """Return rake for each hand for specified player and period"""
        output = []
        # creating date filter
        date_fltr = self._generate_date_filter(start_date, finish_date)
        # generating query
        for i in range(1, 11):
            sql = (
                f"SELECT datetime, (rake * p{i}_bets / total_pot) FROM {self.MAIN_TABLE}"
                f" WHERE p{i}='{player}' AND p{i}_bets>0 AND rake>0"
            )
            sql = sql + date_fltr
            cur = self.conn.cursor()
            cur.execute(sql)
            output.extend(cur.fetchall())
            cur.close()
        return output

    # returns the list containing profit data for specified player and period
    def get_profit(
        self, player: str, start_date: datetime = None, finish_date: datetime = None
    ) -> list[tuple[datetime, Decimal]]:
        """Return rake for each hand for specified player and period"""
        output = []
        date_fltr = self._generate_date_filter(start_date, finish_date)
        # generating query
        for i in range(1, 11):
            sql = (
                f"SELECT datetime, (p{i}_result - p{i}_bets) FROM {self.MAIN_TABLE}"
                f" WHERE p{i}='{player}' AND p{i}_bets>0"
            )
            sql = sql + date_fltr
            cur = self.conn.cursor()
            cur.execute(sql)
            output.extend(cur.fetchall())
        return output

    def _generate_date_filter(self, start_date: datetime, finish_date: datetime) -> str:
        """Generate date filter for SQL query"""
        date_fltr = ""
        # creating date filter
        if start_date and finish_date:
            date_fltr = f" AND datetime BETWEEN '{start_date}' and '{finish_date}'"
        elif start_date:
            date_fltr = f" AND datetime > '{start_date}'"
        elif finish_date:
            date_fltr = f" AND datetime < '{finish_date}'"
        return date_fltr

    def get_all_ids(self) -> set[int]:
        """Return the IDs of all hands in database"""
        sql = f"SELECT id FROM {self.MAIN_TABLE}"
        cur = self.conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        output = set(map(lambda x: x[0], result))
        cur.close()
        return output

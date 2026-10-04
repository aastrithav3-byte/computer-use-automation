import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "bank.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            member_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_number TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL NOT NULL,
            FOREIGN KEY (member_id)
                REFERENCES members(member_id)
        )
        """
    )

    # Sample members
    cursor.execute(
        """
        INSERT OR IGNORE INTO members
        (member_id, name, status)
        VALUES (?, ?, ?)
        """,
        ("12345", "Maya Patel", "Active"),
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO members
        (member_id, name, status)
        VALUES (?, ?, ?)
        """,
        ("67890", "Jonah Kim", "Active"),
    )

    # Maya's accounts
    cursor.execute(
        """
        INSERT OR IGNORE INTO accounts
        (account_number, member_id, account_type, balance)
        VALUES (?, ?, ?, ?)
        """,
        ("CHK-1001", "12345", "Checking", 3120.25),
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO accounts
        (account_number, member_id, account_type, balance)
        VALUES (?, ?, ?, ?)
        """,
        ("SAV-1001", "12345", "Savings", 5240.00),
    )

    # Jonah's accounts
    cursor.execute(
        """
        INSERT OR IGNORE INTO accounts
        (account_number, member_id, account_type, balance)
        VALUES (?, ?, ?, ?)
        """,
        ("CHK-2001", "67890", "Checking", 1450.75),
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO accounts
        (account_number, member_id, account_type, balance)
        VALUES (?, ?, ?, ?)
        """,
        ("SAV-2001", "67890", "Savings", 8125.50),
    )

    connection.commit()
    connection.close()


def get_member(member_id: str):
    connection = get_connection()

    member = connection.execute(
        """
        SELECT member_id, name, status
        FROM members
        WHERE member_id = ?
        """,
        (member_id,),
    ).fetchone()

    connection.close()

    if member is None:
        return None

    return dict(member)


def get_member_accounts(member_id: str):
    connection = get_connection()

    accounts = connection.execute(
        """
        SELECT account_number, member_id, account_type, balance
        FROM accounts
        WHERE member_id = ?
        ORDER BY account_type
        """,
        (member_id,),
    ).fetchall()

    connection.close()

    return [dict(account) for account in accounts]


def get_account(member_id: str, account_type: str):
    connection = get_connection()

    account = connection.execute(
        """
        SELECT account_number, member_id, account_type, balance
        FROM accounts
        WHERE member_id = ?
          AND LOWER(account_type) = LOWER(?)
        """,
        (member_id, account_type),
    ).fetchone()

    connection.close()

    if account is None:
        return None

    return dict(account)


if __name__ == "__main__":
    initialize_database()
    print(f"Database created successfully: {DB_PATH}")
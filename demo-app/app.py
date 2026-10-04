from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from database import (
    initialize_database,
    get_member,
    get_member_accounts,
    get_account,
)

app = FastAPI()

# Make sure the SQLite database/tables exist
initialize_database()


@app.get("/", response_class=HTMLResponse)
def home(member_id: str = ""):

    # No search yet
    if not member_id:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Member Servicing System</title>
        </head>

        <body>

            <h1>Member Servicing System</h1>

            <h2>Member Search</h2>

            <p>Enter a Member ID to search for a member.</p>

            <form method="get" action="/">

                <label for="member_id">Member ID</label>

                <br><br>

                <input
                    type="text"
                    id="member_id"
                    name="member_id"
                    placeholder="Enter Member ID"
                    required
                >

                <br><br>

                <button type="submit">
                    Search Member
                </button>

            </form>

        </body>
        </html>
        """

    # Search SQLite database
    member = get_member(member_id)

    if member is None:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Member Not Found</title>
        </head>

        <body>

            <h1>Member Servicing System</h1>

            <h2>Member Not Found</h2>

            <p>
                No member was found with Member ID:
                {member_id}
            </p>

            <a href="/">
                Back to Member Search
            </a>

        </body>
        </html>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Results</title>
    </head>

    <body>

        <h1>Member Servicing System</h1>

        <h2>Search Results</h2>

        <p>Member found.</p>

        <p>
            <strong>Member ID:</strong>
            {member["member_id"]}
        </p>

        <p>
            <strong>Name:</strong>
            {member["name"]}
        </p>

        <p>
            <strong>Status:</strong>
            {member["status"]}
        </p>

        <a href="/member/{member["member_id"]}">
            Open Member
        </a>

        <br><br>

        <a href="/">
            New Search
        </a>

    </body>
    </html>
    """


@app.get("/member/{member_id}", response_class=HTMLResponse)
def member_details(member_id: str):

    member = get_member(member_id)

    if member is None:
        return """
        <h1>Member Not Found</h1>
        <a href="/">Back to Member Search</a>
        """

    accounts = get_member_accounts(member_id)

    accounts_html = ""

    for account in accounts:
        account_type = account["account_type"]

        accounts_html += f"""
        <li>
            <a href="/member/{member_id}/account/{account_type.lower()}">
                {account_type}
            </a>
        </li>
        """

    if not accounts_html:
        accounts_html = "<li>No accounts found.</li>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Member Details</title>
    </head>

    <body>

        <h1>Member Details</h1>

        <p>
            <strong>Member ID:</strong>
            {member["member_id"]}
        </p>

        <p>
            <strong>Name:</strong>
            {member["name"]}
        </p>

        <p>
            <strong>Status:</strong>
            {member["status"]}
        </p>

        <h2>Accounts</h2>

        <ul>
            {accounts_html}
        </ul>

        <a href="/">
            Back to Member Search
        </a>

    </body>
    </html>
    """


@app.get(
    "/member/{member_id}/account/{account_type}",
    response_class=HTMLResponse,
)
def account_details(
    member_id: str,
    account_type: str,
):

    member = get_member(member_id)

    if member is None:
        return """
        <h1>Member Not Found</h1>
        <a href="/">Back to Member Search</a>
        """

    account = get_account(
        member_id,
        account_type,
    )

    if account is None:
        return """
        <h1>Account Not Found</h1>
        <a href="/">Back to Member Search</a>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Account Details</title>
    </head>

    <body>

        <h1>Account Details</h1>

        <p>
            <strong>Member:</strong>
            {member["name"]}
        </p>

        <p>
            <strong>Account Type:</strong>
            {account["account_type"]}
        </p>

        <p>
            <strong>Account Number:</strong>
            {account["account_number"]}
        </p>

        <p>
            <strong>Current Balance:</strong>
            ${account["balance"]:,.2f}
        </p>

        <br>

        <a href="/member/{member_id}">
            Back to Member Details
        </a>

    </body>
    </html>
    """
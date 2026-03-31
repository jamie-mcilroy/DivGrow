MASTER_RETIREMENT_NAME = "MasterRetirement"
MASTER_RETIREMENT_SOURCE_ACCOUNTS = {"JamieRSP", "MichelleRSP"}
ALL_INVESTMENTS_NAME = "All Investments"


def group_holdings_by_account(holdings_rows):
    accounts = {}
    for row in holdings_rows:
        account = row["Account"].strip()
        symbol = row["Symbol"].strip()
        holding = {
            "Account": account,
            "Symbol": symbol,
            "Quantity": float(row["Quantity"]),
        }

        if "Price" in row:
            holding["Price"] = float(row["Price"]) if row.get("Price") not in ("", None) else 0.0
        if "Yield" in row:
            holding["Yield"] = float(row["Yield"]) if row.get("Yield") not in ("", None) else 0.0

        accounts.setdefault(account, []).append(holding)
    return accounts


def add_master_retirement_account(accounts):
    combined_holdings = []
    for account_name in MASTER_RETIREMENT_SOURCE_ACCOUNTS:
        for holding in accounts.get(account_name, []):
            combined_holdings.append(
                {
                    key: value for key, value in holding.items() if key != "Account"
                }
            )

    if combined_holdings:
        accounts[MASTER_RETIREMENT_NAME] = combined_holdings

    return accounts


def add_all_investments_account(accounts):
    combined_holdings = []
    for account_name, holdings in accounts.items():
        if account_name == MASTER_RETIREMENT_NAME:
            continue
        for holding in holdings:
            combined_holdings.append(
                {
                    key: value for key, value in holding.items() if key != "Account"
                }
            )

    if combined_holdings:
        accounts[ALL_INVESTMENTS_NAME] = combined_holdings

    return accounts


def prepare_accounts(holdings_rows):
    accounts = group_holdings_by_account(holdings_rows)
    accounts = add_master_retirement_account(accounts)
    accounts = add_all_investments_account(accounts)
    for account, holdings in accounts.items():
        for holding in holdings:
            holding["Account"] = account
    return accounts

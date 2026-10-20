ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"


def get_users():
    import pandas as pd

    users = pd.read_csv(f"{ROOT}\\reports\\utils\\users.csv")
    ACCOUNTS = {}
    for index, row in users.iterrows():
        ACCOUNTS[row["username"]] = {"role": row["role"]}
    ACCOUNTS["admin"] = {"role": "admin"}
    return ACCOUNTS

import sys
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\reports\\load_balanced")
sys.path.append(f"{ROOT}\\reports")
from app_prod import app

CERT_PATH = f"\\\\OMPYTSRVD00001V\\testssl\\okadamanila_com_2025"
if __name__ == "__main__":
    import sys
    port = int(sys.argv[1])  # Get port number from command-line argument
    # ssl_context=(f"{CERT_PATH}\\2025_wildcard_okadamanila_com.PEM", f"{CERT_PATH}\\2025_wildcard_okadamanila_com_key.pem"),
    app.run_server(host="0.0.0.0",port=port,debug=False)

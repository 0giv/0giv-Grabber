# -*- coding: utf-8 -*-
# cookies_via_cdp_ws.py
import os, sys, time, json, csv, argparse, socket, subprocess
from urllib.request import urlopen
from datetime import datetime
from websocket import create_connection

def default_user_data_dir():
    return os.path.join(os.environ.get("LOCALAPPDATA",""), "Google","Chrome","User Data")

def find_chrome():
    cands = [
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Google","Chrome","Application","chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Google","Chrome","Application","chrome.exe"),
        "chrome.exe",
    ]
    for p in cands:
        if p == "chrome.exe":
            return p
        if os.path.exists(p):
            return p
    raise RuntimeError("chrome.exe bulunamadı; --chrome-binary ile yol verin")

def find_free_port(start=9222, span=100):
    for port in range(start, start+span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("Boş port bulunamadı")

def wait_devtools_ws_url(port, timeout=20):
    url = f"http://127.0.0.1:{port}/json/version"
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urlopen(url, timeout=2) as r:
                data = json.loads(r.read().decode("utf-8"))
                ws = data.get("webSocketDebuggerUrl")
                if ws:
                    return ws
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("DevTools /json/version hazır değil")

def dt_iso(ts):
    try:
        if not ts:
            return ""
        return datetime.utcfromtimestamp(float(ts)).isoformat() + "Z"
    except Exception:
        return ""

def main():
    ap = argparse.ArgumentParser(description="Export all Chrome cookies (values included) via raw CDP WebSocket.")
    ap.add_argument("--user-data-dir", default=default_user_data_dir(), help="Chrome user data dir")
    ap.add_argument("--profile", default="Default", help='Chrome profile dir (Default, Profile 1, ...)')
    ap.add_argument("--out", default="cookies_live_cdp.csv", help="Output CSV")
    ap.add_argument("--json", default=None, help="Optional JSON output path")
    ap.add_argument("--chrome-binary", default=None, help="Path to chrome.exe (if needed)")
    ap.add_argument("--domain", default=None, help="Filter by domain substring (e.g. paypal.com)")
    ap.add_argument("--headless", action="store_true", help="Run Chrome headless")
    ap.add_argument("--port", type=int, default=None, help="Remote debugging port (auto if omitted)")
    args = ap.parse_args()

    # Profil kontrol
    if not os.path.isdir(args.user_data_dir):
        print(f"[!] user-data-dir yok: {args.user_data_dir}")
        sys.exit(2)
    prof_path = os.path.join(args.user_data_dir, args.profile)
    if not os.path.isdir(prof_path):
        profs = [d for d in os.listdir(args.user_data_dir)
                 if os.path.isdir(os.path.join(args.user_data_dir, d))
                 and (d == "Default" or d.startswith("Profile "))]
        print(f"[!] Profil klasörü yok: {prof_path}")
        print("[i] Mevcut profiller:", ", ".join(profs) if profs else "(yok)")
        sys.exit(2)

    # Aynı profille açık Chrome kalmasın (aksi halde kilit/çakışma olur).
    # Gerekirse Görev Yöneticisi'nden chrome.exe süreçlerini kapatın.

    chrome = args.chrome_binary or find_chrome()
    port = args.port or find_free_port(9222, 100)

    launch = [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={args.user_data_dir}",
        f"--profile-directory={args.profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank",
    ]
    if args.headless:
        launch.insert(1, "--headless=new")

    try:
        proc = subprocess.Popen(launch, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[!] Chrome başlatılamadı: {e}")
        sys.exit(2)

    try:
        ws_url = wait_devtools_ws_url(port, 25)  # /json/version → webSocketDebuggerUrl
        ws = create_connection(ws_url)

        # Network domain'i etkinleştir ve çerezleri çek
        ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))

        cookies = []
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 2 and "result" in msg:
                cookies = msg["result"].get("cookies", [])
                break

        if args.domain:
            cookies = [c for c in cookies if args.domain.lower() in c.get("domain","").lower()]

        if not cookies:
            print("[i] Çerez bulunamadı (profil boş olabilir ya da yanlış profil).")
        else:
            # CSV çıktı
            with open(args.out, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["domain","name","value","path","expires_iso","httpOnly","secure",
                            "sameSite","priority","sourceScheme","partitionKey","sameParty"])
                for c in cookies:
                    w.writerow([
                        c.get("domain",""),
                        c.get("name",""),
                        c.get("value",""),   # ← DÜZ METİN VALUE
                        c.get("path",""),
                        dt_iso(c.get("expires",0)),
                        c.get("httpOnly",""),
                        c.get("secure",""),
                        c.get("sameSite",""),
                        c.get("priority",""),
                        c.get("sourceScheme",""),
                        c.get("partitionKey",""),
                        c.get("sameParty",""),
                    ])
            print(f"[+] Yazıldı: {args.out}  (toplam {len(cookies)})")

            # İsteğe bağlı JSON
            if args.json:
                with open(args.json, "w", encoding="utf-8") as jf:
                    json.dump(cookies, jf, ensure_ascii=False, indent=2)
                print(f"[+] JSON yazıldı: {args.json}")

        ws.close()
    finally:
        try:
            proc.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    main()

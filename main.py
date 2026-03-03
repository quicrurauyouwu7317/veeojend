import asyncio, aiohttp, ujson, time, sys, os, random, traceback, threading, primp

from datetime import datetime

from pathlib import Path

try:

    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    UVLOOP = True

except (ImportError, NotImplementedError):

    UVLOOP = False

try:

    from colorama import Fore, Style, init

    init(autoreset=True)

except ImportError:

    class Fore:

        RED=GREEN=YELLOW=CYAN=WHITE=MAGENTA=BLUE=""

    class Style:

        RESET_ALL=BRIGHT=""

TOKEN         = "MTQxMzYyMTU0MjI0MzQwMTg5MA.GpTG-L.FM8MfACpxKwdt6djH5hOMeKhI5pu7ekAKKpy2A"

PASSWORD      = "sennibroulufa-3869@yopmail.ozm.fr"

GUILD_ID      = "1370039139537256548"

TARGET_VANITY = "elifers"

POLL_INTERVAL = 0.02

PROXY_FILE    = "proxies.txt"

PTB_BASE      = "https://ptb.discord.com/api/v9"

INVITE_CHECK  = f"https://discord.com/api/v10/invites/{TARGET_VANITY}"

def ts():

    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def log(level, msg):

    colors = {

        "INFO": Fore.CYAN, "SUCCESS": Fore.GREEN, "FAIL": Fore.RED,

        "WARN": Fore.YELLOW, "FIRE": Fore.MAGENTA, "BOOT": Fore.WHITE,

        "MFA": Fore.BLUE, "SNIPE": Fore.GREEN, "POLL": Fore.YELLOW,

    }

    print(f"{Fore.WHITE}[{ts()}] {colors.get(level,'')}{f'[{level}]':<9}{Style.RESET_ALL} {msg}", flush=True)

DISCORD_HEADERS = {

    "Authorization": TOKEN,

    "Content-Type": "application/json",

    "User-Agent": (

        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "

        "(KHTML, like Gecko) discord/1.0.1137 Chrome/130.0.6723.191 "

        "Electron/33.4.0 Safari/537.36"

    ),

    "X-Super-Properties": (

        "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNl"

        "X2NoYW5uZWwiOiJwdGIiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC4xMTM3Iiwib3NfdmVy"

        "c2lvbiI6IjEwLjAuMjYxMDAiLCJvc19hcmNoIjoieDY0IiwiYXBwX2FyY2giOiJ4NjQi"

        "LCJzeXN0ZW1fbG9jYWxlIjoiZW4tVVMiLCJoYXNfY2xpZW50X21vZHMiOmZhbHNlLCJi"

        "cm93c2VyX3VzZXJfYWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBX"

        "aW42NDsgeDY0KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBk"

        "aXNjb3JkLzEuMC4xMTM3IENocm9tZS8xMzAuMC42NzIzLjE5MSBFbGVjdHJvbi8zMy40"

        "LjAgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjMzLjQuMCIsIm9zX3Nk"

        "a192ZXJzaW9uIjoiMjYxMDAiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozODUxMTUsIm5h"

        "dGl2ZV9idWlsZF9udW1iZXIiOjYwOTI2LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxs"

        "fQ=="

    ),

}

PROXIES = []

def load_proxies():

    path = Path(PROXY_FILE)

    if not path.exists():

        path.write_text("")

    proxies = [(f"http://{p}" if not p.startswith("http") else p)

               for p in path.read_text().splitlines() if p.strip()]

    if proxies:

        log("INFO", f"Loaded {len(proxies)} proxies.")

    else:

        log("WARN", "No proxies — running direct.")

    return proxies or [None]

def get_proxy():

    p = random.choice(PROXIES)

    return p if p else None

_snipe_started = False

_sniped        = False

_lock          = threading.Lock()

def snipe_thread():

    global _sniped, _snipe_started

    t_start = time.perf_counter()

    try:

        client = primp.Client(impersonate="chrome_131", verify=False)

        log("MFA", "Triggering MFA...")

        r1 = client.patch(

            f"{PTB_BASE}/guilds/{GUILD_ID}/vanity-url",

            headers=DISCORD_HEADERS,

            json={"code": "a"}

        )

        log("MFA", f"Step 1: {r1.status_code} | {r1.text[:200]}")

        mfa_token = None

        if r1.status_code == 200:

            log("MFA", "No MFA required.")

        elif r1.status_code in (400, 401) and "mfa" in r1.json():

            ticket = r1.json()["mfa"]["ticket"]

            r2 = client.post(

                f"{PTB_BASE}/mfa/finish",

                headers=DISCORD_HEADERS,

                json={"ticket": ticket, "mfa_type": "password", "data": PASSWORD}

            )

            log("MFA", f"Step 2: {r2.status_code} | {r2.text[:200]}")

            if r2.status_code != 200:

                log("FAIL", f"MFA failed: {r2.text[:200]}")

                _sniped = _snipe_started = False

                return

            mfa_token = r2.json().get("token")

            if not mfa_token:

                log("FAIL", "No token returned.")

                _sniped = _snipe_started = False

                return

            log("MFA", f"MFA done in {(time.perf_counter()-t_start)*1000:.0f}ms")

        else:

            log("FAIL", f"Unexpected: {r1.status_code} | {r1.text[:200]}")

            _sniped = _snipe_started = False

            return

        snipe_headers = dict(DISCORD_HEADERS)

        if mfa_token:

            snipe_headers["x-discord-mfa-authorization"] = mfa_token

        log("FIRE", "Firing PATCH...")

        r3 = client.patch(

            f"{PTB_BASE}/guilds/{GUILD_ID}/vanity-url",

            headers=snipe_headers,

            json={"code": TARGET_VANITY}

        )

        ms = (time.perf_counter() - t_start) * 1000

        log("SNIPE", f"PATCH -> {r3.status_code} in {ms:.1f}ms | {r3.text[:200]}")

        if r3.status_code in (200, 201, 204):

            log("SUCCESS", f"Sniped discord.gg/{TARGET_VANITY} in {ms:.0f}ms!")

            time.sleep(2)

            os._exit(0)

        else:

            log("WARN", "PATCH failed — resetting...")

            _sniped = _snipe_started = False

    except Exception as e:

        log("FAIL", f"Snipe crashed: {e}")

        traceback.print_exc()

        _sniped = _snipe_started = False

def trigger_snipe():

    global _snipe_started

    with _lock:

        if _snipe_started:

            return

        _snipe_started = True

    log("FIRE", "Vanity FREE — launching snipe!")

    threading.Thread(target=snipe_thread, daemon=True).start()

async def poll_worker(session):

    log("POLL", f"Polling discord.gg/{TARGET_VANITY} every {int(POLL_INTERVAL*1000)}ms (50x/sec)...")

    while not _sniped:

        try:

            async with session.get(

                INVITE_CHECK,

                proxy=get_proxy(),

                timeout=aiohttp.ClientTimeout(total=4),

                headers={"User-Agent": DISCORD_HEADERS["User-Agent"]},

            ) as r:

                if r.status == 404:

                    log("POLL", "404 — vanity is FREE!")

                    trigger_snipe()

                elif r.status == 429:

                    body  = await r.json(loads=ujson.loads)

                    retry = body.get("retry_after", 5)

                    log("WARN", f"Rate-limited — sleeping {retry:.1f}s")

                    await asyncio.sleep(retry)

                    continue

        except asyncio.CancelledError:

            break

        except Exception as e:

            log("WARN", f"Poll error: {e}")

        await asyncio.sleep(POLL_INTERVAL)

async def main():

    global PROXIES

    PROXIES = load_proxies()

    print(f"""

{Fore.MAGENTA}╔══════════════════════════════════════════════════════════════════╗

║          MAXIMUM SPEED DISCORD VANITY SNIPER v10                 ║

╠══════════════════════════════════════════════════════════════════╣

║  Target    : discord.gg/{TARGET_VANITY:<42}║

║  Guild ID  : {GUILD_ID:<54}║

║  Engine    : {"uvloop ⚡" if UVLOOP else "asyncio":<54}║

║  Detection : 20ms polling (50x/sec)                              ║

║  Snipe     : MFA fresh -> single PATCH                          ║

║  primp     : chrome_131                                          ║

╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

""")

    log("BOOT", f"Watching discord.gg/{TARGET_VANITY} 24/7. Ctrl+C to stop.\n")

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=600,

                                     use_dns_cache=True, keepalive_timeout=60)

    async with aiohttp.ClientSession(connector=connector,

                                     json_serialize=ujson.dumps) as session:

        await poll_worker(session)

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        log("INFO", "Sniper stopped.")

        sys.exit(0)

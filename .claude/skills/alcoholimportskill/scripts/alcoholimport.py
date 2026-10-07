#!/usr/bin/env python3
"""alcoholimport — new US alcohol importers (demand) <-> wholesalers/distributors (supply).

Source: TTB FOIA List of Permittees, republished weekly.
  https://www.ttb.gov/public-information/foia/list-of-permittees

Commands (run from the skill folder: data/ and raw snapshots resolve to the skill folder, file arguments to your cwd):
  pull                     download this week's TTB files into data/raw/<YYYY-MM-DD>/
  feed  [--industry X] [--diff]  this week's new permits (event unit = permit)
  supply [--state ST]      wholesalers, deduped to ONE row per company
  sites  IN.csv OUT.jsonl  find each row's own website (search -> name-match gate)
  import-sites IN.csv MAP OUT.jsonl  merge websites found by an Exa agent run / VA sheet
  sweep  IN.jsonl OUT.jsonl  fetch homepage + contact pages, extract inboxes
  export IN.jsonl OUT.csv [--unit event|company]  send-ready rows only
  gate   FILE              print rows | inboxes | COMPANIES (the Unit Law gate)

Stdlib only. Optional EXA_API_KEY in .env switches `sites` from DuckDuckGo to Exa.
Every long step checkpoints to jsonl: re-running skips rows already done.
"""
import argparse, csv, datetime as dt, gzip, html, io, json, os, random, re, sys, time
import urllib.parse, urllib.request, concurrent.futures as cf

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(SKILL, "data")
RAW = os.path.join(DATA, "raw")
BASE = "https://www.ttb.gov/system/files/2025-04/"  # TTB keeps this path; if 404, re-scrape LIST_PAGE
LIST_PAGE = "https://www.ttb.gov/public-information/foia/list-of-permittees"
FILES = {
    "new": "FRL_Basic_Permits_Issued_Since_the_Last_Publication.csv",
    "importer": "FRL_Alcohol_Importer_Permit_List.csv",
    "wholesaler": "FRL_Alcohol_Wholesaler_Permit_List.csv",
    "spirits": "FRL_Spirits_Producers_and_Bottlers_List.csv",
    "wine": "FRL_Wine_Producer_and_Blender_Permit_List.csv",
}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def load_env():
    p = os.path.join(SKILL, ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def get(url, timeout=20, data=None, headers=None, cap=3_000_000):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(cap) if cap else r.read()  # cap protects the sweep; pull must pass cap=None
        return r.status, r.geturl(), raw.decode(r.headers.get_content_charset() or "utf-8", "replace")


def norm(s):
    """Company key: uppercase, punctuation stripped, legal suffixes dropped, whitespace collapsed."""
    s = re.sub(r"[^A-Z0-9 ]+", " ", (s or "").upper())
    s = re.sub(r"\b(LLC|L L C|INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LP|LLP|PLLC|THE|DBA)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def read_csv(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    fields = fields or (list(rows[0].keys()) if rows else ["empty"])
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def snapshots():
    return sorted(d for d in os.listdir(RAW) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)) if os.path.isdir(RAW) else []


# ---------------------------------------------------------------- pull
def cmd_pull(a):
    day = a.date or dt.date.today().isoformat()
    base = BASE
    try:
        _, _, page = get(LIST_PAGE, 30)
        m = re.search(r'href="(/system/files/[^"]+/)FRL_Alcohol_Importer_Permit_List\.csv"', page)
        if m:
            base = "https://www.ttb.gov" + m.group(1)
        upd = re.search(r"updated:\s*([A-Z][a-z]+ \d{1,2}, \d{4})", page)
        print("TTB page says updated:", upd.group(1) if upd else "unknown")
    except Exception as e:
        print("list page unreachable, using known path:", e)
    bodies = {}
    for key, fn in FILES.items():
        st, _, body = get(base + fn, 180, cap=None)
        bodies[fn] = body
        n = len(list(csv.DictReader(io.StringIO(body.lstrip("\ufeff")))))
        print(f"{key:10s} {st} rows={n}")
    # TTB republishes weekly; a second pull in the same week is the SAME publication.
    # Saving it as a new snapshot would make `feed --diff` report 0 new permits.
    snaps = [d for d in snapshots() if d != day]
    if snaps and not a.force:
        prev = os.path.join(RAW, snaps[-1])
        same = all(os.path.exists(os.path.join(prev, fn + ".gz")) and
                   gzip.open(os.path.join(prev, fn + ".gz"), "rt", encoding="utf-8", newline="").read() == body
                   for fn, body in bodies.items())
        if same:
            print(f"identical to snapshot {snaps[-1]} — same TTB publication, nothing saved (use --force to save anyway)")
            return
    out = os.path.join(RAW, day)
    os.makedirs(out, exist_ok=True)
    for fn, body in bodies.items():
        with gzip.open(os.path.join(out, fn + ".gz"), "wt", encoding="utf-8", newline="") as f:
            f.write(body)
    print("saved", out)


# ---------------------------------------------------------------- feed
def cmd_feed(a):
    """Default: TTB's own 'Basic Permits Issued Since the Last Publication' file in the latest snapshot.
    --diff: permits present in the latest snapshot's full lists but absent from the previous snapshot
    (a cross-check that also catches permits TTB published without the flag)."""
    snaps = snapshots()
    if not snaps:
        sys.exit("no snapshots — run `pull` first")
    cur = snaps[-1]
    if a.diff:
        if len(snaps) < 2:
            sys.exit("--diff needs two weekly snapshots in data/raw/; run without --diff")
        prev = snaps[-2]
        rows, old = [], set()
        for key in ("importer", "wholesaler", "spirits", "wine"):
            rows += read_csv(os.path.join(RAW, cur, FILES[key] + ".gz"))
            old |= {r["Permit_Number"] for r in read_csv(os.path.join(RAW, prev, FILES[key] + ".gz"))}
        new = [r for r in rows if r["Permit_Number"] not in old]
        how = f"diff {prev} -> {cur}"
    else:
        new = read_csv(os.path.join(RAW, cur, FILES["new"] + ".gz"))
        how = f"TTB 'issued since last publication' list in snapshot {cur}"
    if a.industry:
        new = [r for r in new if a.industry.lower() in r["Industry_Type"].lower()]
    if a.state:
        new = [r for r in new if r["State"] == a.state.upper()]
    for r in new:
        r["company"] = r["Operating_Name"] or r["Owner_Name"]
        r["snapshot"] = cur
    from collections import Counter
    print(how, "| new permits:", len(new))
    print(Counter(r["Industry_Type"] for r in new).most_common())
    if not new:
        print("WARNING: 0 rows — nothing written")
        return
    out = a.out or os.path.join(DATA, f"feed_{cur}.csv")
    write_csv(out, new)
    print("wrote", out)


# ---------------------------------------------------------------- supply
def cmd_supply(a):
    cur = snapshots()[-1]
    rows = read_csv(os.path.join(RAW, cur, FILES["wholesaler"] + ".gz"))
    if a.state:
        rows = [r for r in rows if r["State"] == a.state.upper()]
    by = {}
    for r in rows:
        k = norm(r["Owner_Name"])
        r["company"] = r["Owner_Name"]  # one owner, many DBAs: the first row's DBA can be another brand entirely
        r["premises"] = 1
        if k in by:
            by[k]["premises"] += 1
        else:
            by[k] = r
    out = list(by.values())
    if a.sample:
        random.seed(a.seed)
        out = random.sample(out, min(a.sample, len(out)))
    print(f"wholesaler rows {len(rows)} | COMPANIES {len(by)} | written {len(out)}")
    print("NOTE: these are WHOLESALER PERMIT holders, mostly wineries/brands selling their own product — "
          "NOT a distributor list. Find sites, sweep, then `export --kind distributor`.")
    path = a.out or os.path.join(DATA, f"supply_{cur}{'_' + a.state.upper() if a.state else ''}.csv")
    write_csv(path, out)
    print("wrote", path)


# ---------------------------------------------------------------- sites
BAD = re.compile(r"(linkedin|facebook|instagram|twitter|x\.com|yelp|bizapedia|opencorporates|dnb\.com|zoominfo|bloomberg|manta|"
                 r"buzzfile|wikipedia|mapquest|yellowpages|ttb\.gov|sec\.gov|corporationwiki|bbb\.org|crunchbase|untappd|vivino|"
                 r"wine-searcher|importgenius|panjiva|volza|importyeti|seair|tradeindia|alibaba|amazon|walmart|totalwine|drizly|"
                 r"youtube|tiktok|pinterest|google\.|apple\.com|indeed|glassdoor|bizjournals|prnewswire|chamberofcommerce|"
                 r"opengovus|govcb|allbiz|cylex|ourcompanies|companiesus|sos\.|\.gov$|duckduckgo|bing\.com|tripadvisor|"
                 r"winespectator|vinepair|liquor\.com|beeradvocate|ratebeer|distiller\.com|delectable|cellartracker|"
                 r"nytimes|forbes|reddit|quora|zillow|loopnet|bestplaces|city-data|whitepages|spokeo|signalhire|rocketreach)", re.I)
STOP = {"WINE", "WINES", "SPIRITS", "IMPORTS", "IMPORT", "IMPORTERS", "IMPORTING", "DISTRIBUTING", "DISTRIBUTION", "DISTRIBUTORS",
        "DISTRIBUTOR", "BEVERAGE", "BEVERAGES", "GROUP", "USA", "US", "AMERICA", "AMERICAN", "INTERNATIONAL", "INTL", "TRADING",
        "HOLDINGS", "ENTERPRISES", "BRANDS", "AND", "OF", "SALES", "SELECTIONS", "CELLARS", "LIQUOR", "LIQUORS", "BEER", "FINE"}


def name_tokens(name):
    t = [w for w in norm(name).split() if len(w) >= 3]
    core = [w for w in t if w not in STOP]
    return core or t


def domain_matches(domain, name):
    """Gate: the domain must carry the company's own name. A search hit that doesn't is not the company."""
    root = re.sub(r"^www\.", "", domain.lower()).split(".")[0].replace("-", "")
    toks = [w.lower() for w in name_tokens(name)]
    if not toks:
        return False
    if any(len(w) >= 4 and w in root for w in toks):
        return True
    initials = "".join(w[0] for w in norm(name).lower().split())
    return len(initials) >= 3 and initials in root


def search_ddg(q):
    data = urllib.parse.urlencode({"q": q}).encode()
    st, _, body = get("https://html.duckduckgo.com/html/", 20, data=data)
    urls = [urllib.parse.unquote(u) for u in re.findall(r'uddg=([^&"]+)', body)]
    if st != 200 or ("anomaly" in body.lower() and not urls):
        raise RuntimeError("ddg blocked")
    return list(dict.fromkeys(urls))


def search_exa(q):
    body = json.dumps({"query": q, "numResults": 8, "type": "auto"}).encode()
    _, _, out = get("https://api.exa.ai/search", 30, data=body,
                    headers={"x-api-key": os.environ["EXA_API_KEY"], "Content-Type": "application/json"})
    return [r["url"] for r in json.loads(out).get("results", [])]


def done_keys(path, key="Permit_Number"):
    if not os.path.exists(path):
        return set()
    return {json.loads(l).get(key) for l in open(path) if l.strip()}


def cmd_import_sites(a):
    """Merge websites found elsewhere (Exa agent JSON, a VA's sheet) into a sites jsonl.
    MAP is .json ({"rows":[{"permit","website","business_kind"}]} or a list) or .csv (permit,website[,business_kind])."""
    if a.map.endswith(".json"):
        m = json.load(open(a.map))
        m = m.get("rows", m) if isinstance(m, dict) else m
    else:
        m = read_csv(a.map)
    by = {x["permit"]: x for x in m}
    n = 0
    with open(a.out, "w") as f:
        for r in read_csv(a.inp):
            x = by.get(r["Permit_Number"], {})
            site = (x.get("website") or "").strip()
            host = urllib.parse.urlparse(site).netloc.lower() if site else ""
            if host and BAD.search(host):
                host = ""  # a directory page is not the company's front door
            r.update(site=f"https://{host}" if host else "", site_status="found" if host else "no_match",
                     business_kind=x.get("business_kind", ""))
            n += bool(host)
            f.write(json.dumps(r) + "\n")
    print(f"{n} sites merged -> {a.out}")


def cmd_sites(a):
    load_env()
    search = search_exa if os.environ.get("EXA_API_KEY") else search_ddg
    rows = read_csv(a.inp)
    seen = done_keys(a.out)
    todo = [r for r in rows if r["Permit_Number"] not in seen]
    print(f"{len(rows)} rows, {len(todo)} to search via {search.__name__}")
    with open(a.out, "a") as f:
        for i, r in enumerate(todo, 1):
            names = [n for n in dict.fromkeys([r.get("Operating_Name"), r["Owner_Name"]]) if n]
            site, status, errored = "", "no_match", False
            for n in names:
                q = f"{n} {r['City'].title()} {r['State']} wine spirits"
                try:
                    urls = search(q)
                except Exception as e:
                    errored = True
                    print(f"  search error ({n}): {e}")
                    time.sleep(10)
                    continue
                for u in urls:
                    host = urllib.parse.urlparse(u).netloc.lower()
                    if host and not BAD.search(host) and domain_matches(host, n):
                        site, status = f"https://{host}", "found"
                        break
                if site:
                    break
                time.sleep(a.delay)
            if errored and not site:
                continue  # not checkpointed: a failed search is not an answer, retry on the next run
            r.update(site=site, site_status=status)
            f.write(json.dumps(r) + "\n")
            f.flush()
            if i % 10 == 0:
                print(i, "done")
            time.sleep(a.delay)


# ---------------------------------------------------------------- sweep
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
JUNK = re.compile(r"(example\.|sentry|wixpress|domain\.com|email\.com|yourdomain|\.png$|\.jpg$|\.gif$|\.webp$|\.svg$|"
                  r"godaddy|squarespace|shopify|wordpress|grappos|vinoshipper|wix\.com|grant|careers@|jobs@|hr@|press@|media@|webmaster@|none@|noreply|no-reply|donotreply|privacy@|abuse@|@2x)", re.I)
CONTACT_HINT = re.compile(r'href="([^"#]*(contact|about|connect|reach|inquir|supplier|brand|partner)[^"#]*)"', re.I)
ROLE_RANK = ["supplier", "brand", "newbrand", "partner", "purchas", "buyer", "sales", "info", "contact", "hello", "office", "orders"]


def rank_email(e):
    lp = e.split("@")[0].lower()
    for i, k in enumerate(ROLE_RANK):
        if k in lp:
            return i
    return len(ROLE_RANK)


def sweep_one(r):
    site = r.get("site")
    if not site:
        r.update(email="", emails="", sweep_status="no_site")
        return r
    host = urllib.parse.urlparse(site).netloc.replace("www.", "")
    # /contact is queued up front: a slow or blocked homepage must not hide the contact page
    pages, found, ok = [site, site + "/contact", site + "/contact-us"], set(), False
    for i, url in enumerate(pages[:7]):
        try:
            _, final, body = get(url, 25)
            ok = True
        except Exception:
            continue
        body = re.sub(r"\\u[0-9a-fA-F]{4}", " ", body)  # JSON-escaped text: \\u2028 glued onto addresses
        body = html.unescape(body).replace("[at]", "@").replace("(at)", "@")
        found |= {e.strip(".").lower() for e in EMAIL.findall(body) if not JUNK.search(e)}
        if i == 0:
            for m in CONTACT_HINT.finditer(body):
                u = urllib.parse.urljoin(final, m.group(1))
                if host in urllib.parse.urlparse(u).netloc and u not in pages:
                    pages.append(u)
    own = sorted((e for e in found if e.split("@")[1].endswith(host)), key=rank_email)
    other = sorted((e for e in found if e not in own), key=rank_email)
    best = (own or other or [""])[0]
    r.update(email=best, emails=";".join(own + other), email_on_own_domain=bool(own),
             sweep_status=("email" if best else "no_email") if ok else "unverified")
    return r


def cmd_sweep(a):
    rows = [json.loads(l) for l in open(a.inp) if l.strip()]
    seen = done_keys(a.out)
    todo = [r for r in rows if r["Permit_Number"] not in seen]
    print(f"{len(rows)} rows, {len(todo)} to sweep")
    with open(a.out, "a") as f, cf.ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(sweep_one, todo):
            f.write(json.dumps(r) + "\n")
            f.flush()


# ---------------------------------------------------------------- export / gate
def cmd_export(a):
    rows = [json.loads(l) for l in open(a.inp) if l.strip()]
    rows = [r for r in rows if r.get("email") and (r.get("email_on_own_domain") or not a.own_domain_only)]
    if a.kind:
        kinds = set(a.kind.split(","))
        rows = [r for r in rows if r.get("business_kind") in kinds]
    if a.unit == "company":
        best = {}
        for r in rows:
            k = norm(r["Owner_Name"])
            if k not in best or rank_email(r["email"]) < rank_email(best[k]["email"]):
                best[k] = r
        rows = list(best.values())
    rows.sort(key=lambda r: (r["State"], r["company"]))
    fields = ["company", "Owner_Name", "Operating_Name", "Industry_Type", "Permit_Number", "City", "State", "Prem_Zip",
              "site", "business_kind", "email", "emails", "email_on_own_domain"]
    write_csv(a.out, rows, fields)
    gate(rows)
    print("wrote", a.out)


def gate(rows):
    print(f"rows {len(rows)} | inboxes {len({(r.get('email') or '').upper() for r in rows if r.get('email')})} "
          f"| COMPANIES {len({norm(r['Owner_Name']) for r in rows})}")


def cmd_gate(a):
    rows = [json.loads(l) for l in open(a.inp) if l.strip()] if a.inp.endswith(".jsonl") else read_csv(a.inp)
    gate(rows)
    from collections import Counter
    c = Counter(r.get("sweep_status") or r.get("site_status") for r in rows)
    if any(c):
        print(dict(c))
    k = Counter(r.get("business_kind") for r in rows if r.get("business_kind"))
    if k:
        print("business_kind:", dict(k))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("pull"); x.add_argument("--date"); x.add_argument("--force", action="store_true")
    x = s.add_parser("feed"); x.add_argument("--diff", action="store_true"); x.add_argument("--industry"); x.add_argument("--state"); x.add_argument("--out")
    x = s.add_parser("supply"); x.add_argument("--state"); x.add_argument("--sample", type=int); x.add_argument("--seed", type=int, default=7); x.add_argument("--out")
    x = s.add_parser("sites"); x.add_argument("inp"); x.add_argument("out"); x.add_argument("--delay", type=float, default=1.5)
    x = s.add_parser("import-sites"); x.add_argument("inp"); x.add_argument("map"); x.add_argument("out")
    x = s.add_parser("sweep"); x.add_argument("inp"); x.add_argument("out"); x.add_argument("--workers", type=int, default=12)
    x = s.add_parser("export"); x.add_argument("inp"); x.add_argument("out"); x.add_argument("--unit", choices=["event", "company"], default="event"); x.add_argument("--own-domain-only", action="store_true"); x.add_argument("--kind", help="comma list, e.g. distributor")
    x = s.add_parser("gate"); x.add_argument("inp")
    a = p.parse_args()
    globals()["cmd_" + a.cmd.replace("-", "_")](a)


if __name__ == "__main__":
    main()

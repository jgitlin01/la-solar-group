---
name: alcoholimportskill
description: Weekly feed of brand-new US alcohol importers (and new wineries/distilleries/wholesalers) from the Treasury TTB permit list, matched to the businesses that sell to them. Pulls the federal file, diffs it week over week, finds each permit holder's own website, sweeps it for an inbox and exports send-ready CSVs. Trigger on "alcoholimportskill", "alcohol importers", "new importer permits", "TTB list", "wine importers", "spirits importers", "run the alcohol market".
---

# alcoholimportskill — new alcohol importers ↔ the businesses that sell to them

## Caveman line

*A foreign wine brand can't put wine in American stores alone. US law (the three-tier
system) forces it through a licensed distributor, and a distributor's whole job is
getting product into stores.* A brand also has to buy label approvals (COLA), a customs
bond and state licences, plus freight and insurance, before it can sell anything.

The moment is the federal importer permit being issued, and the Treasury's alcohol
bureau (TTB) publishes those **weekly**.

## Measured numbers (2026-10-06 file, TTB page "updated October 5, 2026")

| List | Rows (permits) | Companies | Flagged new this week |
|---|---|---|---|
| Importer | 21,365 | 18,999 | 24 |
| Wholesaler | 38,669 | 32,814 | 42 |
| Distilled Spirits Plant | 5,565 | 5,148 | 12 |
| Wine Producer | 18,123 | 16,533 | 18 |

"Companies" = `norm(Owner_Name)` (uppercase, punctuation and legal suffixes stripped). "New this week" = rows
in TTB's own "Basic Permits Issued Since the Last Publication" file (96 total). The `New_Permit_Flag` column in
the full lists disagrees by one: it marks 11 distilled spirits plants, not 12. Trust the dedicated file.

**Contact rate, measured on a 100-row sample** (Exa agent to find the site, $0.90 total,
then this script's homepage + `/contact` sweep):

| Sample | Own site found | Inbox found |
|---|---|---|
| New importers (all 24 flagged this week) | 7 (29%) | 4 (17%) |
| Existing importers (26 random) | 4 (15%) | 2 (8%) |
| Wholesaler permits (50 random companies) | 20 (40%) | 11 (22%) |

What these numbers mean, said plainly:

- **The government file has no email, no phone and no issue date.** Every inbox comes
  from the company's own website.
- **New importers are mostly too new to have a website.** A 17% contact rate on about 24
  a week is about **4 mailable new importers a week** from this method alone. That is thin.
- **TRAP: a TTB "wholesaler" permit is NOT a distributor.** Of the 20 wholesaler-permit
  holders with sites, only 2 were real distributors. The rest were wineries, cideries
  and brands that hold the permit so they can sell their own product. **Never count the
  wholesaler list as the supply side.** Gate on `business_kind == distributor` (from the
  site) before quoting a supply number.

## Unit Law for this market

- **Demand unit = the permit (event).** A company that gets a new importer permit is a
  new opportunity. Use `export --unit event`.
- **Supply unit = the company.** One distributor with six warehouse permits is ONE
  relationship. Use `export --unit company`. Johnson Brothers alone holds permits in
  several states.
- Always run `gate` and quote **companies** first. If rows, inboxes and companies differ,
  say all three.

## How to run it

Run every command from the skill folder (`<repo root>/.claude/skills/alcoholimportskill`).
`data/` resolves to the skill folder, and the file arguments you pass resolve to your
current directory. The script uses only Python 3's standard library, so there is nothing
to install.

```bash
mkdir -p work
python3 scripts/alcoholimport.py pull       # this week's 5 TTB files -> data/raw/<date>/ (skips if same publication)
python3 scripts/alcoholimport.py feed       # TTB's "issued since last publication" list (all industries)
python3 scripts/alcoholimport.py feed --industry importer --out data/demand_new.csv
python3 scripts/alcoholimport.py feed --diff   # cross-check: full lists vs previous weekly snapshot
python3 scripts/alcoholimport.py supply --state CA --out data/supply_CA.csv   # wholesaler PERMITS, 1 row per owner
# feed also takes --state ST
```

- If `pull` says "identical to snapshot", TTB hasn't republished yet, and `feed` keeps
  serving the latest list.
- `feed --diff` needs two *different* weekly snapshots.
- `supply` does **not** give you distributors. It gives everyone holding a wholesaler
  permit (CA: 9,370 permits, 8,893 owners, mostly wineries). You only get distributors
  after the site-finding step labels each `business_kind`, then
  `export --kind distributor`.

Finding websites (pick one):

1. **Exa agent from Claude (what the 100-row measurement used).** Give the rows to
   `mcp__Exa__agent_run` with `effort: "auto"` and a $5 budget. Ask for one row per permit
   (`permit`, `website` or null, `business_kind` = distributor / importer_brand /
   winery_or_producer / retailer / other / unknown). Never guess a site. Save the result
   as JSON or CSV, then:
   `python3 scripts/alcoholimport.py import-sites data/demand_new.csv MAP.json work/demand.sites.jsonl`
   - `data/exa_sites_map_2026-10-07.csv` is the map from the 100-row measurement. It
     holds only the **31 sites found** out of those 100 rows: the 24 new importers, 26
     random older importers and 50 random wholesaler owners. It matches 7 of this week's
     new importers and just 9 of California's 8,893 wholesaler owners. Rows it doesn't
     cover are labelled `not_searched`, never `no_match`. For anything new, run a new
     agent search.
   - The map can be `.json` (the agent's `{"rows":[...]}`) or `.csv` (`permit,website,business_kind`).
   - `effort: "low"` ran 3 searches for 100 rows and found 9 sites. That is a run
     problem, not a market answer. Use `auto`.
2. **`sites` command:** set `EXA_API_KEY` in `.env` for the Exa search API. **Without a
   key it is effectively dead.** It falls back to DuckDuckGo, which blocked from the very
   first query in both test runs (HTTP 202 "anomaly" page or connection reset). There is
   no Bing fallback; Bing's HTML results were junk when tested. A failed search is not
   checkpointed, so re-running retries it.

**Be honest about what a run without an Exa agent search delivers:**
- New importers: about 4 inboxes a week out of about 24, using the committed map, and
  only for the week it was built.
- California distributors: **zero**. The one California distributor in the map
  (caroyalspirits.com) didn't respond when fetched.

Use `export --include-no-email` to keep every row with its TTB street address. That
address is the only contact detail every row has, and it's enough for direct mail.

Supply side, end to end (same steps as demand):

```bash
python3 scripts/alcoholimport.py supply --state CA --out data/supply_CA.csv
# Exa agent on data/supply_CA.csv -> MAP (8,893 owners: sample or pre-filter by name first)
python3 scripts/alcoholimport.py import-sites data/supply_CA.csv MAP work/supply.sites.jsonl
python3 scripts/alcoholimport.py sweep  work/supply.sites.jsonl work/supply.swept.jsonl
```

Then sweep and export:

```bash
python3 scripts/alcoholimport.py sweep  work/demand.sites.jsonl work/demand.swept.jsonl
python3 scripts/alcoholimport.py gate   work/demand.swept.jsonl
python3 scripts/alcoholimport.py export work/demand.swept.jsonl deliverables/<date>_demand.csv --unit event
python3 scripts/alcoholimport.py export work/supply.swept.jsonl deliverables/<date>_supply.csv --unit company --kind distributor
```

`sites` and `sweep` checkpoint to jsonl. Re-running skips rows already done. To redo a
sweep, delete its output file first. Rows marked `unverified` (timeout, dead
certificate, proxy 502) are retried automatically on the next `sweep`. `work/` is scratch (gitignored), so start each
week's run with fresh file names. Check `email_on_own_domain`: a False value can still
be right (Bouchard's site is mdhamerica.com, its inboxes are @bpfamerica.com), but it
can also be a PR agency. Use `--own-domain-only` for a strict list.

## Weekly rhythm

Every Monday: `pull`, then `feed`. `feed` always reads TTB's dedicated "issued since the
last publication" file. `feed --diff` is a cross-check that needs two different weekly
snapshots in `data/raw/`. Snapshots are the only date record you have (the file carries no
issue date), so **commit each week's `data/raw/<date>/`**. Measure 7-day, 30-day and
90-day counts after a month of snapshots, and only then say whether the market is
growing.

## Gotchas (each one produced a believable wrong number)

- **Download truncation.** The HTTP helper caps reads at 3 MB to protect the sweep.
  `pull` must pass `cap=None`, or the 38,669-row wholesaler file silently shrinks to
  about 23,600 rows.
- **Counting lines is not counting rows.** Quoted fields can contain newlines, so count
  with `csv.DictReader`.
- **TTB file path.** Files live under `/system/files/2025-04/`. `pull` re-scrapes the
  list page for the current folder and falls back to that path.
- **A failed fetch is `unverified`, never `no_email`.** 5 of 50 supply sites were
  expired-certificate or dead hosts. Those were recorded as unverified, not as negatives.
- **Queue `/contact` up front.** Johnson Brothers' homepage hides its inboxes, which sit
  on `/contact`. Only queuing contact pages after the homepage loaded missed them.
- **Widget-vendor inboxes.** `info@grappos.com` (a store-locator widget) appeared on a
  winery site. Vendor domains are in `JUNK`. Add any new ones you see.
- **JSON-escaped page text.** `\u2028` glued onto an address (`u2028gilauripr@...`). The sweep strips `\uXXXX` escapes first.
- **Same-week re-pull.** Saving an identical publication as a new snapshot made `feed` report 0 new. `pull` now compares content (byte-exact: gzip text mode turns `\r\n` into `\n` and breaks the comparison) and skips duplicates.
- **Supply company name.** The first premises row's DBA can be another brand (Young's Market showed as "Republic National Distributing"). `supply` uses the legal `Owner_Name`.
- **Non-sales inboxes.** grants@, careers@, press@ and similar are dropped. Gmail and
  sbcglobal inboxes are kept, because small owners really use them.
- **Multi-state firms.** Johnson Brothers SD exported `infonc@`, the North Carolina
  branch. For multi-state distributors, check the inbox matches the state before you
  send.

## Next sourcing moves (not built yet)

- **Supply front door:** distributors publish their own "new brand submissions" or
  "supplier inquiries" email. Better places to find them than TTB: state wholesaler
  associations' member directories, WSWA (Wine & Spirits Wholesalers of America)
  convention exhibitor and attendee lists, and distributor pages that list supplier
  portfolios.
- **Other sellers for the same demand list:** COLA/label compliance firms, customs
  brokers and bond providers, product liability insurers, 3PL and bonded warehouses.
  Source each one the same way as distributors: one row per company, gated on the
  homepage.
- **Demand depth:** add new Distilled Spirits Plants and Wine Producers (about 29 a
  week). Same sellers, slightly older businesses, more likely to have a website.

## Files

- `scripts/alcoholimport.py` — the pipeline (pull, feed, supply, sites, import-sites,
  sweep, export, gate)
- `data/raw/<date>/*.csv.gz` — weekly TTB snapshots (commit these)
- `data/*.csv` — this week's feed and supply slices
- `deliverables/<date>_*.csv` — send-ready rows only
- `work/` — scratch jsonl checkpoints (gitignored)
- `.env.example` — optional `EXA_API_KEY`

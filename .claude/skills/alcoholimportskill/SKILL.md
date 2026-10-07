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
| Importer | 21,365 | 19,152 | 24 |
| Wholesaler | 38,669 | 32,814 | 42 |
| Distilled Spirits Plant | 5,565 | 5,157 | 11 |
| Wine Producer | 18,123 | 16,576 | 18 |

"Companies" = `norm(Owner_Name)` (uppercase, punctuation and legal suffixes stripped).

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

Run all commands from the skill folder. The script uses only Python 3's standard
library, so there is nothing to install.

```bash
cd .claude/skills/alcoholimportskill
python3 scripts/alcoholimport.py pull                 # this week's 5 TTB files -> data/raw/<date>/
python3 scripts/alcoholimport.py feed                 # new permits (diff vs last snapshot)
python3 scripts/alcoholimport.py feed --industry importer --out data/demand_new.csv
python3 scripts/alcoholimport.py supply --state CA    # wholesaler permits, 1 row per company
```

Finding websites (pick one):

1. **Exa agent from Claude (what the 100-row measurement used).** Give the rows to
   `mcp__Exa__agent_run` with `effort: "auto"` and a $5 budget. Ask for one row per permit
   (`permit`, `website` or null, `business_kind` = distributor / importer_brand /
   winery_or_producer / retailer / other / unknown). Never guess a site. Save the result
   as JSON or CSV, then:
   `python3 scripts/alcoholimport.py import-sites data/demand_new.csv MAP.json work/demand.sites.jsonl`
   - `effort: "low"` ran 3 searches for 100 rows and found 9 sites. That is a run
     problem, not a market answer. Use `auto`.
2. **`sites` command:** set `EXA_API_KEY` in `.env` for the Exa search API. Without a key
   it falls back to DuckDuckGo, which **bot-blocks after a handful of queries** (HTTP
   202 "anomaly" page). Bing's HTML results were junk (university sites for company
   names). Don't rely on either for more than about 10 rows.

Then sweep and export:

```bash
python3 scripts/alcoholimport.py sweep  work/demand.sites.jsonl work/demand.swept.jsonl
python3 scripts/alcoholimport.py gate   work/demand.swept.jsonl
python3 scripts/alcoholimport.py export work/demand.swept.jsonl deliverables/<date>_demand.csv --unit event
python3 scripts/alcoholimport.py export work/supply.swept.jsonl deliverables/<date>_supply.csv --unit company
```

`sites` and `sweep` checkpoint to jsonl. Re-running skips rows already done. To redo a
sweep, delete its output file first.

## Weekly rhythm

Every Monday: `pull`, then `feed`. You only get a true week-over-week **refill rate**
once there are two snapshots in `data/raw/`. Until then `feed` falls back to TTB's own
`New_Permit_Flag`. Snapshots are the only date record you have (the file carries no
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

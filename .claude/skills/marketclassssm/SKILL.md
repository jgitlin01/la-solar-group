---
name: marketclassssm
description: The market production line — pick a market that passes the vibe check, measure it live from government data, find where the contacts actually live, source both sides, and build the runnable skill. Trigger on "marketclassssm", "find me a market", "new market from scratch", "build me a market", "next market", "market research".
---

# marketclassssm — the market production line

## North star

One sentence in — *"I need a market"* — and out the same session with three
things: a market that passes the vibe check with MEASURED numbers, both sides
sourced with real contacts, and a working skill that rebuilds the lists on
demand.

This file is the compressed memory of building roofing, landscaping,
commercial production, and trucking. Every rule below was paid for.

---

## PHASE 0 — THE OBJECT METHOD: fifty markets without opening Google

Look around the room. Desk, chair, lamp, coffee cup, dumbbell, a pack of ramen. Every banal
object hides a supply chain, and somewhere inside it: *someone who urgently needs X* ↔
*someone whose entire business is selling X*. Lineage: Leonard Read's "I, Pencil"; Heidegger's
broken hammer — a tool is invisible while it works, you only see it when you stop using it.

But the object is the DOOR, never the room. Run three steps, not one:

1. **Object** → who buys this in bulk?
2. **Moment** → what EVENT makes them buy it all at once, and is that event public? (a gym
   opening, a café opening, a brand deciding to enter the US). No moment = no market
   (water bottle, pen, a laptop).
3. **Front door** → where does that buyer publish its own email on purpose? (PHASE 3)

When the object fails, ask what ROOM it sits in — "car" fails, a dealership lot and a repair
shop's bays both pass. Most passing objects collapse into one family: **every business that
opens fills an empty room**; the gymskill machinery (franchise coming-soon pages, OSM by tag,
contact-page sweep) runs on any of them by changing one tag.

The caveman line must survive the object: *gym owner needs dumbbell, dealer gives dumbbell*;
*Korean ramen company can't put ramen in American stores alone, distributor's job is putting
stuff in stores*. If the object needs a paragraph to explain (floor plan, FCC Part 15), the
caveman line has not survived — go back to the room. Then run PHASE 1 as usual.

## PHASE 1 — Market selection (the vibe check, plus the deeper filters)

The three questions, in order — a market that fails one is dead:

1. **Do they invoice for work?** A business that does a job and sends a bill
   feels money directly. (Or takes a cut when a deal closes.)
2. **Is their next dollar blocked by something they genuinely have to BUY?**
   The nuclear question — it kills ~60% of candidate markets, which is the
   point. The best answer is COMPULSORY purchasing (trucking: illegal to
   operate without insurance, suffocates without factoring). "They could use
   marketing" is a weak yes; "the law/math forces the purchase before dollar
   one" is a great yes.
3. **Growing or drowning?** Measure it, never assume it.

The deeper filters that separate a good market from a great one:

- **Stacked buyer.** Can the same demand-side company be matched to MULTIPLE
  seller species at once? Map the BLEEDS (think bleeds, not needs): every
  place the buyer loses money, and who gets paid to stop it. Trucking had
  six. Each bleed is a separate seller species — a separate supply lane
  against the same demand list.
- **Feed vs list.** Does the demand side REFILL? A license roster trickles;
  trucking mints 1,400/week forever. A feed beats a list — "every Monday is a
  fresh list of owners whose problem started this week" is the strongest
  possible rhythm. Measure the refill rate with a windowed count
  (7d / 30d / 90d / YTD).
- **Durable supply.** Supply that earns recurring revenue per signed customer
  (factoring: every invoice; insurance: annual renewal; fuel cards: every
  gallon; accountants: monthly) is durable. One-shot sellers are not.
- **Government data FIRST.** Before anything else, probe whether a public
  database carries the demand side with CONTACTS. The best markets ship
  send-ready from the government file (owner name + email), zero enrichment.
  Saturation of that data is NOT a kill — measure it, never assume it
  disqualifies the market.

Run all three questions and all four filters before any agent runs.

## PHASE 2 — Measure at the wall (before any building)

- Query the real database the same day. Every number you will repeat anywhere
  gets measured, never estimated. Windowed counts, freshness of newest row,
  field fill rates (owner name %, email %).
- **Audit real rows before believing a field list** — published field lists
  omit the best fields (FMCSA's `company_officer_1` = the owner's name; the
  `classdef` for-hire flag; both missing from the handoff that preceded the
  build).
- Banked source recipes: Socrata (data.transportation.gov etc.), DOL H-2B
  disclosure files, state license rosters (CSLB postback, FL plain CSV),
  NPPES/NPI, smallworldlabs + MapYourShow trade-show directories (recipes in
  the roofing/landscaping/trucking skill gotchas — read those SKILL.md files
  when touching those platforms).
- Numeric traps that produce BELIEVABLE wrong answers (the worst kind):
  Socrata numeric fields are STRINGS (`"10" <= "5"` — enumerate with IN, never
  range-compare); MapYourShow pipe syntax keeps only the last category ID;
  multi-valued fields are semicolon-joined (match LIKE, never equality);
  emails are case-inconsistent (dedupe on UPPER); dates are strings (compare
  as tuples or zero-padded strings, prefer recency when merging re-filers).

## PHASE 3 — WHERE DOES THE CONTACT LIVE?

Before declaring a side unmailable, answer: **where does this business put its own
email on purpose?** Government files carry a business's ADDRESS and almost never its
EMAIL — permits, licences, registries, closure notices are filed to locate a
business, not to contact it. Measuring only there understates the mailable side by
an order of magnitude: on gyms it was 387 from the government file and 8,314 once
the front doors were swept.

A business that wants customers publishes its inbox where customers look:

- its own website (contact-page sweep: 57–77% on gyms, 50–62% on labs)
- a franchisor's per-location page (club-level inbox on 15/17 gym brands; two had open APIs)
- OpenStreetMap (`website`/`email` tags, bulk, free, per state)
- trade-show floor plans and association sponsor pages (supply)

Run this check BEFORE the fan-out is judged, not after. The government row stays as the
timing STORY; the inbox comes from the front door.

## PHASE 4 — THE UNIT LAW

**Every count must name its unit, and the unit must be the real thing on the
other end — one company, or one event.**

Break this and you build on a number that turns out to be a different number.

Registries multiply rows. An establishment registry files per PLANT, not per
firm — one company can appear twenty times or more. A multi-office brokerage
and a chain retailer do the same. Deduping by email is not enough either: one
firm can register several contacts.

**Demand and supply have different units, and they are not interchangeable.**

| Side | Unit | Why |
|---|---|---|
| Demand | the **event** | One filing, one licence, one certification per row is correct. A company that filed three trademarks is three real opportunities. A farm that filed twice is one farm — dedupe by inbox there. Decide per source what the event is. |
| Supply | the **company** | There is one relationship per company. Two inboxes at one factory is one company, not two. Always dedupe supply to one row per company, best contact kept. |

**The gate, run before any supply number is written down:**

```python
print(f"rows {len(r)} | inboxes {len({x['email'].lower() for x in r})} "
      f"| COMPANIES {len({norm(x['company']) for x in r})}")
```

Normalise on uppercase, punctuation stripped, whitespace collapsed. **Lead with
companies.** If the three numbers differ, say all three; never quote the largest.

### A counting rule proven on one source is not portable

`landscapingskill` states "every count is unique inboxes" and that was correct
*there* — H-2B employer rows are one inbox per employer, so inbox and company
coincide. Carry that phrasing to an establishment registry, where they diverge
by up to 21x, and the number comes out wrong. Re-derive the unit every time the
source changes.

### The reporting rule that follows

When a target is named — "1,000 each side" — the answer is the count of the unit
that is actually real, or the honest statement that it does not exist in the
cache. Say it on day one, while it is still a sourcing decision.

## PHASE 5 — Supply sourcing doctrine

- **DEDUPE SUPPLY TO ONE ROW PER COMPANY BEFORE COUNTING IT.** See the Unit Law
  above. An establishment registry, a multi-office brokerage and a chain retailer
  all produce several rows per seller.
- **Native-email lanes are the product; enrichment is a bonus, never the
  plan.** Hunt for supply INSIDE the government data first: when one email
  sits on many UNRELATED filings, that inbox is a service provider (the H-2B
  attorney pattern; trucking's registration agents). Separate them from
  private fleets: shared name-stem = one owner's LLCs; email naming either
  client = the client's own address (self-email test); when the name can't
  settle it, the homepage does.
- **A search result is not a supply list.** Neural search (Exa,
  category:company, about a tenth of a cent per result) returns every
  insurance agency in Texas for a trucking-insurance query — only 11% named
  trucking. Two passes: (1) qualify — the row must prove its segment in its
  own name/domain and must not read as a demand-side company; (2) **verify
  against its own homepage with curl** — free, parallel, checkpointed to jsonl
  as it goes. Brand-named companies (Mudflap, Mazon) fail name-vocab
  qualification — gate those segments at the PAGE with BOTH vocabularies
  required (segment vocab >= 3 AND market vocab >= 1).
- **A failed fetch is NEVER a negative.** Timeouts record `unverified`, not
  "no signal" — recording them as negative silently deletes real companies.
  But shipping unverified rows unjudged once put a food distributor and
  none@none.com in a supply file: unverifiable rows ship only if their own
  domain names the service they sell.
- Sweep foreign firms hiding behind .com (UK phone formats, VAT/Companies
  House markers, ≥2 hits = demote).
- **Enrichment law (three measurements):** homepage-gated rows enrich at
  60–75%. A batch far below that is a RUN problem (tool settings/caps) —
  rerun before re-sourcing. Rank batches by page depth (`signal_hits`) and
  feed deep-page rows first. Never enrich send-ready rows or previously-fed
  rows — cut delta files.
- State fan-out revives dead query yield; dedupe by root domain; drop
  aggregator-shaped domains (≥5 distinct titles across queries).

## PHASE 6 — The skill build

Mirror the existing skills (truckingskill is the newest reference; roofing and
landscaping are siblings). Structure: `SKILL.md` + `scripts/<market>.py` +
`data/*.csv.gz` + `.env.example`.

- **Every skill build ENDS with the naive-agent dry run** — 2+ rounds, fresh
  agent, zero context, STRICTLY read-only on the skill folder. "A glossy
  everything-worked report is a FAILED test." Not optional; it is the gate
  before the skill ships, and it runs in the BUILD session, never later.

## PHASE 7 — Close-out (same session)

- Naive-agent dry runs on the skill (2+ rounds) BEFORE the session ends.
- Update the market's handoff notes with the measured numbers and any new traps
  found, so the next market starts from them.
- Deliverables date-stamped. Enrichment delta files cut so previously-paid rows
  are never re-fed.

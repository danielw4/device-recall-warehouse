# SPEC: FDA device recalls vs. 510(k) clearances

Frozen 2026-10-04, before any modelling. Changes after this date are logged at the bottom.

## Question

Among medical devices cleared through the FDA 510(k) pathway, how often and how soon is a
clearance later named in a recall, and does that differ by clearance type (Traditional,
Special, Abbreviated) once follow-up time, medical specialty and device class are accounted for?

Secondary, descriptive: what root causes do firms report for recalls, and how has the share
attributed to software design and device design moved over time?

## Data

openFDA bulk downloads (CC0), export dated 2026-10-02, listed at https://api.fda.gov/download.json:

| File | Records | Grain |
|---|---|---|
| device/recall | 59,344 | one recalled product (several per recall event) |
| device/510k | 176,223 | one 510(k) decision |
| device/classification | 7,094 | one product code |

Join keys: `recall.k_numbers[]` -> `510k.k_number`; `510k.product_code` -> `classification.product_code`.

Known properties of the real files (profiled 2026-10-04, use these as acceptance checks):

- 13,052 distinct K numbers appear in recalls; 13,046 exist in the 510(k) file.
- About a third of recall rows carry no K number and cannot be linked. Every rate in this
  project is therefore a lower bound.
- At least one malformed date exists (`event_date_initiated = '10-08-17'`).
- About 100 recall links are dated before the clearance decision they cite.
- Raw files are single ~1.5 GB JSON objects; DuckDB cannot read them directly on macOS, so
  they are streamed to newline-delimited JSON first.

## Cohort and definitions (frozen)

- **Cohort:** 510(k) decisions with `decision_code` starting `SE` (found substantially
  equivalent), `decision_date` on or after 2003-01-01, `clearance_type` in
  Traditional / Special / Abbreviated. Recall records are sparse before 2003.
- **Event:** the earliest `event_date_initiated` among recall rows citing that K number,
  counting only recalls initiated on or after the decision date. Links dated before the
  decision are dropped and counted in the data-quality report.
- **Censoring date:** the latest valid `event_date_initiated` in the recall file.
- **Duration:** days from decision date to event, or to the censoring date if no event.
- **Unparseable dates** become NULL and are counted, never guessed.

## Method

1. Raw load into DuckDB (`raw` schema), row counts checked against each file's `meta.results.total`.
2. SQL models in `sql/`, run in filename order: staging (typed, cleaned, one row per recall
   product; K numbers exploded to a bridge table), intermediate (first recall per K number),
   marts (cohort survival table; recall-rate KPIs by specialty, device class, clearance type,
   decision year; root-cause trends by year).
3. Kaplan-Meier survival curves computed **in SQL** with window functions, by clearance type.
4. Cox proportional-hazards model in Python (lifelines): clearance type and device class as
   covariates, stratified by medical specialty, with decision year as a covariate.
5. Marts exported to `exports/*.csv` for a Tableau Public dashboard.

## Reporting rule (frozen)

Report the Cox hazard ratio for Special vs. Traditional with its 95% confidence interval,
whatever it is. A difference is called real only if the interval excludes 1. The unadjusted
recall percentages are shown next to it so the effect of adjustment is visible.

## Limits to state in the README

- Recalls without a K number are invisible to the join (lower-bound rates).
- A recall is a firm's corrective action, not a measure of patient harm.
- PMA and De Novo devices are outside the cohort.
- Special 510(k)s are modifications to a firm's own cleared device, so firms that file them
  differ from firms that do not. This is association, not a causal effect of the pathway.
- One recall event can cover many products and many K numbers.

## Change log

- 2026-10-04: spec frozen.
- 2026-10-04: 75 clearances decided after the censoring date (2026-09-14) have no observable
  follow-up and are excluded from the cohort. Found during the build, before any results were read.
- 2026-10-04: device class enters the Cox model as a number (1, 2, 3); 1,642 clearances with an
  unclassified or missing class are dropped from the model only, not from the descriptive tables.

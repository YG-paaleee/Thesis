# Run-level comparison and Dunn-Bonferroni

Software prepared on 28 October 2026. No field results or Chapter 5 claims are
produced by the artificial regression tests.

## What the script does

`tools/analyze_run.py ... --compare` prepares one summary per complete run.
For each low/medium/high traffic tier it tests PDR, mean delivery latency and
PQA separately across Baseline, Partial, Heuristic, Ablation and Full.

SciPy supplies the tie-corrected Kruskal-Wallis test. When its p-value is below
0.05, scikit-posthocs supplies the two-sided Dunn test with tie correction and
Bonferroni-adjusted p-values. Each family is all ten unordered configuration
pairs for ONE metric in ONE tier. Correction does not pool different metrics or
tiers. Both raw and adjusted probabilities, group sizes, comparison count and
the adjusted significance flag are saved. A significant omnibus test need not
produce a significant adjusted pair; report what the actual tests show.

Non-significant omnibus results produce no Dunn pair rows. Identical pooled
values, missing formal configurations, insufficient samples, duplicate/missing
run identities and unrecognised tiers produce explicit statuses instead of
invented p-values. NaN, infinity and nonnumeric observations are excluded with
counts; a configuration is never silently removed to reduce multiplicity.
Survey/development configurations are excluded from the five-group families.

The script requires at least five finite run-level values in each formal
configuration for the asymptotic calculation. This is a computational minimum,
not a change to the planned TEN trials per configuration/tier or evidence of
adequate power. Finish the agreed trials and review exclusions before reporting.

## Required input and limits

- Each comparison CSV must represent one complete experimental run with source
  and hub evidence, a unique session/run name, verified configuration and the
  correct traffic tier in the session name. Combine paired endpoint captures into
  the run before this analysis; individual node files are not independent runs.
- Separate node files with the same configuration/session are rejected as
  duplicate run identities. Unique filenames or names alone cannot prove
  independence; review the collection design and provenance.
- Kruskal-Wallis assumes independent groups. If trials are deliberately paired,
  blocked or repeated measurements, review the statistical design before using
  its p-values. The code does not convert a dependent design into independence.
- PDR, timing, PQA and battery inputs still need their own validity checks.
  In particular, the existing latency summaries are not automatically verified
  by adding a statistical test. Missing endpoint/clock/queue-entry evidence
  cannot be repaired with a post-hoc test.
- Classifier evaluation uses the separate independent Baseline shadow plan,
  reviewed receiver coverage and frozen-model checks. Its McNemar comparison
  does not use the Dunn-Bonferroni configuration families.

## Usage and outputs

Install the recorded direct dependencies on another laptop if necessary:

```powershell
python -m pip install -r tools/requirements-analysis.txt
python tools/analyze_run.py "evaluation/*.csv" --compare --table evaluation_summary.csv
```

The ordinary comparison command creates:

| File | Contents |
| --- | --- |
| evaluation_summary.csv | One metric summary per input run |
| evaluation_summary_kruskal.csv | Omnibus test or explicit skipped status per metric/tier, usable sample sizes and exclusions |
| evaluation_summary_dunn_bonferroni.csv | Pairs only after significant eligible omnibus tests; header-only if none |
| evaluation_summary_classifier_audit.csv | Separate classifier eligibility audit; a classifier plan and coverage are needed for classifier scores |

No model training, node flashing or radio transmissions are performed by these
commands. Review the saved records before copying actual results into Chapter 5.

## References used for implementation

- [scikit-posthocs Dunn API: tie correction and Bonferroni option](https://scikit-posthocs.readthedocs.io/en/latest/generated/scikit_posthocs.posthoc_dunn.html)
- [SciPy Kruskal-Wallis API: ties, independent samples and sample-size guidance](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html)

Numerical regression fixtures independently check the normal-tail probabilities
for untied ranks and tied ranks, family size, correction bounds and selection
logic. They contain no empirical thesis measurements.

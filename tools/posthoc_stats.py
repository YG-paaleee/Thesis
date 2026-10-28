"""Run-level Kruskal-Wallis and conditional, tie-corrected Dunn-Bonferroni."""
from itertools import combinations
import math

import numpy as np
import pandas as pd

FORMAL_CONFIGS = ('baseline', 'partial', 'heuristic', 'ablation', 'full')
METRICS = ('pdr', 'latency_ms', 'pqa')
PAIR_COLUMNS = ['tier', 'metric', 'config_a', 'config_b', 'n_a', 'n_b',
                'p_raw', 'p_bonferroni', 'comparisons', 'alpha', 'significant']


def rank_comparisons(samples, alpha=0.05, min_group_size=5):
    """A family is all configuration pairs for ONE metric in ONE traffic tier.

    Each value must represent an independent run, never an individual packet.
    Missing/nonfinite values are excluded with explicit counts. No group is
    silently removed to obtain a smaller multiplicity correction.
    """
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be finite and between zero and one')
    if not isinstance(min_group_size, int) or isinstance(min_group_size, bool) or min_group_size < 5:
        raise ValueError('The asymptotic tests require at least five runs per group')
    clean, dropped = {}, {}
    for name, values in samples.items():
        numeric = pd.to_numeric(pd.Series(list(values), dtype=object), errors='coerce')
        finite = numeric.notna() & np.isfinite(numeric.astype(float))
        clean[name] = numeric[finite].to_numpy(dtype=float)
        dropped[name] = int((~finite).sum())
    summary = dict(status='insufficient_groups', h=float('nan'), p=float('nan'),
                   alpha=alpha, n={key: len(value) for key, value in clean.items()},
                   excluded=dropped, posthoc='not_run', comparisons=len(clean) * (len(clean) - 1) // 2)
    if len(clean) < 2:
        return summary, []
    if any(len(values) < min_group_size for values in clean.values()):
        summary['status'] = 'insufficient_runs'
        return summary, []
    pooled = np.concatenate(list(clean.values()))
    if np.unique(pooled).size == 1:
        summary['status'] = 'all_values_identical'
        return summary, []
    from scipy import stats
    h, p = stats.kruskal(*clean.values())
    summary.update(status='tested', h=float(h), p=float(p))
    if p >= alpha:
        summary['posthoc'] = 'not_significant'
        return summary, []
    import scikit_posthocs as sp
    long = pd.DataFrame([(name, value) for name, values in clean.items() for value in values],
                        columns=['config', 'value'])
    raw = sp.posthoc_dunn(long, val_col='value', group_col='config', p_adjust=None)
    adjusted = sp.posthoc_dunn(long, val_col='value', group_col='config', p_adjust='bonferroni')
    pairs = []
    for a, b in combinations(sorted(clean), 2):
        padj = float(adjusted.loc[a, b])
        pairs.append(dict(config_a=a, config_b=b, n_a=len(clean[a]), n_b=len(clean[b]),
                          p_raw=float(raw.loc[a, b]), p_bonferroni=padj,
                          comparisons=summary['comparisons'], alpha=alpha, significant=padj < alpha))
    summary['posthoc'] = 'dunn_bonferroni'
    return summary, pairs


def run_statistics(runs, alpha=0.05):
    """Formal five-configuration comparisons by tier; always return status rows."""
    import json
    summaries, pairs = [], []
    for tier, group in runs.groupby('tier', dropna=False):
        formal = group[group.config.isin(FORMAL_CONFIGS)]
        identity_issue = ''
        if 'session' not in formal or formal.session.isna().any() or formal.session.astype(str).str.strip().eq('').any():
            identity_issue = 'missing_run_identity'
        elif formal.duplicated(['config', 'session']).any():
            identity_issue = 'duplicate_run_identity'
        for metric in METRICS:
            excluded_configs = sorted(set(map(str, group.config)) - set(FORMAL_CONFIGS))
            base = dict(tier=tier, metric=metric, h=float('nan'), p=float('nan'),
                        alpha=alpha, posthoc='not_run', excluded_configs=';'.join(excluded_configs))
            if tier not in ('low', 'medium', 'high'):
                summaries.append({**base, 'status': 'unrecognised_tier', 'n': '{}', 'excluded': '{}'})
                continue
            if identity_issue:
                summaries.append({**base, 'status': identity_issue, 'n': '{}', 'excluded': '{}'})
                continue
            samples = {config: group.loc[group.config == config, metric].tolist() for config in FORMAL_CONFIGS}
            result, comparisons = rank_comparisons(samples, alpha)
            result['n'] = json.dumps(result['n'], sort_keys=True)
            result['excluded'] = json.dumps(result['excluded'], sort_keys=True)
            summaries.append({**base, **result})
            pairs.extend(dict(tier=tier, metric=metric, **pair) for pair in comparisons)
    return pd.DataFrame(summaries), pd.DataFrame(pairs, columns=PAIR_COLUMNS)

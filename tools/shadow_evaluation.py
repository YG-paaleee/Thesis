"""Independent Baseline shadow evaluation, with frozen-model/session checks."""
import json
from pathlib import Path

import pandas as pd

from model_provenance import header_identity
from receiver_labels import detail_fields, reconciled_rows


def read_classifier_plan(path):
    if path is None:
        return None
    location = Path(path)
    plan = json.loads(location.read_text(encoding='utf-8'))
    if plan.get('purpose') != 'independent_baseline_shadow':
        raise ValueError('Classifier plan purpose must be independent_baseline_shadow')
    sessions = plan.get('evaluation_sessions')
    if (not isinstance(sessions, list) or not sessions
            or any(not isinstance(s, str) or not s.strip() for s in sessions)
            or len(set(sessions)) != len(sessions)):
        raise ValueError('List unique nonempty evaluation session names')
    if not isinstance(plan.get('freeze_evidence'), str) or not plan['freeze_evidence'].strip():
        raise ValueError('Record how firmware/model freeze was verified on the boards')
    report = json.loads((location.parent / plan['training_report']).read_text(encoding='utf-8'))
    if report.get('train_source') != 'data' or report.get('split') != 'session':
        raise ValueError('The selected protocol requires data-packet training with a session split')
    identity = header_identity(location.parent / plan['model_header'])
    if any(report.get(key) != value for key, value in identity.items()):
        raise ValueError('Frozen model header does not match its training report')
    development = report.get('development_sessions')
    if (not isinstance(development, list) or not development
            or any(not isinstance(s, str) or not s.strip() for s in development)):
        raise ValueError('Training report must list every development session')
    if set(sessions) & set(development):
        raise ValueError('Evaluation sessions overlap model development sessions')
    return {**plan, **identity, 'development_sessions': development}


def shadow_rows(df, coverage=None, plan=None):
    """Audit every real data TX; eligibility never selects a later successful retry."""
    outcomes = reconciled_rows(df, coverage)
    outcomes['danger'] = outcomes.label
    outcomes['classifier_eligible'] = False
    outcomes['classifier_exclusion'] = 'missing_classifier_plan'
    outcomes['recorded_model_id'] = ''
    if plan is None or outcomes.empty:
        return outcomes
    configs = df[df.event == 'CONFIG'].copy()
    configs['_meta'] = configs.detail.map(detail_fields)
    configs['_boot'] = configs._meta.map(lambda m: m.get('boot', ''))
    models = {}
    for key, group in configs.groupby(['session', 'node', '_boot']):
        values = set(group._meta.map(lambda m: m.get('model', '')))
        if len(values) == 1 and all(m.get('cart') == '1' for m in group._meta):
            models[key] = next(iter(values))
    ordered = outcomes.sort_values(['session', 'node', 'boot', 'ms'], kind='stable')
    first = ~ordered.duplicated(['session', 'node', 'boot', 'origin', 'id', 'peer'])
    first_indices = set(ordered.index[first])
    for index, row in outcomes.iterrows():
        model = models.get((row.session, row.node, row.boot), '')
        outcomes.at[index, 'recorded_model_id'] = model
        if row.config != 'baseline':
            reason = 'not_baseline'
        elif row.session in plan['development_sessions']:
            reason = 'development_session'
        elif row.session not in plan['evaluation_sessions']:
            reason = 'session_not_in_plan'
        elif model != plan['model_id']:
            reason = 'missing_or_mismatched_model'
        elif index not in first_indices:
            reason = 'later_retry'
        elif row.cart_class not in ('Risky', 'Safe') or row.heur_class not in ('Risky', 'Safe'):
            reason = 'missing_paired_verdicts'
        elif pd.isna(row.label):
            reason = row.outcome_reason
        else:
            reason = ''
            outcomes.at[index, 'classifier_eligible'] = True
        outcomes.at[index, 'classifier_exclusion'] = reason
    return outcomes

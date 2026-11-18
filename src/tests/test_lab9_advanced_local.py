"""Public-contract gaps beyond supplied Advanced tests; optional imports are lazy."""
from copy import deepcopy
import pytest

pytestmark = pytest.mark.student


@pytest.fixture
def sample():
    report = {'manifest': {'eval_set_sha': 'fixture', 'items': 2, 'seeds': [1, 2]},
              'rows': [{'item_id': item, 'seed': seed, 'pass_rate': True, 'slices': ['money']}
                       for item in ('a', 'b') for seed in (1, 2)],
              'metrics': {'pass_rate': 1.0}, 'evaluator_failures': []}
    spec = {'eval_set_version': 'v2', 'metrics': [{'id': 'pass_rate', 'threshold': {'min': .8}, 'blocking': True}],
            'slices': [{'name': 'money', 'metric': 'pass_rate', 'min': .9, 'no_significant_drop': True, 'blocking': True}]}
    return report, spec


@pytest.mark.parametrize('damage', ['duplicate', 'slice', 'evaluator', 'aggregate', 'missing_row_value', 'baseline_failure', 'nonfinite_cost', 'missing_manifest'])
def test_advanced_rejects_hidden_evidence_damage(sample, damage):
    from lab9 import gate
    base, spec = sample
    pr = deepcopy(base)
    if damage == 'duplicate': pr['rows'][-1] = deepcopy(pr['rows'][0])
    if damage == 'slice': pr['rows'][0]['slices'] = []
    if damage == 'evaluator': pr['evaluator_failures'] = ['failed evaluator']
    if damage == 'aggregate': pr['metrics']['pass_rate'] = .9
    if damage == 'missing_row_value': pr['rows'][0]['pass_rate'] = None
    if damage == 'baseline_failure': base['evaluator_failures'] = ['baseline evaluator failed']
    if damage == 'nonfinite_cost': pr['rows'][0]['cost'] = float('nan')
    if damage == 'missing_manifest': pr.pop('manifest')
    blocked, lines = gate.check(pr, base, spec)
    assert blocked == ['integrity']
    assert any('INTEGRITY' in line for line in lines)


@pytest.mark.parametrize('damage', ['min', 'remove_ci', 'advisory', 'remove_slice', 'remove_metric'])
def test_advanced_ratchet_slice_and_metric_protections(sample, damage):
    from lab9 import gate
    report, spec = sample
    loose = deepcopy(spec)
    if damage == 'min': loose['slices'][0]['min'] = .1
    if damage == 'remove_ci': loose['slices'][0].pop('no_significant_drop')
    if damage == 'advisory': loose['slices'][0]['blocking'] = False
    if damage == 'remove_slice': loose['slices'] = []
    if damage == 'remove_metric': loose['metrics'] = []
    assert gate.integrity_check(report, report, loose, spec)
    assert gate.integrity_check(report, report, spec, spec) == []


def test_advanced_slice_incomparable_and_warning(sample):
    from lab9 import gate
    base, spec = sample
    pr = deepcopy(base); pr['rows'].pop()
    blocks, lines = gate.slice_check(pr, base, spec)
    assert blocks == ['slice:money/pass_rate'] and 'incomparable' in lines[0]
    spec['slices'][0]['blocking'] = False
    blocks, lines = gate.slice_check(pr, base, spec)
    assert blocks == [] and 'warn' in lines[0]


def test_advanced_reliability_domains_and_ordering():
    from lab9.stats import pass_at_k, pass_hat_k
    for function in (pass_at_k, pass_hat_k):
        for args in [(True, 1, 1), (3, False, 1), (3, 1, True), (0, 0, 1), (3, -1, 1), (3, 1.5, 1)]:
            with pytest.raises(ValueError): function(*args)
    for c in range(6):
        assert 0 <= pass_hat_k(5, c, 3) <= c / 5 <= pass_at_k(5, c, 3) <= 1
    assert pass_hat_k(5, 2, 3) == 0.0


@pytest.mark.parametrize('malformed', ['missing_manifest', 'nonrecord'])
def test_advanced_cli_prints_integrity_instead_of_traceback(sample, tmp_path, capsys, malformed):
    import json
    from lab9 import gate
    base, spec = sample
    pr = deepcopy(base)
    if malformed == 'missing_manifest':
        pr.pop('manifest')
    else:
        pr = []
    paths = [tmp_path / name for name in ('pr.json', 'base.json', 'spec.yaml')]
    for path, value in zip(paths, (pr, base, spec)):
        path.write_text(json.dumps(value), encoding='utf-8')
    assert gate.main(['--pr', str(paths[0]), '--baseline', str(paths[1]), '--spec', str(paths[2])]) == 1
    output = capsys.readouterr().out
    assert 'INTEGRITY' in output and 'exit 1 — blocked: integrity' in output
    assert 'Traceback' not in output

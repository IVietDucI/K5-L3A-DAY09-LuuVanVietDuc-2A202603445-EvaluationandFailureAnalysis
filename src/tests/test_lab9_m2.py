"""M2 boundary policies beyond the supplied public-reference tests."""
import pytest

from lab9 import stats

pytestmark = pytest.mark.student


def test_empty_and_absent_positive_denominators():
    assert stats.confusion([], []) == dict(tp=0, fp=0, fn=0, tn=0)
    assert stats.precision_recall([], []) == (0.0, 0.0)
    assert stats.precision_recall(["FAIL"], ["PASS"]) == (0.0, 0.0)
    assert stats.precision_recall(["PASS"], ["FAIL"]) == (0.0, 0.0)


def test_validation_shared_by_all_paired_metrics():
    for function in (stats.confusion, stats.precision_recall, stats.cohen_kappa):
        for human, judge in [(["PASS"], []), (["pass"], ["PASS"]),
                             ([None], ["PASS"]), (["PASS"], [1])]:
            with pytest.raises(ValueError):
                function(human, judge)


def test_kappa_degeneracy_and_nonconstant_disagreement():
    for labels in ([], ["FAIL"] * 3):
        with pytest.raises(ValueError):
            stats.cohen_kappa(labels, labels)
    assert stats.cohen_kappa(["PASS", "FAIL"], ["PASS", "PASS"]) == 0.0
    assert stats.cohen_kappa(["PASS", "FAIL"], ["FAIL", "PASS"]) == -1.0


def test_rogan_gladen_domain_and_clipping():
    for invalid in (-0.1, 1.1, float("nan"), float("inf"), -float("inf"), "0.5", None, True):
        for position in range(3):
            args = [0.4, 0.8, 0.9]
            args[position] = invalid
            with pytest.raises(ValueError):
                stats.rogan_gladen(*args)
    for sensitivity, specificity in [(0.5, 0.5), (0.0, 1.0), (1.0, 0.0)]:
        with pytest.raises(ValueError):
            stats.rogan_gladen(0.3, sensitivity, specificity)
    assert stats.rogan_gladen(1.0, 0.8, 0.9) == 1.0
    assert stats.rogan_gladen(0.0, 0.8, 0.9) == 0.0
    assert stats.rogan_gladen(0.3, 1.0, 1.0) == pytest.approx(0.3)
    assert stats.rogan_gladen(0.7, 0.0, 0.0) == pytest.approx(0.3)

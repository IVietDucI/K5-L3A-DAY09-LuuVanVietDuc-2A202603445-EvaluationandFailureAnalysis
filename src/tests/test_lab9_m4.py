"""M4 boundary validation and pairing behavior, beyond supplied reference vectors."""
import pytest
from lab9.stats import paired_bootstrap

pytestmark = pytest.mark.student


def test_bootstrap_invalid_inputs_and_parameters():
    for a,b in [([],[]),([1],[1,2]),([float('nan'),0],[1,0]),([1,float('inf')],[1,0]),([[1,2]],[[1,2]]),([1],[0])]:
        with pytest.raises(ValueError):
            paired_bootstrap(a,b)
    for kw in [dict(n_resamples=0),dict(n_resamples=True),dict(n_resamples=1.5),dict(confidence=0),dict(confidence=1),dict(confidence=float('nan')),dict(rng=-1),dict(rng=True)]:
        with pytest.raises(ValueError):
            paired_bootstrap([1,1],[1,1],**kw)


def test_paired_constant_difference_has_point_interval():
    # Shared item variation cancels only when the bootstrap preserves pairing.
    d,lo,hi=paired_bootstrap([1,2,3,4],[0,1,2,3],n_resamples=71,rng=13,confidence=0.8)
    assert (d,lo,hi)==(1.0,1.0,1.0)
    assert paired_bootstrap([2],[2])==(0.0,0.0,0.0)


def test_bootstrap_seed_repeatability_and_direction():
    a,b=[1,0.2,0.9,0.1],[0.4,0.3,0.4,0.2]
    first=paired_bootstrap(a,b,n_resamples=113,rng=77)
    assert first==paired_bootstrap(a,b,n_resamples=113,rng=77)
    reverse=paired_bootstrap(b,a,n_resamples=113,rng=77)
    assert reverse==pytest.approx(tuple(-v for v in (first[0],first[2],first[1])))

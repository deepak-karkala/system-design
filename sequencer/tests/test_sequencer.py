import pytest
from src.sequencer import Sequencer, SnowflakeSequencer


def test_sequencer_with_valid_nodeid():
    seq = SnowflakeSequencer()
    uid = seq.generate_id(42)
    assert (uid >> 12) & ((1 << 10) - 1) == 42


def test_sequencer_with_invalid_nodeid():
    with pytest.raises(ValueError):
        seq = SnowflakeSequencer()
        uid = seq.generate_id(1025)

import pytest

from cogs.rank import calculate_level


def test_calculate_level_zero():
    assert calculate_level(0) == 0


def test_calculate_level_examples():
    # xp=2500 -> level = int(sqrt(2500/50)) = int(sqrt(50)) = 7
    assert calculate_level(2500) == 7
    # xp=50 -> sqrt(50/50)=1 -> level 1
    assert calculate_level(50) == 1

import pytest

from app.agent import find_sightseengs, get_weather


@pytest.mark.parametrize(
    ('city', 'expected'),
    [
        ('Tbilisi', 'Sunny, 25C'),
        ('london', 'Rainy, 20C'),
        ('ROME', 'Sunny, 30C'),
    ],
)
def test_weather_answer_has_a_unit(city, expected):
    assert get_weather.invoke({'city': city}) == expected


def test_unknown_city():
    assert get_weather.invoke({'city': 'Atlantis'}) == 'Unknown'
    assert find_sightseengs.invoke({'city': 'Atlantis'}) == 'Unknown'


def test_sightseeing_for_tbilisi():
    assert 'Narikala Fortress' in find_sightseengs.invoke({'city': 'Tbilisi'})

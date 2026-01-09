from models import Vacancy

def test_parse_salary_range():
    v = Vacancy(
        title=None,
        salary="150 000 - 250 000 ₽",
        experience=None,
        address="Петрозаводск",
        url=None
    )

    assert v.parse_salary() == (150000, 250000)

def test_salary_from():
    v = Vacancy(
        title=None,
        salary="от 40 000 ₽",
        experience=None,
        address="Петрозаводск",
        url=None
    )

    assert v.parse_salary() == (40000, None)

def test_salary_none():
    v = Vacancy(
        title=None,
        salary="по договорённости",
        experience=None,
        address="Петрозаводск",
        url=None
    )

    assert v.parse_salary() == (None, None)

def test_salary_to():
    v = Vacancy(
        title=None,
        salary="до 70 000 ₽",
        experience=None,
        address="Петрозаводск",
        url=None
    )

    assert v.parse_salary() == (None, 70000)



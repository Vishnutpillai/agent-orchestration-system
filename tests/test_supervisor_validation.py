import pytest

from app.agents.supervisor import validate_plan


def test_accepts_valid_plan():
    plan = [
        {
            "id": 1,
            "specialist": "research",
            "description": "Explain machine learning",
        },
        {
            "id": 2,
            "specialist": "coding",
            "description": "Provide a Python example",
        },
    ]

    assert validate_plan(plan) == plan


def test_rejects_non_list_plan():
    with pytest.raises(RuntimeError, match="must be a list"):
        validate_plan({"specialist": "research"})


def test_rejects_empty_plan():
    with pytest.raises(RuntimeError, match="between 1 and 5 steps"):
        validate_plan([])


def test_rejects_plan_with_more_than_five_steps():
    plan = [
        {"specialist": "research"}
        for _ in range(6)
    ]

    with pytest.raises(RuntimeError, match="between 1 and 5 steps"):
        validate_plan(plan)


def test_rejects_non_dictionary_plan_item():
    with pytest.raises(RuntimeError, match="must be an object"):
        validate_plan(["research"])


def test_rejects_unknown_specialist():
    plan = [{"specialist": "unknown_agent"}]

    with pytest.raises(RuntimeError, match="Invalid specialist"):
        validate_plan(plan)
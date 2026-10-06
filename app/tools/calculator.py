def calculator(expression: str):
    """
    Safely evaluate basic mathematical expressions.
    """

    allowed_characters = set(
        "0123456789+-*/(). %"
    )

    if not expression:
        raise ValueError(
            "Expression cannot be empty."
        )

    if not all(
        character in allowed_characters
        for character in expression
    ):
        raise ValueError(
            "Expression contains unsupported characters."
        )

    try:
        result = eval(
            expression,
            {
                "__builtins__": {}
            },
            {},
        )

    except Exception as exc:
        raise ValueError(
            f"Invalid mathematical expression: {expression}"
        ) from exc

    return result
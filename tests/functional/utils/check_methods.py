"""Module for check methods for tests."""


async def assert_status_return_json(response, status) -> dict | list:
    """
    Checks responce status, return responce.json
    """
    assert response.status == status
    return await response.json()


def assert_required_fields(obj: dict, fields: set) -> None:
    """
    Asserts that all required fields are present in the dictionary.
    """
    assert fields.issubset(obj.keys()), (
        f"Missing fields: {fields - obj.keys()}"
    )

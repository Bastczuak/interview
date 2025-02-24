import json

dict1 = {
    "element1": "asdf",
    "element2": "lkjlk",
    "child": {
        "name": "Albert",
        "lastName": "Mueller",
        "age": 12,
        "element": {"level": 3000, "asdf": {"value": 100}},
    },
}

dict2 = {
    "element1": "asdf",
    "element2": "abcd",
    "child": {
        "name": "Johannes",
        "lastName": "Mueller",
        "age": 42,
        "element": {"level": 9000, "asdf": {"value": 200}},
    },
}


def whats_my_output(old: dict, new: dict) -> list[dict]:
    ret_val = []
    path = ""

    def closure(old: dict, new: dict) -> None:
        for key, value in old.items():
            if isinstance(value, dict):
                return closure(value, new[key])

            if value != new[key]:
                nonlocal path
                path = f"{path}.{key}" if path else key
                ret_val.append(
                    {
                        "path": path,
                        "old_value": value,
                        "new_value": new[key],
                    }
                )

    closure(old, new)

    return ret_val


# print(json.dumps(whats_my_output(dict1, dict2), indent=2))

import json
from typing import Any


def get_sat_name_and_num(path: str) -> list[dict[str, Any]]:
    # read json file and find all OBJECT_NAME, OBJECT_ID, NORAD_CAT_ID
    with open(path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        sat_name_and_num = []
        for obj in data:
            sat_name_and_num.append({'name': obj['OBJECT_NAME'],
                                     'OBJECT_ID': obj['OBJECT_ID'],
                                     'NORAD_CAT_ID': obj['NORAD_CAT_ID']})
    return sat_name_and_num


def get_tle_by_name():
    pass


def update_satellite_list():
    # download json tle from celestrak api
    pass


if __name__ == '__main__':
    print(get_sat_name_and_num("active.json"))

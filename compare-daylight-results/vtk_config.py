import pathlib
import json


def daylight_factor_config(results_path: str, folder: pathlib.Path) -> str:
    """Write daylight factor config to a folder."""

    cfg = {
        "data": [
            {
                "identifier": "Daylight factor",
                "object_type": "grid",
                "unit": "Percentage",
                "path": results_path,
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 0,
                    "max": 20,
                    "color_set": "nuanced",
                    "label_parameters": {
                        "color": [34, 247, 10],
                        "size": 0,
                        "bold": True
                    }
                }
            }
        ]
    }

    config_file = folder.joinpath('config.json')
    config_file.write_text(json.dumps(cfg))

    return config_file.as_posix()

import pathlib
import json


def leed_config(folder: pathlib.Path) -> str:
    """Write VTK config for loading results for LEED study."""

    cfg = {
        "data": [
            {
                "identifier": "Illuminance 9am...ecotect",
                "object_type": "grid",
                "unit": "Lux",
                "path": 'illuminance-9am',
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 0,
                    "max": 300,
                    "color_set": "ecotect",
                    "label_parameters": {
                        "color": [34, 247, 10],
                        "size": 0,
                        "bold": True
                    }
                }
            },
            {
                "identifier": "Illuminance 3pm...ecotect",
                "object_type": "grid",
                "unit": "Lux",
                "path": 'illuminance-3pm',
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 0,
                    "max": 300,
                    "color_set": "ecotect",
                    "label_parameters": {
                        "color": [34, 247, 10],
                        "size": 0,
                        "bold": True
                    }
                }
            },
            {
                "identifier": "Pass/Fail 9am...ecotect",
                "object_type": "grid",
                "unit": "",
                "path": 'pass-fail-9am',
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 0,
                    "max": 1,
                    "color_set": "ecotect",
                    "label_parameters": {
                        "color": [34, 247, 10],
                        "size": 0,
                        "bold": True
                    }
                }
            },
            {
                "identifier": "Pass/Fail 3pm...ecotect",
                "object_type": "grid",
                "unit": "",
                "path": 'pass-fail-3pm',
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 0,
                    "max": 1,
                    "color_set": "ecotect",
                    "label_parameters": {
                        "color": [34, 247, 10],
                        "size": 0,
                        "bold": True
                    }
                }
            },
            {
                "identifier": "Pass/Fail...ecotect",
                "object_type": "grid",
                "unit": "",
                "path": 'pass-fail-combined',
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 0,
                    "max": 1,
                    "color_set": "ecotect",
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

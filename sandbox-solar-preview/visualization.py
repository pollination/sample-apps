"""Generate visualization for ground."""
import streamlit as st
import json
import pathlib

from honeybee_vtk.model import Model, HBModel
from par import calc_ppfd_clf

from honeybee_vtk.vtkjs.schema import DisplayMode, SensorGridOptions

model_mapper = [
    '1_fixed_south_facing_tables', '2_fixed_south_facing_canopy',
    '3_north_south_dynamic_single_axis', '4_fixed_east_facing_vertical',
    '5_fixed_east_west_peaked_canopy'
]


def _create_results_folder(temp_folder:pathlib.Path):
    temp_folder.mkdir(parents=True, exist_ok=True)
    config_file = temp_folder.joinpath('config.json')
    config_file.write_text(json.dumps({
        "data": [
                        {
                "identifier": "Average Irradiance",
                "object_type": "grid",
                "unit": "W/m2",
                "path": temp_folder.joinpath('IRR').absolute().as_posix(),
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 60,
                    "max": 200,
                    "color_set": "ecotect",
                    "label_parameters": {
                        "color": [34, 247, 10],
                        "size": 0,
                        "bold": True
                    }
                }
            },
            {
                "identifier": "PPFD",
                "object_type": "grid",
                "unit": "μmol/m2-sec",
                "path": temp_folder.joinpath('PPFD').absolute().as_posix(),
                "hide": False,
                "legend_parameters": {
                    "hide_legend": False,
                    "min": 100,
                    "max": 600,
                    "color_set": "multicolored_2",
                    "label_parameters": {
                        "color": [34, 247, 10],
                        "size": 0,
                        "bold": True
                    }
                }
            }
        ]
    }))

    for subfolder in ['PPFD', 'IRR']:
        grid_info = temp_folder.joinpath(subfolder, 'grids_info.json')
        grid_info.write_text(
            json.dumps(
                [{'full_id': 'Crops_Surface'}]
            )
        )
    return config_file


def get_hbjson_model(fp):
    model = HBModel.from_hbjson(fp)
    return model


def ground_visualization(values, option_index):
    """Create a VTK with PAR and Irradiance values.

    Args:
        values: Annual irradiance values.
        option_index: Index for this design option.
    
    Returns:
        vtkjs: Path to VTKJS file.
        PAR classification: A dictionary for % of PAR classification.
    """
    ppfd_values, ppfd_classification = calc_ppfd_clf(values)

    # load HBJSON model
    __here__ = pathlib.Path(__file__).parent
    model_type = int(option_index.split('_')[0])
    model_fp = __here__.joinpath(
        f'models/{model_mapper[model_type]}/Model1_Updated.hbjson'
    )
    model = get_hbjson_model(model_fp.as_posix())

    for grid in model.properties.radiance.sensor_grids:
        if grid.identifier == 'Crops_Surface':
            crops_grid = grid
            break
    else:
        raise ValueError(f'Failed to find crops grid in {model_fp}')

    model.properties.radiance.sensor_grids = (crops_grid,)
    vtk_model = Model(model, SensorGridOptions.Mesh)

    results_folder = __here__.joinpath('temp_res', option_index)
    # write results to folder
    par_file = results_folder.joinpath('PPFD', 'Crops_Surface.res')
    irr_file = results_folder.joinpath('IRR', 'Crops_Surface.res')
    par_file.parent.mkdir(parents=True, exist_ok=True)
    irr_file.parent.mkdir(parents=True, exist_ok=True)
    par_file.write_text('\n'.join(map(str, ppfd_values)))
    irr_file.write_text('\n'.join(map(str, values)))

    config_file = _create_results_folder(results_folder)
    # copy the file back into the folder
    vtkjs_file = results_folder.joinpath(f'{option_index}.vtkjs')
    if not vtkjs_file.exists():
        vtk_model.to_vtkjs(
            folder=results_folder.as_posix(),
            name=option_index,
            config=config_file.as_posix(),
            model_display_mode=DisplayMode.Shaded
        )
    return ppfd_classification, vtkjs_file


def config_visualization(model_type):
    # load HBJSON model
    __here__ = pathlib.Path(__file__).parent
    model_name = 'Model1_Updated' if model_type != 2 else 'Model1'
    model_fp = __here__.joinpath(
        f'models/{model_mapper[model_type]}/{model_name}.hbjson'
    )
    model = get_hbjson_model(model_fp.as_posix())

    vtk_model = Model(model, SensorGridOptions.Ignore)
    # copy the file back into the folder
    vtkjs_file = model_fp.parent.joinpath(f'model.vtkjs')
    if not vtkjs_file.exists():
        vtk_model.to_vtkjs(
            folder=model_fp.parent.as_posix(),
            name='model',
            model_display_mode=DisplayMode.Shaded
        )
    return vtkjs_file

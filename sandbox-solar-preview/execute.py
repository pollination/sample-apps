import pathlib

from honeybee.model import Model
from honeybee_radiance.modifier.material.glass import Glass
from honeybee_radiance.lightsource.sky.skydome import SkyDome
from honeybee_radiance_command._command_util import run_command
import calendar

from location import LOCATIONS

CFG_OPTIONS = [
    "1_fixed_south_facing_tables", "2_fixed_south_facing_canopy",
    "3_north_south_dynamic_single_axis",
    "4_fixed_east_facing_vertical", "5_fixed_east_west_peaked_canopy"
]
MONTHS = list(calendar.month_abbr)[1:]


def calculate_dc_mtx(model: Model, transparency=1, working_dir='.'):
    """Calculate daylight coefficient matrices for sensor grids."""
    modifier = Glass.from_single_transmissivity(
        identifier="Agrivoltaic_Panel",
        rgb_transmissivity=transparency
    )
    for shade in model.shades:
        shade.properties.radiance.modifier = modifier

    # create a radiance model
    rad_content = model.to.rad(model, False, True)

    rad_file = working_dir.joinpath('model.rad')
    # save the model to file
    rad_file.write_text('\n'.join([rad_content[1], rad_content[0]]))

    resources_folder = working_dir.joinpath('resources')
    # save sky dome
    SkyDome().to_file(resources_folder, 'sky.dome')
    # create the octree
    run_command(
        f'oconv -f {rad_file.as_posix()} > resources/model.oct', cwd=working_dir.as_posix()
    )

    # create two dc matrices for this model with two different sensor grids
    # for grid in model.properties.radiance.sensor_grids:
    # save sensor grids to files
    for grid in model.properties.radiance.sensor_grids:
        grid.to_file(resources_folder)
        cmd = f'rfluxmtx -I -aa 0.0 -ab 3 -ad 5000 -lw 2e-05 -c 1 -faf -y {grid.count} - resources/sky.dome -i resources/model.oct < resources/{grid.identifier}.pts > {grid.identifier}_{int(10 * transparency / 2)}.dc'
        print(cmd)
        run_command(cmd, cwd=working_dir.as_posix())


def generate_hourly_sky(weather_file: str, sky_file: pathlib.Path) -> pathlib.Path:
    """Create an annual hourly sky for PV panels calculation."""
    sky_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = f'gendaymtx -O1 {weather_file} > {sky_file.as_posix()}'
    print(cmd)
    run_command(cmd, cwd=sky_file.parent.as_posix())
    return sky_file


def calculate_ground_values(sky, dc, working_dir: pathlib.Path):
    """Calculate values for ground.

    The initial output is irradiance and the values for PAR is calculated based on that.
    """
    temp_file = working_dir.joinpath('Crops_Surface_Temp.ill')
    cmd = f'rmtxop -fa {dc} {sky} -c 0.265 0.670 0.065 > {temp_file.as_posix()}'
    # print(cmd)
    run_command(cmd, cwd=working_dir.as_posix())
    # clean up and save as csv
    res_file = working_dir.joinpath('Crops_Surface.ill')
    print(f'Cleaning up values: {res_file}')
    with temp_file.open() as inf, res_file.open('w') as outf:
        for _ in range(10):
            line = next(inf)
            if line.startswith('FORMAT='):
                next(inf)
                break
        outf.write(','.join(MONTHS) + '\n')
        for line in inf:
            outf.write(','.join(line.strip().split()) + '\n')

    temp_file.unlink()


def calculate_pv_values(sky, dc, working_dir: pathlib.Path):
    """
    Calculate irradiance and energy production values for a Photovoltaic panel.

    The inputs are a sky file and a daylight coefficient file.
    It averages the results into a single file if needed.
    """
    temp_file = working_dir.joinpath('Agrivoltaic_Panel_Temp.ill')
    cmd = f'rmtxop -fa {dc} {sky} -c 0.265 0.670 0.065 -t > Agrivoltaic_Panel_Temp.ill'
    print(cmd)
    run_command(cmd, cwd=working_dir.as_posix())
    res_file = working_dir.joinpath('Agrivoltaic_Panel.ill')
    print(f'Calculating average values: {res_file}')
    with temp_file.open() as inf, res_file.open('w') as outf:
        for _ in range(10):
            line = next(inf)
            if line.startswith('FORMAT='):
                next(inf)
                break
        for line in inf:
            values = list(map(float, line.split()))
            outf.write(str(sum(values) / len(values)) + '\n')
    temp_file.unlink()


def create_dc_for_all_folders(folder):
    """Calculate DC for all the different geometry combinations.

    Args:
        folder: Models folder.

    """
    for subfolder in pathlib.Path(folder).iterdir():
        if not subfolder.is_dir():
            continue
        working_dir = subfolder
        resources_folder = working_dir.joinpath('resources')
        resources_folder.mkdir(parents=True, exist_ok=True)
        fp = subfolder.joinpath('Model1_Updated.hbjson')
        if not fp.is_file():
            continue
        # get a base model
        model = Model.from_hbjson(fp)
        for tr in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
            calculate_dc_mtx(model, transparency=tr, working_dir=working_dir)


def generate_all_skies(weather_folder, target_folder='.'):
    folder = pathlib.Path(target_folder)
    for wea_file in pathlib.Path(weather_folder).iterdir():
        print(wea_file)
        if wea_file.suffix != '.wea':
            continue
        generate_hourly_sky(wea_file.as_posix(),
                            folder.joinpath(f'{wea_file.stem}.mtx'))


def generate_pv_irradiance_results(sky_folder, models_folder, results_folder):
    res_folder = pathlib.Path(results_folder)
    for sky in pathlib.Path(sky_folder).iterdir():
        location_index = LOCATIONS[sky.stem]['index']
        for subfolder in pathlib.Path(models_folder).iterdir():
            if not subfolder.is_dir():
                continue
            cfg_index = CFG_OPTIONS.index(subfolder.stem)
            if cfg_index == 2:
                # we don't do tracking for now
                continue
            for tr in range(6):
                dc_file = subfolder.joinpath(f'Agrivoltaic_Panel_{tr}.dc')
                calculate_pv_values(
                    sky.as_posix(), dc_file.as_posix(), res_folder.joinpath(
                        f'{cfg_index}_{tr}_{location_index}'
                    )
                )


def generate_pv_irradiance_parametric(sky_folder, dc_folder, ill_folder):
    res_folder = pathlib.Path(ill_folder)
    for sky in pathlib.Path(sky_folder).iterdir():
        location_index = LOCATIONS[sky.stem]['index']
        for subfolder in pathlib.Path(dc_folder).iterdir():
            if not subfolder.is_dir():
                continue
            for tr in range(3):
                dc_file = subfolder.joinpath(f'Agrivoltaic_Panel_{tr}.dc')
                working_dir = res_folder.joinpath(
                    str(location_index), subfolder.name, str(tr)
                )
                working_dir.mkdir(parents=True, exist_ok=True)
                calculate_pv_values(sky.as_posix(), dc_file.as_posix(), working_dir)


def generate_ground_irradiance_results(sky_folder, models_folder, results_folder):
    res_folder = pathlib.Path(results_folder)

    for sky in pathlib.Path(sky_folder).iterdir():
        location_index = LOCATIONS[sky.stem]['index']
        for subfolder in pathlib.Path(models_folder).iterdir():
            if not subfolder.is_dir():
                continue
            cfg_index = CFG_OPTIONS.index(subfolder.stem)
            if cfg_index == 2:
                # we don't do tracking for now
                continue
            for tr in range(6):
                dc_file = subfolder.joinpath(f'Crops_Surface_{tr}.dc')
                calculate_ground_values(
                    sky.as_posix(), dc_file.as_posix(), res_folder.joinpath(
                        f'{cfg_index}_{tr}_{location_index}'
                    )
                )


def generate_ground_irradiance_parametric(sky_folder, models_folder, ill_folder):
    res_folder = pathlib.Path(ill_folder)

    for sky in pathlib.Path(sky_folder).iterdir():
        location_index = LOCATIONS[sky.stem]['index']
        for subfolder in pathlib.Path(models_folder).iterdir():
            if not subfolder.is_dir():
                continue
            for tr in range(3):
                dc_file = subfolder.joinpath(f'Crops_Surface_{tr}.dc')
                working_dir = res_folder.joinpath(
                    str(location_index), subfolder.name, str(tr)
                )
                working_dir.mkdir(parents=True, exist_ok=True)
                calculate_ground_values(
                    sky.as_posix(), dc_file.as_posix(), working_dir
                )



def run_dc_parametric_models(folder: pathlib.Path, results_folder: pathlib.Path):
    sub_folders = ['Fixed_South_Facing', 'Peak', 'Vertical']
    for sf in sub_folders:
        study_folder = folder.joinpath(sf)
        for fp in study_folder.glob('*.hbjson'):
            model = Model.from_hbjson(fp)
            working_dir = results_folder.joinpath(f'{sf}_{fp.stem}')
            working_dir.mkdir(parents=True, exist_ok=True)
            for tr in (0.0, 0.25, 0.5):
                calculate_dc_mtx(model, transparency=tr, working_dir=working_dir)


models_folder = r"C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\sandbox-solar\models"
weather_folder = "c:/Users/Mostapha/Documents/GitHub/sandbox-solar/sandbox-solar-irradiance/app/assets/weather/wea"

sky_folder = r'C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\assets\weather\sky\annual_hourly'
monthly_sky_folder = r'C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\assets\weather\sky\monthly_cumulative'

def generate_dataset():
    results_folder = r'C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\sandbox-solar\sim_data'
    # create_dc_for_all_folders(models_folder)
    # generate_pv_irradiance_results(sky_folder, models_folder, results_folder)
    # generate_ground_irradiance_results(monthly_sky_folder, models_folder, results_folder)


def generate_parametric_dc():
    parametric_folder = pathlib.Path(r'C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\assets\models\parametric')
    dc_folder = pathlib.Path(r'C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\parametric_runs')
    ill_folder = pathlib.Path(r'C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\parametric_data')
    # run_dc_parametric_models(parametric_folder, dc_folder)
    # generate_pv_irradiance_parametric(sky_folder, dc_folder, ill_folder)
    generate_ground_irradiance_parametric(monthly_sky_folder, dc_folder, ill_folder)

generate_parametric_dc()

"""Create a monthly averaged sky."""
import pathlib
from ladybug.wea import Wea
from ladybug.analysisperiod import AnalysisPeriod

import calendar
from honeybee_radiance_command._command_util import run_command

def monthly_averaged_sky(wea, target_folder, name='averaged_sky.mtx'):
    # read the wea file
    wea = Wea.from_file(wea)
    temp_folder = pathlib.Path('C:\\ladybug\\tt\\temp')
    for month in range(12):
        # create 12 separate wea files for each month
        last_day = calendar.monthrange(2022, month + 1)[1]
        ap = AnalysisPeriod(month + 1, 1, 0, month + 1, last_day, 23)
        monthly_wea = wea.filter_by_analysis_period(ap)
        fp = monthly_wea.write(temp_folder.joinpath(f'{month}.wea').as_posix())
        command = f'gendaymtx -u -O1 -A {fp} > {month}.sky'
        # create 12 different averaged skies
        run_command(command, cwd=temp_folder.as_posix())

    # put them back together as one
    sky_file = temp_folder.joinpath(name)
    first_month = temp_folder.joinpath('0.sky')
    with first_month.open() as inf, sky_file.open('w') as outf:
        for i in range(8):
            line = next(inf)
            line = line.replace('NCOLS=1', 'NCOLS=12')
            outf.write(line)
        for line in inf:
            outf.write(line)
        for i in range(11):
            monthly_sky_file = temp_folder.joinpath(f'{i + 1}.sky')
            with monthly_sky_file.open() as inf:
                for _ in range(7):
                    next(inf)
                for line in inf:
                    outf.write(line)

    out_file = pathlib.Path(target_folder).joinpath(name)
    if out_file.exists():
        out_file.unlink()
    sky_file.rename(out_file)
    return out_file


if __name__ == '__main__':

    folder = pathlib.Path(f"c:/Users/Mostapha/Documents/GitHub/sandbox-solar/sandbox-solar-irradiance/app/assets/weather/wea")
    target_folder = r'C:\Users\Mostapha\Documents\GitHub\sandbox-solar\sandbox-solar-irradiance\app\assets\weather\sky'

    for f in folder.glob('*.wea'):
        monthly_averaged_sky(f.as_posix(), target_folder=target_folder, name=f'{f.stem}.mtx')


from ladybug.header import Header
from ladybug.datatype.energyflux import Irradiance
from ladybug.analysisperiod import AnalysisPeriod
from ladybug_charts.to_figure import bar_chart_with_table, MonthlyCollection, Color


def get_graph(panel_data, crops_data):
    ap = AnalysisPeriod()
    panels_header = Header(
        Irradiance('Average Irradiance Panels'), 'W/m2', analysis_period=ap
    )
    data = MonthlyCollection(panels_header, values=panel_data, datetimes=range(1, 13))

    crops_header = Header(
        Irradiance('Average Irradiance Crops'), 'W/m2', analysis_period=ap
    )
    data_2 = MonthlyCollection(crops_header, values=crops_data, datetimes=range(1, 13))
    colors = [Color(243, 114, 32), Color(255, 213, 0)]
    figure = bar_chart_with_table([data, data_2], stack=False, colors=colors)
    return figure

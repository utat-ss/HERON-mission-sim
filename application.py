#!/usr/bin/env python
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import sys
sys.path.insert(0, 'notebooks/modules')
import defaults, satellite, fileio

def load_files():
    areas = fileio.read_areas_from_file(defaults.path, defaults.dt, defaults.t_orbit)
    total_areas = areas['plusX'] - areas['plusX']
    panel_areas = total_areas.copy()
    for h in defaults.headers:
        total_areas += areas[h]
        if h in defaults.panels: panel_areas += areas[h]
    return total_areas, areas, panel_areas


def simulate(n_orbits, areas, total_areas, panel_areas, timings=defaults.timings, eps=defaults.eps, temperatures=defaults.temperatures, setpoints=defaults.setpoints, structure_constants=defaults.structure_constants):
    n_pts_per_orbit = len(areas)
    n_points = n_orbits * n_pts_per_orbit
    t_sim = n_points * defaults.dt
    heron = satellite.Satellite(timings,eps, temperatures, setpoints, structure_constants)
    for i in range(n_points):
        heron.set_state(i)
        heron.draw_powers()
        heron.update_thermal(total_areas[i % len(areas)], areas['negZ'][i%len(areas)], heron.batt_current_net)
        heron.charge_from_solar_panel(panel_areas[i % len(areas)] / (0.03 * 0.01), defaults.dt)
        heron.update_state_tracker(i*defaults.dt)
    return heron


t_a, a, p_a = load_files()
eps = defaults.eps.copy()
temperatures = defaults.temperatures.copy()
setpoints = defaults.setpoints.copy()
structure_constants = defaults.structure_constants.copy()
timings = defaults.timings.copy()
timings['n_orbits'] = 3

timings_names = [
    ('exp_start_time', "Start time of Experiment (hours)"),
    ('exp_duration', "Duration of Experiment (hours)")
]
eps_names = [
    ('battery_capacity_mAh', 'Max. Batt. Capacity (mAh)'),
    ('converter_efficiency', 'Converter Efficiency (0-1)'),
    ('starting_charge_frac', 'Starting Charge Frac of Batt. (0-1)')
]
temperatures_names = [
    ('structure', 'Init Temp. of the Structure (K)'),
    ('battery', 'Init Temp. of the Battery (K)'),
    ('payload', 'Init Temp. of the Payload (K)'),
]
setpoints_names = [
    ('payload_stasis', 'Payload Stasis Setpoint (K)'),
    ('payload_exp', 'Payload Experiment Setpoint (K)'),
    ('battery', "Battery Setpoint (K)")
]
structure_constants_names = [
    ('c_str', "Heat Capacity of Structure (C_str)"),
    ('c_batt', "Heat Capacity of Battery (C_batt)"),
    ('c_pay', "Heat Capacity of Payload (C_pay)"),
    ('e', "Emissivity (e)"),
    ('a', "Absorptivity (a)"),
    ('R_str_pay', "R between Str and Payload", 'R_str_pay'),
    ('R_str_batt', "R between Str and Battery", 'R_str_batt'),
]


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
server = flask.Flask(__name__)
application = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

application.layout = html.Div(
    [
        html.Div(
            [
                html.H1(
                    'HERON Mk II Mission Simulator',
                    className='twelve columns',
                    
                    style = {
                        'textAlign' : 'center',
                        'color'  : 'rgb(0,0,0)',
                        'font-size' : '5.0rem',
                        'font-family': 'Arial Black',
                        'align-items' : 'center'
                    }
                ),
                # html.Img(
                #     src="https://static1.squarespace.com/static/583f323f46c3c427a3c86949/t/583f41af579fb3daf4751a4d/favicon.ico",
                #     className='one columns',
                #     style={
                #         'height': '125',
                #         'width': '125',
                #         'float': 'right',
                #         'position': 'relative',
                #     },
                # ),

            ],
            className='row'
        ),

        html.Div(
            [
                html.Div( # Structure Constants Sliders
                    [
                        html.H4('Structure Constants', style = {'textAlign' : 'center', 'font-family' : 'Arial'}),
                        html.Div(id = 'text-c_str'),
                        dcc.Slider(
                            id='slider-c_str',
                            min=300,
                            max=2000,
                            value=defaults.structure_constants['c_str'],
                        ),
                        html.Div(id = 'text-c_batt'),
                        dcc.Slider(
                            id='slider-c_batt',
                            min=300,
                            max=2000,
                            value=defaults.structure_constants['c_batt'],
                        ),
                        html.Div(id = 'text-c_pay'),
                        dcc.Slider(
                            id='slider-c_pay',
                            min=300,
                            max=2000,
                            value=defaults.structure_constants['c_pay'],
                        ),
                        html.Div(id = 'text-e'),
                        dcc.Slider(
                            id='slider-e',
                            min=0,
                            max=100,
                            value=100*defaults.structure_constants['e'],
                        ),
                        html.Div(id = 'text-a'),
                        dcc.Slider(
                            id='slider-a',
                            min=0,
                            max=100,
                            value=100*defaults.structure_constants['a']
                            ),
                        html.Div(id = 'text-R_str_pay'),
                        dcc.Slider(
                            id='slider-R_str_pay',
                            min=1,
                            max=40,
                            value=defaults.structure_constants['R_str_pay']
                        ),
                        html.Div(id = 'text-R_str_batt'),
                        dcc.Slider(
                            id='slider-R_str_batt',
                            min=1,
                            max=40,
                            value=defaults.structure_constants['R_str_batt']
                        ),
                    ],
                    className='three columns'
                ),

                html.Div( # Temperatures Sliders
                    [
                        html.H4('Temperatures', style={
                                'textAlign': 'center', 'font-family': 'Arial'}),
                        html.Div(id='text-init-temp-payload'),
                        dcc.Slider(
                            id='slider-init-temp-payload',
                            min=100,
                            max=400,
                            value=defaults.temperatures['payload'],
                        ),
                        html.Div(id='text-init-temp-battery'),
                        dcc.Slider(
                            id='slider-init-temp-battery',
                            min=100,
                            max=400,
                            value=defaults.temperatures['battery'],
                        ),
                        html.Div(id='text-init-temp-structure'),
                        dcc.Slider(
                            id='slider-init-temp-structure',
                            min=100,
                            max=400,
                            value=defaults.temperatures['structure'],
                        ),
                        html.Div(id='text-setpoint-temp-payload_exp'),
                        dcc.Slider(
                            id='slider-setpoint-temp-payload_exp',
                            min=250,
                            max=350,
                            value=defaults.setpoints['payload_exp'],
                        ),
                        html.Div(id='text-setpoint-temp-payload_stasis'),
                        dcc.Slider(
                            id='slider-setpoint-temp-payload_stasis',
                            min=250,
                            max=350,
                            value=defaults.setpoints['payload_stasis'],
                        ),
                        html.Div(id='text-setpoint-temp-battery'),
                        dcc.Slider(
                            id='slider-setpoint-temp-battery',
                            min=250,
                            max=350,
                            value=defaults.setpoints['battery'],
                        ),
                    ],
                    className='three columns'
                ),
                html.Div( # EPS and Timing Sliders
                    [
                        html.H4('EPS Settings', style={
                                'textAlign': 'center', 'font-family': 'Arial'}),
                        html.Div(id='text-eps-battery_capacity_mAh'),
                        dcc.Slider(
                            id='slider-eps-battery_capacity_mAh',
                            min=10000.0,
                            max=30000.0,
                            value=defaults.eps['battery_capacity_mAh'],
                        ),
                        html.Div(id='text-eps-converter_efficiency'),
                        dcc.Slider(
                            id='slider-eps-converter_efficiency',
                            min=0.0,
                            max=100.0,
                            value=100.0*defaults.eps['converter_efficiency'],
                        ),
                        html.Div(id='text-eps-starting_charge_frac'),
                        dcc.Slider(
                            id='slider-eps-starting_charge_frac',
                            min=0.0,
                            max=100.0,
                            value=100.0*defaults.eps['starting_charge_frac'],
                        ),


                    ],
                    className='three columns'
                ),
                html.Div(
                    [
                        html.H4('Timings', style={
                                'textAlign': 'center', 'font-family': 'Arial'}),
                        html.Div(id='text-timings-n_orbits'),
                        dcc.Input(
                            id='input-timings-n_orbits',
                            type='text',
                            value=str(timings['n_orbits'])
                        ),
                        html.Div(id='text-timings-exp_start_time'),
                        dcc.Input(
                            id='input-timings-exp_start_time',
                            type='text',
                            value=str(int(defaults.timings['exp_start_time']/3600))
                        ),
                        html.Div(id='text-timings-exp_duration'),
                        dcc.Input(
                            id='input-timings-exp_duration',
                            type='text',
                            value=str(int(defaults.timings['exp_duration']/3600))
                        ),   
                        html.Button('Reprocess', id='reprocess-button'),
                        
                    ],
                    className='three columns'
                ),
            ],
            className='row'
        ),
        html.Div([
            dcc.Graph(id='graph-batt_v'),
            # dcc.Graph(id='graph-loads'),
            dcc.Graph(id='graph-temps'),
        ])
    ],
    style={'font-family' : 'Arial'},
    className='ten columns offset-by-one'
)


@application.callback(Output('text-timings-n_orbits', 'children'),
                      [Input('input-timings-n_orbits', 'value')])
def display_value(value):
        timings['n_orbits'] = int(value)
        return "%d orbits, corresponds to %.2f hours" % (timings['n_orbits'], defaults.t_orbit * timings['n_orbits'] / 3600)

for i in range(len(timings_names)):
    @application.callback(Output('text-timings-'+timings_names[i][0], 'children'),
                          [Input('input-timings-'+timings_names[i][0], 'value')])
    def display_value(value, i=i):
        key = timings_names[i][0]
        value = int(value) * 60 * 60
        timings[key] = value
        return timings_names[i][1] + ': %.2f' % (value/3600)

for i in range(len(eps_names)):
    @application.callback(Output('text-eps-'+eps_names[i][0], 'children'),
                          [Input('slider-eps-'+eps_names[i][0], 'value')])
    def display_value(value, i=i):
        key = eps_names[i][0]
        if key in ('starting_charge_frac', 'converter_efficiency'):
            value /= 100.0
        eps[key] = value
        return eps_names[i][1] + ': %.2f' % value

for i in range(len(temperatures_names)):
    @application.callback(Output('text-init-temp-'+temperatures_names[i][0], 'children'),
                          [Input('slider-init-temp-'+temperatures_names[i][0], 'value')])
    def display_value(value, i=i):
        key= temperatures_names[i][0]
        temperatures[key]= value
        return temperatures_names[i][1] + ': %.2f' % value

for i in range(len(setpoints_names)):
    @application.callback(Output('text-setpoint-temp-'+setpoints_names[i][0], 'children'),
                          [Input('slider-setpoint-temp-'+setpoints_names[i][0], 'value')])
    def display_value(value, i=i):
        key = setpoints_names[i][0]
        setpoints[key] = value
        return setpoints_names[i][1] + ': %.2f' % value

for i in range(len(structure_constants_names)):
    @application.callback(Output('text-'+structure_constants_names[i][0], 'children'),
                [Input('slider-'+structure_constants_names[i][0], 'value')])
    def display_value(value, i=i):
        key = structure_constants_names[i][0]
        if key in ('a', 'e'):
            value /= 100.0
            structure_constants[key] = value 
            return structure_constants_names[i][1] + ': %.2f, a/e is %.4f' % (value, structure_constants['a'] / structure_constants ['e'])
        else:
            structure_constants[key] = value
            return structure_constants_names[i][1] + ': %.2f' % value


# @application.callback(
#     Output('graph-batt_v', 'figure'),
#     [Input('reprocess-button', 'n_clicks')])
# def update_load_figure(n_clicks):

#     print("Running sim...")
#     heron = simulate(n_orbits, a, t_a, p_a, structure_constants=structure_constants,
#      temperatures=temperatures, eps=eps, timings=timings)
#     print("Done Sim")
#     traces = []

#     traces.append(go.Scatter(
#         x = heron.trackers['time'],
#         y = heron.trackers['batt_v'],
#         text = "Battery Voltage",
#         mode = 'lines',
#         opacity = 0.8,
#         name = 'batt_v'
#     ))
    
#     return {
#         'data': traces,
#         'layout': go.Layout(
#             xaxis={ 'title': 'Time (s)'},
#             yaxis={'title': 'Battery Voltage'},
#             margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
#             legend={'x': 0, 'y': 1},
#             hovermode='closest'
#         )
#     }


@application.callback(
    Output('graph-batt_v', 'figure'),
    [Input('reprocess-button', 'n_clicks')])
def update_batt_figure(n_clicks):
    n_orbits = timings['n_orbits']
    print("Running sim with %d orbits..." % n_orbits) 
    heron = simulate(n_orbits, a, t_a, p_a, structure_constants=structure_constants,
                     temperatures=temperatures, eps=eps, timings=timings)
    print("Done Sim")
    traces = []

    traces.append(go.Scatter(
        x=[t / 3600 for t in heron.trackers['time']],
        y=heron.trackers['batt_v'],
        text="Battery Voltage",
        mode='lines',
        opacity=0.8,
        name='batt_v'
    ))

    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'title': 'Time (h)'},
            yaxis={'title': 'Battery Voltage'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }



@application.callback(
    Output('graph-temps', 'figure'),
    [Input('reprocess-button', 'n_clicks')])
def update_temp_figure(n_clicks):

    n_orbits = timings['n_orbits']
    print("Running sim...")
    heron = simulate(n_orbits, a, t_a, p_a, structure_constants=structure_constants,
                     temperatures=temperatures, eps=eps, timings=timings)
    print("Done Sim")
    traces = []

    traces.append(go.Scatter(
        x=[t / 3600 for t in heron.trackers['time']],
        y=[temp['structure'] for temp in heron.trackers['temperatures']],
        text="Structure Temperature (K)",
        mode='lines',
        opacity=0.8,
        name='temp_str'
    ))    
    traces.append(go.Scatter(
        x=[t / 3600 for t in heron.trackers['time']],
        y=[temp['payload'] for temp in heron.trackers['temperatures']],
        text="Payload Temperature (K)",
        mode='lines',
        opacity=0.8,
        name='temp_pay'
    ))    
    traces.append(go.Scatter(
        x= [t / 3600 for t in heron.trackers['time']],
        y=[temp['battery'] for temp in heron.trackers['temperatures']],
        text="Battery Temperature (K)",
        mode='lines',
        opacity=0.8,
        name='temp_batt'
    ))

    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'title': 'Time (h)'},
            yaxis={'title': 'Temperature'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }



if __name__ == '__main__':

    application.run_server(debug=True)

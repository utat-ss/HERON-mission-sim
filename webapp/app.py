import copy
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import sys
import json
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

def simulate(n_orbits, areas, total_areas, panel_areas):
    n_pts_per_orbit = len(areas)
    n_points = n_orbits * n_pts_per_orbit
    t_sim = n_points * defaults.dt
    heron = satellite.Satellite(defaults.timings,defaults.eps, defaults.temperatures, defaults.setpoints, defaults.structure_constants)
    for i in range(n_points):
        heron.set_state(i)
        heron.draw_powers()
        heron.update_thermal(total_areas[i % len(areas)], areas['negZ'][i%len(areas)], heron.batt_current_net)
        heron.charge_from_solar_panel(panel_areas[i % len(areas)] / (0.03 * 0.01), defaults.dt)
        heron.update_state_tracker(i*defaults.dt)
    return heron
def plot_loads(satellite):
    pass

t_a, a, p_a = load_files()
timings = copy.deepcopy(defaults.timings)


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div([
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        id='orbits-slider',
        min=1,
        max=50,
        value=3,
        marks={i*5:i*5 for i in range(11)}
    ),
    dcc.Dropdown(id='dropdown',
            options = [{'label':k, 'value':k} for k in defaults.timings.keys()],
            value = list(defaults.timings.keys())[0]),
    dcc.Textarea(
        placeholder='Select a property.',
        value='Select a property.',
        style={'width': '100%'},
        id = 'property-editor'
    ),
    html.Div(id='saved_sim_params', 
            style={'display' : 'none'},
            children=json.dumps(timings)),
    html.Button('Reprocess', id='reproc-btn')
])

@app.callback(
    Output('property-editor', 'value'),
    [Input('dropdown', 'value')]
)
def choose_property(value):
    return defaults.timings[value]

@app.ca

@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('reproc-btn', 'n_clicks')])
def update_figure(n_clicks):

    print("Running sim...")
    heron = simulate(3, a, t_a, p_a)
    print("Done Sim")
    traces = []

    traces.append(go.Scatter(
        x = heron.trackers['time'],
        y = heron.trackers['batt_v'],
        text = "Battery Voltage",
        mode = 'lines',
        opacity = 0.8,
        name = 'batt_v'

    ))
    
    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={ 'title': 'Time (s)'},
            yaxis={'title': 'Battery Voltage'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }



if __name__ == '__main__':

    app.run_server(debug=True)

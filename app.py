import dash
import serial
import os
from dash import _dash_renderer, html, dcc, Input, Output, callback
import pandas as pd
import threading
import dash_draggable
import dash_mantine_components as dmc
import dash_daq as daq 
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_vtk
from dash_vtk.utils import to_mesh_state
from vtkmodules.vtkFiltersSources import vtkCylinderSource
import vtk

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

_dash_renderer._set_react_version("18.2.0")

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=external_stylesheets
)

SERIAL_PORT = 'COM5'
BAUD_RATE = 115200

data = pd.DataFrame(columns=['time', 'sensor_type', 'value'])

serial_connection = serial.Serial(SERIAL_PORT, BAUD_RATE)
previous_clicks = 0
data_lock = threading.Lock()


cylinder_source = vtkCylinderSource()
cylinder_source.SetResolution(100)
cylinder_source.SetHeight(1.5)
cylinder_source.SetRadius(0.5)
cylinder_source.SetCenter(0, 0, 0)
cylinder_source.Update()
poly_data = cylinder_source.GetOutput()
mesh_state = to_mesh_state(poly_data)

angle_x = 0
angle_y = 0
angle_z = 0

def read_serial():
    global data
    while True:
        try:
            code = serial_connection.readline().decode('utf-8').strip()

            if code == 'panditas':
                
                print ('Correct code')
                
                time = serial_connection.readline().decode('utf-8').strip()
                sensor_type = serial_connection.readline().decode('utf-8').strip()
                value = serial_connection.readline().decode('utf-8').strip()

                new_row = pd.DataFrame({
                    'time': [time],
                    'sensor_type': [sensor_type],
                    'value': [value]
                })

                with data_lock:
                    data = pd.concat([data, new_row], ignore_index=True)
                    # data.to_csv('data.csv', index=False)  
                        
                    print(f"Stored Data: {data}")
            
            else: 
                print('Incorrect code')
                
        except (IndexError, ValueError) as e:
            print(f"Error parsing data: {e}")
                       
threading.Thread(target=read_serial, daemon=True).start()

app.layout = dmc.MantineProvider(
    html.Div([
        dbc.Nav(
            id="sidebar",
            children=[
                html.Div(
                    "SatDash",
                    id = "sidebar_title"
                ),
                html.Button('Save Data', id='save_data_button', n_clicks=0)
            ],
            vertical=True
        ),
        
        html.Div(
            [                       
                dash_draggable.ResponsiveGridLayout(
                    id='draggable',
                    style = {'margin-left' : '150px'},
                    children=[
                        # Temperature chart
                        html.Div(children=[
                            html.H3("Temperature over time", style={"marginBottom": "2px", "fontSize": "18px", "textAlign": "center"}, id="temperature_title"),
                            dmc.AreaChart(
                                id="temp_chart", 
                                h=300,
                                dataKey="time",
                                data=[],  
                                series=[{"name": "temperature", "color": "orange.7"}],
                                curveType="bump",
                                tickLine="xy",
                                withGradient=False,
                                withXAxis=True,
                                withDots=True,
                                xAxisLabel="Time (seconds)",
                                yAxisLabel="Values",
                                type="stacked",
                            )
                        ], style={
                            "height": '100%',
                            "width": '100%',
                            "display": "flex",
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "color" : "white"
                        }),

                        # Pressure chart
                        html.Div(children=[
                            html.H3("Pressure over time", style={"marginBottom": "2px", "fontSize": "18px", "textAlign": "center"}, id="pressure_chart_title"),
                            dmc.AreaChart(
                                id="pressure_chart", 
                                h=300,
                                dataKey="time",
                                data=[],  
                                series=[{"name": "pressure", "color": "pink.7"}],
                                curveType="bump",
                                tickLine="xy",
                                withGradient=False,
                                withXAxis=True,
                                withDots=True,
                                xAxisLabel="Time (seconds)",
                                yAxisLabel="Values", 
                            )
                        ], style={
                            "height": '100%',
                            "width": '100%',
                            "display": "flex",
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "color" : "white"

                        }),

                        # Thermometer to display the latest temperature
                        html.Div(id = "thermometer_div" ,children=[
                            html.H3("Current Temperature", style={"textAlign": "center", "fontSize": "18px"}, id="thermometer_title"),
                            daq.Thermometer(
                                id="thermometer",
                                min=0,  
                                max=100,  
                                value=0,  
                                color="#e84175",
                                showCurrentValue=True,
                                height=40,
                                width=10, 
                            ),
                        ], style={
                            "height": '100%',  
                            "width": '100%',  
                            "display": "flex",
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "align-items": "center", 
                            "justify-content": "center",
                        }),

                        # Pressure gauge
                        html.Div(id = "pressure_div", children=[
                            html.H3("Current Pressure", style={"textAlign": "center", "fontSize": "18px"}, id="pressure_title"),
                            dcc.Graph(id='pressure_gauge')
                        ], style={
                            "height": '100%',  
                            "width": '100%',  
                            "display": "flex",
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "align-items": "center", 
                            "justify-content": "center"
                        }),

                        # Velocity display
                        html.Div(id="velocity_div", children=[
                            html.H3("Current Velocity", style={"textAlign": "center", "fontSize": "18px"}, id="velocity_title"),
                            dcc.Graph(id='velocity_display')
                        ], style={
                            "height": '100%',  
                            "width": '100%',  
                            "display": "flex",
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "align-items": "center", 
                            "justify-content": "center"
                        }),

                        # Light display
                        html.Div(id = "light_div", children=[
                            html.H3("Current Light Intensity", style={"textAlign": "center", "fontSize": "18px"}, id="light_title"),
                            html.Div(children=[
                                html.H4(id='light_display', style={
                                    'position': 'absolute', 'top': '25%', 'left': '50%', 'transform': 'translate(-50%, -50%)',
                                    'textAlign': 'center', 'fontSize': '18px', 'color': '#0f1d39', 'zIndex': 10
                                }),
                                html.H3('☀️',id="sun_emoji",style={
                                    'fontSize': '60px', 'textAlign': 'center', 'display': 'inline',
                                    'position': 'absolute', 'top': '35%', 'left': '50%', 'transform': 'translate(-50%, -50%)',
                                    'zIndex': 1
                                }),
                            ], style={
                                'position': 'relative', 'height': '100px', 'width': '100px', 'display': 'inline-block'
                            }),
                        ], style={
                            "height": '100%',  
                            "width": '100%',  
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "align-items": "center",
                            'display': 'flex',
                            "justify-content": "center",
                        }),

                        # Accelerometer display
                        html.Div(id = "accelerometer_div", children=[
                            html.H3("Current Acceleration", style={"textAlign": "center", "fontSize": "18px"}, id="accelerometer_title"),
                            daq.Gauge(
                                id="accelerometer_gauge", 
                                size=80,
                                min=0,
                                max=120,
                                value=0,
                                showCurrentValue=True,
                                color = "#fb6b29",
                                units ="m/s^2",
                                scale={
                                    "custom": {
                                        0: {"style": {"fill": "#0f1d39"}, "label": "hey"},
                                        20: {"style": {"fill": "#0f1d39"}, "label": "hey"},
                                        40: {"style": {"fill": "#0f1d39"}, "label": "hey"},
                                        60: {"style": {"fill": "#0f1d39"}, "label": "hey"},
                                        80: {"style": {"fill": "#0f1d39"}, "label": "hey"},
                                        100: {"style": {"fill": "#0f1d39"}, "label": "hey"},
                                        120: {"style": {"fill": "#0f1d39"}, "label": "hey"},
                                    }
                                },
                                style={
                                    "height": '90%',
                                    'margin-bottom': '0px',
                                    'padding-bottom': '0px',
                                }
                            ),
                        ], style={
                            "height": '100%',  
                            "width": '100%',  
                            "display": "flex",
                            "flex-direction": "column",
                            "align-items": "center",
                            "justify-content": "center"
                        }),
                        
                        # Can3D
                        html.Div(
                            style={"width": "100%", "height": "100%"},
                                children=[
                                dash_vtk.View([
                                    dash_vtk.GeometryRepresentation([
                                        dash_vtk.Mesh(id='cylinder-mesh', state=mesh_state)
                                    ])
                                ], background=[0.059,0.114,0.224], cameraPosition=[0, 0, -10]),
                            ]),
                        
                        html.Div(
                            id = "pitch_div",
                            children = [
                                html.H1("Pitch"),
                                html.H2(id='gyro_x')
                            ], 
                            style={
                            "height": '100%',  
                            "width": '100%',  
                            "display": "flex",
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "align-items": "center",
                            "justify-content": "center"
                        }),                       
                        html.Div(
                            id = "roll_div",
                            children = [
                                html.H1("Roll"),
                                html.H2(id='gyro_y')
                            ],  
                            style={
                                "height": '100%',  
                                "width": '100%',  
                                "display": "flex",
                                "flex-direction": "column",
                                "flex-grow": "0",
                                "align-items": "center",
                                "justify-content": "center"
                            }
                        ),
                        html.Div(
                            id = "yaw_div",
                            children = [
                                html.H1("Yaw"),
                                html.H2(id='gyro_z')
                            ],
                            style={
                            "height": '100%',  
                            "width": '100%',  
                            "display": "flex",
                            "flex-direction": "column",
                            "flex-grow": "0",
                            "align-items": "center",
                            "justify-content": "center"
                        })                      
                    ]
                ),
                dcc.Interval(id='interval-component', interval=35, n_intervals=0),
                # dcc.Interval(id='can3d-interval-component', interval=10, n_intervals=0)

            ])
        ])
)

@callback(
    Output('save_data_button', 'n_clicks'),
    Input('save_data_button', 'n_clicks')
)

def save_data(n_clicks):
    if n_clicks > 0:
        with data_lock:
            if not data.empty:
                for sensor_type in ['gyroscope', 'accelerometer','velocity','temperature','pressure','light']:
                    sensor_data = data[data['sensor_type'] == sensor_type]
                    if not sensor_data.empty:
                        filename = f'{sensor_type}_data.csv'
                        if os.path.exists(filename):
                            last_entry = pd.read_csv(filename).iloc[-1]
                            last_entry_index = sensor_data[(sensor_data == last_entry).all(axis=1)].index
                            
                            if not last_entry_index.empty:
                                new_data = sensor_data.loc[last_entry_index[-1] + 1:]
                            else:
                                new_data = sensor_data          
                        else:
                            new_data = sensor_data  
                        
                        if not new_data.empty:
                            new_data.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
                            print(f"New data appended to {filename}.")
                        else:
                            print(f"No new data to append for {sensor_type}.")
                    else:
                        print(f"No data to save for {sensor_type}.")
            else:
                print("No data to save.")
    return 0



@app.callback(
    [
        Output('temp_chart', 'data'), 
        Output('pressure_chart', 'data'),
        Output('thermometer', 'value'),
        Output('pressure_gauge','figure'),
        Output('velocity_display', 'figure'),
        Output('light_display','children' ),
        Output('accelerometer_gauge','value'),
        Output('gyro_x','children'),
        Output('gyro_y','children'),
        Output('gyro_z','children'),
        Output('cylinder-mesh', 'state')
    ],
    [
        Input('interval-component', 'n_intervals')
    ]
)

def update_graphs(n):
    global angle_x, angle_y, angle_z
    
    transformation = vtk.vtkTransformPolyDataFilter()
    transform = vtk.vtkTransform()
    transform.RotateX(angle_y)
    transform.RotateY(angle_x)
    transform.RotateZ(angle_z)

    transformation.SetTransform(transform)
    transformation.SetInputData(poly_data)
    transformation.Update()

    new_poly_data = transformation.GetOutput()
    new_mesh_state = to_mesh_state(new_poly_data)
    
    temp_chart_data = []
    pressure_chart_data = []

    thermometer_value = 0 
    acceleration_value = 0
    latest_velocity = 0
    latest_light = 0
    
    yaw_value = ""
    pitch_value = ""
    roll_value = ""
    
          
    gauge_pressure_fig = go.Figure()  
    velocity_display_fig = go.Figure()

    with data_lock:
        if not data.empty:
            
            try:
            # temperature data filtering
                temperature_data = data[data['sensor_type'] == 'temperature'].copy()
                if not temperature_data.empty:
                    temperature_data = temperature_data.astype({'value': float, 'time': float})
                    temp_chart_data = temperature_data[['time', 'value']].rename(columns={'value': 'temperature'}).to_dict('records')

                    #thermometer value
                    thermometer_value = temperature_data['value'].iloc[-1]
                    
            except ValueError as e:
                    print(f"Error processing temperature data: {e}")
  
            #pressure data filtering
            try:
                pressure_data = data[data['sensor_type'] == 'pressure'].copy()
                if not pressure_data.empty:
                    pressure_data = pressure_data.astype({'value': float, 'time': float})
                    pressure_chart_data = pressure_data[['time', 'value']].rename(columns={'value': 'pressure'}).to_dict('records')
                    
                    latest_pressure = pressure_data.iloc[-1]['value']
                    
                    #gauge for pressure
                    gauge_pressure_fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=latest_pressure,
                        gauge={
                            'axis': {'range': [None, 100], 'tickcolor': 'white'},
                            'bar': {'color': '#d8eaff'},
                            'steps': [
                                {'range': [0, 50], 'color': '#2e547f'},
                                {'range': [50, 100], 'color': '#61c3df'},
                            ]
                        }
                    ))
                    
                    gauge_pressure_fig.update_layout(
                        paper_bgcolor='#0f1d39', 
                        font_color='white', 
                        margin=dict(l=30, r=40, t=0, b=10)
                    )
                    
            except ValueError as e:
                    print(f"Error processing pressure data: {e}")
                    
            # velocity display       
            try:
                velocity_data = data[data['sensor_type'] == 'velocity'].copy()
                if not velocity_data.empty:

                    latest_velocity = float(velocity_data.iloc[-1]['value']) 
                    
                    velocity_display_fig = go.Figure(
                        data=[go.Pie(
                            values=[abs(latest_velocity)/5*100, 100 - abs(latest_velocity)/5*100],
                            hole=.6,
                            marker=dict(colors=['#432267', '#b463b1']),
                            textinfo='none',
                            direction='clockwise',
                            hoverinfo='none'
                            )
                        ]
                    )
                    
                    velocity_display_fig.update_layout(    
                        paper_bgcolor='#0f1d39', 
                        font_color='white',
                        showlegend=False,
                        margin=dict(l=0, r=0, t=0, b=0),
                        annotations=[
                            dict(
                                x=0.5,
                                y=0.5,  
                                text=f"{abs(latest_velocity):.1f}",
                                font=dict(size=14, color="white"),  
                                showarrow=False
                            )
                        ]
                    )

            except ValueError as e:
                    print(f"Error processing velocity data: {e}")
            
            
            # light display       
            try:
                light_data = data[data['sensor_type'] == 'light'].copy()
                if not light_data.empty:
                    latest_light = float(light_data.iloc[-1]['value'])                 
                    
            except ValueError as e:
                    print(f"Error processing light data: {e}")
                    
            # accelerometer display       
            try:
                accelerometer_data = data[data['sensor_type'] == 'accelerometer'].copy()
                if not accelerometer_data.empty:
                    
                    acceleration_value = float(accelerometer_data.iloc[-1]['value'])
                    
            except ValueError as e:
                    print(f"Error processing accelerometer data: {e}")  
            
            
            # gyroscope display       
            try:
                gyro_data = data[data['sensor_type'] == 'gyroscope'].copy()
                if not gyro_data.empty:
                    
                    gyro_data[['yaw', 'pitch', 'roll']] = gyro_data['value'].str.split(',', expand=True)
                    gyro_data = gyro_data.drop(columns=['value'])
                    gyro_data = gyro_data.astype({'yaw': float, 'pitch': float, 'roll': float})
                    latest_gyro = gyro_data.iloc[-1]
                    yaw_value = f"{latest_gyro['yaw']:.2f}"
                    pitch_value = f"{latest_gyro['pitch']:.2f}"
                    roll_value = f"{latest_gyro['roll']:.2f}"
                    
                    angle_x = float(latest_gyro["yaw"])
                    angle_y = float(latest_gyro["pitch"])
                    angle_z = float(latest_gyro["roll"])
                    

            except ValueError as e:
                    print(f"Error processing gyro data: {e}")
                    
                    
                
    return [temp_chart_data, pressure_chart_data, thermometer_value, gauge_pressure_fig, velocity_display_fig, latest_light, acceleration_value, yaw_value, pitch_value, roll_value, new_mesh_state] 

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
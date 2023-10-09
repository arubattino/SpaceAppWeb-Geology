from folium import Map
from dash import html, Dash, Input, Output
from folium.plugins import MousePosition, Draw, LocateControl, MiniMap
import dash_bootstrap_components as dbc
import os

LOGO = 'https://timur.es/wp-content/uploads/2019/10/Space-Apps-NASA.png'

def create_map(output_file="./templates/index.html"):

    # Create a map centered at the first pair of coordinates
    my_map = Map(location=[0, 0], zoom_start=3)

    MiniMap(zoom_level_offset=-8, toggle_display=True, width=250, height=250).add_to(my_map)

    buttons = {'polyline':False, 'polygon':False, 'rectangle':False, 'circle':False, 'marker':True, 'circlemarker':False}
    Draw(export=False, draw_options=buttons).add_to(my_map)

    LocateControl(auto_start=False).add_to(my_map)

    MousePosition(
    position="topright",
    separator=" | Lon: ",
    empty_string="NaN",
    lng_first=True,
    prefix="Lat:",
                ).add_to(my_map)

    # Save the map as an HTML file
    my_map.save(output_file)


if __name__ == "__main__":
    # Replace these with your desired list of coordinates

    create_map()

    # Initialize the Dash app
    app = Dash(__name__,  external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Read the map HTML file
    with open("./templates/index.html", "r") as f:
        map_html = f.read()

    # Define the app layout
    app.layout = html.Div([
        dbc.Container([
                
                dbc.Row([
                    dbc.Col(html.Img(src=LOGO, height="35", ), width={"size": 0, "offset": 2},),
                    dbc.Col(dbc.Select(id='year-input', options=[
                                                                                {"label": "2023", "value": "2023"},
                                                                                {"label": "2022", "value": "2022"},
                                                                                {"label": "2024", "value": "2024", "disabled": True},
                                                                            ],placeholder='Year',size="sm", style={'margin-left': '0', 'margin-right': '0'}), width={"size": 1, "offset": 0}),

                    dbc.Col(dbc.Select(id='month-input', options=[
                                                                                {"label": "January", "value": "01"},
                                                                                {"label": "February", "value": "02"},
                                                                                {"label": "March", "value": "03"},
                                                                                {"label": "April", "value": "04"},
                                                                                {"label": "May", "value": "05"},
                                                                                {"label": "June", "value": "06"},
                                                                                {"label": "July", "value": "07"},
                                                                                {"label": "August", "value": "08"},
                                                                                {"label": "September", "value": "09"},
                                                                                {"label": "Octuber", "value": "10"},
                                                                                {"label": "November", "value": "11"},
                                                                                {"label": "December", "value": "12"},
                                                                            ],placeholder='Month', className='ml-0',size="sm"), width={"size": 1, "offset": 0}),

                    dbc.Col(dbc.Input(id='box-input', type='text', placeholder='Coordinates', className='ml-0',size="sm"), width={"size": 2, "offset": 0}),
                    dbc.Col(dbc.Input(id='username-input', type='text', placeholder='User EarthData ', className='ml-0',size="sm"), width={"size": 2, "offset": 0}),  # Reducir el tamaño del campo y añadir margen inferior
                    dbc.Col(dbc.Input(id='password-input', type='password', placeholder='Password', className='ml-0',size="sm"), width={"size": 1, "offset": 0}),  # Reducir el tamaño del campo y añadir margen inferior
                    dbc.Col(dbc.Button('Send Order', id='login-button', n_clicks=0, color='primary', className='ml-0',size="sm"), width=2),  # Añadir margen inferior al botón
                ], className='mt-1', align="center"),
                
                html.Div(id='output-message')
            ], className='mb-1'),
        

        html.Iframe(srcDoc=map_html, width="100%", height="700px")
        ])
    
    # Callback para manejar el clic del botón y enviar coords
    @app.callback(
        Output('output-message', 'children'),
        Input('login-button', 'n_clicks'),
        Input('username-input', 'value'),
        Input('password-input', 'value'),
        Input('box-input', 'value'),
        Input('year-input', 'value'),
        Input('month-input', 'value'),
    )

    
    def check_credentials(n_clicks, username, password, box, year, month):
        if n_clicks == 1:

            lat, lon = box.split(',')

            bx = f'{lat},{lon},{lat},{lon}'

            date = f'{year}-{month}-01,{year}-{month}-30'

            os.system('python main.py --u ' + username + ' --p ' + password + ' --d ' + date  + ' --bx ' + '"'+"'"+bx+"'"+'"')

    

    # Run the Dash app
    app.run_server(debug=False)
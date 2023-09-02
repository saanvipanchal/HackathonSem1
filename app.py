from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px  # used to create visualization and graph
import pandas as pd  # used to read csv file and graph data
import geojson  #used for Geo Graph
import dash
import dash_ag_grid as dag  # used for Grid
import dash_bootstrap_components as dbc  # for bootstrap UI and Styles

#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')


#Create Dash object
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title="Crop Analyzer"

server = app.server  # require for Heroku deployment

#Load Entire dataset downloaded from Kaggle : https://www.kaggle.com/datasets/abhinand05/crop-production-in-india?resource=download
df=pd.read_csv('data/crop_production.csv')
 
with open('data/indian_states.geojson') as f:
    geoIndianState = geojson.load(f)

#History data is from year 1997 to 2015. We will use history data from year 2008 to 2015. Hence we are cleaning data
df = df[df['Crop_Year'] >= 2008]

#Get Unique statename
stateNames=df["State_Name"].unique()


# app.layout = html.Div([
#     html.H1(children='Indian Crop Analyzer', style={'textAlign':'center'}),
#     dcc.Dropdown(stateNames, 'Gujarat', id='dropdown-selection'),
#     dcc.Graph(id='graph-content')
# ])

def GeoMap():
    dfGeo=df.groupby('State_Name').sum("Production")
    dfGeo.reset_index(inplace=True)
    dfGeo.rename(columns = {'State_Name':'state'}, inplace = True)
    
    fig = px.choropleth(
            dfGeo,
            geojson=geoIndianState,
            featureidkey='properties.ST_NM',
            locations='state',
            color='Production',
            color_continuous_scale='Reds'
        )

    fig.update_geos(fitbounds="locations", visible=False)
    return fig

def populationTable():
    dfTable=df.groupby('State_Name').sum("Production")
    dfTable.reset_index(inplace=True)

    columnDefs = [
        {"field": "State_Name"},
        {"field":"Crop_Year"},
        {"field": "Production"}
    ]    
        
    return html.Div(
    [
        dcc.Markdown(
             "Use the 'Update Filter' button to set the `filterModel` "
         ),
        html.Button("Update Filter", id="filter-model-btn-2", n_clicks=0),
        dag.AgGrid(
            id="filter-model-grid-2",
            columnSize="sizeToFit",
            rowData=dfTable.to_dict("records"),
            columnDefs=columnDefs,
            defaultColDef={"filter": True, "sortable": True, "floatingFilter": True},
            persistence=True,
            persisted_props=["filterModel"]
        ),
    ]
)

@callback(
    Output("filter-model-grid-2", "filterModel"),
    Input("filter-model-btn-2", "n_clicks"),
)
def get_cur_filter(n):
    if n >0:
        return {'State_Name': {'filterType': 'text', 'type': 'contains', 'filter': 'Guj'}}
    return dash.no_update

layout1 = html.Div([
    html.H1(children='Indian Crop Analyzer', style={'textAlign':'center'}),
    dcc.Dropdown(stateNames, 'Gujarat', id='dropdown-selection'),
    dcc.Graph(id='graph-content'),
    dcc.Graph(id='bar-graph-content'),
    dcc.Graph(
        figure=GeoMap(),id='geo-graph-content'
    ),
    populationTable()
])

app.layout = html.Div([

    dbc.Row(dbc.Col(html.H1(children='Indian Crop Analyzer', style={'textAlign':'center'}))),
    dbc.Row(dbc.Col(html.H2(children='A Indian Crop Analyzer show Production and statistics.', style={'textAlign':'center'}))),
    dbc.Row(
            [
                dbc.Col(dcc.Dropdown(stateNames, 'Gujarat', id='dropdown-selection'),),
                dbc.Col(html.Div(" ")),
            ]
        ),   
    dbc.Row(
            [
                dbc.Col(dcc.Graph(id='graph-content')),
                dbc.Col(dcc.Graph(id='bar-graph-content')),
            ]
        ),   
    dbc.Row(
            [
                dbc.Col(dcc.Graph(
                            figure=GeoMap(),id='geo-graph-content'
                        )),
                dbc.Col(populationTable()),
            ]
        ),   
    
])


@callback(
    Output('graph-content', 'figure'),
    Output('bar-graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    dff=df[df['State_Name']==value].groupby('Crop_Year').sum("Production")
    dff.reset_index(inplace=True)
    return [px.line(dff, x='Crop_Year', y='Production'),px.bar(dff, x='Crop_Year', y='Production')]


if __name__ == '__main__':
    app.run(debug=True)
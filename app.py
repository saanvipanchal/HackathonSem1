from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px  # used to create visualization and graph
import pandas as pd  # used to read csv file and graph data
import geojson  #used for Geo Graph
import dash
import dash_ag_grid as dag  # used for Grid
import dash_bootstrap_components as dbc  # for bootstrap UI and Styles
import plotly.graph_objects as go


#############################################
#Initialize Objects and Get Data: START

#Create Dash object
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title="Crop Analyzer"

server = app.server  # require for Heroku deployment

#Load Entire dataset downloaded from Kaggle : https://www.kaggle.com/datasets/abhinand05/crop-production-in-india?resource=download
df=pd.read_csv('data/crop_production.csv')

#Get indian state name used of geo chart 
with open('data/indian_states.geojson') as f:
    geoIndianState = geojson.load(f)

#Data Cleaning
#History data is from year 1997 to 2015. We will use history data from year 2008 to 2015. Hence we are cleaning data
df = df[df['Crop_Year'] >= 2008]

#Get Unique statename used for dropdown
stateNames=df["State_Name"].unique()


#Initialize Objects and Get Data: END
#############################################

#Bubble Chart for State Name, Area, and Production for year 2014
def BubbleChart():
    dfData=df[df['Crop_Year']==2014].groupby(['State_Name','Crop_Year']).sum("Production")
    dfData.reset_index(inplace=True)

    fig = px.scatter(dfData, x="Production", y="Area",
                size="Production", color="State_Name",
                    hover_name="State_Name", log_x=True, size_max=60)
                        
    return fig

#Geo chart 
def GeoMap():
    dfGeo=df.groupby('State_Name').sum("Production")
    dfGeo.reset_index(inplace=True)
    dfGeo = dfGeo.replace('Jammu and Kashmir ','Jammu & Kashmir', regex=True)    
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

#############################################
#Create Crop Production Table : START
def CropProductionTable():
    dfTable=df.groupby(['State_Name','Crop_Year']).sum("Production")
    dfTable.reset_index(inplace=True)

    columnDefs = [
        {"field": "State_Name"},
        {"field":"Crop_Year"},
        {"field": "Production"}
    ]    
        
    table1= html.Div(
    [
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
    return table1

@callback(
    Output("filter-model-grid-2", "filterModel"),
    Input("filter-model-btn-2", "n_clicks"),
)
def get_cur_filter(n):
    if n >0:
        return {'State_Name': {'filterType': 'text', 'type': 'contains', 'filter': 'Guj'}}
    return dash.no_update
#Create Crop Production Table : END
#############################################

#Main Web Application Layout
app.layout = dbc.Container([

    dbc.Row(dbc.Col(html.H1(children='Indian Crop Analyzer', style={'textAlign':'center'}), class_name='bg-primary text-white'),class_name='p-2'),
    dbc.Row(dbc.Col(html.H4(children='Help Agriculture.Help Farmers', style={'textAlign':'center'}))),
    dbc.Row(dbc.Col(html.Hr())),
    dbc.Row(
            [
                dbc.Col(dcc.Dropdown(stateNames, 'Gujarat', id='dropdown-selection')),
                dbc.Col(html.Div(" ")),
            ], class_name="m-2"
        ),   
    dbc.Row(
            [
                dbc.Col(
                    [html.H5(children="Indian crop production year wise", style={'textAlign':'center'}),
                     dcc.Graph(id='graph-content')], class_name='border-2  border-success'
                   ,sm=12 ,lg=6 ),
                dbc.Col(
                    [(html.H5(children="Analysis of crop production year-wise", style={'textAlign':'center'})),
                    dcc.Graph(id='bar-graph-content')],sm=12 ,lg=6),
            ], class_name="m-2"
        ),   
    dbc.Row(
            [
                dbc.Col(
                         [(html.H5(children="Analysis of state-wise and year-wise crop production", style={'textAlign':'center'})),
                            dcc.Graph(
                            figure=GeoMap(),id='geo-graph-content')]
                        ,sm=12 ,lg=6),
                dbc.Col(
                    [(html.H5(children="Analysis of state-wise and year-wise crop production", style={'textAlign':'center'})),
                    CropProductionTable()],sm=12 ,lg=6)
            ], class_name="m-2"
        ),
      dbc.Row(
            [
                dbc.Col(  [          
                       ( html.H5(children="Analysis of Season-wise Crop Production" , style={'textAlign':'center'})),
                        dcc.Dropdown(stateNames,'Gujarat', id="dropdown-season-pie"),
                        dcc.Graph(id="graph-season-pie")
                    ],sm=12 ,lg=6),
                dbc.Col([
                    (html.H5(children="Analysis of area-wise and state-wise crop production",style={'textAlign':'center'})),
                    dcc.Graph(id='datatable-upload-graph', figure = BubbleChart())],sm=12 ,lg=6),
            ], class_name="m-2"
        ),         
    
], class_name="bg-light mt-n1 border-2 border-success")

#Main Callback
@callback(
    Output('graph-content', 'figure'),
    Output('bar-graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    dff=df[df['State_Name']==value].groupby('Crop_Year').sum("Production")
    dff.reset_index(inplace=True)
    return [px.line(dff, x='Crop_Year', y='Production'),px.bar(dff, x='Crop_Year', y='Production')]

#############################################
#Seasonwise Pie chart : START
@callback(
    Output("graph-season-pie", "figure"),
    Input("dropdown-season-pie", "value")
)
def generate_chart_seasonwiseProduction(value):
    dfData=df[df['State_Name']==value].groupby('Season').sum("Production")
    if 'Whole Year ' in dfData.index:
        dfData=dfData.drop('Whole Year ')
    dfData.reset_index(inplace=True)

      
    fig = px.pie(dfData, values='Production', names='Season', hole=0.3)
    return fig
#Seasonwise Pie chart : END
#############################################

if __name__ == '__main__':
    app.run(debug=True)
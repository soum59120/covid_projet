#!/usr/bin/env python
# coding: utf-8

# In[1]:


# charger les packages

from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
import requests
#import numpy
#import json
import dash
import csv
import ssl


# autoriser l'accès à des sites internet
ssl._create_default_https_context = ssl._create_unverified_context


# données concernant les cas covid19 dans le monde
raw = requests.get("https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/Coronavirus_2019_nCoV_Cases/FeatureServer/2/query?where=1%3D1&outFields=*&outSR=4326&f=json")
raw_json = raw.json()
df_world = pd.DataFrame(raw_json["features"])
df_world = df_world["attributes"].tolist()
df_final_world = pd.DataFrame(df_world)
df_final_world = df_final_world[["Country_Region", "Lat", "Long_", "Confirmed", "Deaths", "Recovered"]]


# données concernant le dépistage par département
depist = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/b4ea7b4b-b7d1-4885-a099-71852291ff20", sep = ";")
depist = depist.loc[depist['clage_covid'] == '0'] # avoir tous les ages compris
depist = depist[["dep","jour","nb_test","nb_pos"]]


# données concernant les cas hospitalisés/réanimés/décès/guéris
sante_public = pd.read_csv("https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c", sep = ";")
sante_public = sante_public.rename(columns={'incid_hosp':'hosp',"incid_rea":"rea", "incid_rad":"rad",'incid_dc':'dc'})
sante_public = sante_public[["dep","jour","hosp","rea","rad","dc"]]


# données concernant le nombre de cas confirmés par régions
casconf = pd.read_csv('https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv')
casconf_reg = casconf.loc[casconf['granularite'] == 'region']
casconf_reg = casconf_reg[["date", "maille_nom", "cas_confirmes"]]
casconf_reg = casconf_reg.rename(columns={'maille_nom': 'region_name', "date": "jour"})
casconf_reg = casconf_reg.drop_duplicates(['jour','region_name'], keep='first')
casconf_reg = casconf_reg.dropna()


# données concernant le nombre de cas confirmés pour l'ensemble du pays
casconf_fr = pd.read_csv("https://www.coronavirus-statistiques.com/corostats/openstats/open_stats_coronavirus.csv?fbclid=IwAR3UIrk4TZ6B0ZrJGEvKSgo9tULZsQDiIWGMSQF1WwK8bqzUBIWHoEUht7g",sep=";")
casconf_fr = casconf_fr.loc[casconf_fr['nom'] == "france"]
casconf_fr = casconf_fr.drop(['source','code','nom','guerisons','deces'], axis = 1)
casconf_fr = casconf_fr.rename(columns={'cas': 'cas_confirmes'})
casconf_fr['date'] = pd.to_datetime(casconf_fr['date'])
casconf_fr = casconf_fr.fillna(0)


## code des départements
code_dep = pd.read_csv('https://www.data.gouv.fr/fr/datasets/r/987227fb-dcb2-429e-96af-8979f97c9c84')
code_dep = code_dep.rename(columns={'num_dep': 'dep'})



# merger les données de la table santé_public + les données concernant les tests de dépistage
df_santepub_dep = pd.merge(sante_public, depist, on=["dep","jour"], how="left")
df_santepub_dep = pd.merge(df_santepub_dep, code_dep, on=["dep"], how="left")




## AGGREGATION DES TABLEES 

# Par département, avoir le total de décés (dc), réanimés (rea), hospotalisés (hosp) et guéris (rad)
df_total = df_santepub_dep.groupby("dep_name", as_index=False).agg(
    {
        "dc" : "sum",
        "rad" : "sum",
        "hosp" : "sum",
        "rea" : "sum"
    }
)

# Avoir le top 10 des départements ayant un taux de décès élevé
df_top10 = df_total.nlargest(10, "dc")
top10_countries = df_top10["dep_name"].tolist()
top10_dc = df_top10["dc"].tolist()

# Avoir le nombre total pour chaque type de cas (cas confirmeé, décès, guéris, réanimés et hospitalisés)
total_confirmed = casconf_fr['cas_confirmes'].iloc[-1]
total_deaths = df_santepub_dep["dc"].sum()
total_recovered = df_santepub_dep["rad"].sum()
total_hosp = df_santepub_dep["hosp"].sum()
total_rea = df_santepub_dep["rea"].sum()

# Avoir les noms uniques des régions
regions = df_santepub_dep['region_name'].unique()




## Construire la grille pour insérer les figures
fig = make_subplots(
    rows = 4, cols = 6,
    specs=[
            [    {"type": "scattergeo", "rowspan": 4, "colspan": 3}, None, None, {"type": "indicator","colspan": 3}, None, None],
            [    None, None, None, {"type": "indicator"},{"type": "indicator"},{"type": "indicator"}],
            [    None, None, None, {"type": "indicator"}, None, {"type": "indicator"}],
            [    None, None, None, {"type": "bar", "colspan":3}, None, None],
          ],
    subplot_titles=(None,"Cas du Covid-19 en France",None,None,None,None,None,"Taux Mortalité : TOP10 des départements"),
    vertical_spacing=0.1
)



## Ajouter une colonne pour les annotations pour afficher les informations (décès, etc) dans la world map
message = df_final_world["Country_Region"] + "<br>"
message += "confirmés: " + df_final_world["Confirmed"].astype(str) + "<br>"
message += "décès: " + df_final_world["Deaths"].astype(str) + "<br>"
message += "guéris: " + df_final_world["Recovered"].astype(str) + "<br>"
df_final_world["text"] = message



## Configuration de la world map 
fig.add_trace(
    go.Scattergeo(
        lon = df_final_world["Long_"],
        lat = df_final_world["Lat"],
        hovertext = df_final_world["text"],
        showlegend=False,
        marker = dict(
            size = 10,
            opacity = 0.8,
            reversescale = True,
            autocolorscale = True,
            symbol = 'square',
            line = dict(
                width=1,
                color='rgba(102, 102, 102)'
            ),
            cmin = 0,
            color = df_final_world['Confirmed'],
            cmax = df_final_world['Confirmed'].max(),
            colorbar_title="Cas confirmés",  
            colorbar_x = -0.1
        )

    ),
   
    row=1, col=1
)



## Configuration des indicateurs (nombre de cas confirmés, etc)
fig.add_trace(
    go.Indicator(
        mode="number",
        value=total_confirmed,
        title="Confirmés",
    ),
    row=2, col=4
)

fig.add_trace(
    go.Indicator(
        mode="number",
        value=total_recovered,
        title="Guérisons",
    ),
    row=2, col=5
)

fig.add_trace(
    go.Indicator(
        mode="number",
        value=total_deaths,
        title="Décès",
    ),
    row=2, col=6
)

fig.add_trace(
    go.Indicator(
        mode="number",
        value=total_rea,
        title="Réanimés",
    ),
    row=3, col=4
)

fig.add_trace(
    go.Indicator(
        mode="number",
        value=total_hosp,
        title="Hospitalisés",
    ),
    row=3, col=6
)


## Configuration du graphique en bâton pour avoir le top 10 des départements touchés par un taux de décès élevé
fig.add_trace(
    go.Bar(
        x=top10_countries,
        y=top10_dc,
        marker=dict(color="Red"),
        showlegend=False,
    ),
    row=4, col=4
)

## Configuration des paramètres de visualisation (template, police d'écriture, etc) de notre dashboard
fig.update_layout(
    template="plotly_dark",
    title = "Cas du COVID-19 dans le Monde",
    yaxis=dict(showgrid=False),
    showlegend=True,
    legend_orientation="h",
    legend=dict(x=0.65, y=0.8),
    geo = dict(
            projection_type="orthographic",
            showcoastlines=True,
            landcolor="white",
            showland= True,
            showocean = True,
            lakecolor= "LightBlue"
    )
)



## CREATION DU DASHBOARD

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    "/assets/style.css",
]
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)


server = app.server


# configuration des composants du dashboard
app.layout = html.Div([
        dcc.Tabs(id="tabs",
                children=[
                   
            dcc.Tab(label='Aperçu de la pandémie COVID-19 dans le Monde',
                    value='tab-1',
                    children = [
                               dcc.Graph(
                                   style={"height":"100vh"},
                                   figure=fig
                               )]
                    ),
                   
            dcc.Tab(label="Chiffres de la pandémie COVID-19 en France",
                    value='tab-2',
                    children=[
                        
                 html.Div(
                    className="content",
                    children=[
                
                    html.Div(
                    className="left_menu", children=[      
                        html.Div(children=[
                            html.H3('Sélectionner la région :'),
                            dcc.Dropdown(
                                    id='metric-regions',
                                    options=[{'label': i, 'value': i} for i in regions],
                                    value='Hauts-de-France'),
                            html.Div([]),
                            html.H3('Sélectionner la métrique :'),
                            dcc.Checklist(
                                    id='metric-list',
                                    options=[{'label': m, 'value': m} for m in ['Hospitalisés','Décès','Guéris']],
                                    value=['Hospitalisés','Décès','Guéris'])                       
                        ]), 
                    ],
                        style = {
                        'width': '20%',
                        'position': 'fixed',
                        'left': '0',
                        'height': '100vh',
                        'z-index': '999',
                        'background':'#dce6e6',
                        'textAlign': 'center',
                        'color': '#000000',
                        'font-family':'Rockwell', 
                        'font-size':'18'}
                    ),

       
                    html.Div(
                    className="content",
                    children=[
                        html.Div(
                            children=[ 
                                html.P(' '),
                                html.Div(
                                    [html.P("Nombre total de tests de dépistage effectués : "), html.H3(id="test_txt")],
                                    className="five columns",
                                    style =  {'background':'#F7F7F7',
                                              'color':'#000000',
                                              'font-family':'Rockwell',
                                             }
                                ),
                                html.Div(
                                    [html.P("Nombre total de tests de dépistage positifs :"), html.H3(id="testpos_txt")],
                                    className="five columns",
                                    style =  {'background': '#F7F7F7',
                                              'color':'#000000',
                                              'font-family':'Rockwell', 
                                              'font-size':'18'
                                             }
                                ), 
                                ],
                            style = {'width':'75%',
                                    'position':'absolute',
                                    'center': '0',
                                    'right': '0',
                                    'textAlign':'center',
                                    'height': '80vh',
                                    'z-index': '999'}
                        ),
                        
                        ], style = {
                        'background': '#2A3F54',
                        'color':'#dce6e6',
                        'height': '120px',
                        'width':'80',
                        'position':'relative',
                        'top': '0',
                        'right': '0'}),
                
                     
                        html.Div([
                             dcc.Graph(id='indicator-graphic'),
                             dcc.Graph(id='indicator-graphic2')  
                            ],
                             style = {'width':'80%',
                                      'position':'absolute',
                                      'down': '0',
                                      'right': '0',
                                      'textAlign':'center'}),
                        
                    ], style =  {'width': '100%','background': '#F7F7F7'}
                    ),

            ]),
        ],
                colors={
                    "border": "white",
                    "primary": "#dce6e6",
                    "background": "#dce6e6"},
                style =  {'font-family':'Rockwell'},
    ),
])




# configuration des sorties des composantes du dashboard à partir de la fonction @app.callback
@app.callback(
    Output('indicator-graphic', 'figure'),
    [Input('metric-regions', 'value'),Input('metric-list', 'value')])

def update_graph(metric_regions_name, metric_list_name):    
    d = df_santepub_dep
    data = d.loc[d['region_name'] == metric_regions_name].drop(['region_name','dep','dep_name','rea'], axis=1)
    data = data.astype({'jour':'datetime64[ns]'})
    data = data.groupby('jour',as_index=False).sum()
    data = data.sort_values(by=['jour'])
    data['dateStr'] = data['jour'].dt.strftime('%b %d, %Y')
    data = data.rename(columns={'dc': 'Décès', "rad": "Guéris", "hosp":"Hospitalisés"})
    metrics = ['Décès','Guéris','Hospitalisés']

    data = [
        go.Scatter(
            name = metrics,
            x=data.dateStr, y=data[metrics],
            mode = "lines", 
            stackgroup='one',
            line=dict(width=0.5),
            marker_color={ 'Décès':'rgb(200,30,30)', 'Hospitalisés':'rgb(100,140,240)', 'Guéris':'rgb(50,200,200)' }[metrics])
        for metrics in metric_list_name]
   
    layout = go.Layout(
        title="Evolution quotidienne des cas COVID-19",
        height=600,
        yaxis_title="Nombre de personnes",
        legend_title="Choix des métriques",
        yaxis=dict(showgrid=False),
        xaxis=dict(showgrid=False),
        hovermode = "x",
        font=dict(
            family="Arial",
            size=16),
        title_font = dict(family = 'Rockwell', size = 24),
        template = 'plotly_dark'
        )
    
    fig2 = go.Figure(data=data, layout=layout)
    return fig2



@app.callback(
    Output('indicator-graphic2', 'figure'),
    [Input('metric-regions', 'value')])

def update_graph(metric_regions_name):  
    d2 = casconf_reg
    data2 = d2.loc[d2['region_name'] == metric_regions_name]
    data2 = data2.astype({'jour':'datetime64[ns]'})

    data2 = [
        go.Scatter(
            x=data2.jour, y=data2.cas_confirmes,
            mode = "lines", fill='tozeroy')]
   
    layout2 = go.Layout(
        title="Cumul quotidien des cas confirmés COVID-19",
        height=600,
        yaxis_title="Nombre de personnes",
        legend_title="Choix des métriques",
        yaxis=dict(showgrid=False),
        xaxis=dict(showgrid=False),
        hovermode = "closest",
        font=dict(
            family="Arial",
            size=16),
        title_font = dict(family = 'Rockwell', size = 24),
        template = 'plotly_dark'
        )
    
    fig3 = go.Figure(data=data2, layout=layout2)
    return fig3

  

@app.callback(Output('test_txt', 'children'),
              [Input('metric-regions', 'value')])

def update_test_text(metric_regions_name):
    nb_test = df_santepub_dep.loc[df_santepub_dep['region_name'] == metric_regions_name]
    nb_test = nb_test['nb_test'].sum()
   
    return nb_test


   
@app.callback(Output('testpos_txt', 'children'),
              [Input('metric-regions', 'value')])

def update_testpos_text(metric_regions_name):
    nb_pos = df_santepub_dep.loc[df_santepub_dep['region_name'] == metric_regions_name]
    nb_pos = nb_pos['nb_pos'].sum()
   
    return nb_pos 

   
# lancer le dashboard
if __name__ == '__main__':
    app.run_server(debug=False)
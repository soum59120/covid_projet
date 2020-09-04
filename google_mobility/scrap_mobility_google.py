# Installer les packages
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import urllib.request
import zipfile as zp
import pandas as pd
import datetime
import requests
import time
import json
import os
import re
import ssl
ssl._create_default_https_context = ssl._create_unverified_context




# Garder les données concernant la France
# récupérer le fichier csv dans le chemin choisis et l'ouvrir
google = pd.read_csv("https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv?cachebust=204bd65a761b3b2a", low_memory=False)
# renommer les colonnes 
google.columns = google.columns.str.replace(
    r'_percent_change_from_baseline', '')
# enlever les tirets du bas des noms de colonnes
google.columns = google.columns.str.replace(r'_', ' ')
# renommer le nom de colonne 'country region' par 'country' 
google = google.rename(columns={'country region': 'country'})
# renommer le nom de colonne 'sub region 1' par 'region'
google = google.rename(columns={'sub region 1': 'region'})
# garder les colonnes d'intérêt
google = google.loc[:,
                    ['country',
                     'region',
                     'date',
                     'retail and recreation',
                     'grocery and pharmacy',
                     'parks',
                     'transit stations',
                     'workplaces',
                     'residential']]
# remplacer tous les NA par 'Total'
google['region'].fillna('Total', inplace=True)
# filtrer pour avoir les données concernant la France globalement et non par régions
google_fr = google.loc[google['country'] == 'France']
google_fr = google_fr.loc[google['region'] == 'Total']
google_fr



# données concernant le nombre de cas confirmés pour l'ensemble du pays
casconf_fr = pd.read_csv("https://www.coronavirus-statistiques.com/corostats/openstats/open_stats_coronavirus.csv?fbclid=IwAR3UIrk4TZ6B0ZrJGEvKSgo9tULZsQDiIWGMSQF1WwK8bqzUBIWHoEUht7g",sep=";")
casconf_fr = casconf_fr.loc[casconf_fr['nom'] == "france"]
casconf_fr = casconf_fr.drop(['source','code','nom','guerisons','deces'], axis = 1)
casconf_fr = casconf_fr.rename(columns={'cas': 'cas_confirmes'})
casconf_fr['date'] = pd.to_datetime(casconf_fr['date'])
casconf_fr = casconf_fr.fillna(0)

# avoir l'inverse du nombre cumulé pour les cas confirmés
casconf['cas_confirmes_nb'] = casconf['cas_confirmes'].diff().fillna(casconf.cas_confirmes)
casconf = casconf[casconf["jour"] >= "2020-02-15"]




# Obtenir le graphique des tendances de déplacements et du nombre de cas COVID-19 en France

## Créer une figure avec un seconde axe Y
fig = make_subplots(specs=[[{"secondary_y": True}]])


## Ajouter toutes les traces 
    # graphes des tendances de déplacements en fonction des différents lieux
fig.add_trace(
    go.Scatter(
        x=google_fr["date"],
        y=google_fr["retail and recreation"],
        name="commerces et loisirs"
    ), secondary_y=False,)
fig.add_trace(
    go.Scatter(
        x=google_fr["date"],
        y=google_fr["grocery and pharmacy"],
        name="alimentations et pharmacies"
    ), secondary_y=False,)
fig.add_trace(
    go.Scatter(
        x=google_fr["date"],
        y=google_fr["parks"],
        name="parcs"
    ), secondary_y=False,)
fig.add_trace(
    go.Scatter(
        x=google_fr["date"],
        y=google_fr["transit stations"],
        name="arrêts transports en commun"
    ), secondary_y=False,)
fig.add_trace(
    go.Scatter(
        x=google_fr["date"],
        y=google_fr["workplaces"],
        name="lieux de travail"
    ), secondary_y=False,)
fig.add_trace(
    go.Scatter(
        x=google_fr["date"],
        y=google_fr["residential"],
        name="lieux de résidence"
    ), secondary_y=False,)

    # graphe du nombre de nouveaux cas
fig.add_trace(
    go.Bar(
        x=casconf["jour"],
        y=casconf["cas_confirmes_nb"],
        name="nombre de nouveaux cas",
        opacity=0.5,
        marker=dict(
            color='#FFFFFF',
            line=dict(
                color='#000000'
            )
        ),
    ), secondary_y=True,)

    # choisisr un titre pour les axes et du graphique ainsi qu'un template
fig.update_layout(
    hovermode = "x",    
    template= "plotly_white",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
        ),
    shapes=[
        # 1st highlight during Feb 4 - Feb 6
        dict(
            type="rect",
           # x-reference is assigned to the x-values
            xref="x",
            # y-reference is assigned to the plot paper [0,1]
            yref="paper",
            x0="2020-03-17",
            y0=0,
            x1="2020-05-11",
            y1=1,
            fillcolor="LightSalmon",
            opacity=0.2,
            layer="below",
            line_width=0,
    z        )
        ]
    )
fig.update_yaxes(title_text="<b>tendances de déplacement dans un type lieu (en %)</b>", secondary_y=False)
fig.update_yaxes(title_text="<b>nombre de nouveaux cas</b>", secondary_y=True)


## montrer la figure
fig.show()



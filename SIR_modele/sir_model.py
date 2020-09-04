#!/usr/bin/env python
# coding: utf-8




# importer les packages
from scipy.integrate import odeint
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly
import ssl
import csv
ssl._create_default_https_context = ssl._create_unverified_context




# données concernant le nombre de cas confirmés pour l'ensemble du pays
casconf_fr = pd.read_csv("https://www.coronavirus-statistiques.com/corostats/openstats/open_stats_coronavirus.csv?fbclid=IwAR3UIrk4TZ6B0ZrJGEvKSgo9tULZsQDiIWGMSQF1WwK8bqzUBIWHoEUht7g",sep=";")
casconf_fr = casconf_fr.loc[casconf_fr['nom'] == "france"]
casconf_fr = casconf_fr.drop(['source','code','nom','guerisons','deces'], axis = 1)
casconf_fr = casconf_fr.rename(columns={'cas': 'cas_confirmes'})
casconf_fr['date'] = pd.to_datetime(casconf_fr['date'])
casconf_fr = casconf_fr.fillna(0)




# créer de nouvelles colonnes 'infected', 'recovered' et 'susceptible'
df['population'] = 67064000
df['infected'] = df['cas'].diff().fillna(df.cas) #infected = nombre de cas journalier au jour i
df['recovered'] = df['deces'] + df['guerisons'] #recovered = nombre cumulé de décès + nombre cumulé de guérisons au jour i
df['susceptible'] = df['population'] - df['cas'] - df['recovered'] #susceptible = nombre population - nombre cumulé de cas - nombre de guérisons(+décès) au jour i





# fonction de lissage pour enlever les fortes fluctuations
def lissage(Lx,Ly,p):
    '''Fonction qui débruite une courbe par une moyenne glissante
    sur 2P+1 points'''
    Lxout=[]
    Lyout=[]
    for i in range(p,len(Lx)-p):   
        Lxout.append(Lx[i])
    for i in range(p,len(Ly)-p):
        val=0
        for k in range(2*p):
            val+=Ly[i-p+k]
        Lyout.append(val/2/p)
    return Lxout,Lyout

# récupérer les données après avoir appliqué la fonction de lissage
x,y1 = lissage(df['date'], df['susceptible'],15)
x,y2 = lissage(df['date'], df['infected'],15)
y2 = [i * 2 for i in y2]
x,y3 = lissage(df['date'], df['recovered'],15)





# choix de la période = confinement (+/- 10jours)
df_conf = df.loc[(df['date'] >= "2020-03-07") & (df['date'] <= "2020-06-01")]





# ploter le résultat 
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=np.arange(len(df_conf)), # x = la durée en jours de la période choisie
    y=y1,
    name="susceptible"
))

fig.add_trace(go.Scatter(
    x=np.arange(len(df_conf)),
    y=y2,
    name="infected",
    yaxis="y2"
))

fig.add_trace(go.Scatter(
    x=np.arange(len(df_conf)),
    y=y3,
    name="recovered",
    yaxis="y3"
))

# créer les templates des axes
fig.update_layout(
    yaxis=dict(
        tickfont=dict(
            color="#0000FF"
        )
    ),
    yaxis2=dict(
        tickfont=dict(
            color="#FF0000"
        ),
        anchor="x",
        overlaying="y",
        side="left",
        position=0.001
    ),
    yaxis3=dict(
        tickfont=dict(
            color="#66CDAA"
        ),
        anchor="x",
        overlaying="y",
        side="right"
    ),
)

# mettre à jour le template du graphique global
fig.update_layout(    
    template= "plotly_white",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
        ),
    title_text="Nombre quotidien de personnes infectées, susceptibles et guéries liées au COVID-19 en France",
)

fig.show()




# définir la fonction pour la modélisation SIR
def SIR(
    total_pop, inital_infected, initial_recovered, recovery_rate, reproduction_rate, t
):
    # Nombre la population totale
    N = total_pop
    # Nombre initial de personnes guéries et infectées (I0 et R0)
    I0, R0 = inital_infected, initial_recovered
    # Taux de reproduction 
    r0 = reproduction_rate
    # S0, nombre de personnes susceptibles d'être infectées initialement
    S0 = N - I0 - R0
    # Taux de transmission/contact (beta) et le taux moyen de guérison (1/days = gamma)
    gamma = 1.0 / recovery_rate
    beta = gamma * r0

    # Les équations différentielles du modèle SIR
    def deriv(y, t, N, beta, gamma):
        S, I, R = y
        dSdt = -beta * S * I / N
        dIdt = beta * S * I / N - gamma * I
        dRdt = gamma * I
        return dSdt, dIdt, dRdt

    # Créer une grille de points représentant le temps en jour
    t = np.linspace(0, t, t)

    # Vecteur contenant les conditions initiales
    y0 = S0, I0, R0
    # Intégration des équations SIR durant la grille de temps (t)
    ret = odeint(deriv, y0, t, args=(N, beta, gamma))
    S, I, R = ret.T
    return S, I, R




# Mettre les paramètres initiaux 
total_pop = 67064000.0 
inital_infected = df_conf['infected'].iloc[0] # première valeure de personne infectée
initial_recovered = df_conf['recovered'].iloc[0] # première valeure de personne guéries
recovery_rate = 7
reproduction_rate = 3.5
t = len(df_conf)

# Modélisation et transformation en dataframe pour le plot
SIR = SIR(total_pop, inital_infected, initial_recovered, recovery_rate, reproduction_rate, t)
SIR = pd.DataFrame(data=SIR).transpose().rename(columns={0:'S',1:'I',2:'R'})




# ploter le résultat de la modélisation
fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    y=SIR['S'],
    name="susceptible"
))
fig2.add_trace(go.Scatter(
    y=SIR['I'],
    name="infected"
))
fig2.add_trace(go.Scatter(
    y=SIR['R'],
    name="recovered"
))

# Update layout properties
fig2.update_layout(    
    template= "plotly_white",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
        ),
    title_text="COVID-19 : Modèle SIR",
)

fig2.show()


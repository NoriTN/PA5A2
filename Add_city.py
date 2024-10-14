import requests
import streamlit as st
import folium as fo
from streamlit_folium import st_folium
import numpy as np
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from datetime import datetime
from dateutil.relativedelta import relativedelta

if __name__ == "__main__":
    datetoday = datetime.now()
    date_debut = datetoday - relativedelta(years=4)
    date_debut_str = date_debut.strftime("%Y-%m-%d")
    columns = ['date_mesure', 'hauteur_eau']
    source ='https://pa5a2.blob.core.windows.net/pa5a2blob/listes_stations_map_virgule.csv?sp=r&st=2024-10-12T09:26:22Z&se=2024-10-12T17:26:22Z&spr=https&sv=2022-11-02&sr=b&sig=MGLck3vVwLt8QZxxMTdjDUBWor1%2FnKXB9MP2VTYkjKw%3D'
    df = pd.read_csv(source)
    dftest = pd.DataFrame(df)
    server = 'pa5a2sqlserver.database.windows.net'
    database = 'pa5a2'
    username = 'ntn94210'
    password = 'Password97'
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    cursor = cnxn.cursor()
    for index, row in dftest.iterrows():
        cursor.execute(
            "INSERT INTO dbo.City (date_debut_mesure, code_commune_insee, nom_commune, x, y, hauteur_moyenne, hauteur_actuelle) values(?,?,?,?,?,?,?)",
            row.date_debut_mesure, row.code_commune_insee, row.nom_commune, row.x, row.y, 0, 0)
    cnxn.commit()
    cursor.close()
    cnxn.close()

    '''
    average = pd.DataFrame(columns=["code_bss", "moyenne_hauteur"])
    for i in dftest.iterrows() :
        request2 = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?code_commune=' + i[1]['code_commune_insee'] + '&date_recherche=2024-01-01&format=json&size=1'
        response2 = requests.get(request2)
        data2 = response2.json()
        if data2.get('count') != 0:
            list_releves = data2.get('data', [])
            df2 = pd.DataFrame(list_releves)
            request = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques?code_bss='+df2['code_bss'][0]+'&date_debut_mesure='+date_debut_str
            response = requests.get(request)
            if response.status_code == 200 or response.status_code == 206 :
                data = response.json()
                chroniques = data.get('data', [])
                df3 = pd.DataFrame(chroniques)
                if 'profondeur_nappe' in df3.columns and 'niveau_nappe_eau' in df3.columns:
                    df3['hauteur_eau'] = df3['niveau_nappe_eau'] - df3['profondeur_nappe']
                    moyenne_hauteur = round(df3['hauteur_eau'].mean(), 2)
                    average.loc[len(average)] = [df3['code_bss'], moyenne_hauteur]'''
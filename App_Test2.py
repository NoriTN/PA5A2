import requests
import streamlit as st
import numpy as np
import pandas as pd
import folium as fo
import pyodbc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from branca.element import Figure
from streamlit_folium import st_folium
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from datetime import datetime, date
from dateutil.relativedelta import relativedelta








# Fonction pour créer des séquences de données pour LSTM
def create_sequences(data, seq_length):
    x = []
    y = []
    for i in range(seq_length, len(data)):
        x.append(data[i-seq_length:i, 0])
        y.append(data[i, 0])
    return np.array(x), np.array(y)

# Titre de l'application
st.title("Prédiction avec LSTM")
placeholder = st.empty()

# Chargement des données depuis une textbox

server = 'pa5a2sqlserver.database.windows.net'
database = 'pa5a2'
username = 'ntn94210'
password = 'Password97'
cnxn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
cursor = cnxn.cursor()
query = "SELECT code_commune_insee, nom_commune, x, y FROM dbo.City;"
df = pd.read_sql(query, cnxn)
m = fo.Map(location=[45.866667, 2.333333], zoom_start=6)
for index, row in df.iterrows():
    popupvalue = row['nom_commune'] + " - " + str(row['code_commune_insee'])
    fo.Marker([row['y'], row['x']], popup=popupvalue, icon=fo.Icon(icon='info-sign')).add_to(m)
st_data = st_folium(m, width = 725)



st.title("Sélection d'une valeur ou choisissez dans la liste")

options = ["Faites votre choix", "Quintenic", "Saintes", "Congy", "Simacourbe"]
#Toggle_Option = '<p style = "font-family:Arial; color:Black; font-size: 17px;"> Sélectionnez une option : </p>'
selected_option = st.selectbox("Sélectionnez une option :", options)

selected_option2 = st.text_area("Entrez le code INSEE voulu")


code_commune = "0"

match selected_option :
    case "Quintenic" :
        code_commune = "22261"
    case "Saintes" :
        code_commune = "17415"
    case "Congy" :
        code_commune = "51163"
    case "Simacourbe" :
        code_commune = "64524"
    case "Faites votre choix" :
        code_commune = selected_option2

# Paramètres
sequence_length = 25 #st.slider("Taille de la séquence", min_value=10, max_value=100, value=25)
epochs = 25 #st.slider("Nombre d'époques", min_value=10, max_value=200, value=25)

col1, col2, col3 = st.columns([0.50,0.30,0.20])

if col1.button("Valider les données"):
    query = "SELECT nom_commune FROM dbo.City where code_commune_insee="+code_commune+";"
    City_Name = pd.read_sql(query, cnxn)
    st.write("Code INSEE de la commune choisie : " + code_commune)
    datetoday = date.today()
    date_debut = datetoday - relativedelta(years=4)
    date_debut_str = date_debut.strftime("%Y-%m-%d")
    columns = ['date_mesure', 'hauteur_eau']

    # On trouve la bonne station en rapport avec le code INSEE
    request2 = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?code_commune='+code_commune+'&date_recherche=2024-01-01&format=json&size=1'

    response2 = requests.get(request2)
    data2 = response2.json()
    if data2.get('count') != 0 :
        list_releves = data2.get('data', [])
        df2 = pd.DataFrame(list_releves)
        request = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques?code_bss='+df2['code_bss'][0]+'&date_debut_mesure='+date_debut_str
        response = requests.get(request)
        nb_days = 0
        values = []
        if response.status_code == 200 or response.status_code == 206:
            data = response.json()
            chroniques = data.get('data', [])
            df = pd.DataFrame(chroniques)
            if 'profondeur_nappe' in df.columns and 'niveau_nappe_eau' in df.columns:
                df['hauteur_eau'] = df['niveau_nappe_eau'] - df['profondeur_nappe']
                moyenne_hauteur = round(df['hauteur_eau'].mean(), 2)
            else:
                print("Les colonnes nécessaires ne sont pas présentes dans les données.")
            df['date_mesure'] = pd.to_datetime(df['date_mesure'])
            date_max = df['date_mesure'].max()
            value = df.loc[df['date_mesure'] == date_max, 'hauteur_eau'].values[0]
            dffiltered = df[columns]
            with st.spinner('Please wait... Calculating...'):
                while value < moyenne_hauteur*0.9 :
                    # Prétraitement : Normalisation des valeurs entre 0 et 1
                    scaler = MinMaxScaler(feature_range=(0, 1))
                    scaled_data = scaler.fit_transform(dffiltered['hauteur_eau'].values.reshape(-1, 1))

                    # Création des séquences de données
                    x_train, y_train = create_sequences(scaled_data, sequence_length)

                    # Reshape pour correspondre à l'entrée LSTM (échantillons, séquence, caractéristiques)
                    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

                    # Création du modèle LSTM
                    model = Sequential()
                    model.add(LSTM(units=150, return_sequences=True, input_shape=(x_train.shape[1], 1)))
                    model.add(LSTM(units=100))
                    model.add(Dense(units=1))  # Couche de sortie

                    # Compilation du modèle
                    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])

                    model.fit(x_train, y_train, epochs=epochs, batch_size=64, verbose=2)

                    # Prédiction sur les dernières séquences
                    last_sequence = scaled_data[-sequence_length:]
                    last_sequence = np.reshape(last_sequence, (1, sequence_length, 1))
                    predicted_value = model.predict(last_sequence)

                    # Transformation inverse pour obtenir la valeur prédite
                    predicted_value = scaler.inverse_transform(predicted_value)

                    value = predicted_value[0][0]
                    st.write("Value : " + str(value))
                    dffiltered.loc[len(dffiltered.index)] = [datetoday + relativedelta(days=nb_days), predicted_value[0][0]]
                    st.write("90% de la hauteur moyenne : " + str(moyenne_hauteur*0.90))
                    st.write(datetoday + relativedelta(days=nb_days))
                    if value < moyenne_hauteur * 0.9 :
                        nb_days = nb_days + 1
            st.success('Done!')
            dfresult = pd.DataFrame({
                "Date": [datetoday],
                "Ville": [City_Name["nom_commune"].iloc[0]],
                "Code_Insee" : [code_commune],
                "Date_Retour_Normal" : [datetoday + relativedelta(days=nb_days)],
                "Nombre_jours" : [nb_days]
            })
            cursor = cnxn.cursor()
            for index, row in dfresult.iterrows():
                cursor.execute(
                    "INSERT INTO dbo.History (Date, Ville, Code_Insee, Date_Retour_Normal, Nb_Jours, Avis) values(?,?,?,?,?,?)",
                    datetime.now(), row.Ville, row.Code_Insee, datetime.now()+relativedelta(days=nb_days), row.Nombre_jours, 0)
            cnxn.commit()
            cursor.close()
            cnxn.close()
        else:
            print(f"Erreur {response.status_code} : {response.text}")
        if nb_days > 0 :
            st.write("retour à la normale dans environ : " + str(nb_days) + " jours soit le " + str(datetoday + relativedelta(days=nb_days)) + ".")
        else :
            st.write("La nappe est déjà au bon niveau !")
    else :
        st.write("Le code INSEE rentré n'a pas de données suffisantes")


col2.write("  OU  ")
if col3.button("Afficher l'historique"):
    query = "SELECT Date, Ville, Code_Insee, Date_Retour_Normal, Nb_Jours FROM dbo.History where code_insee="+code_commune+";"
    Histo = pd.read_sql(query, cnxn)
    if len(Histo) > 1 :
        st.write(Histo)
    else :
        #Toggle_Histo = '<p style = "font-family:Arial; color:Black; font-size: 17px;"> Aucun historique à afficher. </p>'
        #st.markdown(Toggle_Histo, unsafe_allow_html=True)
        st.write("Aucun historique à afficher.")
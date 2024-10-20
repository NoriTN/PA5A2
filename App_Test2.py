import requests
import streamlit as st
import numpy as np
import pandas as pd
import folium as fo
import pyodbc
from streamlit_folium import st_folium
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, BatchNormalization
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
st.markdown("<h1 style='text-align: center; color: red;'>Variaqua</h1>", unsafe_allow_html=True)
st.markdown("<p style = 'font-family:Arial; color:Grey; font-size: 17px;'>Cliquer sur une ville pour obtenir le code INSEE</p>", unsafe_allow_html=True)
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
m = fo.Map(location=[46.866667, 2.333333], zoom_start=6)
for index, row in df.iterrows():
    popupvalue = row['nom_commune'] + " - " + str(row['code_commune_insee'])
    fo.Marker([row['y'], row['x']], popup=popupvalue, icon=fo.Icon(icon='info-sign')).add_to(m)
st_folium(m, width = 725)

query = "SELECT * FROM dbo.Settings"
settings = pd.read_sql(query, cnxn)


st.markdown("<p style = 'font-family:Arial; color:Black; font-size: 20px;'>Veuillez choisir une ville dans la liste déroulante ou saisissez un code INSEE dans le champ ci-dessous. </p>", unsafe_allow_html=True)

options = ["Faites votre choix", "Quintenic", "Saintes", "Congy", "Simacourbe"]
selected_option = st.selectbox("Sélectionnez une option :", options)

st.markdown("<h2 style='text-align: center; color: Black;'>OU</h2>", unsafe_allow_html=True)

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
sequence_length = int(settings['sequence_length'].iloc[0]) #st.slider("Taille de la séquence", min_value=10, max_value=100, value=25)
epochs = int(settings['epochs'].iloc[0]) #st.slider("Nombre d'époques", min_value=10, max_value=200, value=25)

col1, col3 = st.columns([0.75,0.25])

if col1.button("Lancement de la prédiction"):
    if code_commune != "" :
        query = "SELECT nom_commune FROM dbo.City where code_commune_insee="+code_commune+";"
        City_Name = pd.read_sql(query, cnxn)
        #st.write("Code INSEE de la commune choisie : " + code_commune)
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
                        model.add(LSTM(units=int(settings['lstm1'].iloc[0]), return_sequences=True, input_shape=(x_train.shape[1], 1)))
                        model.add(Dropout(0.2))
                        model.add(LSTM(units=int(settings['lstm2'].iloc[0])))
                        model.add(Dropout(0.2))
                        model.add(Dense(units=1))  # Couche de sortie

                        # Compilation du modèle
                        model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])

                        model.fit(x_train, y_train, epochs=epochs, batch_size=32, verbose=2)

                        # Prédiction sur les dernières séquences
                        last_sequence = scaled_data[-sequence_length:]
                        last_sequence = np.reshape(last_sequence, (1, sequence_length, 1))
                        predicted_value = model.predict(last_sequence)

                        # Transformation inverse pour obtenir la valeur prédite
                        predicted_value = scaler.inverse_transform(predicted_value)

                        value = predicted_value[0][0]
                        #st.write("Value : " + str(value))
                        dffiltered.loc[len(dffiltered.index)] = [datetoday + relativedelta(days=nb_days), predicted_value[0][0]]
                        #st.write("90% de la hauteur moyenne : " + str(moyenne_hauteur*0.90))
                        #st.write(datetoday + relativedelta(days=nb_days))
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
            else:
                print(f"Erreur {response.status_code} : {response.text}")
            if nb_days > 0 :
                st.write("retour à la normale dans environ : " + str(nb_days) + " jours soit le " + str(datetoday + relativedelta(days=nb_days)) + ".")
            else :
                st.write("La nappe est déjà au bon niveau !")
        else :
            st.write("Le code INSEE rentré n'a pas de données suffisantes")
    else :
        st.write("Veuillez renseigner un code INSEE.")

if col3.button("Afficher l'historique"):
    if code_commune != "" :
        query = "SELECT Date, Ville, Code_Insee, Date_Retour_Normal, Nb_Jours FROM dbo.History where code_insee="+code_commune+";"
        Histo = pd.read_sql(query, cnxn)
        if len(Histo) > 1 :
            st.write(Histo)
        else :
            #Toggle_Histo = '<p style = "font-family:Arial; color:Black; font-size: 17px;"> Aucun historique à afficher. </p>'
            #st.markdown(Toggle_Histo, unsafe_allow_html=True)
            st.write("Aucun historique à afficher.")
    else :
        st.write("Veuillez renseigner un code INSEE.")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
query = "SELECT Scorepos, Scoreneg, nb_vote FROM dbo.score;"
upgrade = pd.read_sql(query, cnxn)

if upgrade['nb_vote'].iloc[0] == 11 :
    if upgrade['Scorepos'].iloc[0] < upgrade['Scoreneg'].iloc[0] :
        query = "SELECT * FROM dbo.Settings"
        settings = pd.read_sql(query, cnxn)
        if settings['sequence_length'].iloc[0] < 200 :
            query = "UPDATE dbo.Settings set sequence_length = sequence_length + 10;"
            cursor.execute(query)
            cnxn.commit()
        if settings['epochs'].iloc[0] < 200 :
            query = "UPDATE dbo.Settings set epochs = epochs + 25;"
            cursor.execute(query)
            cnxn.commit()
        if settings['lstm1'].iloc[0] < 500 :
            query = "UPDATE dbo.Settings set lstm1 = lstm1 + 50;"
            cursor.execute(query)
            cnxn.commit()
        if settings['lstm2'].iloc[0] < 450 :
            query = "UPDATE dbo.Settings set lstm2 = lstm2 + 50;"
            cursor.execute(query)
            cnxn.commit()
        query = "UPDATE dbo.score set Scorepos = 1, Scoreneg=1, nb_vote=0;"
        cursor.execute(query)
        cnxn.commit()
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.text("")
st.markdown("<p style = 'font-family:Arial; color:Grey; font-size: 17px;'>Etes vous satisfait des prédictions ? Donnez nous votre avis ! </p>", unsafe_allow_html=True)
col31, col32, col33 = st.columns([0.35, 0.35, 0.3])
if col31.button("Oui"):
    query = "UPDATE dbo.score set Scorepos = Scorepos + 1, nb_vote = nb_vote +1;"
    cursor.execute(query)
    cnxn.commit()
    st.write("Le vote a bien été pris en compte.")
if col32.button("Non"):
    query = "UPDATE dbo.score set Scoreneg = Scoreneg + 1, nb_vote = nb_vote +1;"
    cursor.execute(query)
    cnxn.commit()
    st.write("Le vote a bien été pris en compte.")
if col33.button("Mon application est vraiment trop lente !") :
    query = "SELECT * FROM dbo.Settings"
    settings = pd.read_sql(query, cnxn)
    if settings['sequence_length'].iloc[0] > 25:
        query = "UPDATE dbo.Settings set sequence_length = sequence_length - 10;"
        cursor.execute(query)
        cnxn.commit()
    if settings['epochs'].iloc[0] > 25:
        query = "UPDATE dbo.Settings set epochs = epochs - 25;"
        cursor.execute(query)
        cnxn.commit()
    if settings['lstm1'].iloc[0] > 100:
        query = "UPDATE dbo.Settings set lstm1 = lstm1 - 50;"
        cursor.execute(query)
        cnxn.commit()
    if settings['lstm2'].iloc[0] > 50:
        query = "UPDATE dbo.Settings set lstm2 = lstm2 - 50;"
        cursor.execute(query)
        cnxn.commit()
    query = "UPDATE dbo.score set Scorepos = 1, Scoreneg=1, nb_vote=0;"
    cursor.execute(query)
    cnxn.commit()
    st.write("Des modifications ont été apportées.")

cursor.close()
cnxn.close()
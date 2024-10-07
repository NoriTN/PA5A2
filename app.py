import requests
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from datetime import datetime
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

# Chargement des données depuis une textbox

st.title("Sélection d'une Valeur ou choisissez dans la liste")

options = ["Bordeaux", "Rouen", "Caen", "Toulon"]

selected_option = st.selectbox("Sélectionnez une option :", options)

st.write(f"Vous avez sélectionné : {selected_option}")


code_commune = st.text_area("Entrez le code INSEE voulu")

# Paramètres
sequence_length = 25 #st.slider("Taille de la séquence (jours)", min_value=10, max_value=100, value=25)
epochs = 25 #st.slider("Nombre d'époques", min_value=10, max_value=200, value=25)

if st.button("Valider les données"):
    datetoday = datetime.now()
    date_debut = datetoday - relativedelta(years=4)
    date_debut_str = date_debut.strftime("%Y-%m-%d")
    columns = ['date_mesure', 'hauteur_eau']

    # On trouve la bonne station en rapport avec le code INSEE
    request2 = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?code_commune='+code_commune+'&date_recherche=2024-01-01&format=json&size=1'

    response2 = requests.get(request2)
    data2 = response2.json()
    list_releves = data2.get('data', [])
    df2 = pd.DataFrame(list_releves)

    request = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques?code_bss='+df2['code_bss'][0]+'&date_debut_mesure='+date_debut_str
    response = requests.get(request)
    value = 0
    nb_days = 1
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
                model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
                model.add(LSTM(units=50))
                model.add(Dense(units=1))  # Couche de sortie

                # Compilation du modèle
                model.compile(optimizer='adam', loss='mean_squared_error')

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
                nb_days = nb_days + 1
        st.success('Done!')
    else:
        print(f"Erreur {response.status_code} : {response.text}")
    st.write("retour à la normale dans environ : " + str(nb_days) + " jours.")

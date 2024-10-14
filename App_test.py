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

if __name__ == "__main__":
    request = 'https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations?fields=code_commune_insee%2Cnom_commune%2Cdate_debut_mesure%2Cx%2Cy&format=json&nb_mesures_piezo_min=3650&size=3000'

    response = requests.get(request)

    data = response.json()

    list_releves = data.get('data', [])

    df = pd.DataFrame(list_releves)

    df = df.rename(columns={"y": "LAT", "x": "LON"})

    st.title("Prédiction avec LSTM")

    st.map(df)
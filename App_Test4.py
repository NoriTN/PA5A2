import requests
import streamlit as st
import folium as fo
from streamlit_folium import st_folium
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
    datetoday = datetime.now()
    date_debut = datetoday - relativedelta(years=4)
    date_debut_str = date_debut.strftime("%Y-%m-%d")
    columns = ['date_mesure', 'hauteur_eau']
    source ='https://pa5a2.blob.core.windows.net/pa5a2blob/listes_stations_map_virgule.csv?sp=r&st=2024-10-11T14:42:06Z&se=2024-10-11T22:42:06Z&sip=37.66.176.140&spr=https&sv=2022-11-02&sr=b&sig=crv8jd4nrITMUBjZsSnnVC6d%2B7lmyFYafja1%2B5dllaE%3D'
    df = pd.read_csv(source)
    dftest = pd.DataFrame(df)
    average = pd.DataFrame()
    average2 = pd.DataFrame()
    average['value'] = [5]
    average2['value'] = [9]
    average3 = pd.concat([average, average2])
    print(average3)
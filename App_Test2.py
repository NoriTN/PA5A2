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

m = fo.Map(location=[48.866667, 2.333333], zoom_start=0)
fo.Marker([43.661048556, 4.662014313], popup="Arles", icon=fo.Icon(icon='info-sign')).add_to(m)

st_data = st_folium(m, width = 725)
import sqlite3
from sqlite3 import Error
import numpy as np
import pandas as pd
import streamlit as st
import dateutil
import datetime
from datetime import datetime as dt
from datetime import timedelta
import matplotlib.pyplot as plt
#%matplotlib inline
import seaborn as sns
from PIL import Image
from string import punctuation
import time
from pathlib import Path
import os, json, requests, pytz
from streamlit import caching 

st.set_page_config(layout="wide")

#----------Conexion con la Base de datos-----------------

@st.cache(show_spinner=False)
def get_base():
    HOST = "http://django-email-detector-dev.us-east-1.elasticbeanstalk.com/app/"
    data_login = {'username': "dashboard", 'password':"d4shb0ard123"}
    response = requests.post(HOST+'api-token-auth/',data_login)
    token = json.loads(response.content.decode('utf-8'))['token']
    headers = { 'Authorization': f'JWT {token}' }
    res = requests.get(HOST+'database/',headers=headers)
    df = pd.DataFrame.from_dict(json.loads(res.content.decode('utf-8')))
    df.created_at = pd.to_datetime(df.created_at)
    df['created_at'] = df['created_at'].dt.tz_convert('America/Argentina/Buenos_Aires')
    df = df.rename(columns={"usuario": "ID", "text": 'Texto', "result":'Resultado', "created_at":'Timestamp'})
    df['Fecha'] = df['Timestamp'].dt.date
    df['Dia_sem'] = df['Timestamp'].dt.day_name()
    df['Hora'] = df['Timestamp'].dt.hour
    df['Longitud'] = df['Texto'].str.translate(str.maketrans("", "", punctuation)).str.split().str.len()
    df = df.sort_values('Timestamp',ascending=False)
    return df

df = get_base()

#----------Template del dashboard---------------------

path = os.getcwd()
img = Image.open(os.path.join(path,"images/udesa.jpg"))
st.image(img,width=150)
st.title("Dashboard Monitoreo API clasificacion de Spam-Ham")

st.sidebar.title("Filtros y segmentación de datos")
if st.sidebar.button ("Actualizar base de datos"):
    caching.clear_cache()
    df = get_base()
    st.balloons()

size = st.sidebar.slider("Cantidad de consultas a visualizar en la tabla",1,len(df))

#---------Graficos Dashboard---------

def graficos_totales1(df):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = np.arange(0,24)
    df['Dia_sem'] = pd.Categorical(df.Dia_sem, categories=days, ordered=True)
    df_consultas = df.groupby(['Dia_sem','Hora'])['Resultado'].count()
    df_consultas = pd.DataFrame(df_consultas).reset_index()
    mapa = pd.DataFrame(np.array(np.meshgrid(days,hours)).T.reshape(-1, 2)).rename(columns={0:'Dia_sem',1:'Hora'})
    mapa['Dia_sem'] = mapa['Dia_sem'].astype(str)
    mapa['Dia_sem'] = pd.Categorical(mapa.Dia_sem, categories=days, ordered=True)
    mapa['Hora'] = mapa['Hora'].astype(int)
    df_consultas = pd.merge(left=mapa, right=df_consultas, how='left', left_on=['Dia_sem','Hora'], right_on=['Dia_sem','Hora'])
    df_consultas = df_consultas.pivot(index='Hora', columns='Dia_sem').sort_values('Hora',ascending=False)
    df_consultas.columns = df_consultas.columns.get_level_values(1)

    fig, (ax1,ax2) = plt.subplots(1,2,figsize=(15, 5))
    
    #Heatmap del total de consultas a la API
    sns.heatmap(df_consultas,ax=ax1,cmap='Blues',vmin=1)
    ax1.set_title('Resumen historico de consultas por fecha y hora',size=12)
    ax1.set_xlabel('Dia de semana')
    ax1.set_ylabel('Hora')
    ax1.tick_params(axis='x',rotation=45)

    #HSerie de tiempo de uso de la API.
    df_uso = df.groupby('Fecha')['Resultado'].count().reset_index(name="uso_diario")
    sns.lineplot(ax=ax2,x=df_uso.Fecha,y=df_uso.uso_diario,data=df_uso,palette="Blues", marker='o')
    ax2.set_title('Serie de tiempo de uso de la API',size=12)
    ax2.set_ylabel('Cantidad de consultas diarias')
    ax2.set_xlabel('Fecha')
    ax2.set_xlim(min(df_uso['Fecha']),max(df_uso['Fecha']))
    ax2.tick_params(axis='x',rotation=45)

    return fig

def graficos_totales2(df):

    fig, (ax3,ax4) = plt.subplots(1,2,figsize=(15, 5))

    #Top 10 Usuarios que hicieron consultas históricamente
    df_user = df.groupby('ID')['Resultado'].count().reset_index(name='total').nlargest(10,'total')
    sns.barplot(x=df_user.total,y=df_user.ID,order=df_user.sort_values('total',ascending=False).ID,data=df_user,orient='h',ax=ax3,color='#69d')
    ax3.set_title('Top 10 - Usuarios con mas consultas',size=12)
    ax3.set_xlabel('Total consultas realizadas')
    ax3.set_ylabel('Usuario')
    ax3.spines['right'].set_visible(False)
    ax3.spines['top'].set_visible(False)
    ax3.spines['left'].set_visible(False)
    ax3.spines['bottom'].set_visible(False)

    #Histograma de Longitud de los mails
    sns.histplot(ax=ax4, data=df, x="Longitud",hue="Resultado")#, kde=True)
    ax4.set_title('Histograma de longitud de los textos según clasificación',size=12)
    ax4.set_xlabel('Cantidad de palabras')
    ax4.set_ylabel('Cantidad de consultas')

    return fig

def graficos_seg(df_filter):
    #Graficos segmentados
    fig, (ax1, ax2) = plt.subplots(1, 2,figsize=(15, 5),sharex=False, sharey=False)
    fig.suptitle('Actividad')

    #Grafico de barras por usuario
    df_spam = df_filter.groupby(['ID','Resultado']).size().reset_index(name='qty')
    sns.barplot(ax=ax1,data=df_spam,x=df_spam.ID,y=df_spam.qty,hue=df_spam.Resultado, palette="Blues")
    ax1.set_title('Total clasificaciones por usuario')
    ax1.set_xlabel('Usuario')
    ax1.set_ylabel('Consultas')
    ax1.tick_params(axis='x',rotation=0,labelsize=8)

    #Grafico de lineas de actividad
    df_counts = df_filter.groupby(['Fecha', 'ID']).size().reset_index(name='counts')
    df_counts['cum_count'] = df_counts.groupby('ID')['counts'].cumsum()
    sns.lineplot(ax=ax2,x=df_counts.Fecha,y=df_counts.cum_count,hue=df_counts.ID,data=df_counts,palette="Blues", marker='o')
    ax2.set_title('Acumulado de consultas')
    ax2.set_xlabel('Fecha')
    ax2.set_ylabel('Consultas acumuladas')    
    ax2.tick_params(axis='x',rotation=0,labelsize=8)

    return fig

#---------Main Dashboard---------

if st.sidebar.checkbox("Busqueda avanzada"):

    st.header('Gráficos segmentados por filtros')    
    options = np.sort(df.ID.unique()).tolist()
    select = st.sidebar.multiselect('Seleccione el/los usuarios',options,default=options)
    df_filter = df[df['ID'].isin(select)]
    start_date = st.sidebar.date_input('Seleccione la fecha desde', df['Fecha'].min())
    end_date = st.sidebar.date_input('Seleccione la fecha hasta', df['Fecha'].max() + timedelta(days=1))
    mail = st.sidebar.radio("Clasificación de mails",("Todos","SPAM","HAM"))

    if start_date < end_date:
        mask = (df_filter['Fecha'] >= start_date) & (df_filter['Fecha'] <= end_date)
        dias = end_date - start_date
        st.sidebar.success('Ha seleccionado `%s` dias' % (dias.days))
        df_filter = df_filter.loc[mask]
        
        if mail != "Todos":
            df_filter = df_filter[df_filter['Resultado']==mail]
            if len(df_filter)>0:
                st.pyplot(graficos_seg(df_filter))
                #Base de datos
                df_filter = df_filter[:size]
                st.table(df_filter.astype('object'))
            else:
                st.warning('No hay resultados en la base de datos que responden a los criterios seleccionados')
        else:        
            if len(df_filter)>0:
                st.pyplot(graficos_seg(df_filter))
                #Base de datos
                df_filter = df_filter[:size]
                st.table(df_filter.astype('object'))
            else:
                st.warning('No hay resultados en la base de datos.')
    else:
        st.warning('Error: Debe seleccionar al menos un dia posterior a la fecha inicial.')
else:

    st.header("Resumen total de registros de actividad histórico")
    st.pyplot(graficos_totales1(df))
    st.pyplot(graficos_totales2(df))
    #Base de datos
    df = df[:size]
    if len(df)>0:
        st.table(df.astype('object'))
    else:
        st.warning('No hay resultados en la base de datos')

    

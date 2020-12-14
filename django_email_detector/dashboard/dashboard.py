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
import os

st.set_page_config(layout="wide")

#----------Conexion con la Base de datos-----------------

BASE_DIR = Path().absolute()

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn

@st.cache
def main():
    database = os.path.join(BASE_DIR.parent, 'db.sqlite3')

    conn = create_connection(database)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM 'app_detector_emails_historico'")
        df = cur.fetchall()
    return pd.DataFrame(df)
 

if __name__ == '__main__':
    df = main()

df = df.rename(columns={0:'ID', 1: 'Texto',2:'Resultado',3:'Timestamp',4:'Indice'})
df['Timestamp'] = pd.to_datetime(df['Timestamp'],utc=False)
df['Fecha']=pd.to_datetime(df['Timestamp']).dt.date
df['Dia_sem']=pd.to_datetime(df['Timestamp']).dt.day_name()
df['Hora']=pd.to_datetime(df['Timestamp']).dt.hour
df['Longitud'] = df['Texto'].str.translate(str.maketrans("", "", punctuation)).str.split().str.len()
df = df.sort_values('Timestamp',ascending=False)

#----------Template del dashboard---------------------

img = Image.open(os.path.join(BASE_DIR, 'udesa.jpg'))
st.image(img,width=150)
st.title("Dashboard Monitoreo API clasificacion de Spam-Ham")

st.sidebar.title("Filtros y segmentación de datos")
size = st.sidebar.slider("Cantidad de consultas a visualizar en la tabla",1,len(df))

#---------Filtro avanzado---------
if st.sidebar.checkbox("Busqueda avanzada"):
    
    options = np.sort(df.ID.unique()).tolist()
    select = st.sidebar.multiselect('Seleccione el/los usuarios',options,default=options)
    df_filter = df[df['ID'].isin(select)]

    start_date = st.sidebar.date_input('Seleccione la fecha desde', df['Fecha'].min())
    end_date = st.sidebar.date_input('Seleccione la fecha hasta', df['Fecha'].max() + timedelta(days=1))

    if start_date < end_date:
        mask = (df_filter['Fecha'] >= start_date) & (df_filter['Fecha'] <= end_date)
        dias = end_date - start_date
        st.sidebar.success('Ha seleccionado `%s` dias' % (dias.days))
    else:
        st.sidebar.error('Error: Debe seleccionar al menos un dia posterior a la fecha inicial.')

    df_filter = df_filter.loc[mask]

    mail = st.sidebar.radio("Clasificación de mails",("Todos","SPAM","HAM"))

    if mail != "Todos":
        df_filter = df_filter[df_filter['Resultado']==mail]


    st.header('Gráficos segmentados por filtros')

    #Graficos segmentados
    fig, (ax1, ax2) = plt.subplots(1, 2,figsize=(15, 5),sharex=False, sharey=False)
    fig.suptitle('Actividad')

    df_spam = df_filter.groupby(['ID','Resultado']).size().reset_index(name='qty')
    sns.barplot(ax=ax1,data=df_spam,x=df_spam.ID,y=df_spam.qty,hue=df_spam.Resultado, palette="Blues")
    # ax1.legend(loc="upper right", title="Tipo", labels=["Ham","Spam"])
    # leg = ax1.get_legend()
    # leg.legendHandles[0].set_color(sns.color_palette("Blues")[0])
    # leg.legendHandles[1].set_color(sns.color_palette("Blues")[3])
    ax1.set_title('Total clasificaciones por usuario')
    ax1.set_xlabel('Usuario')
    ax1.set_ylabel('Consultas')
    ax1.tick_params(axis='x',rotation=0,labelsize=8)

    df_counts = df_filter.groupby(['Fecha', 'ID']).size().reset_index(name='counts')
    df_counts['cum_count'] = df_counts.groupby('ID')['counts'].cumsum()
    sns.lineplot(ax=ax2,x=df_counts.Fecha,y=df_counts.cum_count,hue=df_counts.ID,data=df_counts,palette="Blues", marker='o')
    ax2.set_title('Acumulado de consultas')
    ax2.set_xlabel('Fecha')
    ax2.set_ylabel('Consultas acumuladas')    
    ax2.tick_params(axis='x',rotation=0,labelsize=8)

    st.pyplot(fig)

    st.header('Base de datos segmentada por filtros')

    #Base de datos
    df_filter = df_filter[:size]
    st.table(df_filter)

else:
    st.header("Resumen registro de actividad histórico")
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
    ax2.tick_params(axis='x',rotation=45)

    st.pyplot(fig)

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
    sns.histplot(ax=ax4, data=df, x="Longitud",hue="Resultado", kde=True)
    ax4.set_title('Histograma de longitud de los textos según clasificación',size=12)
    ax4.set_xlabel('Cantidad de palabras')
    ax4.set_ylabel('Cantidad de consultas')


    st.pyplot(fig)

    #Base de datos
    df = df[:size]
    st.table(df.astype('object'))

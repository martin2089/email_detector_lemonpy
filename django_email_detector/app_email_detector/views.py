from django.shortcuts import render

# Create your views here.

# Importo las librerias
import os
import re
import pickle
import numpy as np
import pandas as pd
import nltk
import json

from django.conf import settings
from sklearn import datasets
from rest_framework import views, status, viewsets, exceptions
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

# Importo modelos de datos
from app_email_detector.models import Emails_Historico, Quota_Info

nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from string import punctuation

#--------------------------------------------------------------

class QuotaInfo(views.APIView):
    def get(self, request):
        username = request.user.username
        for item in Quota_Info.objects.all():
            if item.usuario == username:
                cuota_disp = item.quota - item.quota_used
                cuota_used = item.quota_used
                context = {"disponible": cuota_disp, "procesados": cuota_used}
                return Response(context, status=status.HTTP_200_OK) 
        return Response(status=status.HTTP_401_UNAUTHORIZED)
        
#--------------------------------------------------------------

class Predict(views.APIView):

    def clasificador(msg,username):    
        clasificacion = []
        texto_mail = msg
        path_modelo = os.path.join(settings.MODEL_ROOT, "spam_ham_model.pkl")
        with open(path_modelo, 'rb') as file:
            clf, Xtrain, Ytrain, vector = pickle.load(file)
            stopword = set(stopwords.words('english'))
        try:
            msg = re.sub(r'http\S+', ' ', msg)                            # Eliminacion de URLs.
            msg = re.sub("\d+", " ", msg)                                 # Eliminamos de caracteres numericos.
            msg = msg.replace('\n', ' ')                                  # Eliminamos de nuevas lineas.
            msg = msg.lower()                                             # Convertimos a minuscula.
            msg = msg.translate(str.maketrans("", "", punctuation))       # Eliminamos caracteres de puntuacion
            words = ""
            lemmatizer = WordNetLemmatizer()                              # Utilizo Lemmatising.
            msg = [word for word in msg.split() if word not in stopword]  # Elimino los stopwords
            for word in msg:
                words = words + lemmatizer.lemmatize(word) + " "      
            words = vector.transform([words])
            if clf.predict(words) == 0:
                prediction = "HAM"
            else:
                prediction = "SPAM"
            Emails_Historico.objects.create(usuario = username, texto = texto_mail, result = prediction)
        except Exception as err:
            return Response(str(err), status=status.HTTP_400_BAD_REQUEST)
        return prediction
    
    def post(self, request):    
        username = request.user.username
        entro = 0
        for item in Quota_Info.objects.all():
            if item.usuario == username:
                entro = 1
                cuota_disp = item.quota - item.quota_used
                if cuota_disp <= 0:
                    context = {"status":"fail","message":"No quota left"}
                    return Response(context, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    item.quota_used = item.quota_used + 1
                    item.save()
                    prediction = Predict.clasificador(request.data["text"], username)
                    if prediction == 0:
                        context = {"result":"HAM","status":"ok"}
                    else:
                        context = {"result":"SPAM","status":"ok"}
                    return Response(context, status=status.HTTP_200_OK)
        if entro == 0:   
            return Response(status=status.HTTP_404_NOT_FOUND)

#--------------------------------------------------------------

class History(views.APIView):
    # Guardo el número y paso la lista de históricos:
    def get(self, request, num):
        #Creo un objeto de mis modelos para persistir este numero
        contador = num
        email_hist = Emails_Historico.objects.all().orderby("indice")
        context = []
        for eh in email_hist:
            if (eh.usuario == request.user.username) and contador:
                 contador = contador - 1
                 dic = {"text": eh.texto, "result": eh.result, "created_at": eh.created_at}
                 context.append(dic)
        return Response(context, status=status.HTTP_200_OK)


#--------------------------------------------------------------

class DataBase(views.APIView):
    # Guardo el número y paso la lista de históricos:
    def get(self, request):
        #Creo un objeto de mis modelos para persistir este numero
        email_hist = Emails_Historico.objects.all()
        context = []
        if (request.user.username == "dashboard"):
            for eh in email_hist:
                dic = {
                "usuario": eh.usuario,
                "text": eh.texto, 
                "result": eh.result, 
                "created_at": eh.created_at
                }
                context.append(dic)
            return Response(context, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
            
#--------------------------------------------------------------
        
@permission_classes([AllowAny])       
class QuotaRegistration(views.APIView):
    def post(self, request):
        username = request.data.get("usuario")
        quota = request.data.get("quota")
        quota_used = request.data.get("quota_used")
        status_code = status.HTTP_201_CREATED
        Quota_Info.objects.create(usuario=username, quota=quota, quota_used=quota_used)
        response = {
            'message': 'User registered  successfully',
            }
        return Response(response, status=status_code)

#--------------------------------------------------------------

@permission_classes([AllowAny])       
class QuotaUpdate(views.APIView):
    def post(self, request):
        entro = 0
        username = request.data.get("usuario")
        quota = request.data.get("quota")
        quota_used = request.data.get("quota_used")
        for item in Quota_Info.objects.all():
            if item.usuario == username:
                entro = 1
                item.quota_used = quota_used
                item.quota = quota
                item.save()
        if entro == 1:
            response = {'message': 'User registered  successfully'}
        else:
            response = {'message': 'FAILED'}
        return Response(response)

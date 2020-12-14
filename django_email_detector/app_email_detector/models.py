from django.db import models
#from django.conf import settings

# Create your models here.

class Emails_Historico(models.Model):
    indice = models.AutoField(primary_key=True,unique=True)
    usuario = models.CharField(max_length=255)
    texto = models.TextField(blank=True)
    result = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now=True)
    
class Quota_Info(models.Model):
    usuario = models.CharField(primary_key=True, max_length=255, unique=True)
    quota = models.IntegerField(default=10)
    quota_used = models.IntegerField(default=0)

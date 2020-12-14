from django.conf.urls import url, include
from django.urls import path
from app_email_detector.views import QuotaInfo, Predict, History, QuotaRegistration, QuotaUpdate, DataBase
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    url('quota_info', QuotaInfo.as_view()),
    url('process_email', Predict.as_view()),
    path('history/<int:num>', History.as_view()),
    url('api-token-auth/', obtain_jwt_token),
    url('quota_reg/', QuotaRegistration.as_view()),
    url('quota_upd/', QuotaUpdate.as_view()),
    url('database/', DataBase.as_view()),
]

from django.urls import path
from .views import serve_db_file

app_name = "utils"

urlpatterns = [
    # Route used by DatabaseStorage to serve files from the database
    path("media/<str:name>/", serve_db_file, name="serve_db_file"),
]

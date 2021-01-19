from os import name
from django.urls import path

from . import views

urlpatterns = [
	path("", views.index, name="index"),
	path("wiki/random_page", views.random_page, name="random_page"),
	path("wiki/create_page", views.create_page, name="create_page"),
	path("wiki/<str:title>", views.entry, name="entry")
]

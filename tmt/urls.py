from django.urls import path
from . import views

app_name = "tmt"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", views.home, name="home"),
    path("upload/", views.upload_deck, name="upload"),
    path("decks/<uuid:pk>/", views.deck_detail, name="deck_detail"),
    path("decks/<uuid:pk>/edit/", views.deck_edit, name="deck_edit"),
    path("decks/<uuid:pk>/delete/", views.deck_delete, name="deck_delete"),
    path("decks/<uuid:pk>/download/", views.deck_download, name="deck_download"),
    path("decks/<uuid:pk>/retry/", views.retry_job, name="retry_job"),
    path("slides/<uuid:pk>/", views.slide_detail, name="slide_detail"),
    path("slides/<uuid:pk>/image/", views.slide_image, name="slide_image"),
    path("slides/<uuid:pk>/thumb/", views.slide_image, {"thumb": True}, name="slide_thumbnail"),
    path("slides/<uuid:pk>/star/", views.toggle_star, name="toggle_star"),
    path("slides/<uuid:slide_pk>/collection/", views.collection_add, name="collection_add"),
    path("collections/", views.collections, name="collections"),
    path("collections/new/", views.collection_create, name="collection_create"),
    path("collections/<int:pk>/", views.collection_detail, name="collection_detail"),
    path("collections/<int:pk>/edit/", views.collection_edit, name="collection_edit"),
    path("collections/<int:pk>/delete/", views.collection_delete, name="collection_delete"),
    path("collections/<int:pk>/items/<int:item_pk>/note/", views.collection_item_note, name="collection_item_note"),
    path("collections/<int:pk>/items/<int:item_pk>/remove/", views.collection_remove, name="collection_remove"),
    path("me/contributions/", views.my_contributions, name="contributions"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("register/", views.register, name="register"),
]

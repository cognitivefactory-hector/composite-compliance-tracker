from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("healthz", views.healthz, name="healthz"),
    path("criteria/<str:criterion_id>/", views.criterion_detail, name="criterion_detail"),
    path("lots/<int:pk>/", views.lot_detail, name="lot_detail"),
    path("cure/<int:pk>/", views.cure_detail, name="cure_detail"),
    path("trace/", views.trace_index, name="trace_index"),
]

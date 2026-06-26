from django.urls import path
from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="auth_register"),
    path("auth/token/", views.TokenObtainPairViewExt.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", views.TokenRefreshViewExt.as_view(), name="token_refresh"),
    path("auth/token/verify/", views.TokenVerifyViewExt.as_view(), name="token_verify"),
    path("auth/profile/", views.ProfileView.as_view(), name="auth_profile"),
    path("auth/me/", views.MeView.as_view(), name="auth_me"),
    path("pets/", views.PetListCreateAPIView.as_view(), name="pet_list_create"),
    path("pets/<int:pk>/", views.PetDetailAPIView.as_view(), name="pet_detail"),
    path("pedidos/", views.PedidoListCreateAPIView.as_view(), name="pedido_list_create"),
    path("pedidos/<int:pk>/", views.PedidoDetailAPIView.as_view(), name="pedido_detail"),
    path("pedidos/<int:pk>/aprovar/", views.PedidoAprovarAPIView.as_view(), name="pedido_aprovar"),
    path("pedidos/<int:pk>/rejeitar/", views.PedidoRejeitarAPIView.as_view(), name="pedido_rejeitar"),
    path("pedidos/<int:pk>/cancelar/", views.PedidoCancelarAPIView.as_view(), name="pedido_cancelar"),
]

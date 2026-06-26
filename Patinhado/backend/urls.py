from django.urls import path
from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="auth_register"),
    path("auth/token/", views.TokenObtainPairViewExt.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", views.TokenRefreshViewExt.as_view(), name="token_refresh"),
    path("auth/token/verify/", views.TokenVerifyViewExt.as_view(), name="token_verify"),
    path("auth/me/", views.MeView.as_view(), name="auth_me"),
    path("auth/profile/", views.ProfileView.as_view(), name="auth_profile"),
    path("auth/password/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("auth/password/reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("auth/password/change/", views.PasswordChangeView.as_view(), name="password_change"),
    path("auth/account/delete/", views.DeleteAccountView.as_view(), name="delete_account"),
    path("pets/", views.PetListCreateAPIView.as_view(), name="pet_list_create"),
    path("pets/<int:pk>/", views.PetDetailAPIView.as_view(), name="pet_detail"),
    path("pedidos/", views.PedidoListCreateAPIView.as_view(), name="pedido_list_create"),
    path("pedidos/recebidos/", views.PedidosRecebidosAPIView.as_view(), name="pedido_recebidos"),
    path("pedidos/<int:pk>/", views.PedidoDetailAPIView.as_view(), name="pedido_detail"),
    path("pedidos/<int:pk>/aprovar/", views.PedidoAprovarAPIView.as_view(), name="pedido_aprovar"),
    path("pedidos/<int:pk>/rejeitar/", views.PedidoRejeitarAPIView.as_view(), name="pedido_rejeitar"),
    path("pedidos/<int:pk>/cancelar/", views.PedidoCancelarAPIView.as_view(), name="pedido_cancelar"),
]

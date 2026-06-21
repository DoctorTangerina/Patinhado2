from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Pet, PedidoAdocao

Usuario = get_user_model()


class AuthTests(TestCase):
    """Tests for authentication endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "username": "testuser",
            "password": "senha123456",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
        }

    def test_register_valid(self):
        response = self.client.post("/api/auth/register/", self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], self.user_data["username"])
        self.assertEqual(response.data["user"]["email"], self.user_data["email"])

    def test_token_obtain_valid(self):
        Usuario.objects.create_user(**self.user_data)
        response = self.client.post(
            "/api/auth/token/",
            {"username": self.user_data["username"], "password": self.user_data["password"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_refresh_valid(self):
        user = Usuario.objects.create_user(**self.user_data)
        login = self.client.post(
            "/api/auth/token/",
            {"username": self.user_data["username"], "password": self.user_data["password"]},
            format="json",
        )
        refresh_token = login.data["refresh"]
        response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_verify_valid(self):
        user = Usuario.objects.create_user(**self.user_data)
        login = self.client.post(
            "/api/auth/token/",
            {"username": self.user_data["username"], "password": self.user_data["password"]},
            format="json",
        )
        access_token = login.data["access"]
        response = self.client.post(
            "/api/auth/token/verify/", {"token": access_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    def test_profile_get_authenticated(self):
        user = Usuario.objects.create_user(**self.user_data)
        login = self.client.post(
            "/api/auth/token/",
            {"username": self.user_data["username"], "password": self.user_data["password"]},
            format="json",
        )
        access_token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user_data["username"])
        self.assertEqual(response.data["email"], self.user_data["email"])

    def test_profile_put_valid(self):
        user = Usuario.objects.create_user(**self.user_data)
        login = self.client.post(
            "/api/auth/token/",
            {"username": self.user_data["username"], "password": self.user_data["password"]},
            format="json",
        )
        access_token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        update_data = {
            "username": "updateduser",
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "telefone": "(11) 98888-8888",
            "endereco": "Rua Nova, 456",
        }
        response = self.client.put("/api/auth/profile/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], update_data["username"])
        self.assertEqual(response.data["email"], update_data["email"])
        self.assertEqual(response.data["telefone"], update_data["telefone"])
        self.assertEqual(response.data["endereco"], update_data["endereco"])

    def test_profile_patch_valid(self):
        user = Usuario.objects.create_user(**self.user_data)
        login = self.client.post(
            "/api/auth/token/",
            {"username": self.user_data["username"], "password": self.user_data["password"]},
            format="json",
        )
        access_token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        patch_data = {"telefone": "(11) 97777-7777"}
        response = self.client.patch("/api/auth/profile/", patch_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["telefone"], patch_data["telefone"])
        self.assertEqual(response.data["username"], self.user_data["username"])


class PetTests(TestCase):
    """Tests for pet endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.donor = Usuario.objects.create_user(username="donor", password="pass1234")
        self.pet_data = {"nome": "Rex", "especie": "cachorro", "raca": "Labrador", "idade": 3}

    def test_pet_list_public(self):
        Pet.objects.create(doador=self.donor, **self.pet_data)
        response = self.client.get("/api/pets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nome"], self.pet_data["nome"])

    def test_pet_create_authenticated(self):
        login = self.client.post(
            "/api/auth/token/", {"username": "donor", "password": "pass1234"}, format="json"
        )
        access_token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.post("/api/pets/", self.pet_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome"], self.pet_data["nome"])
        self.assertEqual(response.data["doador"], self.donor.id)
        self.assertFalse(response.data["adotado"])

    def test_pet_detail(self):
        pet = Pet.objects.create(doador=self.donor, **self.pet_data)
        response = self.client.get(f"/api/pets/{pet.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], self.pet_data["nome"])
        self.assertEqual(response.data["id"], pet.id)

    def test_pet_update_by_donor(self):
        pet = Pet.objects.create(doador=self.donor, **self.pet_data)
        login = self.client.post(
            "/api/auth/token/", {"username": "donor", "password": "pass1234"}, format="json"
        )
        access_token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        update_data = {
            "nome": "Rex Updated",
            "especie": "cachorro",
            "raca": "Golden Retriever",
            "idade": 4,
            "descricao": "Updated description",
        }
        response = self.client.put(f"/api/pets/{pet.id}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], update_data["nome"])
        self.assertEqual(response.data["raca"], update_data["raca"])
        self.assertEqual(response.data["idade"], update_data["idade"])

    def test_pet_partial_update_by_donor(self):
        pet = Pet.objects.create(doador=self.donor, **self.pet_data)
        login = self.client.post(
            "/api/auth/token/", {"username": "donor", "password": "pass1234"}, format="json"
        )
        access_token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        patch_data = {"idade": 5}
        response = self.client.patch(f"/api/pets/{pet.id}/", patch_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["idade"], patch_data["idade"])
        self.assertEqual(response.data["nome"], self.pet_data["nome"])

    def test_pet_delete_by_donor(self):
        pet = Pet.objects.create(doador=self.donor, **self.pet_data)
        login = self.client.post(
            "/api/auth/token/", {"username": "donor", "password": "pass1234"}, format="json"
        )
        access_token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.delete(f"/api/pets/{pet.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Pet.objects.filter(id=pet.id).exists())


class PedidoTests(TestCase):
    """Tests for adoption request endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.donor = Usuario.objects.create_user(username="donor", password="pass1234")
        self.requester = Usuario.objects.create_user(username="req", password="pass1234")
        self.pet = Pet.objects.create(nome="Rex", especie="cachorro", doador=self.donor)

    def _get_requester_token(self):
        login = self.client.post(
            "/api/auth/token/", {"username": "req", "password": "pass1234"}, format="json"
        )
        return login.data["access"]

    def _get_donor_token(self):
        login = self.client.post(
            "/api/auth/token/", {"username": "donor", "password": "pass1234"}, format="json"
        )
        return login.data["access"]

    def test_pedido_list_own(self):
        PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        PedidoAdocao.objects.create(solicitante=self.donor, animal=self.pet)
        token = self._get_requester_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/pedidos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["solicitante"], self.requester.id)

    def test_pedido_create_valid(self):
        token = self._get_requester_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        data = {"animal": self.pet.id, "mensagem": "Gostaria de adotar"}
        response = self.client.post("/api/pedidos/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["animal"], self.pet.id)
        self.assertEqual(response.data["solicitante"], self.requester.id)
        self.assertEqual(response.data["status"], "pendente")

    def test_pedido_detail_requester(self):
        pedido = PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        token = self._get_requester_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(f"/api/pedidos/{pedido.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], pedido.id)
        self.assertEqual(response.data["animal"], self.pet.id)

    def test_pedido_update_pending(self):
        pedido = PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        token = self._get_requester_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        update_data = {"animal": self.pet.id, "mensagem": "Mensagem atualizada"}
        response = self.client.put(f"/api/pedidos/{pedido.id}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mensagem"], update_data["mensagem"])

    def test_pedido_partial_update_pending(self):
        pedido = PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        token = self._get_requester_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        patch_data = {"mensagem": "Nova mensagem"}
        response = self.client.patch(f"/api/pedidos/{pedido.id}/", patch_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mensagem"], patch_data["mensagem"])

    def test_pedido_delete_requester(self):
        pedido = PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        token = self._get_requester_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.delete(f"/api/pedidos/{pedido.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PedidoAdocao.objects.filter(id=pedido.id).exists())

    def test_pedido_aprovar_by_donor(self):
        pedido = PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        token = self._get_donor_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(f"/api/pedidos/{pedido.id}/aprovar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "aprovado")
        self.pet.refresh_from_db()
        self.assertTrue(self.pet.adotado)

    def test_pedido_rejeitar_by_donor(self):
        pedido = PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        token = self._get_donor_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(f"/api/pedidos/{pedido.id}/rejeitar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "rejeitado")
        self.pet.refresh_from_db()
        self.assertFalse(self.pet.adotado)

    def test_pedido_cancelar_by_requester(self):
        pedido = PedidoAdocao.objects.create(solicitante=self.requester, animal=self.pet)
        token = self._get_requester_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(f"/api/pedidos/{pedido.id}/cancelar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelado")
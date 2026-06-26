from rest_framework import status, serializers
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view, inline_serializer,
)

from .models import Pet, PedidoAdocao, Usuario
from .permissions import IsDoadorDoPet, IsDoadorOrReadOnly, IsSolicitanteOrReadOnly
from .serializers import (
    PedidoAdocaoCreateSerializer,
    PedidoAdocaoSerializer,
    PetCreateSerializer,
    PetSerializer,
    PetUpdateSerializer,
    RegistroSerializer,
    UsuarioSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
    DeleteAccountSerializer,
)


@extend_schema_view(
    post=extend_schema(
        tags=["Autenticação"],
        summary="Obter tokens JWT",
        description="Obtém par de tokens (access + refresh) usando username e password.",
        request=TokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(
                description="Tokens obtidos com sucesso",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        },
                        response_only=True,
                    ),
                ],
            ),
            401: OpenApiResponse(description="Credenciais inválidas"),
        },
        auth=[],
    ),
)
class TokenObtainPairViewExt(TokenObtainPairView):
    pass


@extend_schema_view(
    post=extend_schema(
        tags=["Autenticação"],
        summary="Renovar access token",
        description="Renova o access token usando o refresh token.",
        request=TokenRefreshSerializer,
        responses={
            200: OpenApiResponse(
                description="Novo access token",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={"access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                        response_only=True,
                    ),
                ],
            ),
            401: OpenApiResponse(description="Refresh token inválido ou expirado"),
        },
        auth=[],
    ),
)
class TokenRefreshViewExt(TokenRefreshView):
    pass


@extend_schema_view(
    post=extend_schema(
        tags=["Autenticação"],
        summary="Verificar token JWT",
        description="Verifica se um token JWT é válido.",
        request=TokenVerifySerializer,
        responses={
            200: OpenApiResponse(
                description="Token válido",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={},
                        response_only=True,
                    ),
                ],
            ),
            401: OpenApiResponse(description="Token inválido"),
        },
        auth=[],
    ),
)
class TokenVerifyViewExt(TokenVerifyView):
    pass

@extend_schema_view(
    get=extend_schema(
        tags=["Autenticação"],
        summary="Obter dados básicos do usuário autenticado",
        description="Retorna id e nome do usuário logado com base no token JWT.",
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="MeResponse",
                    fields={
                        "id": serializers.IntegerField(),
                        "username": serializers.CharField(),
                    }
                ),
                description="Dados do usuário",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={"id": 1, "username": "João Silva"},
                        response_only=True,
                    ),
                ],
            ),
            401: OpenApiResponse(description="Não autenticado"),
        },
    ),
)
class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.get_full_name() or user.username,
        })

@extend_schema_view(
    post=extend_schema(
        tags=["Autenticação"],
        summary="Registrar novo usuário",
        description="Cria uma nova conta de usuário e retorna tokens JWT (access + refresh).",
        request=RegistroSerializer,
        responses={
            201: OpenApiResponse(
                description="Usuário criado com sucesso",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={
                            "user": {
                                "id": 1,
                                "username": "joao",
                                "first_name": "João",
                                "last_name": "Silva",
                                "email": "joao@email.com",
                                "telefone": "(11) 99999-9999",
                                "endereco": "Rua A, 123",
                                "imagem": None,
                                "date_joined": "2024-01-15T10:30:00Z",
                            },
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        },
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(description="Dados inválidos"),
        },
        auth=[],
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={
                    "username": "joao",
                    "password": "senha123456",
                    "first_name": "João",
                    "last_name": "Silva",
                    "email": "joao@email.com",
                    "telefone": "(11) 99999-9999",
                    "endereco": "Rua A, 123",
                },
                request_only=True,
            ),
        ],
    ),
)
class RegisterView(APIView):
    """Register a new user and return JWT tokens."""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UsuarioSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["Autenticação"],
        summary="Obter perfil do usuário autenticado",
        description="Retorna os dados do usuário logado.",
        responses={
            200: UsuarioSerializer,
            401: OpenApiResponse(description="Não autenticado"),
        },
    ),
    put=extend_schema(
        tags=["Autenticação"],
        summary="Atualizar perfil completo",
        description="Atualiza todos os campos do perfil do usuário autenticado.",
        request=UsuarioSerializer,
        responses={
            200: UsuarioSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={
                    "username": "joao",
                    "first_name": "João",
                    "last_name": "Silva Santos",
                    "email": "joao.novo@email.com",
                    "telefone": "(11) 98888-8888",
                    "endereco": "Rua B, 456",
                },
                request_only=True,
            ),
        ],
    ),
    patch=extend_schema(
        tags=["Autenticação"],
        summary="Atualizar perfil parcialmente",
        description="Atualiza apenas os campos enviados do perfil do usuário autenticado.",
        request=UsuarioSerializer,
        responses={
            200: UsuarioSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={"telefone": "(11) 97777-7777"},
                request_only=True,
            ),
        ],
    ),
)
class ProfileView(APIView):
    """Get or update authenticated user profile."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data,
                                       partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Pets"],
        summary="Listar pets",
        description="Retorna lista de pets com filtros opcionais.",
        parameters=[
            OpenApiParameter(
                name="especie",
                description="Filtrar por espécie (cachorro, gato, outro)",
                required=False,
                type=str,
                enum=["cachorro", "gato", "outro"],
            ),
            OpenApiParameter(
                name="adotado",
                description="Filtrar por status de adoção (true/false)",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="doador",
                description="Filtrar por ID do doador",
                required=False,
                type=int,
            ),
        ],
        responses={
            200: PetSerializer(many=True),
        },
        auth=[],
        examples=[
            OpenApiExample(
                "Resposta Exemplo",
                value=[{
                    "id": 1,
                    "nome": "Rex",
                    "especie": "cachorro",
                    "raca": "Labrador",
                    "idade": 3,
                    "descricao": "Cachorro amigável e brincalhão",
                    "doador": 1,
                    "doador_nome": "João Silva",
                    "adotado": False,
                    "adotante": None,
                    "adotante_nome": None,
                    "data_chegada": "2024-01-10T14:30:00Z",
                    "data_adocao": None,
                    "foto": None,
                    "foto_url": "https://example.com/foto.jpg",
                    "disponivel": True,
                }],
                response_only=True,
            ),
        ],
    ),
    post=extend_schema(
        tags=["Pets"],
        summary="Criar novo pet",
        description="Cria um novo pet para adoção. Requer autenticação. Aceita upload de imagem (foto) ou URL externa (foto_url).",
        request=PetCreateSerializer,
        responses={
            201: PetSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição (JSON)",
                value={
                    "nome": "Rex",
                    "especie": "cachorro",
                    "raca": "Labrador",
                    "idade": 3,
                    "descricao": "Cachorro amigável e brincalhão",
                    "foto_url": "https://example.com/foto.jpg",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Resposta Sucesso",
                value={
                    "id": 1,
                    "nome": "Rex",
                    "especie": "cachorro",
                    "raca": "Labrador",
                    "idade": 3,
                    "descricao": "Cachorro amigável e brincalhão",
                    "doador": 1,
                    "doador_nome": "João Silva",
                    "adotado": False,
                    "adotante": None,
                    "adotante_nome": None,
                    "data_chegada": "2024-01-10T14:30:00Z",
                    "data_adocao": None,
                    "foto": None,
                    "foto_url": "https://example.com/foto.jpg",
                    "disponivel": True,
                },
                response_only=True,
            ),
        ],
    ),
)
class PetListCreateAPIView(APIView):
    """List all pets or create a new pet."""
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_permissions(self):
        if self.request.method == "POST":
            return (IsAuthenticated(),)
        return (AllowAny(),)

    def get(self, request):
        queryset = Pet.objects.all()
        especie = request.query_params.get("especie")
        if especie:
            queryset = queryset.filter(especie=especie)
        adotado = request.query_params.get("adotado")
        if adotado is not None:
            adotado_bool = adotado.lower() in ("true", "1", "yes")
            queryset = queryset.filter(adotado=adotado_bool)
        doador = request.query_params.get("doador")
        if doador:
            queryset = queryset.filter(doador_id=doador)
        serializer = PetSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PetCreateSerializer(data=request.data,
                                         context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        pet = serializer.save()
        out = PetSerializer(pet)
        return Response(out.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["Pets"],
        summary="Obter detalhes de um pet",
        description="Retorna os detalhes completos de um pet específico.",
        responses={
            200: PetSerializer,
            404: OpenApiResponse(description="Pet não encontrado"),
        },
        auth=[],
    ),
    put=extend_schema(
        tags=["Pets"],
        summary="Atualizar pet completamente",
        description="Atualiza todos os campos de um pet. Apenas o doador pode atualizar.",
        request=PetUpdateSerializer,
        responses={
            200: PetSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o doador do pet"),
            404: OpenApiResponse(description="Pet não encontrado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={
                    "nome": "Rex",
                    "especie": "cachorro",
                    "raca": "Labrador",
                    "idade": 4,
                    "descricao": "Cachorro amigável, brincalhão e vacinado",
                    "foto_url": "https://example.com/foto_nova.jpg",
                    "adotado": False,
                },
                request_only=True,
            ),
        ],
    ),
    patch=extend_schema(
        tags=["Pets"],
        summary="Atualizar pet parcialmente",
        description="Atualiza apenas os campos enviados de um pet. Apenas o doador pode atualizar.",
        request=PetUpdateSerializer,
        responses={
            200: PetSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o doador do pet"),
            404: OpenApiResponse(description="Pet não encontrado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={"idade": 4, "adotado": False},
                request_only=True,
            ),
        ],
    ),
    delete=extend_schema(
        tags=["Pets"],
        summary="Excluir pet",
        description="Remove um pet do sistema. Apenas o doador pode excluir.",
        responses={
            204: OpenApiResponse(description="Pet excluído com sucesso"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o doador do pet"),
            404: OpenApiResponse(description="Pet não encontrado"),
        },
    ),
)
class PetDetailAPIView(APIView):
    """Retrieve, update, or delete a specific pet."""
    permission_classes = (IsDoadorOrReadOnly,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Pet, pk=pk)

    def get(self, request, pk):
        pet = self.get_object(pk)
        self.check_object_permissions(request, pet)
        serializer = PetSerializer(pet)
        return Response(serializer.data)

    def put(self, request, pk):
        pet = self.get_object(pk)
        self.check_object_permissions(request, pet)
        serializer = PetUpdateSerializer(pet, data=request.data,
                                         context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        out = PetSerializer(pet)
        return Response(out.data)

    def patch(self, request, pk):
        pet = self.get_object(pk)
        self.check_object_permissions(request, pet)
        serializer = PetUpdateSerializer(pet, data=request.data,
                                         partial=True,
                                         context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        out = PetSerializer(pet)
        return Response(out.data)

    def delete(self, request, pk):
        pet = self.get_object(pk)
        self.check_object_permissions(request, pet)
        pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Listar pedidos de adoção do usuário",
        description="Retorna os pedidos de adoção feitos pelo usuário autenticado, com filtros opcionais.",
        parameters=[
            OpenApiParameter(
                name="animal",
                description="Filtrar por ID do animal",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="status",
                description="Filtrar por status (pendente, aprovado, rejeitado, cancelado)",
                required=False,
                type=str,
                enum=["pendente", "aprovado", "rejeitado", "cancelado"],
            ),
        ],
        responses={
            200: PedidoAdocaoSerializer(many=True),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Resposta Exemplo",
                value=[{
                    "id": 1,
                    "solicitante": 2,
                    "solicitante_nome": "Maria Santos",
                    "animal": 1,
                    "animal_nome": "Rex",
                    "mensagem": "Gostaria de adotar o Rex",
                    "status": "pendente",
                    "data_pedido": "2024-01-12T09:15:00Z",
                    "data_resposta": None,
                }],
                response_only=True,
            ),
        ],
    ),
    post=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Criar pedido de adoção",
        description="Cria um novo pedido de adoção para um pet disponível. Requer autenticação.",
        request=PedidoAdocaoCreateSerializer,
        responses={
            201: PedidoAdocaoSerializer,
            400: OpenApiResponse(description="Dados inválidos ou animal já adotado"),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={
                    "animal": 1,
                    "mensagem": "Gostaria de adotar o Rex, tenho experiência com cães.",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Resposta Sucesso",
                value={
                    "id": 1,
                    "solicitante": 2,
                    "solicitante_nome": "Maria Santos",
                    "animal": 1,
                    "animal_nome": "Rex",
                    "mensagem": "Gostaria de adotar o Rex, tenho experiência com cães.",
                    "status": "pendente",
                    "data_pedido": "2024-01-12T09:15:00Z",
                    "data_resposta": None,
                },
                response_only=True,
            ),
        ],
    ),
)
class PedidoListCreateAPIView(APIView):
    """List user's adoption requests or create a new request."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = PedidoAdocao.objects.filter(solicitante=request.user)
        animal = request.query_params.get("animal")
        if animal:
            queryset = queryset.filter(animal_id=animal)
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        serializer = PedidoAdocaoSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PedidoAdocaoCreateSerializer(
            data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        pedido = serializer.save()
        out = PedidoAdocaoSerializer(pedido)
        return Response(out.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Obter detalhes de um pedido de adoção",
        description="Retorna os detalhes completos de um pedido de adoção específico.",
        responses={
            200: PedidoAdocaoSerializer,
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o solicitante do pedido"),
            404: OpenApiResponse(description="Pedido não encontrado"),
        },
    ),
    put=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Atualizar pedido de adoção completamente",
        description="Atualiza todos os campos de um pedido (animal, mensagem). Apenas o solicitante pode atualizar e apenas se status for 'pendente'.",
        request=PedidoAdocaoCreateSerializer,
        responses={
            200: PedidoAdocaoSerializer,
            400: OpenApiResponse(description="Dados inválidos ou pedido não está pendente"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o solicitante do pedido"),
            404: OpenApiResponse(description="Pedido não encontrado"),
        },
    ),
    patch=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Atualizar pedido de adoção parcialmente",
        description="Atualiza apenas os campos enviados de um pedido. Apenas o solicitante pode atualizar e apenas se status for 'pendente'.",
        request=PedidoAdocaoCreateSerializer,
        responses={
            200: PedidoAdocaoSerializer,
            400: OpenApiResponse(description="Dados inválidos ou pedido não está pendente"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o solicitante do pedido"),
            404: OpenApiResponse(description="Pedido não encontrado"),
        },
    ),
    delete=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Excluir pedido de adoção",
        description="Remove um pedido de adoção. Apenas o solicitante pode excluir.",
        responses={
            204: OpenApiResponse(description="Pedido excluído com sucesso"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o solicitante do pedido"),
            404: OpenApiResponse(description="Pedido não encontrado"),
        },
    ),
)
class PedidoDetailAPIView(APIView):
    """Retrieve, update, or delete a specific adoption request."""
    permission_classes = (IsSolicitanteOrReadOnly,)

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(PedidoAdocao, pk=pk)

    def get(self, request, pk):
        pedido = self.get_object(pk)
        self.check_object_permissions(request, pedido)
        serializer = PedidoAdocaoSerializer(pedido)
        return Response(serializer.data)

    def put(self, request, pk):
        pedido = self.get_object(pk)
        self.check_object_permissions(request, pedido)
        serializer = PedidoAdocaoCreateSerializer(
            pedido, data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        out = PedidoAdocaoSerializer(pedido)
        return Response(out.data)

    def patch(self, request, pk):
        pedido = self.get_object(pk)
        self.check_object_permissions(request, pedido)
        serializer = PedidoAdocaoCreateSerializer(
            pedido, data=request.data, partial=True,
            context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        out = PedidoAdocaoSerializer(pedido)
        return Response(out.data)

    def delete(self, request, pk):
        pedido = self.get_object(pk)
        self.check_object_permissions(request, pedido)
        pedido.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Aprovar pedido de adoção",
        description="Aprova um pedido de adoção pendente. Apenas o doador do pet pode aprovar. O pet será marcado como adotado.",
        responses={
            200: PedidoAdocaoSerializer,
            400: OpenApiResponse(description="Animal já adotado ou erro de validação"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o doador do pet"),
            404: OpenApiResponse(description="Pedido não encontrado"),
        },
        examples=[
            OpenApiExample(
                "Resposta Sucesso",
                value={
                    "id": 1,
                    "solicitante": 2,
                    "solicitante_nome": "Maria Santos",
                    "animal": 1,
                    "animal_nome": "Rex",
                    "mensagem": "Gostaria de adotar o Rex",
                    "status": "aprovado",
                    "data_pedido": "2024-01-12T09:15:00Z",
                    "data_resposta": "2024-01-13T10:00:00Z",
                },
                response_only=True,
            ),
        ],
    ),
)
class PedidoAprovarAPIView(APIView):
    """Approve an adoption request (donor only)."""
    permission_classes = (IsAuthenticated, IsDoadorDoPet)
    serializer_class = PedidoAdocaoSerializer

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(PedidoAdocao, pk=pk)

    def post(self, request, pk):
        pedido = self.get_object(pk)
        self.check_object_permissions(request, pedido)
        try:
            pedido.aprovar()
        except Exception as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = PedidoAdocaoSerializer(pedido)
        return Response(serializer.data)


@extend_schema_view(
    post=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Rejeitar pedido de adoção",
        description="Rejeita um pedido de adoção pendente. Apenas o doador do pet pode rejeitar.",
        responses={
            200: PedidoAdocaoSerializer,
            400: OpenApiResponse(description="Erro de validação"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o doador do pet"),
            404: OpenApiResponse(description="Pedido não encontrado"),
        },
        examples=[
            OpenApiExample(
                "Resposta Sucesso",
                value={
                    "id": 1,
                    "solicitante": 2,
                    "solicitante_nome": "Maria Santos",
                    "animal": 1,
                    "animal_nome": "Rex",
                    "mensagem": "Gostaria de adotar o Rex",
                    "status": "rejeitado",
                    "data_pedido": "2024-01-12T09:15:00Z",
                    "data_resposta": "2024-01-13T10:00:00Z",
                },
                response_only=True,
            ),
        ],
    ),
)
class PedidoRejeitarAPIView(APIView):
    """Reject an adoption request (donor only)."""
    permission_classes = (IsAuthenticated, IsDoadorDoPet)
    serializer_class = PedidoAdocaoSerializer

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(PedidoAdocao, pk=pk)

    def post(self, request, pk):
        pedido = self.get_object(pk)
        self.check_object_permissions(request, pedido)
        try:
            pedido.rejeitar()
        except Exception as e:
            return Response({"detail": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = PedidoAdocaoSerializer(pedido)
        return Response(serializer.data)


@extend_schema_view(
    post=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Cancelar pedido de adoção",
        description="Cancela um pedido de adoção pendente. Apenas o solicitante pode cancelar e apenas se o status for 'pendente'.",
        responses={
            200: PedidoAdocaoSerializer,
            400: OpenApiResponse(description="Só é possível cancelar pedidos pendentes"),
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenApiResponse(description="Não é o solicitante do pedido"),
            404: OpenApiResponse(description="Pedido não encontrado"),
        },
        examples=[
            OpenApiExample(
                "Resposta Sucesso",
                value={
                    "id": 1,
                    "solicitante": 2,
                    "solicitante_nome": "Maria Santos",
                    "animal": 1,
                    "animal_nome": "Rex",
                    "mensagem": "Gostaria de adotar o Rex",
                    "status": "cancelado",
                    "data_pedido": "2024-01-12T09:15:00Z",
                    "data_resposta": "2024-01-13T10:00:00Z",
                },
                response_only=True,
            ),
        ],
    ),
)
class PedidoCancelarAPIView(APIView):
    """Cancel an adoption request (requester only, pending only)."""
    permission_classes = (IsAuthenticated, IsSolicitanteOrReadOnly)
    serializer_class = PedidoAdocaoSerializer

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(PedidoAdocao, pk=pk)

    def post(self, request, pk):
        pedido = self.get_object(pk)
        self.check_object_permissions(request, pedido)
        if pedido.status not in ("pendente",):
            return Response(
                {"detail": "Só é possível cancelar pedidos pendentes."},
                status=status.HTTP_400_BAD_REQUEST)
        pedido.status = PedidoAdocao.Status.CANCELADO
        pedido.save()
        serializer = PedidoAdocaoSerializer(pedido)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Pedidos de Adoção"],
        summary="Pedidos dos pets do usuário autenticado",
        description="Retorna todos os pedidos de adoção feitos para os pets que o usuário doou. Permite filtrar por status.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Filtrar por status (pendente, aprovado, rejeitado, cancelado)",
                required=False,
                type=str,
                enum=["pendente", "aprovado", "rejeitado", "cancelado"],
            ),
        ],
        responses={
            200: PedidoAdocaoSerializer(many=True),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Resposta Exemplo",
                value=[{
                    "id": 1,
                    "solicitante": 2,
                    "solicitante_nome": "Maria Santos",
                    "animal": 1,
                    "animal_nome": "Rex",
                    "mensagem": "Gostaria de adotar o Rex",
                    "status": "pendente",
                    "data_pedido": "2024-01-12T09:15:00Z",
                    "data_resposta": None,
                }],
                response_only=True,
            ),
        ],
    ),
)
class PedidosRecebidosAPIView(APIView):
    """List adoption requests received for the authenticated user's pets."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = PedidoAdocao.objects.filter(animal__doador=request.user)
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        serializer = PedidoAdocaoSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    post=extend_schema(
        tags=["Autenticação"],
        summary="Solicitar recuperação de senha",
        description="Envia e-mail com link para redefinição de senha. O link contém uid e token que devem ser usados no endpoint de confirmação.",
        request=PasswordResetSerializer,
        responses={
            200: OpenApiResponse(
                description="E-mail enviado (verifique console do servidor)",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={"detail": "Se o e-mail existir, um link de recuperação será enviado."},
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(description="E-mail inválido"),
        },
        auth=[],
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={"email": "joao@email.com"},
                request_only=True,
            ),
        ],
    ),
)
class PasswordResetView(APIView):
    """Request password reset email."""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        user = Usuario.objects.get(email__iexact=email, is_active=True)

        token_generator = PasswordResetTokenGenerator()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        reset_link = "http://localhost:3000/accounts/password_reset_confirm.html?uid=" + uid + "&token=" + token
        if settings.DEBUG:
            print(f"\n🔑 RESET LINK:\n{reset_link}\n")

        html = f"""
        <html>
        <body style="margin:0;padding:40px;background:#f5f5f5;font-family:sans-serif;">
          <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;">

            <h2 style="margin-top:0;color:#111;">Redefinição de senha</h2>

            <p style="color:#444;">
              Você solicitou a redefinição da sua senha. 
              Clique no botão abaixo para continuar:
            </p>

            <a href="{reset_link}" style="
              display:inline-block;
              margin:8px 0 24px;
              padding:12px 28px;
              background:#1a73e8;
              color:#fff;
              border-radius:6px;
              text-decoration:none;
              font-weight:bold;
              font-size:15px;
            ">Redefinir senha</a>

            <p style="color:#999;font-size:12px;margin:0;">
              Se você não solicitou isso, ignore este email. 
              O link expira em 24 horas.
            </p>

          </div>
        </body>
        </html>
        """

        msg = EmailMultiAlternatives(
            subject="Redefinição de senha",
            body=f"Acesse o link para redefinir sua senha:\n{reset_link}",  # fallback plain text
            from_email="noreply@seusite.com",
            to=[user.email],
        )
        msg.attach_alternative(html, "text/html")
        msg.send()

        return Response(
            {"detail": "Se o e-mail existir, um link de recuperação será enviado."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Autenticação"],
        summary="Confirmar recuperação de senha",
        description="Redefine a senha usando o uid e token recebidos por e-mail.",
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(
                description="Senha alterada com sucesso",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={"detail": "Senha alterada com sucesso."},
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(description="UID ou token inválido, ou senhas não conferem"),
        },
        auth=[],
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={
                    "uid": "MQ",
                    "token": "abc123...",
                    "new_password": "novaSenha123",
                    "confirm_password": "novaSenha123",
                },
                request_only=True,
            ),
        ],
    ),
)
class PasswordResetConfirmView(APIView):
    """Confirm password reset with token."""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"detail": "Senha alterada com sucesso."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Autenticação"],
        summary="Alterar senha",
        description="Altera a senha do usuário autenticado. Requer senha atual.",
        request=PasswordChangeSerializer,
        responses={
            200: OpenApiResponse(
                description="Senha alterada com sucesso",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={"detail": "Senha alterada com sucesso."},
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(description="Senha atual incorreta ou novas senhas não conferem"),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={
                    "old_password": "senhaAntiga123",
                    "new_password": "novaSenha123",
                    "new_password2": "novaSenha123",
                },
                request_only=True,
            ),
        ],
    ),
)
class PasswordChangeView(APIView):
    """Change password for authenticated user."""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"detail": "Senha alterada com sucesso."},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    delete=extend_schema(
        tags=["Autenticação"],
        summary="Excluir conta (soft delete)",
        description="Desativa a conta do usuário autenticado (soft delete). Requer senha para confirmação.",
        request=DeleteAccountSerializer,
        responses={
            200: OpenApiResponse(
                description="Conta desativada com sucesso",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={"detail": "Conta desativada com sucesso."},
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(description="Senha incorreta"),
            401: OpenApiResponse(description="Não autenticado"),
        },
        examples=[
            OpenApiExample(
                "Exemplo de Requisição",
                value={"password": "minhaSenha123"},
                request_only=True,
            ),
        ],
    ),
)
class DeleteAccountView(APIView):
    """Soft delete authenticated user's account."""
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])

        return Response(
            {"detail": "Conta desativada com sucesso."},
            status=status.HTTP_200_OK,
        )

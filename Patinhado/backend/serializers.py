from rest_framework import serializers
from drf_spectacular.utils import OpenApiExample, extend_schema_field, extend_schema_serializer

from .models import Usuario, Pet, PedidoAdocao


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Exemplo de Cadastro",
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
        OpenApiExample(
            "Resposta com Tokens",
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
)
class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ("username", "password", "first_name", "last_name",
                  "email", "telefone", "endereco")

    def create(self, validated_data):
        user = Usuario(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Perfil do Usuário",
            value={
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
            response_only=True,
        ),
    ],
)
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ("id", "username", "first_name", "last_name", "email",
                  "telefone", "endereco", "imagem", "date_joined")
        read_only_fields = ("id", "date_joined")


class PetSerializer(serializers.ModelSerializer):
    doador_nome = serializers.SerializerMethodField()
    adotante_nome = serializers.SerializerMethodField()
    disponivel = serializers.BooleanField(source="disponivel_para_adocao", read_only=True)
    foto = serializers.ImageField(allow_null=True, required=False)
    foto_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = Pet
        fields = ("id", "nome", "especie", "raca", "idade", "descricao",
                  "doador", "doador_nome", "adotado", "adotante",
                  "adotante_nome", "data_chegada", "data_adocao", "foto",
                  "foto_url", "disponivel")
        read_only_fields = ("id", "doador_nome", "adotante_nome",
                            "disponivel", "data_chegada", "data_adocao")

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_doador_nome(self, obj):
        return obj.doador.get_full_name() or obj.doador.username

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_adotante_nome(self, obj):
        if obj.adotante:
            return obj.adotante.get_full_name() or obj.adotante.username


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Criar Pet com URL de Foto",
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
            "Criar Pet com Upload de Arquivo",
            value={
                "nome": "Mimi",
                "especie": "gato",
                "raca": "Siamês",
                "idade": 2,
                "descricao": "Gata carinhosa e quieta",
            },
            request_only=True,
        ),
    ],
)
class PetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = ("nome", "especie", "raca", "idade", "descricao",
                  "foto", "foto_url")

    def create(self, validated_data):
        validated_data["doador"] = self.context["request"].user
        return super().create(validated_data)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Atualização Parcial",
            value={
                "idade": 4,
                "descricao": "Cachorro amigável, brincalhão e vacinado",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Marcar como Adotado (apenas doador)",
            value={"adotado": True},
            request_only=True,
        ),
    ],
)
class PetUpdateSerializer(PetCreateSerializer):
    class Meta(PetCreateSerializer.Meta):
        fields = PetCreateSerializer.Meta.fields + ("adotado",)


class PedidoAdocaoSerializer(serializers.ModelSerializer):
    solicitante_nome = serializers.SerializerMethodField()
    animal_nome = serializers.SerializerMethodField()

    class Meta:
        model = PedidoAdocao
        fields = ("id", "solicitante", "solicitante_nome", "animal",
                  "animal_nome", "mensagem", "status", "data_pedido",
                  "data_resposta")
        read_only_fields = ("id", "solicitante_nome", "animal_nome",
                            "status", "data_pedido", "data_resposta")

    @extend_schema_field(serializers.CharField())
    def get_solicitante_nome(self, obj):
        return obj.solicitante.get_full_name() or obj.solicitante.username

    @extend_schema_field(serializers.CharField())
    def get_animal_nome(self, obj):
        return obj.animal.nome


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Criar Pedido de Adoção",
            value={
                "animal": 1,
                "mensagem": "Gostaria de adotar o Rex, tenho experiência com cães e espaço adequado.",
            },
            request_only=True,
        ),
    ],
)
class PedidoAdocaoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PedidoAdocao
        fields = ("animal", "mensagem")

    def validate_animal(self, animal):
        if animal.adotado:
            raise serializers.ValidationError(
                "Este animal já foi adotado.")
        return animal

    def create(self, validated_data):
        validated_data["solicitante"] = self.context["request"].user
        return super().create(validated_data)

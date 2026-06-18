from rest_framework import serializers
from .models import Usuario, Pet, PedidoAdocao


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

    def get_doador_nome(self, obj):
        return obj.doador.get_full_name() or obj.doador.username

    def get_adotante_nome(self, obj):
        if obj.adotante:
            return obj.adotante.get_full_name() or obj.adotante.username


class PetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = ("nome", "especie", "raca", "idade", "descricao",
                  "foto", "foto_url")

    def create(self, validated_data):
        validated_data["doador"] = self.context["request"].user
        return super().create(validated_data)


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

    def get_solicitante_nome(self, obj):
        return obj.solicitante.get_full_name() or obj.solicitante.username

    def get_animal_nome(self, obj):
        return obj.animal.nome


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

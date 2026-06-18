from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
)


class RegisterView(APIView):
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


class ProfileView(APIView):
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


class PetListCreateAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

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


class PetDetailAPIView(APIView):
    permission_classes = (IsDoadorOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser)

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


class PedidoListCreateAPIView(APIView):
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


class PedidoDetailAPIView(APIView):
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


class PedidoAprovarAPIView(APIView):
    permission_classes = (IsAuthenticated, IsDoadorDoPet)

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


class PedidoRejeitarAPIView(APIView):
    permission_classes = (IsAuthenticated, IsDoadorDoPet)

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


class PedidoCancelarAPIView(APIView):
    permission_classes = (IsAuthenticated, IsSolicitanteOrReadOnly)

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

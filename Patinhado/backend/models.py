from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.TextField(blank=True)
    imagem = models.ImageField(upload_to="usuarios/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.password:
            self.password = '!'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["first_name"]
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username


class Pet(models.Model):
    class Especie(models.TextChoices):
        CACHORRO = "cachorro", "Cachorro"
        GATO = "gato", "Gato"
        OUTRO = "outro", "Outro"

    nome = models.CharField(max_length=100)
    especie = models.CharField(max_length=20, choices=Especie.choices, default=Especie.CACHORRO)
    raca = models.CharField(max_length=100, blank=True)
    idade = models.PositiveIntegerField(blank=True, null=True, help_text="Idade em anos")
    descricao = models.TextField(blank=True)
    doador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="animais_doacao",
        help_text="Usuário que doou o animal.",
    )
    adotado = models.BooleanField(default=False, help_text="Quando verdadeiro, o pet já foi adotado e não está mais disponível para adoção.")
    adotante = models.ForeignKey(
        Usuario,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="pets_adotados",
    )
    data_chegada = models.DateTimeField(auto_now_add=True)
    data_adocao = models.DateTimeField(blank=True, null=True)
    foto = models.ImageField(upload_to='pets/%Y/%m/%d/', blank=True, null=True)
    foto_url = models.URLField(blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Pet"
        verbose_name_plural = "Pets"

    def clean(self):
        if self.adotado and not self.adotante:
            raise ValidationError("Um pet adotado deve ter um adotante associado.")
        if not self.adotado and self.adotante:
            raise ValidationError("Um pet disponível não pode ter adotante definido.")
        if self.adotado and not self.data_adocao:
            self.data_adocao = timezone.now()

    def save(self, *args, **kwargs):
        self.clean()
        if not self.adotado:
            self.adotante = None
            self.data_adocao = None
        super().save(*args, **kwargs)

    def marcar_adotado(self, adotante: Usuario):
        self.adotado = True
        self.adotante = adotante
        self.data_adocao = timezone.now()
        self.save()

    @property
    def disponivel_para_adocao(self):
        return not self.adotado

    def __str__(self):
        status = "Disponível" if not self.adotado else "Adotado"
        return f"{self.nome} ({self.get_especie_display()}) - {status}"


class PedidoAdocao(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADO = "aprovado", "Aprovado"
        REJEITADO = "rejeitado", "Rejeitado"
        CANCELADO = "cancelado", "Cancelado"

    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="pedidos_adocao",
    )
    animal = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name="pedidos_adocao",
    )
    mensagem = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    data_pedido = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-data_pedido"]
        verbose_name = "Pedido de adoção"
        verbose_name_plural = "Pedidos de adoção"
        constraints = [
            models.UniqueConstraint(fields=["solicitante", "animal"], name="unique_pedido_adocao")
        ]

    def clean(self):
        if not self.animal_id:
            return
        if self.status == self.Status.PENDENTE and self.animal.adotado:
            raise ValidationError("Não é possível criar um pedido pendente para um animal já adotado.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.status != self.Status.PENDENTE and not self.data_resposta:
            self.data_resposta = timezone.now()
        super().save(*args, **kwargs)

    def aprovar(self):
        if self.animal.adotado:
            raise ValidationError("Este animal já foi adotado.")
        self.status = self.Status.APROVADO
        self.data_resposta = timezone.now()
        self.save(update_fields=['status', 'data_resposta'])
        self.animal.marcar_adotado(self.solicitante)

    def rejeitar(self):
        self.status = self.Status.REJEITADO
        self.data_resposta = timezone.now()
        self.save()

    def __str__(self):
        return f"Pedido de adoção de {self.animal.nome} por {self.solicitante.nome} - {self.get_status_display()}"
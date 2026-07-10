from django.db import models


class ConjuntoGraficas(models.Model):
    """
    Representa un conjunto de gráficas: cada vez que el usuario sube un
    Excel, elige un nombre para agrupar esos datos y sus gráficas.
    """
    nombre = models.CharField(max_length=200)
    archivo_original = models.CharField(max_length=255, blank=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_carga']
        verbose_name = 'Conjunto de gráficas'
        verbose_name_plural = 'Conjuntos de gráficas'

    def __str__(self):
        return self.nombre

    @property
    def total_registros(self):
        return self.registros.count()


TIPO_ENERGIA_CHOICES = [
    ('Activa', 'Activa'),
    ('Reactiva', 'Reactiva'),
    ('Capacitiva', 'Capacitiva'),
    ('Penalizada', 'Penalizada'),
    ('Factor', 'Factor'),
]


class RegistroEnergia(models.Model):
    """
    Una fila del Excel: una fecha + un tipo de energía + sus 24 horas + total.
    """
    conjunto = models.ForeignKey(
        ConjuntoGraficas, related_name='registros', on_delete=models.CASCADE
    )
    fecha = models.DateField()
    id_cliente = models.CharField(max_length=50)
    tipo_energia = models.CharField(max_length=20, choices=TIPO_ENERGIA_CHOICES)
    horas = models.JSONField(help_text='Lista de 24 valores, Hora 1 a Hora 24')
    total = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['fecha', 'tipo_energia']
        indexes = [
            models.Index(fields=['conjunto', 'tipo_energia']),
            models.Index(fields=['conjunto', 'fecha']),
        ]
        verbose_name = 'Registro de energía'
        verbose_name_plural = 'Registros de energía'

    def __str__(self):
        return f'{self.fecha} · {self.tipo_energia} · cliente {self.id_cliente}'

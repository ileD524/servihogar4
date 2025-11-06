#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servihogar.settings')
django.setup()

from apps.promociones.models import Promocion
from apps.servicios.models import Categoria
from django.utils import timezone
from datetime import timedelta

# Obtener la primera categoría
categoria = Categoria.objects.first()

if categoria:
    # Crear promoción de ejemplo
    promocion = Promocion.objects.create(
        titulo='Descuento de Bienvenida',
        descripcion='20% de descuento en tu primer servicio',
        tipo_descuento='porcentaje',
        valor_descuento=20,
        categoria=categoria,
        fecha_inicio=timezone.now(),
        fecha_fin=timezone.now() + timedelta(days=30),
        activa=True,
        codigo='BIENVENIDA20'
    )
    print(f'✓ Promoción creada: {promocion.titulo} (ID: {promocion.id})')
    print(f'  Código: {promocion.codigo}')
    print(f'  Descuento: {promocion.valor_descuento}%')
    print(f'  Categoría: {promocion.categoria.nombre}')
else:
    print('✗ No se encontró ninguna categoría')

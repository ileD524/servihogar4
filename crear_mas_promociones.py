#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servihogar.settings')
django.setup()

from apps.promociones.models import Promocion
from apps.servicios.models import Categoria
from django.utils import timezone
from datetime import timedelta

# Obtener categorías
categorias = list(Categoria.objects.all())

if categorias:
    # Crear más promociones de ejemplo
    promociones_data = [
        {
            'titulo': 'Descuento Verano 2025',
            'descripcion': 'Aprovecha $500 de descuento en servicios seleccionados',
            'tipo_descuento': 'monto_fijo',
            'valor_descuento': 500,
            'categoria': categorias[0] if len(categorias) > 0 else None,
            'fecha_inicio': timezone.now() - timedelta(days=5),
            'fecha_fin': timezone.now() + timedelta(days=60),
            'activa': True,
            'codigo': 'VERANO500'
        },
        {
            'titulo': 'Black Friday',
            'descripcion': '30% de descuento en todos los servicios',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': 30,
            'categoria': None,  # Aplica a todas las categorías
            'fecha_inicio': timezone.now() - timedelta(days=10),
            'fecha_fin': timezone.now() - timedelta(days=3),
            'activa': False,
            'codigo': 'BLACKFRIDAY30'
        },
        {
            'titulo': 'Promo Cliente Frecuente',
            'descripcion': '15% de descuento para clientes frecuentes',
            'tipo_descuento': 'porcentaje',
            'valor_descuento': 15,
            'categoria': categorias[1] if len(categorias) > 1 else categorias[0],
            'fecha_inicio': timezone.now(),
            'fecha_fin': timezone.now() + timedelta(days=90),
            'activa': True,
            'codigo': 'FRECUENTE15'
        },
    ]
    
    for promo_data in promociones_data:
        promocion = Promocion.objects.create(**promo_data)
        tipo = 'Porcentaje' if promocion.tipo_descuento == 'porcentaje' else 'Monto Fijo'
        valor = f'{promocion.valor_descuento}%' if promocion.tipo_descuento == 'porcentaje' else f'${promocion.valor_descuento}'
        cat_nombre = promocion.categoria.nombre if promocion.categoria else 'Todas las categorías'
        print(f'✓ Promoción creada: {promocion.titulo}')
        print(f'  - Código: {promocion.codigo}')
        print(f'  - Tipo: {tipo}, Valor: {valor}')
        print(f'  - Categoría: {cat_nombre}')
        print(f'  - Estado: {"Activa" if promocion.activa else "Inactiva"}')
        print()
    
    print(f'Total de promociones creadas: {len(promociones_data)}')
else:
    print('✗ No se encontraron categorías')

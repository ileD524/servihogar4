"""
Servicio de lógica de negocio para Promociones
Implementa las validaciones y reglas de negocio para CU-18, CU-19, CU-20
"""
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from .models import Promocion
from apps.turnos.models import Turno


class PromocionService:
    """Servicio para gestión de promociones con reglas de negocio"""
    
    # Constantes de validación
    MIN_PORCENTAJE = Decimal('0.01')
    MAX_PORCENTAJE = Decimal('100.00')
    MIN_MONTO_FIJO = Decimal('0.01')
    MAX_MONTO_FIJO = Decimal('999999.99')
    
    @staticmethod
    def validar_fechas(fecha_inicio, fecha_fin):
        """
        Valida que las fechas sean coherentes:
        - La fecha de inicio debe ser anterior o igual a la fecha de fin
        - Ambas fechas deben estar presentes
        
        Returns:
            tuple: (es_valido: bool, mensaje_error: str)
        """
        if not fecha_inicio or not fecha_fin:
            return False, "Las fechas de inicio y fin son obligatorias"
        
        if fecha_inicio > fecha_fin:
            return False, "La fecha de inicio debe ser anterior o igual a la fecha de fin"
        
        return True, ""
    
    @staticmethod
    def validar_valor_descuento(tipo_descuento, valor_descuento):
        """
        Valida que el valor del descuento esté dentro del rango permitido
        según el tipo de descuento.
        
        Args:
            tipo_descuento: 'porcentaje' o 'monto_fijo'
            valor_descuento: Decimal con el valor del descuento
            
        Returns:
            tuple: (es_valido: bool, mensaje_error: str)
        """
        if valor_descuento is None:
            return False, "El valor del descuento es obligatorio"
        
        if tipo_descuento == 'porcentaje':
            if valor_descuento < PromocionService.MIN_PORCENTAJE:
                return False, f"El porcentaje debe ser mayor o igual a {PromocionService.MIN_PORCENTAJE}%"
            if valor_descuento > PromocionService.MAX_PORCENTAJE:
                return False, f"El porcentaje no puede superar el {PromocionService.MAX_PORCENTAJE}%"
        
        elif tipo_descuento == 'monto_fijo':
            if valor_descuento < PromocionService.MIN_MONTO_FIJO:
                return False, f"El monto fijo debe ser mayor o igual a ${PromocionService.MIN_MONTO_FIJO}"
            if valor_descuento > PromocionService.MAX_MONTO_FIJO:
                return False, f"El monto fijo no puede superar ${PromocionService.MAX_MONTO_FIJO}"
        else:
            return False, "Tipo de descuento inválido. Debe ser 'porcentaje' o 'monto_fijo'"
        
        return True, ""
    
    @staticmethod
    def validar_promociones_solapadas(fecha_inicio, fecha_fin, categoria=None, servicios=None, promocion_id=None):
        """
        Valida que no existan promociones activas solapadas para el mismo período y condiciones.
        
        Dos promociones se consideran solapadas si:
        - Tienen períodos de vigencia que se superponen
        - Aplican a las mismas categorías o servicios
        
        Args:
            fecha_inicio: Fecha de inicio de la nueva/modificada promoción
            fecha_fin: Fecha de fin de la nueva/modificada promoción
            categoria: Categoría a la que aplica (puede ser None)
            servicios: Lista de servicios a los que aplica (puede ser None o vacío)
            promocion_id: ID de la promoción a excluir (para modificaciones)
            
        Returns:
            tuple: (es_valido: bool, mensaje_error: str)
        """
        # Buscar promociones activas con períodos solapados
        promociones_query = Promocion.objects.filter(
            activa=True,
            fecha_fin__gte=fecha_inicio,  # La promoción existente termina después del inicio de la nueva
            fecha_inicio__lte=fecha_fin    # La promoción existente comienza antes del fin de la nueva
        )
        
        # Excluir la promoción actual si es una modificación
        if promocion_id:
            promociones_query = promociones_query.exclude(id=promocion_id)
        
        # Filtrar por condiciones de aplicación
        if categoria:
            # Buscar promociones que apliquen a la misma categoría
            promociones_query = promociones_query.filter(categoria=categoria)
        
        if servicios:
            # Buscar promociones que apliquen a los mismos servicios
            for servicio in servicios:
                promociones_solapadas = promociones_query.filter(servicios=servicio)
                if promociones_solapadas.exists():
                    promocion_existente = promociones_solapadas.first()
                    return False, f"Ya existe una promoción activa '{promocion_existente.titulo}' para el servicio '{servicio.nombre}' en el período indicado"
        
        # Si hay promociones solapadas con la misma categoría
        if categoria and promociones_query.exists():
            promocion_existente = promociones_query.first()
            return False, f"Ya existe una promoción activa '{promocion_existente.titulo}' para la categoría '{categoria.nombre}' en el período indicado"
        
        return True, ""
    
    @staticmethod
    def validar_nombre_unico(titulo, promocion_id=None):
        """
        Valida que el nombre de la promoción no duplique otra existente.
        
        Args:
            titulo: Título de la promoción
            promocion_id: ID de la promoción a excluir (para modificaciones)
            
        Returns:
            tuple: (es_valido: bool, mensaje_error: str)
        """
        if not titulo or not titulo.strip():
            return False, "El nombre de la promoción es obligatorio"
        
        query = Promocion.objects.filter(titulo__iexact=titulo.strip())
        
        if promocion_id:
            query = query.exclude(id=promocion_id)
        
        if query.exists():
            return False, f"Ya existe una promoción con el nombre '{titulo}'"
        
        return True, ""
    
    @staticmethod
    def puede_eliminar_promocion(promocion):
        """
        Verifica si una promoción puede ser eliminada/inactivada.
        Solo puede eliminarse si no hay turnos activos asociados.
        
        Turnos activos son aquellos que no están en estado 'cancelado' o 'completado'.
        
        Args:
            promocion: Instancia de Promocion
            
        Returns:
            tuple: (puede_eliminar: bool, mensaje_error: str, cantidad_turnos: int)
        """
        # Estados que se consideran "activos" (no finalizados)
        estados_activos = ['pendiente', 'confirmado', 'en_curso']
        
        # Contar turnos activos asociados a esta promoción
        turnos_activos = Turno.objects.filter(
            promocion=promocion,
            estado__in=estados_activos
        )
        
        cantidad = turnos_activos.count()
        
        if cantidad > 0:
            return False, f"No se puede eliminar la promoción porque tiene {cantidad} turno(s) activo(s) asociado(s)", cantidad
        
        return True, "", 0
    
    @staticmethod
    def registrar_promocion(datos):
        """
        Registra una nueva promoción validando todos los datos.
        
        Args:
            datos: Diccionario con los datos de la promoción
                - titulo: str
                - descripcion: str
                - tipo_descuento: str ('porcentaje' o 'monto_fijo')
                - valor_descuento: Decimal
                - categoria: Categoria instance (opcional)
                - servicios: QuerySet de Servicio (opcional)
                - fecha_inicio: datetime
                - fecha_fin: datetime
                - codigo: str (opcional)
                
        Returns:
            tuple: (promocion: Promocion|None, errores: dict)
        """
        errores = {}
        
        # Validar fechas
        fecha_inicio = datos.get('fecha_inicio')
        fecha_fin = datos.get('fecha_fin')
        fechas_validas, mensaje_fechas = PromocionService.validar_fechas(fecha_inicio, fecha_fin)
        if not fechas_validas:
            errores['fechas'] = mensaje_fechas
        
        # Validar valor del descuento
        tipo_descuento = datos.get('tipo_descuento')
        valor_descuento = datos.get('valor_descuento')
        valor_valido, mensaje_valor = PromocionService.validar_valor_descuento(tipo_descuento, valor_descuento)
        if not valor_valido:
            errores['valor_descuento'] = mensaje_valor
        
        # Validar nombre único
        titulo = datos.get('titulo')
        nombre_valido, mensaje_nombre = PromocionService.validar_nombre_unico(titulo)
        if not nombre_valido:
            errores['titulo'] = mensaje_nombre
        
        # Validar promociones solapadas (solo si las fechas son válidas)
        if fechas_validas:
            categoria = datos.get('categoria')
            servicios = datos.get('servicios')
            no_solapada, mensaje_solape = PromocionService.validar_promociones_solapadas(
                fecha_inicio, fecha_fin, categoria, servicios
            )
            if not no_solapada:
                errores['solape'] = mensaje_solape
        
        # Si hay errores, retornar
        if errores:
            return None, errores
        
        # Crear la promoción
        try:
            promocion = Promocion.objects.create(
                titulo=datos['titulo'],
                descripcion=datos.get('descripcion', ''),
                tipo_descuento=datos['tipo_descuento'],
                valor_descuento=datos['valor_descuento'],
                categoria=datos.get('categoria'),
                fecha_inicio=datos['fecha_inicio'],
                fecha_fin=datos['fecha_fin'],
                codigo=datos.get('codigo'),
                activa=True
            )
            
            # Asignar servicios si existen
            if datos.get('servicios'):
                promocion.servicios.set(datos['servicios'])
            
            return promocion, {}
            
        except Exception as e:
            return None, {'general': f"Error al crear la promoción: {str(e)}"}
    
    @staticmethod
    def modificar_promocion(promocion, datos):
        """
        Modifica una promoción existente validando todos los datos.
        
        Args:
            promocion: Instancia de Promocion a modificar
            datos: Diccionario con los nuevos datos
            
        Returns:
            tuple: (promocion: Promocion|None, errores: dict)
        """
        errores = {}
        
        # Validar fechas
        fecha_inicio = datos.get('fecha_inicio', promocion.fecha_inicio)
        fecha_fin = datos.get('fecha_fin', promocion.fecha_fin)
        fechas_validas, mensaje_fechas = PromocionService.validar_fechas(fecha_inicio, fecha_fin)
        if not fechas_validas:
            errores['fechas'] = mensaje_fechas
        
        # Validar valor del descuento
        tipo_descuento = datos.get('tipo_descuento', promocion.tipo_descuento)
        valor_descuento = datos.get('valor_descuento', promocion.valor_descuento)
        valor_valido, mensaje_valor = PromocionService.validar_valor_descuento(tipo_descuento, valor_descuento)
        if not valor_valido:
            errores['valor_descuento'] = mensaje_valor
        
        # Validar nombre único (excluyendo la promoción actual)
        titulo = datos.get('titulo', promocion.titulo)
        nombre_valido, mensaje_nombre = PromocionService.validar_nombre_unico(titulo, promocion.id)
        if not nombre_valido:
            errores['titulo'] = mensaje_nombre
        
        # Validar promociones solapadas (solo si las fechas son válidas)
        if fechas_validas:
            categoria = datos.get('categoria', promocion.categoria)
            servicios = datos.get('servicios', promocion.servicios.all())
            no_solapada, mensaje_solape = PromocionService.validar_promociones_solapadas(
                fecha_inicio, fecha_fin, categoria, servicios, promocion.id
            )
            if not no_solapada:
                errores['solape'] = mensaje_solape
        
        # Si hay errores, retornar
        if errores:
            return None, errores
        
        # Actualizar la promoción
        try:
            for campo, valor in datos.items():
                if campo != 'servicios':  # Los servicios se manejan aparte
                    setattr(promocion, campo, valor)
            
            promocion.save()
            
            # Actualizar servicios si se proporcionaron
            if 'servicios' in datos:
                promocion.servicios.set(datos['servicios'])
            
            return promocion, {}
            
        except Exception as e:
            return None, {'general': f"Error al modificar la promoción: {str(e)}"}
    
    @staticmethod
    def eliminar_promocion(promocion):
        """
        Elimina (inactiva) una promoción si no tiene turnos activos.
        
        Args:
            promocion: Instancia de Promocion a eliminar
            
        Returns:
            tuple: (exitoso: bool, mensaje: str)
        """
        # Verificar si puede eliminarse
        puede_eliminar, mensaje, cantidad = PromocionService.puede_eliminar_promocion(promocion)
        
        if not puede_eliminar:
            return False, mensaje
        
        # Inactivar la promoción (soft delete)
        try:
            promocion.activa = False
            promocion.save()
            return True, "Promoción eliminada exitosamente"
        except Exception as e:
            return False, f"Error al eliminar la promoción: {str(e)}"

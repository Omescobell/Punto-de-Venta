from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Sum, Avg, Max, Min, Count, F
from django.db.models.functions import ExtractHour
from orders.models import Order, OrderItems
from products.models import Product
from customers.models import Customer


class ProductAnalyticsService:

    @staticmethod
    def _calculate_product_stats(period_orders, limit=None, criterion=None):
        """
        Calcula estadísticas de productos..
        """
        base_qs = OrderItems.objects.filter(order__in=period_orders).values(
            'product__id', 'product_name'
        ).annotate(
            units_sold=Sum('quantity'),
            revenue=Sum('amount')
        )

        if criterion is None:
            products_stats = base_qs.order_by('-revenue')
            
            total_piezas = products_stats.aggregate(total=Sum('units_sold'))['total'] or 0
            top_product = products_stats.first() if products_stats else None

            return {
                "total_units_sold": total_piezas,
                "top_product": top_product,
                "breakdown": list(products_stats)
            }
        else:
            sales_list = list(base_qs.order_by('units_sold'))

            if not sales_list:
                return {"message": "No hubo productos vendidos en el período seleccionado."}

            results = {"criterion": criterion, "limite_results": limit}

            if criterion in ['least', 'both']:
                results['least_sold'] = sales_list[:limit]

            if criterion in ['most', 'both']:
                results['most_sold'] = sales_list[-limit:][::-1]

            return results

    @classmethod
    def get_product_ranking(cls, start_date_str, end_date_str, limit_str, criterion):
        try:
            limit = int(limit_str)
            if limit <= 0: limit = 10
        except (ValueError, TypeError):
            limit = 10

        if criterion not in ['most', 'least', 'both']:
            criterion = 'most'

        base_orders = Order.objects.filter(status='PAID')

        start_date, end_date, error = DateValidationService.validate_and_get_date_range(
            queryset=base_orders,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            date_field='created_at',
            entity_name='ventas'
        )

        if error:
            return None, error

        period_orders = base_orders.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        data = cls._calculate_product_stats(period_orders, limit, criterion)

        response_data = {
            "periodo_analizado": {
                "fecha_inicio": start_date.strftime('%Y-%m-%d'),
                "fecha_fin": end_date.strftime('%Y-%m-%d')
            }
        }

        # Manejar el caso de que no haya ventas en ese periodo
        if "message" in data:
            response_data["detail"] = data["message"]
        else:
            response_data["results"] = data

        return response_data, None
    
class SalesAnalyticsService:

    @staticmethod
    def _get_orders_by_status(status='PAID'):
        """Obtiene todas las órdenes filtradas por su estado."""
        return Order.objects.filter(status=status)

    @staticmethod
    def _calculate_general_totals(period_orders):
        """Calcula métricas generales como ingresos totales, ticket promedio, min y max."""
        return period_orders.aggregate(
            total_revenue=Sum('final_amount'),
            average_ticket=Avg('final_amount'),
            lowest_ticket=Min('final_amount'),
            highest_ticket=Max('final_amount'),
            total_tickets=Count('id')
        )

    @staticmethod
    def _calculate_hourly_stats(period_orders):
        """Calculates which hour had the most revenue and most activity (tickets)."""
        hourly_stats = period_orders.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            total_revenue=Sum('final_amount'),
            ticket_count=Count('id')
        ).order_by('hour')

        most_profitable = max(hourly_stats, key=lambda x: x['total_revenue'], default=None) if hourly_stats else None
        busiest = max(hourly_stats, key=lambda x: x['ticket_count'], default=None) if hourly_stats else None

        return {
            "most_profitable_hour": most_profitable,
            "busiest_hour": busiest,
            "hourly_breakdown": list(hourly_stats)
        }

    @staticmethod
    def _calculate_payment_stats(period_orders):
        """Groups and sums sales by payment method."""
        payment_stats = period_orders.values('payment_method').annotate(
            total_sales=Count('id'),
            average_ticket=Avg('final_amount'),
            highest_ticket=Max('final_amount'),
            accumulated_amount=Sum('final_amount')
        )
        return list(payment_stats)

    @classmethod
    def get_sales_summary(cls, start_date_str=None, end_date_str=None):
        """
        Orquestador principal. 
        Usa los submétodos para construir el informe final.
        """
        # 1. Obtener base de datos de órdenes a utilizar (solo pagadas)
        base_orders = cls._get_orders_by_status(status='PAID')
        
        # 2. Validar fechas
        start_date, end_date, error = DateValidationService.validate_and_get_date_range(
            queryset=base_orders,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            date_field='created_at',
            entity_name='sales'
)
        
        # Si hubo un error en la validación, lo retornamos inmediatamente
        if error:
            return error

        # 3. Filtrar órdenes en el rango de fechas válido
        period_orders = base_orders.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        # 4. Consolidar el informe llamando a los servicios independientes
        return {
            "analyzed_period": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            },
            "general_summary": cls._calculate_general_totals(period_orders),
            "products": ProductAnalyticsService._calculate_product_stats(period_orders),
            "peak_hours": cls._calculate_hourly_stats(period_orders),
            "payment_methods": cls._calculate_payment_stats(period_orders)
        }
    
class DateValidationService:
    """
    Servicio independiente para validar y calcular rangos de fechas 
    en cualquier QuerySet del sistema.
    """

    @staticmethod
    def validate_and_get_date_range(
        queryset, 
        start_date_str=None, 
        end_date_str=None, 
        date_field='created_at', 
        entity_name='registros'
    ):
        """
        Valida fechas dinámicamente para cualquier QuerySet.
        
        :param queryset: QuerySet de Django sobre el cual validar.
        :param start_date_str: Fecha inicial en string (YYYY-MM-DD).
        :param end_date_str: Fecha final en string (YYYY-MM-DD).
        :param date_field: Nombre del campo de fecha en el modelo (default: 'created_at').
        :param entity_name: Nombre de los datos para los messages de error (default: 'registros').
        :return: (start_date, end_date, dict_error_si_hubo)
        """
        
        boundaries = queryset.aggregate(
            first_record=Min(date_field),
            last_record=Max(date_field)
        )
        
        if not boundaries['first_record']:
            return None, None, {"error": f"No hay {entity_name} en el sistema aún."}
            
        system_first_date = timezone.localtime(boundaries['first_record']).date() if hasattr(boundaries['first_record'], 'date') else boundaries['first_record']
        system_last_date = timezone.localtime(boundaries['last_record']).date() if hasattr(boundaries['last_record'], 'date') else boundaries['last_record']

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return None, None, {"error": "Formato de fecha inválido. Usa YYYY-MM-DD."}
            
            start_filter = {f"{date_field}__date": start_date}
            end_filter = {f"{date_field}__date": end_date}
            
            start_exists = queryset.filter(**start_filter).exists()
            end_exists = queryset.filter(**end_filter).exists()
            
            if not start_exists or not end_exists:
                invalid_date = start_date_str if not start_exists else end_date_str
                return None, None, {
                    "error": f"La fecha {invalid_date} no tiene {entity_name} en el sistema.",
                    "first_system_record": system_first_date.strftime('%Y-%m-%d'),
                    "last_system_records": system_last_date.strftime('%Y-%m-%d')
                }
            return start_date, end_date, None
            
        else:
            end_date = timezone.localtime(timezone.now()).date()
            start_date = max(end_date - timedelta(days=30), system_first_date)
            
            return start_date, end_date, None

class InventoryService:
    
    @staticmethod
    def get_low_stock_report(threshold=None):
        """
        Genera el reporte de productos con bajo stock cumpliendo las reglas de negocio.
        Retorna un diccionario con el estado, el mensaje (si aplica) y los datos.
        """
        if not Product.objects.exists():
            return {
                "success": False,
                "message": "No hay productos registrados en el sistema."
            }

        if threshold is not None:
            try:
                threshold_val = int(threshold)
                queryset = Product.objects.filter(current_stock__lte=threshold_val)
            except ValueError:
                return {
                    "success": False,
                    "message": "El umbral proporcionado no es un número válido."
                }
        else:
            queryset = Product.objects.filter(low_stock=True)

        if not queryset.exists():
            return {
                "success": False,
                "message": "No hay productos dentro del umbral establecido."
            }

        queryset = queryset.order_by('-current_stock')
        report_data = list(queryset.values('name', 'current_stock'))

        return {
            "success": True,
            "data": report_data
        }
    
    @staticmethod
    def get_dead_inventory_report(reference_date_str=None):
        
        """
        Identifica el inventario muerto: Productos sin ventas desde una fecha dada.
        """
        if not Product.objects.exists():
            return {
                "success": False,
                "message": "No hay productos registrados en el sistema para analizar."
            }

        if reference_date_str:
            reference_date = parse_date(reference_date_str)
            if not reference_date:
                return {
                    "success": False,
                    "message": "Formato de fecha inválido. Utilice YYYY-MM-DD."
                }
        else:
            reference_date = timezone.now().date() - timedelta(days=30)

        sold_product_ids = OrderItems.objects.filter(
            order__created_at__date__gte=reference_date,
            order__status='PAID'
        ).values_list('product_id', flat=True).distinct()

        dead_inventory_qs = Product.objects.exclude(id__in=sold_product_ids)

        if not dead_inventory_qs.exists():
            return {
                "success": False,
                "message": "Todos los productos han tenido ventas en este período."
            }

        # Generamos la lista final (solo necesitamos el nombre y si gustas, el stock actual)
        report_data = list(dead_inventory_qs.values('id', 'name', 'current_stock'))

        return {
            "success": True,
            "data": report_data
        }

class CustomerAnalyticsService:

    @classmethod
    def get_customer_history(cls, customer_id, start_date_str=None, end_date_str=None):
        # 1. Validación Obligatoria del Cliente
        if not customer_id:
            return None, {"error": "customer_id parameter is required."}, 400
            
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return None, {"error": "Customer not registered in the system."}, 404

        # 2. Filtrar órdenes del cliente (Solo pagadas)
        customer_orders = Order.objects.filter(customer=customer, status='PAID')

        # 3. Validación de Fechas (CORRECCIÓN AQUÍ)
        # Usamos TODAS las órdenes de la tienda para validar que las fechas existen en el sistema.
        all_store_orders = Order.objects.filter(status='PAID')
        
        start_date, end_date, error = DateValidationService.validate_and_get_date_range(
            queryset=all_store_orders,  # Cambiado de customer_orders a all_store_orders
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            date_field='created_at',
            entity_name='purchases' 
        )

        if error:
            return None, error, 400

        # 4. Recopilación de Datos Filtrados
        period_orders = customer_orders.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        # 5. Construir info base (CORRECCIÓN DE KEYS AQUÍ)
        base_response = {
            "customer_info": {
                "id": customer.id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone_number": customer.phone_number
            },
            "analyzed_period": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
        }

        # 6. Si no hay compras del cliente en el periodo válido, devolvemos 200 OK con el detalle
        if not period_orders.exists():
            base_response["detail"] = "This customer made no purchases during the selected period."
            return base_response, None, 200

        # 7. Cálculo de Métricas
        sales_metrics = cls._calculate_customer_totals(period_orders)
        top_product = cls._get_customer_top_product(period_orders)
        
        # Reutilizamos lógica de SalesAnalyticsService
        peak_hours = SalesAnalyticsService._calculate_hourly_stats(period_orders)['hourly_breakdown']
        payment_methods = SalesAnalyticsService._calculate_payment_stats(period_orders)

        # 8. Construir Informe Final
        base_response.update({
            "sales_metrics": sales_metrics,
            "top_product": top_product,
            "peak_buying_hours": peak_hours,
            "payment_methods": payment_methods
        })

        return base_response, None, 200

    @staticmethod
    def _calculate_customer_totals(period_orders):
        from django.db.models import Sum, Avg, Count
        return period_orders.aggregate(
            total_spent=Sum('final_amount'),
            average_ticket=Avg('final_amount'),
            total_tickets=Count('id')
        )

    @staticmethod
    def _get_customer_top_product(period_orders):
        top_product = OrderItems.objects.filter(order__in=period_orders).values(
            'product_name'
        ).annotate(
            total_spent_on_product=Sum('amount'),
            units_bought=Sum('quantity')
        ).order_by('-total_spent_on_product').first()
        
        return top_product
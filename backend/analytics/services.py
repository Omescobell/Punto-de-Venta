from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Sum, Avg, Max, Min, Count, F, Q, DecimalField
from django.db.models.functions import ExtractHour
from orders.models import Order, OrderItems
from products.models import Product
from customers.models import Customer
from decimal import Decimal

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
        base_orders = cls._get_orders_by_status(status='PAID')

        start_date, end_date, error = DateValidationService.validate_and_get_date_range(
            queryset=base_orders,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            date_field='created_at',
            entity_name='sales'
)
        
        if error:
            return error

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

    @staticmethod
    def calculate_product_contribution(product_identifier, start_date=None, end_date=None):
        if not product_identifier:
            return None, {"error": "Product identifier is required."}, 400

        # ! Validación del Producto
        try:
            product = Product.objects.get(Q(sku=product_identifier) | Q(name__iexact=product_identifier))
        except Product.DoesNotExist:
            return None, {"error": "Product not found."}, 404
        except Product.MultipleObjectsReturned:
            product = Product.objects.filter(Q(sku=product_identifier) | Q(name__iexact=product_identifier)).first()

        # ! Definición del Período
        if not start_date or not end_date:
            end_date_parsed = timezone.now()
            start_date_parsed = end_date_parsed - timedelta(days=30)
        else:
            start_parsed = parse_date(start_date)
            end_parsed = parse_date(end_date)
            
            if not start_parsed or not end_parsed:
                return None, {"error": "Invalid date format. Use YYYY-MM-DD."}, 400
            # Convertimos a datetime con timezone aware (inicio del día y fin del día)
            start_date_parsed = timezone.make_aware(datetime.combine(start_parsed, datetime.min.time()))
            end_date_parsed = timezone.make_aware(datetime.combine(end_parsed, datetime.max.time()))

        # ! Cálculo de Ventas Totales (General)
        orders_in_period = Order.objects.filter(
            status='PAID', 
            created_at__range=(start_date_parsed, end_date_parsed)
        )

        total_general_sales = orders_in_period.aggregate(
            total=Sum('final_amount')
        )['total'] or Decimal('0.00')

        if total_general_sales == Decimal('0.00'):
            return None, {"error": "No sales recorded in the specified period."}, 404

        # ! Cálculo de Ventas Totales (Producto Específico)
        product_sales = OrderItems.objects.filter(
            order__in=orders_in_period,
            product=product
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # ! Cálculo del Porcentaje de Contribución
        contribution_percentage = (product_sales / total_general_sales) * Decimal('100.00')

        # ! Generación del Informe
        report = {
            "product": {
                "sku": product.sku,
                "name": product.name
            },
            "period": {
                "start_date": start_date_parsed.strftime('%Y-%m-%d'),
                "end_date": end_date_parsed.strftime('%Y-%m-%d')
            },
            "contribution_metrics": {
                "contribution_percentage": round(contribution_percentage, 2),
                "total_product_sales": round(product_sales, 2),
                "total_general_sales": round(total_general_sales, 2)
            }
        }

        return report, None, 200
    
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
    
    @classmethod
    def calculate_sales_velocity(cls, identifier, period_days=30):
        if not identifier:
            return None, {"error": "Product identifier (Name or SKU) is required."}, 400

        try:
            product = Product.objects.get(Q(sku=identifier) | Q(name__iexact=identifier))
        except Product.DoesNotExist:
            return None, {"error": "Product not found in the system."}, 404
        except Product.MultipleObjectsReturned:
            product = Product.objects.filter(Q(sku=identifier) | Q(name__iexact=identifier)).first()

        now = timezone.now()
        
        first_sale_data = OrderItems.objects.filter(
            product=product,
            order__status='PAID'
        ).aggregate(first_sale_date=Min('order__created_at'))
        
        first_sale_date = first_sale_data['first_sale_date']
        
        actual_period_days = int(period_days)
        start_date = now - timedelta(days=actual_period_days)
        if first_sale_date:
            days_since_first_sale = (now - first_sale_date).days
            days_since_first_sale = max(1, days_since_first_sale)
            if days_since_first_sale < actual_period_days:
                actual_period_days = days_since_first_sale
                start_date = first_sale_date

        # Recopilación de ventas del producto en el periodo ajustado
        period_items = OrderItems.objects.filter(
            product=product,
            order__status='PAID',
            order__created_at__gte=start_date
        )

        # Suma de unidades
        total_units_sold = period_items.aggregate(total=Sum('quantity'))['total'] or 0

        # Cálculo del Promedio Diario (Velocidad de venta)
        sales_velocity = total_units_sold / actual_period_days

        # 4. Consulta de Inventario y Estimación de Agotamiento
        current_stock = product.current_stock
        
        if sales_velocity > 0:
            # current_stock / velocidad diaria = días para agotarse
            depletion_estimation = round(current_stock / sales_velocity)
        else:
            depletion_estimation = "Indefinida"

        # 5. Generación del Informe Consolidado
        report = {
            "product_name": product.name,
            "product_sku": product.sku,
            "analyzed_period_days": actual_period_days,
            "total_units_sold": total_units_sold,
            "sales_velocity": round(sales_velocity, 2),  # Redondeamos a 2 decimales
            "current_stock": current_stock,
            "depletion_estimation_days": depletion_estimation
        }

        return report, None, 200

    @classmethod
    def calculate_inventory_valuation(cls, product_identifier=None):
        # 1. Filtramos solo los productos que tienen stock
        queryset = Product.objects.filter(current_stock__gt=0)
        scope_name = "Entire Inventory"
        
        # Filtrado por producto específico si se envía
        if product_identifier:
            queryset = queryset.filter(Q(sku=product_identifier) | Q(name__iexact=product_identifier))
            scope_name = f"Specific Product: {product_identifier}"

        if not queryset.exists():
            return None, {"error": "No products available in the selected scope."}, 404

        # 2. Suma a nivel de BD usando 'price' (costo proveedor) y 'final_price' (venta al público)
        totals = queryset.aggregate(
            total_net_cost=Sum(
                F('price') * F('current_stock'), 
                output_field=DecimalField()
            ),
            total_potential_sale=Sum(
                F('final_price') * F('current_stock'), 
                output_field=DecimalField()
            )
        )

        total_net_cost = totals['total_net_cost'] or Decimal('0.00')
        total_potential_sale = totals['total_potential_sale'] or Decimal('0.00')

        # ! Cálculo de Ganancia y Margen
        potential_profit = total_potential_sale - total_net_cost

        if total_potential_sale > 0:
            profit_margin_percentage = (potential_profit / total_potential_sale) * Decimal('100.00')
        else:
            profit_margin_percentage = Decimal('0.00')

        # ! Generación del Informe Financiero
        report = {
            "scope": scope_name,
            "financial_metrics": {
                "total_inventory_cost": round(total_net_cost, 2),
                "total_potential_sale": round(total_potential_sale, 2),
                "total_potential_profit": round(potential_profit, 2),
                "profit_margin_percentage": round(profit_margin_percentage, 2)
            }
        }

        return report, None, 200
    @staticmethod
    def calculate_inventory_valuation(product_identifier=None):
        queryset = Product.objects.filter(current_stock__gt=0)
        scope_name = "Entire Inventory"
        
        if product_identifier:
            queryset = queryset.filter(Q(sku=product_identifier) | Q(name__iexact=product_identifier))
            scope_name = f"Specific Product: {product_identifier}"

        if not queryset.exists():
            return None, {"error": "No products available in the selected scope."}, 404

        totals = queryset.aggregate(
            total_net_cost=Sum(
                F('price') * F('current_stock'), 
                output_field=DecimalField()
            ),
            total_potential_sale=Sum(
                F('final_price') * F('current_stock'), 
                output_field=DecimalField()
            )
        )
        total_net_cost = totals['total_net_cost'] or Decimal('0.00')
        total_potential_sale = totals['total_potential_sale'] or Decimal('0.00')
        # ! Cálculo de Ganancia y Margen
        potential_profit = total_potential_sale - total_net_cost

        if total_potential_sale > 0:
            profit_margin_percentage = (potential_profit / total_potential_sale) * Decimal('100.00')
        else:
            profit_margin_percentage = Decimal('0.00')

        # ! Generación del Informe Financiero
        report = {
            "scope": scope_name,
            "financial_metrics": {
                "total_inventory_cost": round(total_net_cost, 2),
                "total_potential_sale": round(total_potential_sale, 2),
                "total_potential_profit": round(potential_profit, 2),
                "profit_margin_percentage": round(profit_margin_percentage, 2)
            }
        }

        return report, None, 200

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

        customer_orders = Order.objects.filter(customer=customer, status='PAID')
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

        period_orders = customer_orders.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
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

        if not period_orders.exists():
            base_response["detail"] = "This customer made no purchases during the selected period."
            return base_response, None, 200

        sales_metrics = cls._calculate_customer_totals(period_orders)
        top_product = cls._get_customer_top_product(period_orders)
        
        peak_hours = SalesAnalyticsService._calculate_hourly_stats(period_orders)['hourly_breakdown']
        payment_methods = SalesAnalyticsService._calculate_payment_stats(period_orders)

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
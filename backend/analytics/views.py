from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .services import SalesAnalyticsService, ProductAnalyticsService,InventoryService, CustomerAnalyticsService
from .permissions import IsAdminOrOwner

class AnalyticsViewSet(viewsets.ViewSet):
    
    permission_classes = [IsAdminOrOwner] 

    # ! /api/analytics/sales-summary/
    @action(detail=False, methods=['get'], url_path='sales-summary')
    def sales_summary(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        data = SalesAnalyticsService.get_sales_summary(start_date, end_date)

        if "error" in data:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status.HTTP_200_OK)

    # ! /api/analytics/product-ranking/?limit=5&criterion=most
    @action(detail=False, methods=['get'], url_path='product-ranking')
    def product_ranking(self, request):

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        limit = request.query_params.get('limit', 10)
        criterion = request.query_params.get('criterion', 'most')

        data, error = ProductAnalyticsService.get_product_ranking(
            start_date, 
            end_date, 
            limit, 
            criterion
        )

        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)
    
    # ! /api/analytics/reports/low-stock/?threshold=10
    @action(detail=False, methods=['get'], url_path='reports/low-stock', url_name='low-stock')
    def low_stock(self, request):
        """
        Endpoint para obtener el reporte de productos con bajo inventario.
        """
        threshold = request.query_params.get('threshold')
        
        result = InventoryService.get_low_stock_report(threshold)

        if not result.get('success'):
            return Response(
                {"message": result['message']}, 
                status=status.HTTP_200_OK
            )
            
        return Response(result['data'], status=status.HTTP_200_OK)
    
    # ! /api/analytics/reports/dead-inventory/?reference_date=2023-10-01
    @action(detail=False, methods=['get'], url_path='reports/dead-inventory', url_name='dead-inventory')
    def dead_inventory(self, request):
        """
        Endpoint para obtener el reporte de productos sin ventas (Inventario Muerto).
        Acepta el parámetro opcional ?reference_date=YYYY-MM-DD
        """
        reference_date_str = request.query_params.get('reference_date')
        
        result = InventoryService.get_dead_inventory_report(reference_date_str)
        
        if not result.get('success'):
            return Response(
                {"message": result['message']}, 
                status=status.HTTP_200_OK
            )
            
        # Respuesta exitosa con la lista final de productos
        return Response(result['data'], status=status.HTTP_200_OK)

    # ! /api/analytics/customer-sales/?customer_id=5&start_date=2023-10-01
    @action(detail=False, methods=['get'], url_path='customer-sales')
    def customer_sales(self, request):
        """
        Endpoint para obtener el historial y métricas de un cliente específico.
        """
        customer_id = request.query_params.get('customer_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        data, error, status_code = CustomerAnalyticsService.get_customer_history(
            customer_id, start_date, end_date
        )

        if error:
            return Response(error, status=status_code)

        return Response(data, status=status_code)
    # * Con SKU
    # ! /api/analytics/sales-velocity/?identifier=FAST123&period_days=30
    # * Con nombre y el 30 dias por defecto
    # ! /api/analytics/sales-velocity/?identifier=Laptop%20Gamer
    @action(detail=False, methods=['get'], url_path='sales-velocity')
    def sales_velocity(self, request):
        """
        Calcula la velocidad de venta de un producto y estima en cuántos días se agotará.
        Params: 
        - identifier (obligatorio): Nombre exacto o Código de Barras (SKU)
        - period_days (opcional): Número de días a analizar (default: 30)
        """
        identifier = request.query_params.get('identifier')
        period_days = request.query_params.get('period_days', 30)

        data, error, status_code = InventoryService.calculate_sales_velocity(
            identifier=identifier,
            period_days=period_days
        )

        if error:
            return Response(error, status=status_code)

        return Response(data, status=status_code)
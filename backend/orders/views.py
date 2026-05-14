from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Order
from .serializers import OrderSerializer, OrderPaymentSerializer, OrderCancelSerializer
from .permissions import IsAdminOrOwner

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related('items').order_by('-created_at')
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminOrOwner()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'pay':
            return OrderPaymentSerializer
        if self.action == 'cancel':
            return OrderCancelSerializer
        return OrderSerializer

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        """
        Recibe la petición, valida con el serializer y ejecuta el pago.
        """
        order = self.get_object()

        serializer = OrderPaymentSerializer(
            data=request.data, 
            context={'order': order}
        )


        serializer.is_valid(raise_exception=True)

        order_pagada = serializer.process_payment()

        return Response(
            OrderSerializer(order_pagada).data, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Endpoint para cancelar una orden PENDING.
        Ruta: POST /api/orders/{id}/cancel/
        """
        order = self.get_object()
        
        serializer = self.get_serializer(order, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'Order cancelled', 
                'detail': f'La orden {order.id} fue cancelada y el stock restaurado.'
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='send-email')
    def send_ticket_email(self, request, pk=None):
        """
        Envía el ticket de una orden por correo electrónico.
        Ruta: POST /api/orders/{id}/send-email/
        Body: { "email": "cliente@ejemplo.com" }
        """
        order = self.get_object()
        recipient_email = request.data.get('email', '').strip()

        if not recipient_email:
            return Response(
                {'error': 'El campo "email" es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = order.items.all()
        payment_display = {
            'CASH': 'Efectivo',
            'CARD': 'Tarjeta',
            'STORE_CREDIT': 'Crédito Tienda',
            'LOYALTY_POINTS': 'Puntos',
        }.get(order.payment_method, order.payment_method or 'N/A')

        # Construir tabla de ítems en HTML
        items_rows = ''.join(
            f"""<tr>
                <td style='padding:8px;border-bottom:1px solid #eee;'>{item.product_name}</td>
                <td style='padding:8px;border-bottom:1px solid #eee;text-align:center;'>{item.quantity}</td>
                <td style='padding:8px;border-bottom:1px solid #eee;text-align:right;'>${float(item.unit_price):.2f}</td>
                <td style='padding:8px;border-bottom:1px solid #eee;text-align:right;'>${float(item.amount):.2f}</td>
            </tr>"""
            for item in items
        )

        customer_name = order.customer.first_name + ' ' + order.customer.last_name if order.customer else 'Cliente Visitante'

        html_message = f"""
        <html><body style='font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:0;'>
          <div style='max-width:600px;margin:30px auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);'>
            <div style='background:#1a1a2e;color:#fff;padding:24px;text-align:center;'>
              <h1 style='margin:0;font-size:24px;letter-spacing:2px;'>🧾 TICKET DE VENTA</h1>
              <p style='margin:6px 0 0;opacity:.75;'>Orden #{order.id} &nbsp;&bull;&nbsp; Folio: {order.ticket_folio}</p>
            </div>
            <div style='padding:24px;'>
              <table style='width:100%;margin-bottom:16px;'>
                <tr>
                  <td><strong>Fecha:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M')}</td>
                  <td style='text-align:right;'><strong>Cliente:</strong> {customer_name}</td>
                </tr>
              </table>
              <table style='width:100%;border-collapse:collapse;'>
                <thead>
                  <tr style='background:#f0f0f0;'>
                    <th style='padding:10px;text-align:left;'>Producto</th>
                    <th style='padding:10px;text-align:center;'>Cant.</th>
                    <th style='padding:10px;text-align:right;'>P. Unitario</th>
                    <th style='padding:10px;text-align:right;'>Subtotal</th>
                  </tr>
                </thead>
                <tbody>{items_rows}</tbody>
              </table>
              <div style='margin-top:20px;text-align:right;'>
                <p style='margin:4px 0;'><strong>Método de Pago:</strong> {payment_display}</p>
                <p style='margin:4px 0;font-size:20px;font-weight:bold;color:#1a1a2e;'>TOTAL: ${float(order.final_amount):.2f}</p>
              </div>
            </div>
            <div style='background:#f8f8f8;text-align:center;padding:16px;font-size:12px;color:#888;'>
              Gracias por su compra. Este es un comprobante automático.
            </div>
          </div>
        </body></html>
        """

        plain_message = strip_tags(html_message)

        # Determinar la dirección remitente con fallbacks seguros
        from_email = (
            getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            or getattr(settings, 'EMAIL_HOST_USER', None)
            or ''
        ).strip()

        if not from_email:
            return Response(
                {'error': 'El servidor no tiene configurada una dirección de correo remitente. '
                          'Contacta al administrador del sistema.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            send_mail(
                subject=f'Tu ticket de compra - Orden #{order.id}',
                message=plain_message,
                from_email=from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            return Response(
                {'detail': f'Ticket enviado exitosamente a {recipient_email}.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Error al enviar el correo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
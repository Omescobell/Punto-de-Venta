from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Actualiza el estatus low_stock masivamente (Ideal para Cron Jobs)'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando cálculo de Low Stock...")
        
        products = Product.objects.all()
        count = 0
        
        # Iteramos producto por producto usando la lógica del modelo
        for p in products:
            if p.update_inventory_status():
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Proceso terminado. Productos actualizados: {count}'))
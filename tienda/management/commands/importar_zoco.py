import pandas as pd
from django.core.management.base import BaseCommand
from tienda.models import Deuda, Abono
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Importa deudas y abonos desde el Excel de El Zoco'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta del archivo .xlsx')

    def handle(self, *args, **options):
        ruta = options['archivo']
        try:
            df = pd.read_excel(ruta)
            count_deudas = 0

            for _, row in df.iterrows():
                persona = row['PROVEEDORES']
                monto_total = row['Deuda']
                total_abonado = row['Abonado']
                fechas_str = str(row['Fechas de Abonos'])

                # 1. Crear o recuperar la Deuda
                # Usamos fecha_inicio que es el nombre real en tu modelo
                deuda_obj, created = Deuda.objects.get_or_create(
                    persona=persona,
                    monto_total=monto_total,
                    defaults={
                        'fecha_inicio': timezone.now().date(), 
                        'yo_debo': True,
                        'cantidad_pagos': 1 # Evitamos generación automática masiva
                    }
                )

                # 2. Procesar Abonos (Solo si la deuda es nueva o no tiene abonos aún)
                if (fechas_str and fechas_str not in ['nan', 'Sin abonos']) and (created or deuda_obj.abonos.count() == 0):
                    lista_fechas = fechas_str.split(', ')
                    monto_por_abono = total_abonado / len(lista_fechas) if lista_fechas else 0

                    for f_texto in lista_fechas:
                        try:
                            # Limpieza de espacios por si el Excel tiene " 10/05/2026"
                            fecha_dt = datetime.strptime(f_texto.strip(), '%d/%m/%Y')
                            
                            Abono.objects.create(
                                deuda=deuda_obj,
                                monto=monto_por_abono,
                                fecha=timezone.make_aware(fecha_dt),
                                pagado=True # Asumimos que si están en el historial del Excel, ya se pagaron
                            )
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'⚠️ Fecha omitida: {f_texto} - {e}'))
                            continue
                
                count_deudas += 1

            self.stdout.write(self.style.SUCCESS(f'✅ Importación exitosa: {count_deudas} deudas procesadas.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error crítico: {e}'))
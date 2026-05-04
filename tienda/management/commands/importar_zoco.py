import pandas as pd
from django.core.management.base import BaseCommand
from tienda.models import Deuda, Abono
from datetime import datetime

class Command(BaseCommand):
    help = 'Importa deudas y abonos desde el Excel de El Zoco'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta del archivo .xlsx')

    def handle(self, *args, **options):
        ruta = options['archivo']
        try:
            # Leer el Excel usando pandas
            df = pd.read_excel(ruta)

            for _, row in df.iterrows():
                persona = row['PROVEEDORES']
                monto_total = row['Deuda']
                total_abonado = row['Abonado']
                fechas_str = str(row['Fechas de Abonos'])

                # 1. Crear o actualizar la Deuda
                deuda_obj, created = Deuda.objects.get_or_create(
                    persona=persona,
                    monto_total=monto_total,
                    defaults={'fecha_limite': datetime.now(), 'yo_debo': True}
                )

                # 2. Procesar las fechas de abonos si existen
                if fechas_str and fechas_str != 'nan' and fechas_str != 'Sin abonos':
                    lista_fechas = fechas_str.split(', ')
                    # Calculamos un monto individual estimado para cada abono
                    monto_por_abono = total_abonado / len(lista_fechas) if lista_fechas else 0

                    for f_texto in lista_fechas:
                        try:
                            fecha_dt = datetime.strptime(f_texto, '%d/%m/%Y')
                            # Creamos el abono vinculado a la deuda
                            Abono.objects.create(
                                deuda=deuda_obj,
                                monto=monto_por_abono,
                                fecha=fecha_dt
                            )
                        except:
                            continue

            self.stdout.write(self.style.SUCCESS('✅ Importación de El Zoco completada con éxito'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
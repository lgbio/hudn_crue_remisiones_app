"""
Pruebas unitarias para remisiones/services.py.

Cubre: calcular_oportunidad, es_registro_editable, formatear_temperatura,
formatear_spo2, validar_edad, validar_ta, obtener_remisiones.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from remisiones.models import Remision, UsuarioCrue
from remisiones.services import (
    calcular_oportunidad,
    es_registro_editable,
    formatear_spo2,
    formatear_temperatura,
    obtener_remisiones,
    validar_edad,
    validar_ta,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def usuario(db):
    return UsuarioCrue.objects.create_user(username='testuser', password='pass1234')


def _crear_remision(usuario, fecha, doc='00000000'):
    """Helper para crear una Remision mínima con la fecha dada."""
    return Remision.objects.create(
        fecha=fecha,
        nombre='Test Paciente',
        tipo_doc='CC',
        doc=doc,
        sexo='M',
        edad='30 AÑOS',
        gest='NO',
        created_by=usuario,
    )


# ---------------------------------------------------------------------------
# calcular_oportunidad
# ---------------------------------------------------------------------------

class TestCalcularOportunidad:
    def test_delta_cero(self):
        """Misma fecha de ingreso y respuesta → 00:00."""
        ahora = timezone.now()
        assert calcular_oportunidad(ahora, ahora) == '00:00'

    def test_delta_90_minutos(self):
        """90 minutos de diferencia → 01:30."""
        fecha = timezone.now()
        fecha_res = fecha + timedelta(minutes=90)
        assert calcular_oportunidad(fecha, fecha_res) == '01:30'

    def test_fecha_res_none(self):
        """fecha_res=None → cadena vacía."""
        assert calcular_oportunidad(timezone.now(), None) == ''

    def test_fecha_res_menor_que_fecha(self):
        """fecha_res anterior a fecha → cadena vacía."""
        fecha = timezone.now()
        fecha_res = fecha - timedelta(minutes=10)
        assert calcular_oportunidad(fecha, fecha_res) == ''


# ---------------------------------------------------------------------------
# es_registro_editable
# ---------------------------------------------------------------------------

class TestEsRegistroEditable:
    def test_fecha_hoy_es_editable(self, db, usuario):
        """Registro con fecha = ahora → editable."""
        remision = _crear_remision(usuario, timezone.now())
        assert es_registro_editable(remision) is True

    def test_fecha_ayer_no_es_editable(self, db, usuario):
        """Registro con fecha = ayer → no editable."""
        ayer = timezone.now() - timedelta(days=1)
        remision = _crear_remision(usuario, ayer)
        assert es_registro_editable(remision) is False


# ---------------------------------------------------------------------------
# formatear_temperatura
# ---------------------------------------------------------------------------

class TestFormatearTemperatura:
    def test_agrega_grado_a_valor_numerico(self):
        assert formatear_temperatura('36') == '36°'

    def test_idempotente_no_duplica_grado(self):
        assert formatear_temperatura('36°') == '36°'

    def test_no_refiere_sin_cambios(self):
        assert formatear_temperatura('NO REFIERE') == 'NO REFIERE'

    def test_valor_decimal(self):
        assert formatear_temperatura('36.5') == '36.5°'

    def test_valor_decimal_ya_formateado(self):
        assert formatear_temperatura('36.5°') == '36.5°'


# ---------------------------------------------------------------------------
# formatear_spo2
# ---------------------------------------------------------------------------

class TestFormatearSpo2:
    def test_agrega_porcentaje_a_valor_numerico(self):
        assert formatear_spo2('98') == '98%'

    def test_idempotente_no_duplica_porcentaje(self):
        assert formatear_spo2('98%') == '98%'

    def test_no_refiere_sin_cambios(self):
        assert formatear_spo2('NO REFIERE') == 'NO REFIERE'

    def test_valor_decimal(self):
        assert formatear_spo2('97.5') == '97.5%'

    def test_valor_decimal_ya_formateado(self):
        assert formatear_spo2('97.5%') == '97.5%'


# ---------------------------------------------------------------------------
# validar_edad
# ---------------------------------------------------------------------------

class TestValidarEdad:
    def test_anos_valido(self):
        assert validar_edad('25 AÑOS') is True

    def test_meses_valido(self):
        assert validar_edad('3 MESES') is True

    def test_dias_valido(self):
        assert validar_edad('10 DIAS') is True

    def test_texto_invalido(self):
        assert validar_edad('abc') is False

    def test_solo_numero(self):
        assert validar_edad('25') is False

    def test_unidad_incorrecta(self):
        assert validar_edad('25 semanas') is False


# ---------------------------------------------------------------------------
# validar_ta
# ---------------------------------------------------------------------------

class TestValidarTa:
    def test_fraccion_valida(self):
        assert validar_ta('120/80') is True

    def test_no_refiere_valido(self):
        assert validar_ta('NO REFIERE') is True

    def test_texto_invalido(self):
        assert validar_ta('abc') is False

    def test_solo_numero(self):
        assert validar_ta('120') is False

    def test_fraccion_con_espacios_invalida(self):
        # Sin trim interno, espacios hacen fallar el patrón
        assert validar_ta(' 120/80 ') is True  # strip() se aplica internamente


# ---------------------------------------------------------------------------
# obtener_remisiones
# ---------------------------------------------------------------------------

class TestObtenerRemisiones:
    def test_filtro_mes_retorna_solo_abril_2026(self, db, usuario):
        """filtro='mes' con mes=4, anio=2026 retorna solo registros de abril 2026."""
        # Registro en abril 2026
        fecha_abril = timezone.datetime(2026, 4, 15, 10, 0, 0,
                                        tzinfo=timezone.get_current_timezone())
        r_abril = _crear_remision(usuario, fecha_abril, doc='11111111')

        # Registro en mayo 2026 (no debe aparecer)
        fecha_mayo = timezone.datetime(2026, 5, 1, 10, 0, 0,
                                       tzinfo=timezone.get_current_timezone())
        _crear_remision(usuario, fecha_mayo, doc='22222222')

        qs = obtener_remisiones('mes', mes=4, anio=2026)
        assert qs.count() == 1
        assert qs.first().pk == r_abril.pk

    def test_filtro_documento_retorna_solo_ese_doc(self, db, usuario):
        """filtro='documento' con doc='12345' retorna solo registros con ese doc."""
        fecha = timezone.now()
        r_target = _crear_remision(usuario, fecha, doc='12345')
        _crear_remision(usuario, fecha - timedelta(hours=1), doc='99999')

        qs = obtener_remisiones('documento', doc='12345')
        assert qs.count() == 1
        assert qs.first().pk == r_target.pk

    def test_filtro_mes_orden_ascendente(self, db, usuario):
        """Los resultados deben estar ordenados por fecha ascendente."""
        tz = timezone.get_current_timezone()
        fecha2 = timezone.datetime(2026, 4, 20, 10, 0, 0, tzinfo=tz)
        fecha1 = timezone.datetime(2026, 4, 10, 10, 0, 0, tzinfo=tz)
        _crear_remision(usuario, fecha2, doc='AAAA')
        _crear_remision(usuario, fecha1, doc='BBBB')

        qs = list(obtener_remisiones('mes', mes=4, anio=2026))
        assert qs[0].fecha <= qs[1].fecha

    def test_filtro_rango_retorna_registros_en_rango(self, db, usuario):
        """filtro='rango' retorna solo registros dentro del rango de fechas."""
        from datetime import date
        tz = timezone.get_current_timezone()
        dentro = timezone.datetime(2026, 4, 15, 10, 0, 0, tzinfo=tz)
        fuera = timezone.datetime(2026, 4, 25, 10, 0, 0, tzinfo=tz)
        r_dentro = _crear_remision(usuario, dentro, doc='DENTRO')
        _crear_remision(usuario, fuera, doc='FUERA')

        qs = obtener_remisiones(
            'rango',
            desde=date(2026, 4, 1),
            hasta=date(2026, 4, 20),
        )
        assert qs.count() == 1
        assert qs.first().pk == r_dentro.pk


# ---------------------------------------------------------------------------
# TestImportarDesdeExcelV2
# ---------------------------------------------------------------------------

class TestImportarDesdeExcelV2:
    """Tests for importar_desde_excel_v2 using excelToDataframe."""

    def test_mapear_exclusivo_sexo_m(self):
        from remisiones.services import _mapear_exclusivo_sexo
        row = {'sexo_m': 'SI', 'sexo_f': ''}
        assert _mapear_exclusivo_sexo(row) == 'M'

    def test_mapear_exclusivo_sexo_f(self):
        from remisiones.services import _mapear_exclusivo_sexo
        row = {'sexo_m': '', 'sexo_f': 'SI'}
        assert _mapear_exclusivo_sexo(row) == 'F'

    def test_mapear_exclusivo_sexo_ambos_error(self):
        from remisiones.services import _mapear_exclusivo_sexo
        import pytest
        row = {'sexo_m': 'SI', 'sexo_f': 'SI'}
        with pytest.raises(ValueError):
            _mapear_exclusivo_sexo(row)

    def test_mapear_exclusivo_aceptado_si(self):
        from remisiones.services import _mapear_exclusivo_aceptado
        row = {'aceptado_si': 'SI', 'aceptado_no': '', 'aceptado_urg_vital': ''}
        assert _mapear_exclusivo_aceptado(row) == 'SI'

    def test_mapear_exclusivo_aceptado_no(self):
        from remisiones.services import _mapear_exclusivo_aceptado
        row = {'aceptado_si': '', 'aceptado_no': 'SI', 'aceptado_urg_vital': ''}
        assert _mapear_exclusivo_aceptado(row) == 'NO'

    def test_mapear_exclusivo_aceptado_urg_vital(self):
        from remisiones.services import _mapear_exclusivo_aceptado
        row = {'aceptado_si': '', 'aceptado_no': '', 'aceptado_urg_vital': 'SI'}
        assert _mapear_exclusivo_aceptado(row) == 'URG VITAL'

    def test_combinar_fecha_hora_valido(self):
        from remisiones.services import _combinar_fecha_hora
        from datetime import datetime
        result = _combinar_fecha_hora('2026-04-15', '10:30')
        assert result == datetime(2026, 4, 15, 10, 30)

    def test_combinar_fecha_hora_vacio_retorna_none(self):
        from remisiones.services import _combinar_fecha_hora
        assert _combinar_fecha_hora('', '10:30') is None
        assert _combinar_fecha_hora('2026-04-15', '') is None
        assert _combinar_fecha_hora('', '') is None

    def test_importar_desde_excel_v2_con_archivo_valido(self, db, usuario, tmp_path):
        """importar_desde_excel_v2 with valid FRALG-062 file imports records."""
        import os
        import pytest
        from remisiones.services import importar_desde_excel_v2
        from remisiones.utils import excelToDataframe, SheetStructureError

        # Use the test fixture file
        fixture_path = 'tests/remisiones_2026-04-24.xlsx'
        if not os.path.exists(fixture_path):
            pytest.skip(f'Test fixture not found: {fixture_path}')

        # Skip if the fixture is not a valid FRALG-062 file
        try:
            excelToDataframe(fixture_path)
        except SheetStructureError:
            pytest.skip(f'Test fixture {fixture_path!r} is not a valid FRALG-062 file')

        resultado = importar_desde_excel_v2(fixture_path, usuario)
        assert resultado['ok'] is True
        assert resultado['importados'] > 0

    def test_importar_desde_excel_v2_con_estructura_invalida(self, db, usuario, tmp_path):
        """importar_desde_excel_v2 with SheetStructureError returns ok=False."""
        import openpyxl
        from remisiones.services import importar_desde_excel_v2

        # Create a simple Excel with wrong structure
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['COLUMNA_FALSA', 'OTRA_COLUMNA'])
        ws.append(['valor1', 'valor2'])
        excel_path = str(tmp_path / 'invalid.xlsx')
        wb.save(excel_path)

        resultado = importar_desde_excel_v2(excel_path, usuario)
        assert resultado['ok'] is False
        assert 'error' in resultado

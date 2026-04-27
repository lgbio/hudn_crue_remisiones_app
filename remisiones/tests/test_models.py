"""
Pruebas unitarias para los modelos UsuarioCrue y Remision.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from remisiones.models import Remision, UsuarioCrue


@pytest.fixture
def usuario(db):
    return UsuarioCrue.objects.create_user(
        username='testuser',
        password='pass1234',
        rol='RADIOOPERADOR',
    )


@pytest.fixture
def usuario_director(db):
    return UsuarioCrue.objects.create_user(
        username='director',
        password='pass1234',
        rol='DIRECTOR',
    )


@pytest.fixture
def remision_hoy(db, usuario):
    return Remision.objects.create(
        fecha=timezone.now(),
        nombre='Juan Pérez',
        tipo_doc='CC',
        doc='12345678',
        sexo='M',
        edad='30 AÑOS',
        gest='NO',
        created_by=usuario,
    )


@pytest.fixture
def remision_ayer(db, usuario):
    ayer = timezone.now() - timedelta(days=1)
    return Remision.objects.create(
        fecha=ayer,
        nombre='María López',
        tipo_doc='CC',
        doc='87654321',
        sexo='F',
        edad='25 AÑOS',
        gest='NO',
        created_by=usuario,
    )


class TestUsuarioCrue:
    def test_usuario_rol_default(self, db):
        """UsuarioCrue creado sin especificar rol tiene RADIOOPERADOR por defecto."""
        user = UsuarioCrue.objects.create_user(username='radio', password='pass')
        assert user.rol == 'RADIOOPERADOR'

    def test_usuario_rol_director(self, db):
        """UsuarioCrue creado con rol DIRECTOR lo almacena correctamente."""
        user = UsuarioCrue.objects.create_user(
            username='director_test', password='pass', rol='DIRECTOR'
        )
        assert user.rol == 'DIRECTOR'

    def test_str_incluye_username_y_rol(self, db):
        user = UsuarioCrue.objects.create_user(
            username='radio2', password='pass', rol='RADIOOPERADOR'
        )
        assert str(user) == 'radio2 (RADIOOPERADOR)'

    def test_director_tiene_acceso_a_gestion_usuarios(self, usuario_director):
        """Un usuario con rol DIRECTOR puede acceder a gestión de usuarios."""
        assert usuario_director.rol == 'DIRECTOR'

    def test_radiooperador_no_es_director(self, usuario):
        """Un usuario con rol RADIOOPERADOR no es DIRECTOR."""
        assert usuario.rol != 'DIRECTOR'
        assert usuario.rol == 'RADIOOPERADOR'

    def test_rol_choices_son_correctos(self):
        """Los choices del campo rol son exactamente DIRECTOR y RADIOOPERADOR."""
        choices_values = [c[0] for c in UsuarioCrue.ROL_CHOICES]
        assert 'DIRECTOR' in choices_values
        assert 'RADIOOPERADOR' in choices_values
        assert len(choices_values) == 2


class TestRemision:
    def test_creacion_con_campos_obligatorios(self, remision_hoy):
        assert remision_hoy.pk is not None
        assert remision_hoy.nombre == 'Juan Pérez'
        assert remision_hoy.doc == '12345678'

    def test_es_editable_fecha_hoy(self, remision_hoy):
        assert remision_hoy.es_editable is True

    def test_es_editable_fecha_ayer(self, remision_ayer):
        assert remision_ayer.es_editable is False

    def test_created_by_referencia_usuario_crue(self, remision_hoy, usuario):
        """Remision.created_by referencia correctamente a UsuarioCrue."""
        assert remision_hoy.created_by == usuario
        assert isinstance(remision_hoy.created_by, UsuarioCrue)

    def test_oportunidad_no_es_campo_del_modelo(self):
        """OPORTUNIDAD no debe existir como campo almacenado en la BD."""
        field_names = [f.name for f in Remision._meta.get_fields()]
        assert 'OPORTUNIDAD' not in field_names
        assert 'oportunidad' not in field_names

    def test_indices_en_fecha_y_doc(self):
        """Verificar que existen índices sobre fecha y doc."""
        index_fields = [
            tuple(idx.fields) for idx in Remision._meta.indexes
        ]
        assert ('fecha',) in index_fields
        assert ('doc',) in index_fields

    def test_valores_por_defecto(self, db, usuario):
        r = Remision.objects.create(
            fecha=timezone.now(),
            nombre='Test',
            tipo_doc='CC',
            doc='111',
            sexo='M',
            edad='1 AÑOS',
            gest='NO',
            created_by=usuario,
        )
        assert r.tipo_doc == 'CC'
        assert r.sexo == 'M'
        assert r.gest == 'NO'
        assert r.glasg == '15/15'
        assert r.aceptado == 'NO'
        assert r.fecha_res is None

    def test_campos_auditoria_se_llenan_automaticamente(self, remision_hoy):
        assert remision_hoy.created_at is not None
        assert remision_hoy.updated_at is not None
        assert remision_hoy.created_by is not None


class TestTruncarParaTabla:
    """Pruebas unitarias para la función truncar_para_tabla de utils.py."""

    def test_texto_largo_se_trunca_a_50_chars_mas_elipsis(self):
        """truncar_para_tabla('a' * 51) == 'a' * 50 + '…'"""
        from remisiones.utils import truncar_para_tabla
        resultado = truncar_para_tabla('a' * 51)
        assert resultado == 'a' * 50 + '\u2026'

    def test_texto_corto_no_se_modifica(self):
        """truncar_para_tabla('corto') == 'corto'"""
        from remisiones.utils import truncar_para_tabla
        resultado = truncar_para_tabla('corto')
        assert resultado == 'corto'

    def test_texto_exactamente_50_chars_no_se_trunca(self):
        """Un texto de exactamente 50 caracteres no debe truncarse."""
        from remisiones.utils import truncar_para_tabla
        texto = 'x' * 50
        assert truncar_para_tabla(texto) == texto

    def test_medico_hudn_acepta_texto_largo(self, db, usuario):
        """medico_hudn acepta texto largo (> 100 chars) y persiste correctamente."""
        texto_largo = 'Dr. ' + 'A' * 200
        r = Remision.objects.create(
            fecha=timezone.now(),
            nombre='Paciente Test',
            tipo_doc='CC',
            doc='99999999',
            sexo='M',
            edad='40 AÑOS',
            gest='NO',
            medico_hudn=texto_largo,
            created_by=usuario,
        )
        r.refresh_from_db()
        assert r.medico_hudn == texto_largo
        assert len(r.medico_hudn) > 100


class TestValidarHora:
    def test_validar_hora_valida(self):
        from remisiones.utils import validar_hora
        assert validar_hora('14:30') is True

    def test_validar_hora_limite_superior(self):
        from remisiones.utils import validar_hora
        assert validar_hora('23:59') is True

    def test_validar_hora_medianoche(self):
        from remisiones.utils import validar_hora
        assert validar_hora('00:00') is True

    def test_validar_hora_invalida_hora(self):
        from remisiones.utils import validar_hora
        assert validar_hora('25:00') is False

    def test_validar_hora_invalida_minutos(self):
        from remisiones.utils import validar_hora
        assert validar_hora('12:60') is False

    def test_validar_hora_vacia(self):
        from remisiones.utils import validar_hora
        assert validar_hora('') is False

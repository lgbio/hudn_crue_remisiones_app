"""
Pruebas de vistas críticas.
Cubre: login, logout, acceso sin sesión, edición/eliminación de Registro_Historico,
acceso a gestión de usuarios solo para DIRECTOR.
"""
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from remisiones.models import Remision, UsuarioCrue


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return Client()


@pytest.fixture
def usuario_radio(db):
    return UsuarioCrue.objects.create_user(
        username='radio1',
        password='pass1234',
        email='radio@test.com',
        rol='RADIOOPERADOR',
    )


@pytest.fixture
def usuario_director(db):
    return UsuarioCrue.objects.create_user(
        username='director1',
        password='pass1234',
        email='director@test.com',
        rol='DIRECTOR',
    )


@pytest.fixture
def remision_hoy(db, usuario_radio):
    return Remision.objects.create(
        fecha=timezone.now(),
        nombre='Paciente Hoy',
        tipo_doc='CC',
        doc='11111111',
        sexo='M',
        edad='30 AÑOS',
        gest='NO',
        created_by=usuario_radio,
    )


@pytest.fixture
def remision_historica(db, usuario_radio):
    ayer = timezone.now() - timedelta(days=2)
    return Remision.objects.create(
        fecha=ayer,
        nombre='Paciente Histórico',
        tipo_doc='CC',
        doc='22222222',
        sexo='F',
        edad='25 AÑOS',
        gest='NO',
        created_by=usuario_radio,
    )


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_exitoso_redirige_a_main(self, client, usuario_radio):
        resp = client.post('/login/', {'username': 'radio1', 'password': 'pass1234'})
        assert resp.status_code == 302
        assert resp['Location'] == '/'

    def test_login_fallido_no_redirige(self, client, usuario_radio):
        """Login con credenciales incorrectas: no redirige, vuelve al formulario."""
        resp = client.post('/login/', {'username': 'radio1', 'password': 'wrongpass'})
        assert resp.status_code == 200
        # La vista pasa 'error' al contexto — verificamos que no redirige a /
        assert resp.get('Location') != '/'

    def test_acceso_sin_sesion_redirige_a_login(self, client):
        resp = client.get('/')
        assert resp.status_code == 302
        assert '/login/' in resp['Location']

    def test_logout_redirige_a_login(self, client, usuario_radio):
        client.login(username='radio1', password='pass1234')
        resp = client.post('/logout/')
        assert resp.status_code == 302
        assert '/login/' in resp['Location']


# ---------------------------------------------------------------------------
# Edición de Registro_Historico → 403
# ---------------------------------------------------------------------------

class TestEdicionRegistroHistorico:
    def test_editar_registro_historico_retorna_403(self, client, usuario_radio, remision_historica):
        client.login(username='radio1', password='pass1234')
        resp = client.post(
            f'/remisiones/{remision_historica.pk}/editar/',
            {'fecha': '2020-01-01T10:00', 'nombre': 'Cambio'},
            content_type='application/x-www-form-urlencoded',
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data['ok'] is False
        assert 'histórico' in data['error']

    def test_eliminar_registro_historico_retorna_403(self, client, usuario_radio, remision_historica):
        client.login(username='radio1', password='pass1234')
        resp = client.post(f'/remisiones/{remision_historica.pk}/eliminar/')
        assert resp.status_code == 403
        data = resp.json()
        assert data['ok'] is False
        assert 'histórico' in data['error']


# ---------------------------------------------------------------------------
# Gestión de usuarios — solo DIRECTOR
# ---------------------------------------------------------------------------

class TestGestionUsuarios:
    def test_radioperador_no_puede_acceder_a_usuarios(self, client, usuario_radio):
        client.login(username='radio1', password='pass1234')
        resp = client.get('/usuarios/')
        # Debe redirigir a / (no tiene permisos)
        assert resp.status_code == 302
        assert resp['Location'] == '/'

    def test_director_puede_acceder_a_usuarios(self, client, usuario_director):
        client.login(username='director1', password='pass1234')
        resp = client.get('/usuarios/')
        assert resp.status_code == 200

    def test_director_no_puede_eliminarse_a_si_mismo(self, client, usuario_director):
        client.login(username='director1', password='pass1234')
        resp = client.post(f'/usuarios/{usuario_director.pk}/eliminar/')
        assert resp.status_code == 400
        data = resp.json()
        assert data['ok'] is False
        assert 'propio' in data['error']


# ---------------------------------------------------------------------------
# Autollenado de RADIO_OPERADOR — NR-02.1, NR-02.4
# ---------------------------------------------------------------------------

class TestAutorellenadoRadioOperador:
    def test_main_view_incluye_usuario_nombre_completo_en_contexto(self, client, db):
        """GET / incluye usuario_nombre_completo en contexto con nombre completo del usuario."""
        user = UsuarioCrue.objects.create_user(
            username='juanperez',
            password='pass1234',
            email='juan@test.com',
            first_name='Juan',
            last_name='Pérez',
        )
        client.login(username='juanperez', password='pass1234')
        resp = client.get('/')
        assert resp.status_code == 200
        assert resp.context['usuario_nombre_completo'] == 'Juan Pérez'

    def test_main_view_usuario_sin_nombre_retorna_cadena_vacia(self, client, db):
        """GET / retorna cadena vacía en usuario_nombre_completo cuando el usuario no tiene nombre."""
        user = UsuarioCrue.objects.create_user(
            username='sinnombre',
            password='pass1234',
            email='sinnombre@test.com',
        )
        client.login(username='sinnombre', password='pass1234')
        resp = client.get('/')
        assert resp.status_code == 200
        assert resp.context['usuario_nombre_completo'] == ''

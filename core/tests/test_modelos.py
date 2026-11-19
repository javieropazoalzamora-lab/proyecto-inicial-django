"""Modelo PerfilSansano: cálculo del IMC."""
from django.contrib.auth.models import User
from django.test import TestCase

from ..models import PerfilSansano


class ModeloTests(TestCase):
    def test_imc_property(self):
        u = User.objects.create_user('a', 'a@usm.cl', 'x')
        p = PerfilSansano.objects.create(usuario=u, peso=70, altura=1.75)
        self.assertEqual(p.imc, 22.86)

    def test_imc_altura_cero(self):
        u = User.objects.create_user('a', 'a@usm.cl', 'x')
        p = PerfilSansano.objects.create(usuario=u, peso=70, altura=0)
        self.assertIsNone(p.imc)

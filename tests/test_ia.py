import unittest
from unittest.mock import patch

import server
from utils.ollama_service import ServicioIA


class IAEndpointsTest(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_estado_ia(self):
        with patch.object(server.servicio_ia, "estado", return_value={
            "disponible": False,
            "modelo": "llama3.2:1b",
            "fuente": "fallback",
            "mensaje": "Modo sin conexion activo.",
            "error": "Ollama no disponible.",
        }):
            res = self.client.get("/api/ia/estado")
        self.assertEqual(res.status_code, 200)
        datos = res.get_json()
        self.assertFalse(datos["disponible"])
        self.assertEqual(datos["modelo"], "llama3.2:1b")

    def test_chat_con_fallback(self):
        res = self.client.post("/api/ia/chat", json={
            "mensaje": "Necesito una pista",
            "personaje": "El Riviel",
            "materia": "matematicas",
            "nivel": 1,
        })
        self.assertEqual(res.status_code, 200)
        datos = res.get_json()
        self.assertIn("respuesta", datos)
        self.assertIn(datos["fuente"], ("fallback", "ollama", "cache"))

    def test_retroalimentacion(self):
        res = self.client.post("/api/ia/retroalimentacion", json={
            "personaje": "La Tunda",
            "materia": "lenguaje",
            "nivel": 2,
            "puntaje": 80,
        })
        self.assertEqual(res.status_code, 200)
        datos = res.get_json()
        self.assertIn("respuesta", datos)
        self.assertIn("fuente", datos)

    def test_pista(self):
        res = self.client.post("/api/ia/pista", json={
            "personaje": "El Duende",
            "materia": "ingles",
            "nivel": 1,
            "instruccion": "Toca los objetos azules",
            "minijuego": "point_and_click",
        })
        self.assertEqual(res.status_code, 200)
        datos = res.get_json()
        self.assertIn("respuesta", datos)
        self.assertIn("fuente", datos)


class ServicioIATest(unittest.TestCase):
    def test_servicio_usa_fallback_si_ollama_falla(self):
        servicio = ServicioIA(modelo="modelo-inexistente", url="http://127.0.0.1:9")
        resultado = servicio.generar_respuesta(
            personaje="El Riviel",
            mensaje="hola",
            contexto_materia="matematicas",
            contexto_nivel=1,
        )
        self.assertEqual(resultado["fuente"], "fallback")
        self.assertTrue(resultado["respuesta"])


if __name__ == "__main__":
    unittest.main()

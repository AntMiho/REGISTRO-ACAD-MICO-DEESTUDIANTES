"""Pruebas de las 10 funcionalidades del proyecto."""


def test_crear_y_listar(cliente, estudiante_base):
    resp = cliente.post("/estudiantes", json=estudiante_base)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["_id"] is not None
    assert body["contacto"]["telefono"] == "+595981123456"
    assert "Programación I" in body["materias"]

    resp = cliente.get("/estudiantes")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_obtener_por_id_y_404(cliente, estudiante_base):
    _id = cliente.post("/estudiantes", json=estudiante_base).json()["_id"]
    resp = cliente.get(f"/estudiantes/{_id}")
    assert resp.status_code == 200
    assert resp.json()["apellido"] == "González"

    resp = cliente.get("/estudiantes/9999")
    assert resp.status_code == 404


def test_modificar_parcial(cliente, estudiante_base):
    _id = cliente.post("/estudiantes", json=estudiante_base).json()["_id"]
    resp = cliente.patch(f"/estudiantes/{_id}", json={"semestre": 6})
    assert resp.status_code == 200
    assert resp.json()["semestre"] == 6
    assert resp.json()["nombre"] == "María"  # lo demás no cambia


def test_eliminar(cliente, estudiante_base):
    _id = cliente.post("/estudiantes", json=estudiante_base).json()["_id"]
    assert cliente.delete(f"/estudiantes/{_id}").status_code == 200
    assert cliente.get(f"/estudiantes/{_id}").status_code == 404


def test_buscar_por_nombre_apellido_ci(cliente, estudiante_base):
    cliente.post("/estudiantes", json=estudiante_base)
    for q in ("Mar", "Gonz", "4812"):
        resp = cliente.get("/estudiantes/buscar", params={"q": q})
        assert resp.status_code == 200
        assert len(resp.json()) == 1


def test_filtro_carrera_semestre_estado(cliente, estudiante_base):
    cliente.post("/estudiantes", json=estudiante_base)
    r = cliente.get("/estudiantes/filtro", params={"carrera": "ingeniería informática"})
    assert r.status_code == 200 and len(r.json()) == 1

    r = cliente.get("/estudiantes/filtro", params={"semestre": 5})
    assert r.status_code == 200 and len(r.json()) == 1

    r = cliente.get("/estudiantes/filtro", params={"estado": "activo"})
    assert r.status_code == 200 and len(r.json()) == 1

    r = cliente.get("/estudiantes/filtro", params={"estado": "retirado"})
    assert r.status_code == 422


def test_estudiantes_por_materia(cliente, estudiante_base):
    cliente.post("/estudiantes", json=estudiante_base)
    r = cliente.get("/estudiantes/materia", params={"materia": "Programación I"})
    assert r.status_code == 200 and len(r.json()) == 1

    r = cliente.get("/estudiantes/materia", params={"materia": "Química"})
    assert r.status_code == 200 and len(r.json()) == 0


def test_validaciones_unicidad_y_errores(cliente, estudiante_base):
    cliente.post("/estudiantes", json=estudiante_base)
    # CI duplicada -> 409
    duplicado = {**estudiante_base, "email": "otro@uni.edu"}
    assert cliente.post("/estudiantes", json=duplicado).status_code == 409
    # Email inválido -> 422
    malo = {**estudiante_base, "ci": "9999999", "email": "no-es-email"}
    assert cliente.post("/estudiantes", json=malo).status_code == 422
    # Semestre fuera de rango -> 422
    malo = {**estudiante_base, "ci": "8888888", "email": "x@uni.edu", "semestre": 15}
    assert cliente.post("/estudiantes", json=malo).status_code == 422
    # Contacto faltante -> 422
    sin_contacto = {k: v for k, v in estudiante_base.items() if k != "contacto"}
    sin_contacto.update({"ci": "7777777", "email": "y@uni.edu"})
    assert cliente.post("/estudiantes", json=sin_contacto).status_code == 422

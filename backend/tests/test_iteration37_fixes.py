# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Backend tests for iteration 37:
- Auth dependency fix in users.py / settings.py / products.py (no more 500s)
- Settings PUT preserves logo
- CRM contacts isolation (admin vs non-admin)
- DELETE /clients/{id} behavior (linked users + ?force=true)
- /digitalizador/history endpoint
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://erp-home-kitchen.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_USER = "mario@luiggihome.es"
ADMIN_PASS = "Mario2025*"


# ---------------------------- Fixtures ----------------------------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=20)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    token = (
        data.get("accessToken")
        or data.get("token")
        or (data.get("tokens") or {}).get("accessToken")
        or (data.get("tokens") or {}).get("access_token")
    )
    assert token, f"No access token returned: {data}"
    return token


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def rep_user(admin_headers):
    """Create a temporary non-admin (representative) user for CRM isolation testing"""
    suffix = uuid.uuid4().hex[:6]
    username = f"TEST_rep_{suffix}@luiggihome.test"
    password = "RepTest2025*"
    payload = {
        "username": username,
        "password": password,
        "clientName": "TEST Rep",
        "isAdmin": False,
        "isRepresentative": True,
        "canAccessCRM": True,
    }
    r = requests.post(f"{API}/users", json=payload, headers=admin_headers, timeout=20)
    assert r.status_code in (200, 201), f"Create rep failed: {r.status_code} {r.text}"
    user = r.json()
    user_id = user.get("id")

    # login as that rep
    lr = requests.post(f"{API}/auth/login", json={"username": username, "password": password}, timeout=20)
    assert lr.status_code == 200, f"Rep login failed: {lr.status_code} {lr.text}"
    ld = lr.json()
    rep_token = (
        ld.get("accessToken")
        or ld.get("token")
        or (ld.get("tokens") or {}).get("accessToken")
        or (ld.get("tokens") or {}).get("access_token")
    )
    assert rep_token, f"No token for rep: {ld}"

    yield {"id": user_id, "username": username, "token": rep_token,
           "headers": {"Authorization": f"Bearer {rep_token}", "Content-Type": "application/json"}}

    # cleanup
    requests.delete(f"{API}/users/{user_id}", headers=admin_headers, timeout=20)


# ---------------------------- 1. /users ----------------------------
def test_get_users_200(admin_headers):
    r = requests.get(f"{API}/users", headers=admin_headers, timeout=20)
    assert r.status_code == 200, f"GET /users failed: {r.status_code} {r.text}"
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0
    # no password should be returned
    assert all("password" not in u for u in body)


def test_get_users_no_auth_returns_401(admin_headers):
    r = requests.get(f"{API}/users", timeout=20)
    assert r.status_code in (401, 403), f"Expected 401/403 without auth, got {r.status_code}"


# ---------------------------- 2. /settings ----------------------------
def test_get_settings_200(admin_headers):
    r = requests.get(f"{API}/settings", headers=admin_headers, timeout=20)
    assert r.status_code == 200, f"GET /settings failed: {r.status_code} {r.text}"
    body = r.json()
    assert isinstance(body, dict)


def test_put_settings_preserves_logo(admin_headers):
    """PUT with only companyName must NOT erase previously saved logo"""
    # 1) Save a fake logo (small base64)
    fake_logo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    r1 = requests.put(f"{API}/settings", json={"logo": fake_logo}, headers=admin_headers, timeout=20)
    assert r1.status_code == 200, f"Failed to set logo: {r1.status_code} {r1.text}"
    assert r1.json().get("logo") == fake_logo

    # 2) Update ONLY companyName -> logo must persist
    new_name = f"TEST Persistence {uuid.uuid4().hex[:4]}"
    r2 = requests.put(f"{API}/settings", json={"companyName": new_name}, headers=admin_headers, timeout=20)
    assert r2.status_code == 200, f"Failed updating companyName: {r2.status_code} {r2.text}"
    body = r2.json()
    assert body.get("companyName") == new_name
    assert body.get("logo") == fake_logo, "Logo was erased after PUT without logo field!"

    # 3) GET /settings re-check persistence
    r3 = requests.get(f"{API}/settings", headers=admin_headers, timeout=20)
    assert r3.status_code == 200
    assert r3.json().get("logo") == fake_logo


# ---------------------------- 3. /products ----------------------------
def test_get_products_200(admin_headers):
    r = requests.get(f"{API}/products", headers=admin_headers, timeout=30)
    assert r.status_code == 200, f"GET /products failed: {r.status_code} {r.text}"


# ---------------------------- 4. /digitalizador/history ----------------------------
def test_get_digitalizador_history_200(admin_headers):
    r = requests.get(f"{API}/digitalizador/history", headers=admin_headers, timeout=20)
    assert r.status_code == 200, f"GET /digitalizador/history failed: {r.status_code} {r.text}"
    body = r.json()
    assert body.get("success") is True
    assert "history" in body
    assert isinstance(body["history"], list)


# ---------------------------- 5. CRM contacts isolation ----------------------------
def test_admin_sees_all_contacts(admin_headers):
    r = requests.get(f"{API}/crm/contacts", headers=admin_headers, timeout=20)
    assert r.status_code == 200, f"GET /crm/contacts admin: {r.status_code} {r.text}"
    assert isinstance(r.json(), list)


def test_post_contact_assigns_created_by_user_id(rep_user):
    payload = {
        "name": f"TEST Contact {uuid.uuid4().hex[:5]}",
        "company": "TEST Co",
        "email": "test@example.com",
        "phone": "600000000",
    }
    r = requests.post(f"{API}/crm/contacts", json=payload, headers=rep_user["headers"], timeout=20)
    assert r.status_code in (200, 201), f"POST contact failed: {r.status_code} {r.text}"
    body = r.json()
    assert body.get("createdByUserId") == rep_user["id"], (
        f"createdByUserId expected {rep_user['id']} got {body.get('createdByUserId')}"
    )
    # Should also auto-assign assignedToId to creator if not provided
    assert body.get("assignedToId") == rep_user["id"]
    return body.get("id")


def test_rep_only_sees_own_contacts(admin_headers, rep_user):
    # Create a contact as admin (NOT belonging to rep)
    admin_contact_payload = {
        "name": f"TEST AdminContact {uuid.uuid4().hex[:5]}",
        "company": "TEST AdminCo",
    }
    cr = requests.post(f"{API}/crm/contacts", json=admin_contact_payload, headers=admin_headers, timeout=20)
    assert cr.status_code in (200, 201), f"Admin create contact: {cr.status_code} {cr.text}"
    admin_contact_id = cr.json().get("id")

    # Create a contact as rep
    rep_contact_payload = {
        "name": f"TEST RepContact {uuid.uuid4().hex[:5]}",
        "company": "TEST RepCo",
    }
    rr = requests.post(f"{API}/crm/contacts", json=rep_contact_payload, headers=rep_user["headers"], timeout=20)
    assert rr.status_code in (200, 201), f"Rep create contact: {rr.status_code} {rr.text}"
    rep_contact_id = rr.json().get("id")

    # Rep listing should ONLY include their own
    lr = requests.get(f"{API}/crm/contacts", headers=rep_user["headers"], timeout=20)
    assert lr.status_code == 200, f"Rep GET contacts: {lr.status_code} {lr.text}"
    contacts = lr.json()
    ids = [c.get("id") for c in contacts]
    assert rep_contact_id in ids, "Rep does not see own contact"
    assert admin_contact_id not in ids, "Isolation BROKEN: rep can see admin's contact!"

    # Every contact must belong to the rep
    for c in contacts:
        assert (c.get("createdByUserId") == rep_user["id"]) or (c.get("assignedToId") == rep_user["id"]), \
            f"Contact {c.get('id')} not owned by rep: createdBy={c.get('createdByUserId')} assignedTo={c.get('assignedToId')}"

    # Cleanup
    requests.delete(f"{API}/crm/contacts/{admin_contact_id}", headers=admin_headers, timeout=20)
    requests.delete(f"{API}/crm/contacts/{rep_contact_id}", headers=admin_headers, timeout=20)


# ---------------------------- 6. DELETE /clients/{id} ----------------------------
@pytest.fixture
def temp_client_in_db(admin_headers):
    """Create a client directly in MongoDB to bypass the broken POST /clients endpoint.
    POST /clients is currently broken (references nonexistent 'codigo' field on ClientCreate).
    We still want to validate the DELETE behavior (force flag, error message)."""
    import pymongo
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "luiggi_home")
    mclient = pymongo.MongoClient(mongo_url)
    mdb = mclient[db_name]
    cid = f"cli-test-{uuid.uuid4().hex[:8]}"
    doc = {
        "id": cid,
        "code": "",
        "codigo": "",
        "name": f"TEST DeleteClient {uuid.uuid4().hex[:5]}",
        "company": "",
        "email": "",
        "phone": "",
        "address": "",
        "status": "potential",
        "segment": "particular",
    }
    mdb.clients.insert_one(doc)
    yield cid
    # cleanup if still there
    mdb.clients.delete_one({"id": cid})
    mclient.close()


def test_delete_client_with_linked_users_requires_force(admin_headers, temp_client_in_db):
    client_id = temp_client_in_db
    # Create a user linked to that client
    suffix = uuid.uuid4().hex[:5]
    uname = f"TEST_link_{suffix}@luiggihome.test"
    ur = requests.post(f"{API}/users", json={
        "username": uname, "password": "Pwd2025*", "isTienda": True
    }, headers=admin_headers, timeout=20)
    assert ur.status_code in (200, 201), f"Create user: {ur.status_code} {ur.text}"
    user_id = ur.json().get("id")

    # Link the user to the client (use link-user endpoint with direct DB write)
    import pymongo
    mclient = pymongo.MongoClient(os.environ.get("MONGO_URL"))
    mdb = mclient[os.environ.get("DB_NAME", "luiggi_home")]
    mdb.users.update_one({"id": user_id}, {"$set": {"linkedClientId": client_id}})
    mclient.close()

    # Try delete WITHOUT force -> should 400
    dr = requests.delete(f"{API}/clients/{client_id}", headers=admin_headers, timeout=20)
    assert dr.status_code == 400, f"Expected 400 with linked users, got {dr.status_code} {dr.text}"
    assert "vinculado" in dr.text.lower(), f"Error message missing 'vinculado': {dr.text}"

    # Try delete WITH force -> should succeed
    dr2 = requests.delete(f"{API}/clients/{client_id}?force=true", headers=admin_headers, timeout=20)
    assert dr2.status_code == 200, f"Force delete failed: {dr2.status_code} {dr2.text}"

    # Verify client gone
    gr = requests.get(f"{API}/clients/{client_id}", headers=admin_headers, timeout=20)
    assert gr.status_code == 404, f"Client should be 404 after delete, got {gr.status_code}"

    # Cleanup user
    requests.delete(f"{API}/users/{user_id}", headers=admin_headers, timeout=20)


def test_delete_client_no_links(admin_headers, temp_client_in_db):
    client_id = temp_client_in_db
    dr = requests.delete(f"{API}/clients/{client_id}", headers=admin_headers, timeout=20)
    assert dr.status_code == 200, f"Delete unlinked client failed: {dr.status_code} {dr.text}"


def test_post_clients_spanish_payload(admin_headers):
    """POST /clients with Spanish field names {nombre, codigo, cif, ...} -> 200"""
    suffix = uuid.uuid4().hex[:6].upper()
    payload = {
        "nombre": f"TEST ClienteESP {suffix}",
        "codigo": f"TESTESP{suffix}",
        "cif": "B12345678",
        "direccion": "Calle Falsa 123",
        "localidad": "Madrid",
        "provincia": "Madrid",
        "codigoPostal": "28001",
        "telefono": "600111222",
        "descuento": 5,
        "activo": True,
        "notas": "TEST cliente español",
    }
    r = requests.post(f"{API}/clients", json=payload, headers=admin_headers, timeout=20)
    assert r.status_code in (200, 201), f"POST /clients ES failed: {r.status_code} {r.text}"
    body = r.json()
    assert body.get("nombre") == payload["nombre"], f"nombre mismatch: {body}"
    assert body.get("codigo") == payload["codigo"].upper(), f"codigo not uppercased: {body.get('codigo')}"
    assert body.get("cif") == payload["cif"]
    assert body.get("direccion") == payload["direccion"]
    assert "id" in body and body["id"].startswith("cli-")

    # Cleanup
    requests.delete(f"{API}/clients/{body['id']}?force=true", headers=admin_headers, timeout=20)


def test_post_clients_english_payload_normalized(admin_headers):
    """POST /clients with English field names {name, code, taxId, address, ...} -> 200 (normalized to ES)"""
    suffix = uuid.uuid4().hex[:6].upper()
    payload = {
        "name": f"TEST ClientENG {suffix}",
        "code": f"TESTENG{suffix}",
        "taxId": "B87654321",
        "address": "Fake Street 99",
        "city": "Barcelona",
        "province": "Barcelona",
        "postalCode": "08001",
        "phone": "600999888",
        "discount": 10,
        "active": True,
        "notes": "TEST english normalized",
    }
    r = requests.post(f"{API}/clients", json=payload, headers=admin_headers, timeout=20)
    assert r.status_code in (200, 201), f"POST /clients EN failed: {r.status_code} {r.text}"
    body = r.json()
    # Should normalize to Spanish field names
    assert body.get("nombre") == payload["name"], f"name->nombre mapping failed: {body}"
    assert body.get("codigo") == payload["code"].upper(), f"code->codigo mapping failed: {body}"
    assert body.get("cif") == payload["taxId"], f"taxId->cif mapping failed: {body}"
    assert body.get("direccion") == payload["address"]
    assert body.get("telefono") == payload["phone"]
    assert "id" in body and body["id"].startswith("cli-")

    # Cleanup
    requests.delete(f"{API}/clients/{body['id']}?force=true", headers=admin_headers, timeout=20)


def test_post_clients_duplicate_codigo_returns_400(admin_headers):
    """POST /clients with a codigo that already exists -> 400"""
    suffix = uuid.uuid4().hex[:6].upper()
    codigo = f"TESTDUP{suffix}"
    payload = {"nombre": f"TEST Dup1 {suffix}", "codigo": codigo}
    r1 = requests.post(f"{API}/clients", json=payload, headers=admin_headers, timeout=20)
    assert r1.status_code in (200, 201), f"First create failed: {r1.status_code} {r1.text}"
    cid = r1.json().get("id")

    # Second attempt with same codigo
    r2 = requests.post(f"{API}/clients",
                       json={"nombre": f"TEST Dup2 {suffix}", "codigo": codigo},
                       headers=admin_headers, timeout=20)
    assert r2.status_code == 400, f"Expected 400 on duplicate codigo, got {r2.status_code} {r2.text}"

    # Cleanup
    requests.delete(f"{API}/clients/{cid}?force=true", headers=admin_headers, timeout=20)

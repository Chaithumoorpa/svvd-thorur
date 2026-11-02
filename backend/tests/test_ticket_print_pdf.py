"""GET /seva-tickets/{id}/print and /pdf - only the underlying HTML template
(SevaTicketService.generate_ticket_html) is unit-tested elsewhere
(test_seva_ticket_printing.py); these hit the actual HTTP endpoints for
permission gating, the response itself, and the not-found edge case."""
import uuid
from datetime import date, timedelta


def _ticket(client, headers):
    pooja = client.post("/api/v1/poojas/", headers=headers,
                        json={"name": "Print Test Archana", "is_paid": False}).json()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return client.post("/api/v1/seva-tickets/admin", headers=headers, json={
        "seva_id": pooja["id"], "devotee_name": "Ravi", "mobile_number": "9876543210",
        "seva_date": tomorrow, "payment_status": "FREE", "amount": 0,
    }).json()


def test_print_ticket_html(client, admin, trustee):
    _, headers = admin
    ticket = _ticket(client, headers)

    r = client.get(f"/api/v1/seva-tickets/{ticket['id']}/print", headers=headers)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert ticket["ticket_number"] in r.text
    assert "onclick=\"window.print()\"" in r.text  # the print button is injected

    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}/print", headers={}).status_code == 401
    _, trustee_headers = trustee
    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}/print", headers=trustee_headers).status_code == 403

    assert client.get(f"/api/v1/seva-tickets/{uuid.uuid4()}/print", headers=headers).status_code == 404


def test_get_ticket_pdf(client, admin, trustee):
    _, headers = admin
    ticket = _ticket(client, headers)

    printed = client.get(f"/api/v1/seva-tickets/{ticket['id']}/pdf", headers=headers)
    assert printed.status_code == 200
    assert printed.content.startswith(b"%PDF")
    assert "inline" in printed.headers["content-disposition"]

    downloaded = client.get(f"/api/v1/seva-tickets/{ticket['id']}/pdf?action=download", headers=headers)
    assert downloaded.status_code == 200
    assert "attachment" in downloaded.headers["content-disposition"]
    assert ticket["ticket_number"] in downloaded.headers["content-disposition"]

    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}/pdf", headers={}).status_code == 401
    _, trustee_headers = trustee
    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}/pdf", headers=trustee_headers).status_code == 403

    assert client.get(f"/api/v1/seva-tickets/{uuid.uuid4()}/pdf", headers=headers).status_code == 404


def test_get_ticket_pdf_rejects_bad_action_value(client, admin):
    _, headers = admin
    ticket = _ticket(client, headers)
    r = client.get(f"/api/v1/seva-tickets/{ticket['id']}/pdf?action=delete-everything", headers=headers)
    assert r.status_code == 422


def test_get_ticket_details_permission_and_404(client, admin, trustee):
    _, headers = admin
    ticket = _ticket(client, headers)

    ok = client.get(f"/api/v1/seva-tickets/{ticket['id']}", headers=headers)
    assert ok.status_code == 200 and ok.json()["id"] == ticket["id"]

    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}", headers={}).status_code == 401
    _, trustee_headers = trustee
    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}", headers=trustee_headers).status_code == 403
    assert client.get(f"/api/v1/seva-tickets/{uuid.uuid4()}", headers=headers).status_code == 404

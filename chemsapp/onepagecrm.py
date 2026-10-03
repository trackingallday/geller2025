"""Shared helper for pushing leads into OnePageCRM (v3 API).

Used by chemsapp (website contact form, SDS downloads) and reports (Site
Assessment submissions) so every lead source authenticates and shapes
contacts/notes the same way.
"""
import requests
from django.conf import settings


def create_contact_with_note(name, email, note_text, tags, company_name=''):
    """Create (or let OnePageCRM dedupe) a contact and attach a note. Returns the
    contact id. Auth is HTTP Basic (user_id : api_key). Raises RuntimeError with the
    HTTP body on any non-OK response so callers can log a useful reason.
    """
    base = settings.ONEPAGECRM_ENDPOINT.rstrip('/')
    auth = (settings.ONEPAGECRM_USER_ID, settings.ONEPAGECRM_API_KEY)

    # Split the single "name" field into first/last for OnePageCRM.
    full_name = (name or '').strip()
    first_name, _, last_name = full_name.partition(' ')
    if not first_name:
        first_name = full_name or 'Unknown'

    contact_payload = {
        'first_name': first_name,
        'last_name': last_name,
        'company_name': company_name or '',
        'emails': [{'type': 'work', 'value': email or ''}],
        'tags': tags,
    }
    create_resp = requests.post(
        base + '/contacts.json', json=contact_payload, auth=auth, timeout=10,
    )
    if not create_resp.ok:
        raise RuntimeError('create contact failed: HTTP {} {}'.format(
            create_resp.status_code, create_resp.text[:500]))
    contact_id = create_resp.json()['data']['contact']['id']

    if note_text:
        note_resp = requests.post(
            base + '/contacts/{}/notes.json'.format(contact_id),
            json={'contact_id': contact_id, 'text': note_text}, auth=auth, timeout=10,
        )
        if not note_resp.ok:
            raise RuntimeError('add note failed: HTTP {} {}'.format(
                note_resp.status_code, note_resp.text[:500]))
    return contact_id

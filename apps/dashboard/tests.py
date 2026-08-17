from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.masters.models import Event, Upashray
from apps.requirements.models import RequirementHeader
from apps.accounts.context_processors import portal_navigation
from django.test import RequestFactory


class InactiveEventAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="admin1", password="pass", is_superuser=True)
        self.client.force_login(self.user)
        self.active = Event.objects.create(name="Active", slug="e-active", start_date="2026-01-01", end_date="2026-12-31", is_current=True, is_active=True)
        self.inactive = Event.objects.create(name="Past", slug="e-past", start_date="2025-01-01", end_date="2025-12-31", is_current=False, is_active=False)
        self.rf = RequestFactory()

    def test_sidebar_lists_inactive_event(self):
        req = self.rf.get("/")
        req.user = self.user
        nav = portal_navigation(req)
        pks = [b["event"].pk for b in nav["sidebar_events"]]
        self.assertIn(self.inactive.pk, pks)
        block = [b for b in nav["sidebar_events"] if b["event"].pk == self.inactive.pk][0]
        self.assertFalse(block["is_active"])

    def test_selected_event_resolves_inactive(self):
        req = self.rf.get(f"/?event={self.inactive.pk}")
        req.user = self.user
        nav = portal_navigation(req)
        self.assertEqual(nav["sidebar_selected_event"].pk, self.inactive.pk)

    def test_requirement_list_shows_inactive_event_data(self):
        up = Upashray.objects.create(event=self.inactive, name="Upashray Past")
        rh = RequirementHeader.objects.create(event=self.inactive, volunteer_name="Past Volunteer", upashray=up)
        resp = self.client.get(f"/requirements/?event={self.inactive.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Past Volunteer")

    def test_requirement_list_defaults_to_current(self):
        up = Upashray.objects.create(event=self.active, name="Upashray Active")
        RequirementHeader.objects.create(event=self.active, volunteer_name="Active Volunteer", upashray=up)
        resp = self.client.get("/requirements/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Active Volunteer")

    def test_dashboard_home_accepts_event_param(self):
        resp = self.client.get(f"/dashboard/home/?event={self.inactive.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Past")

    def test_chaturmas_dashboard_accepts_event_param(self):
        resp = self.client.get(f"/dashboard/chaturmas/?event={self.inactive.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Past")

    def test_dashboard_api_accepts_event_param(self):
        resp = self.client.get(f"/dashboard/api/data/?event={self.inactive.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("records", resp.json())

    def test_item_control_center_accepts_inactive_event(self):
        resp = self.client.get(f"/?event={self.inactive.pk}")
        self.assertEqual(resp.status_code, 200)

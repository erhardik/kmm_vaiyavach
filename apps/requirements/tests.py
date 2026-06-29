from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.masters.models import Event, Item, ItemCategory, Upashray
from apps.requirements.models import RequirementHeader, RequirementLine, RequirementStatus


class RequirementCollectionFlowTest(TestCase):
    """QA tests for the collect form flow, focusing on multi-form scenarios."""

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            name="Test Event",
            slug="test-event",
            start_date="2026-06-01",
            end_date="2026-06-30",
            is_current=True,
            is_active=True,
        )
        cls.upashray = Upashray.objects.create(event=cls.event, name="Test Upashray")
        # Create items matching a realistic count
        cls.items = []
        for i in range(5):
            item = Item.objects.create(
                event=cls.event,
                item_code=f"ITM{i+1:03d}",
                item_name=f"Test Item {i+1}",
                category=ItemCategory.GENERAL,
                standard_serial=i + 1,
            )
            cls.items.append(item)
        cls.client = Client()
        cls.base_data = {
            "upashray_name": "Test Upashray",
            "route_area": "A1",
            "route_sub_area": "A1-SUB-1",
            "form_number": "",
            "requirement_date": "2026-06-28",
            "volunteer_name": "Test Volunteer",
            "volunteer_mobile": "9876543210",
            "pujya_shri_name": "Test Saint",
            "pujya_shri_mobile": "9876543211",
            "current_address": "Test Address",
            "thana_count": "1",
            "area": "Test Area",
            "chaturmas_place_address": "Test Chaturmas Address",
            "chaturmas_entry_date": "2026-06-28",
            "caretaker_name": "Test Caretaker",
            "caretaker_mobile": "9876543212",
            "stay_type": "STHIRVAS",
        }

    def _get_formset_data(self, qty_map=None):
        """Build formset POST data for all 5 items + 4 extra forms."""
        data = {}
        qty_map = qty_map or {}
        total = len(self.items) + 4
        data["items-TOTAL_FORMS"] = str(total)
        data["items-INITIAL_FORMS"] = "0"
        data["items-MIN_NUM_FORMS"] = "0"
        data["items-MAX_NUM_FORMS"] = "1000"
        for i, item in enumerate(self.items):
            data[f"items-{i}-item_id"] = str(item.pk)
            data[f"items-{i}-required_qty"] = str(qty_map.get(item.pk, ""))
        for i in range(len(self.items), total):
            data[f"items-{i}-item_id"] = ""
            data[f"items-{i}-required_qty"] = ""
        return data

    def _full_post_data(self, extra=None, qty_map=None):
        data = {}
        data.update(self.base_data)
        data.update(self._get_formset_data(qty_map))
        if extra:
            data.update(extra)
        return data

    # ── Test 1: First form - save details then confirm ──────────────

    def test_first_form_save_and_confirm(self):
        """First form: save_details sets NOT_CONFIRMED, confirm sets CONFIRMED."""
        resp = self.client.get(reverse("requirements:collect"))
        self.assertEqual(resp.status_code, 200)

        # Save details
        post_data = self._full_post_data({"save_details": "1"})
        resp = self.client.post(reverse("requirements:collect"), post_data)
        self.assertEqual(resp.status_code, 200)
        header = RequirementHeader.objects.filter(
            event=self.event, volunteer_name="Test Volunteer"
        ).first()
        self.assertIsNotNone(header)
        self.assertEqual(header.status, RequirementStatus.NOT_CONFIRMED)

        # Confirm with quantities - POST to edit URL with pk in URL
        qty_map = {self.items[0].pk: 5, self.items[1].pk: 3}
        post_data = self._full_post_data({"confirm": "1"}, qty_map)
        resp = self.client.post(
            reverse("requirements:collect-edit", kwargs={"pk": header.pk}),
            post_data
        )
        header.refresh_from_db()
        self.assertEqual(header.status, RequirementStatus.CONFIRMED)

    # ── Test 2: Second form with same route/sub-route ───────────────

    def test_second_form_same_route(self):
        """Second form with same route/sub-route: should save and confirm."""
        # First form - direct confirm (new form, no prior save)
        qty_map = {self.items[0].pk: 5}
        post_data = self._full_post_data(
            {"confirm": "1", "volunteer_name": "Volunteer One",
             "form_number": "F001"}, qty_map
        )
        resp = self.client.post(reverse("requirements:collect"), post_data)
        self.assertEqual(RequirementHeader.objects.count(), 1)
        h1 = RequirementHeader.objects.first()
        self.assertEqual(h1.status, RequirementStatus.CONFIRMED)

        # Second form - save details first
        post_data2 = self._full_post_data(
            {"save_details": "1", "volunteer_name": "Volunteer Two",
             "form_number": "F002"},
            {self.items[0].pk: 10}
        )
        resp = self.client.post(reverse("requirements:collect"), post_data2)
        self.assertEqual(RequirementHeader.objects.count(), 2)
        h2 = RequirementHeader.objects.exclude(pk=h1.pk).first()
        self.assertIsNotNone(h2)
        self.assertEqual(h2.status, RequirementStatus.NOT_CONFIRMED)
        self.assertEqual(h2.route_area, "A1")
        self.assertEqual(h2.route_sub_area, "A1-SUB-1")

        # Confirm second form via edit URL with pk
        post_data3 = self._full_post_data(
            {"confirm": "1", "volunteer_name": "Volunteer Two",
             "form_number": "F002"},
            {self.items[0].pk: 10}
        )
        resp = self.client.post(
            reverse("requirements:collect-edit", kwargs={"pk": h2.pk}),
            post_data3
        )
        h2.refresh_from_db()
        self.assertEqual(h2.status, RequirementStatus.CONFIRMED)

    # ── Test 3: Second form with same form_number ───────────────────

    def test_second_form_same_form_number(self):
        """Multiple forms can share the same form_number."""
        qty_map = {self.items[0].pk: 5}
        # First form - direct confirm via collect (no pk URL)
        post_data = self._full_post_data(
            {"confirm": "1", "volunteer_name": "V1", "form_number": "KH01"}, qty_map
        )
        resp = self.client.post(reverse("requirements:collect"), post_data)
        self.assertEqual(resp.status_code, 302)
        h1 = RequirementHeader.objects.get(volunteer_name="V1")
        self.assertEqual(h1.status, RequirementStatus.CONFIRMED)

        # Second form with same form_number
        post_data2 = self._full_post_data(
            {"confirm": "1", "volunteer_name": "V2", "form_number": "KH01"}, qty_map
        )
        resp = self.client.post(reverse("requirements:collect"), post_data2)
        self.assertEqual(resp.status_code, 302)
        h2 = RequirementHeader.objects.get(volunteer_name="V2")
        self.assertEqual(h2.status, RequirementStatus.CONFIRMED)
        self.assertEqual(h2.form_number, "KH01")

    # ── Test 4: Locked header blocks non-superuser ──────────────────

    def test_locked_header_blocked_for_non_superuser(self):
        """A locked header cannot be edited by non-superuser."""
        header = RequirementHeader.objects.create(
            event=self.event, upashray=self.upashray,
            volunteer_name="Locked",
            status=RequirementStatus.NOT_CONFIRMED, is_locked=True,
        )
        post_data = self._full_post_data(
            {"save_details": "1", "volunteer_name": "Locked"}
        )
        resp = self.client.post(
            reverse("requirements:collect-edit", kwargs={"pk": header.pk}),
            post_data
        )
        header.refresh_from_db()
        # Should still be NOT_CONFIRMED (not advanced)
        self.assertEqual(header.status, RequirementStatus.NOT_CONFIRMED)

    # ── Test 5: Superuser can edit locked header ────────────────────

    def test_superuser_can_edit_locked_header(self):
        """A superuser can save a locked header."""
        User.objects.create_superuser("admin", "admin@test.com", "testpass")
        self.client.login(username="admin", password="testpass")
        header = RequirementHeader.objects.create(
            event=self.event, upashray=self.upashray,
            volunteer_name="Locked",
            status=RequirementStatus.NOT_CONFIRMED, is_locked=True,
        )
        post_data = self._full_post_data(
            {"save_details": "1", "volunteer_name": "Locked Edited"}
        )
        resp = self.client.post(
            reverse("requirements:collect-edit", kwargs={"pk": header.pk}),
            post_data
        )
        header.refresh_from_db()
        self.assertEqual(header.pujya_shri_name, "Test Saint")

    # ── Test 6: Status blocks editing after CONFIRMED ───────────────

    def test_editing_blocked_after_confirmed(self):
        """Editing is blocked for CONFIRMED headers."""
        header = RequirementHeader.objects.create(
            event=self.event, upashray=self.upashray,
            volunteer_name="Old",
            status=RequirementStatus.CONFIRMED,
        )
        post_data = self._full_post_data(
            {"save_details": "1", "volunteer_name": "New Name"}
        )
        resp = self.client.post(
            reverse("requirements:collect-edit", kwargs={"pk": header.pk}),
            post_data
        )
        header.refresh_from_db()
        self.assertEqual(header.volunteer_name, "Old")

    # ── Test 7: Save details with AJAX returns JSON ─────────────────

    def test_save_details_ajax_returns_json(self):
        """AJAX save_details returns JSON with ok=True."""
        post_data = self._full_post_data({"save_details": "1"})
        resp = self.client.post(
            reverse("requirements:collect"),
            post_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertIn("header_pk", data)

    # ── Test 8: Confirm with AJAX returns JSON on validation error ──

    def test_confirm_validation_error_returns_json(self):
        """AJAX confirm with missing fields returns 400 + JSON errors."""
        post_data = self._full_post_data({"confirm": "1"})
        # Remove required fields
        for field in ["route_area", "pujya_shri_name", "thana_count",
                       "area", "current_address", "chaturmas_place_address",
                       "requirement_date", "chaturmas_entry_date",
                       "volunteer_name", "volunteer_mobile", "stay_type"]:
            post_data.pop(field, None)
        resp = self.client.post(
            reverse("requirements:collect"),
            post_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertIn("message", data)

    # ── Test 9: Formset with items created and confirmed via POST ───

    def test_direct_confirm_creates_lines(self):
        """Confirm via POST creates RequirementLine records."""
        post_data = self._full_post_data(
            {"confirm": "1", "volunteer_name": "Direct"},
            {self.items[0].pk: 7, self.items[2].pk: 4}
        )
        resp = self.client.post(reverse("requirements:collect"), post_data)
        self.assertEqual(resp.status_code, 302)
        header = RequirementHeader.objects.get(volunteer_name="Direct")
        self.assertEqual(header.status, RequirementStatus.CONFIRMED)
        lines = header.lines.all()
        self.assertEqual(lines.count(), 2)
        qty_map = {line.item_id: line.required_qty for line in lines}
        self.assertEqual(qty_map[self.items[0].pk], 7)
        self.assertEqual(qty_map[self.items[2].pk], 4)

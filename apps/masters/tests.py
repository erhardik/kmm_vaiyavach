from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.masters.models import Event, JourneyCard


class EventAcceptingResponsesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="admin2", password="pass", is_superuser=True)
        self.client.force_login(self.user)
        self.event = Event.objects.create(
            name="Responsive",
            slug="resp-1",
            start_date="2026-01-01",
            end_date="2026-12-31",
            is_current=True,
            is_active=True,
        )

    def _post_update(self, accepting):
        return self.client.post(
            f"/masters/events/{self.event.pk}/edit/",
            {
                "name": self.event.name,
                "slug": self.event.slug,
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "status": self.event.status,
                "is_current": True,
                "is_active": True,
                "accepting_responses": "on" if accepting else "",
            },
        )

    def test_toggle_off_saves(self):
        resp = self._post_update(False)
        self.assertEqual(resp.status_code, 302)
        self.event.refresh_from_db()
        self.assertFalse(self.event.accepting_responses)

    def test_toggle_on_saves(self):
        self.event.accepting_responses = False
        self.event.save()
        resp = self._post_update(True)
        self.assertEqual(resp.status_code, 302)
        self.event.refresh_from_db()
        self.assertTrue(self.event.accepting_responses)

    def test_edit_page_renders_toggle(self):
        resp = self.client.get(f"/masters/events/{self.event.pk}/edit/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Accepting Responses")
        self.assertContains(resp, 'name="accepting_responses"')

    def test_public_collect_shows_banner_when_closed(self):
        self.event.accepting_responses = False
        self.event.save()
        url = f"/requirements/public/{self.event.public_form_token}/collect/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ઇવેન્ટ પૂર્ણ થઈ ગઈ છે")
        self.assertContains(resp, "અભિપ્રાય આપો")

    def test_public_collect_shows_form_when_open(self):
        url = f"/requirements/public/{self.event.public_form_token}/collect/?lang=en"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Collect Requirements")

    def test_landing_hides_form_button_when_closed(self):
        self.event.accepting_responses = False
        self.event.save()
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "વૈયાવચ્ચ વિનંતી ફોર્મ ભરો")

    def test_landing_shows_form_button_when_open(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "વૈયાવચ્ચ વિનંતી ફોર્મ ભરો")

    def test_public_requests_hides_new_form_when_closed(self):
        self.event.accepting_responses = False
        self.event.save()
        resp = self.client.get("/requests/")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "નવું ફોર્મ ભરો")

    def test_public_requests_shows_new_form_when_open(self):
        resp = self.client.get("/requests/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "નવું ફોર્મ ભરો")


class JourneyCardAdminFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="journey-admin", password="pass", is_superuser=True)
        self.client.force_login(self.user)

    def test_journey_list_renders_seeded_cards(self):
        JourneyCard.objects.create(
            year=2012, month="ફેબ્રુઆરી", title="પરીક્ષણ શીર્ષક", description="પરીક્ષણ વર્ણન", category="social"
        )
        resp = self.client.get(reverse("masters:journey-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Add Journey")
        self.assertContains(resp, "પરીક્ષણ શીર્ષક")

    def test_journey_create_sets_month_order(self):
        resp = self.client.post(
            reverse("masters:journey-create"),
            {
                "year": "2026",
                "month": "ઓગસ્ટ",
                "title": "નવું કાર્ડ",
                "description": "આ એક નવું વર્ણન છે.",
                "category": "social",
            },
        )
        self.assertEqual(resp.status_code, 302)
        card = JourneyCard.objects.get(title="નવું કાર્ડ")
        self.assertEqual(card.month_order, 8)
        self.assertEqual(card.date_label(), "ઓગસ્ટ 2026")

    def test_journey_edit_and_delete(self):
        card = JourneyCard.objects.create(
            year=2024, month="માર્ચ", title="જૂનું", description="જૂનું વર્ણન", category="education"
        )
        resp = self.client.post(
            reverse("masters:journey-update", kwargs={"pk": card.pk}),
            {
                "year": "2025",
                "month": "જૂન",
                "title": "નવું",
                "description": "નવું વર્ણન",
                "category": "medical",
            },
        )
        self.assertEqual(resp.status_code, 302)
        card.refresh_from_db()
        self.assertEqual(card.title, "નવું")
        self.assertEqual(card.month_order, 6)
        self.assertEqual(card.category, "medical")
        resp = self.client.post(reverse("masters:journey-delete", kwargs={"pk": card.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(JourneyCard.objects.filter(pk=card.pk).exists())

    def test_landing_page_injects_journey_json(self):
        JourneyCard.objects.create(
            year=2024, month="ફેબ્રુઆરી", title="પરીક્ષણ", description="વર્ણન", category="social"
        )
        resp = self.client.get(reverse("public-landing"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "window.KMM_JOURNEY_DATA")
        self.assertContains(resp, '"title": "પરીક્ષણ"')
        self.assertContains(resp, 'id="kmm-journey"')
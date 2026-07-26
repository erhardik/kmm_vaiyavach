from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.masters.models import Event


class Feedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="feedbacks")
    volunteer_name = models.CharField(max_length=255, blank=True, verbose_name="Volunteer Name")
    volunteer_mobile = models.CharField(max_length=20, blank=True, verbose_name="Volunteer Mobile")
    event_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Event Rating",
    )
    portal_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Portal Rating",
    )
    event_feedback = models.TextField(blank=True, verbose_name="Event Feedback")
    portal_feedback = models.TextField(blank=True, verbose_name="Portal Feedback / Issues")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"

    def __str__(self):
        name = self.volunteer_name or "Anonymous"
        return f"Feedback from {name} ({self.created_at:%d-%b-%Y})"

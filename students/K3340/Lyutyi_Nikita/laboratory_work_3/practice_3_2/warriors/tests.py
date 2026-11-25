from django.test import TestCase
from rest_framework.test import APIClient
from .models import Profession, Skill, Warrior


class WarriorPracticeTests(TestCase):
    def test_crud_and_nested_relations(self):
        client = APIClient()
        p = Profession.objects.create(title="Разведчик")
        s = Skill.objects.create(title="Маскировка")
        r = client.post("/api/warriors/", {"name": "Олег", "level": 4,
                                          "profession": p.pk, "skills": [s.pk]}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        pk = r.data["id"]
        data = client.get(f"/api/warriors/{pk}/").data
        self.assertEqual(data["profession_details"]["title"], "Разведчик")
        self.assertEqual(data["skill_details"][0]["title"], "Маскировка")
        self.assertEqual(client.patch(f"/api/warriors/{pk}/", {"level": 5}).status_code, 200)
        self.assertEqual(client.delete(f"/api/warriors/{pk}/").status_code, 204)

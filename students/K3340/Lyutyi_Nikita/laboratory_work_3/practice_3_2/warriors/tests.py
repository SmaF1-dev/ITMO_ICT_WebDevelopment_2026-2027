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

    def test_explicit_apiview_lists_warriors_with_relations(self):
        client = APIClient()
        profession = Profession.objects.create(title="Лучник")
        skill = Skill.objects.create(title="Меткость")
        warrior = Warrior.objects.create(name="Анна", level=7, profession=profession)
        warrior.skills.add(skill)

        response = client.get("/api/practice/warriors-list/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Анна")
        self.assertEqual(response.data[0]["profession_details"]["title"], "Лучник")
        self.assertEqual(response.data[0]["skill_details"][0]["title"], "Меткость")

    def test_generic_create_skill(self):
        client = APIClient()
        response = client.post(
            "/api/practice/skills-create/", {"title": "Маскировка"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Skill.objects.filter(title="Маскировка").exists())

    def test_put_replaces_editable_fields(self):
        client = APIClient()
        profession = Profession.objects.create(title="Воин")
        skill = Skill.objects.create(title="Щит")
        warrior = Warrior.objects.create(name="Иван", level=1, profession=profession)
        response = client.put(
            f"/api/warriors/{warrior.pk}/",
            {"name": "Иван", "level": 5, "profession": profession.pk, "skills": [skill.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        warrior.refresh_from_db()
        self.assertEqual(warrior.level, 5)
        self.assertEqual(list(warrior.skills.values_list("pk", flat=True)), [skill.pk])

    def test_browsable_api_html_renders_in_browser(self):
        # Browser clients prefer text/html; API tests without Accept normally use JSON.
        client = APIClient()
        for path in ("/api/", "/api/warriors/", "/api/skills/"):
            with self.subTest(path=path):
                response = client.get(path, HTTP_ACCEPT="text/html")
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response["Content-Type"])
                self.assertGreater(len(response.content), 100)

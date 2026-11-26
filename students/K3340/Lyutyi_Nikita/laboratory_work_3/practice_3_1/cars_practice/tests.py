import io
import os
import runpy
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from .models import Car, CarOwner, DriverLicense, Ownership


class Practice31Tests(TestCase):
    def test_orm_script_creates_records_and_executes_all_queries(self):
        script_path = Path(__file__).resolve().parents[1] / "run_in_lab2.py"
        with patch.dict(os.environ, {"PRACTICE_3_1_STANDALONE": "1"}):
            commands = runpy.run_path(str(script_path), run_name="practice_3_1_script_test")

        output = io.StringIO()
        with redirect_stdout(output):
            owners = commands["seed"]()
            commands["run_queries"](owners)
        result = output.getvalue()

        self.assertEqual(CarOwner.objects.count(), 6)
        self.assertEqual(Car.objects.count(), 6)
        self.assertEqual(DriverLicense.objects.count(), 6)
        self.assertEqual(Ownership.objects.count(), 12)
        for number in range(1, 11):
            self.assertIn(f"{number}.", result)
        self.assertIn("Toyota", result)

        # Повторный запуск должен быть идемпотентным благодаря get_or_create.
        commands["seed"]()
        self.assertEqual(CarOwner.objects.count(), 6)
        self.assertEqual(Ownership.objects.count(), 12)

    def test_local_status_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["practice"], "3.1")
        self.assertEqual(response.json()["status"], "ok")

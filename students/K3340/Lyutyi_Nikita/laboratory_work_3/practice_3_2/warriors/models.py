from django.db import models


class Profession(models.Model):
    title = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.title


class Skill(models.Model):
    title = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.title


class Warrior(models.Model):
    name = models.CharField(max_length=120)
    level = models.PositiveIntegerField(default=1)
    profession = models.ForeignKey(Profession, on_delete=models.PROTECT, related_name="warriors")
    skills = models.ManyToManyField(Skill, related_name="warriors", blank=True)

    def __str__(self):
        return self.name

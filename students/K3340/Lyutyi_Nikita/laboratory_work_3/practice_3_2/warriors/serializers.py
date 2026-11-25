from rest_framework import serializers
from .models import Profession, Skill, Warrior


class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ["id", "title"]


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "title"]


class WarriorSerializer(serializers.ModelSerializer):
    profession_details = ProfessionSerializer(source="profession", read_only=True)
    skill_details = SkillSerializer(source="skills", read_only=True, many=True)

    class Meta:
        model = Warrior
        fields = ["id", "name", "level", "profession", "skills", "profession_details", "skill_details"]

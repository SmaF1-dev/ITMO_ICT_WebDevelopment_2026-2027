from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Profession, Skill, Warrior
from .serializers import ProfessionSerializer, SkillSerializer, WarriorSerializer


class WarriorListAPIView(APIView):
    def get(self, request):
        queryset = Warrior.objects.select_related("profession").prefetch_related("skills").order_by("id")
        return Response(WarriorSerializer(queryset, many=True).data)


class SkillCreateGenericAPIView(generics.CreateAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


class ProfessionViewSet(viewsets.ModelViewSet):
    queryset = Profession.objects.all().order_by("id")
    serializer_class = ProfessionSerializer


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all().order_by("id")
    serializer_class = SkillSerializer


class WarriorViewSet(viewsets.ModelViewSet):
    queryset = Warrior.objects.select_related("profession").prefetch_related("skills").order_by("id")
    serializer_class = WarriorSerializer

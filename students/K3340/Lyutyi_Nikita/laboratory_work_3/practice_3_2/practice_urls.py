from django.urls import include, path
from rest_framework.routers import DefaultRouter
from warriors.views import (
    ProfessionViewSet, SkillViewSet, WarriorViewSet, WarriorListAPIView, SkillCreateGenericAPIView
)

router = DefaultRouter()
router.register("professions", ProfessionViewSet)
router.register("skills", SkillViewSet)
router.register("warriors", WarriorViewSet)
urlpatterns = [
    path("api/", include(router.urls)),
    path("api/practice/warriors-list/", WarriorListAPIView.as_view()),
    path("api/practice/skills-create/", SkillCreateGenericAPIView.as_view()),
]

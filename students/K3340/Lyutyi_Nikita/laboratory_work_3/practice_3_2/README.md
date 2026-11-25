# Практика 3.2 — REST API

Это **отдельный** небольшой учебный проект с SQLite. Его модели `Warrior`, `Profession`, `Skill` не входят в согласованную схему агентства из десяти таблиц и не создаются в PostgreSQL ЛР3.

Запуск из `laboratory_work_3` (после установки зависимостей в виртуальное окружение ЛР3):

```powershell
python practice_3_2/manage.py makemigrations warriors
python practice_3_2/manage.py migrate
python practice_3_2/manage.py test warriors -v 2
python practice_3_2/manage.py runserver 8001
```

В браузере откройте `http://127.0.0.1:8001/api/`.

Для создания персонажа сначала создайте профессию (`POST /api/professions/` с `{"title":"Разведчик"}`) и навык (`POST /api/skills/` с `{"title":"Маскировка"}`). После этого создайте персонажа через `POST /api/warriors/`, передав `name`, `level`, `profession` (ID) и массив `skills` (ID). `GET /api/warriors/` и `GET /api/warriors/<id>/` выдают вложенные данные профессии и навыков; PATCH меняет персонажа, DELETE удаляет его.

Этот проект нужен только для выполнения буквального задания 3.2 из методички и демонстрации `APIView`/`GenericAPIView`/`ModelViewSet`, сериализации, вложенных объектов, HTTP методов и связей 1:N/M:N. Реализация использует `ModelViewSet`, включающий все CRUD-операции.

Дополнительные примеры: `GET /api/practice/warriors-list/` реализован вручную на `APIView`, `POST /api/practice/skills-create/` реализован с помощью `generics.CreateAPIView`, остальные маршруты — с `ModelViewSet`.

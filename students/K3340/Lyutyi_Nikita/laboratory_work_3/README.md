# Лабораторная работа №3 — Рекламное агентство «Луч»

Лютый Никита, ИТМО, K3340. Индивидуальный вариант №8, схема из 10 предметных таблиц, согласована с преподавателем.

Цель — реализовать REST API на Django 5.2, Django REST Framework, Djoser и PostgreSQL. Дополнительно выполнены отдельные практические работы 3.1 (ORM на ЛР2) и 3.2 (REST API для персонажей), подготовлена страница отчёта MkDocs.

## Как работает проект

- `agency/`: настройки Django, входные URL, ASGI/WSGI.
- `ad_agency/models.py`: 10 моделей согласованной ER-схемы; первичные/внешние ключи, уникальные пары и проверки чисел.
- `ad_agency/serializers.py`: преобразование JSON в модели и обратно, валидация и вложенные представления связей.
- `ad_agency/views.py`: CRUD для моделей; запреты на изменение подписанных документов; проведение оплаты.
- `ad_agency/services.py`: расчёт стоимости каждой строки, округление до копеек, транзакционные блокировки и проверки.
- `ad_agency/reports.py`: пять выборок варианта и квартальный отчёт.
- `ad_agency/management/commands/seed_demo.py`: демонстрационные данные, включая оплаченный заказ за прошлый квартал.
- `ad_agency/tests/test_agency.py`: автоматические тесты безопасности, моделей, вложенных GET, округления, оплаты и отчётов.
- `ad_agency/admin.py`: просмотр сущностей, но не изменение заказов напрямую в админке (оно обошло бы транзакционные ограничения API).
- `practice_3_1/`: отдельный скрипт ORM для моделей ЛР2.
- `practice_3_2/`: независимый учебный мини-проект SQLite для буквальных заданий по воинам, профессиям и умениям.
- `DEFENSE.md`: подробные объяснения к защите.
- `scripts/register_mkdocs.py`: осторожно добавляет страницу ЛР3 в существующее меню курса.

## Быстрый запуск (PowerShell, Windows)

Откройте PowerShell в папке `students/K3340/Lyutyi_Nikita/laboratory_work_3`:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Обязательно поменяйте `DJANGO_SECRET_KEY` и `DB_PASSWORD` в `.env` перед запуском. Не выкладывайте `.env` в Git.

```powershell
docker compose up -d --wait postgres
docker compose ps
python manage.py makemigrations ad_agency
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py seed_demo
python manage.py test ad_agency -v 2
python manage.py runserver
```

Адреса: `http://127.0.0.1:8000/api/` — список API, `http://127.0.0.1:8000/admin/` — админка, `/` — состояние сервиса. **Важно:** команда `makemigrations` создаёт файл `ad_agency/migrations/0001_initial.py`; обязательно добавьте его в коммит.

PostgreSQL работает в Docker на порту **5434**, чтобы не конфликтовать с ЛР2 (5433). Запуск основной ЛР3 требует Docker и настоящую PostgreSQL, SQLite для основной БД не применяется.

## Вход и тест API

Djoser отвечает за регистрацию, получение и удаление токена и данные пользователя:

| Метод | Адрес | Назначение |
|---|---|---|
| POST | `/auth/users/` | Зарегистрировать пользователя (`username`, `password`, `re_password`) |
| POST | `/auth/token/login/` | Получить токен (`username`, `password`) |
| POST | `/auth/token/logout/` | Отозвать токен |
| GET | `/auth/users/me/` | Данные текущего пользователя |

Создайте суперпользователя `python manage.py createsuperuser`: он сможет менять данные. Обычный зарегистрированный пользователь может только просматривать API (кроме своих действий в Djoser).

В отдельном PowerShell:

```powershell
$base = 'http://127.0.0.1:8000'
$creds = @{ username = 'admin'; password = 'ВАШ_ПАРОЛЬ' } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$base/auth/token/login/" -Method POST -ContentType 'application/json' -Body $creds
$headers = @{ Authorization = "Token $($login.auth_token)" }
Invoke-RestMethod -Uri "$base/auth/users/me/" -Headers $headers
Invoke-RestMethod -Uri "$base/api/" -Headers $headers
Invoke-RestMethod -Uri "$base/api/reports/services/" -Headers $headers
Invoke-RestMethod -Uri "$base/api/reports/quarterly/" -Headers $headers
```

Текущие примеры есть после `seed_demo`; отчёт за предыдущий квартал заполнен, а часть поручений не оплачена. Для создания рекламодателя:

```powershell
$body = @{ name = 'ООО Пример' } | ConvertTo-Json
Invoke-RestMethod -Uri "$base/api/advertisers/" -Headers $headers -Method POST -ContentType 'application/json' -Body $body
```

### CRUD-ресурсы

| Префикс `/api/` | Модель |
|---|---|
| `advertisers/` | Рекламодатели |
| `employees/` | Сотрудники |
| `categories/` | Категории услуг |
| `services/` | Услуги |
| `materials/` | Материалы |
| `material-norms/` | Нормы расхода (объект идентифицируется парой услуга–материал) |
| `requests/` | Заявки |
| `works/` | Строки работ |
| `contracts/` | Договоры |
| `payment-orders/` | Платёжные поручения |

Для каждого ресурса доступны GET списка и одного объекта, POST создания, PUT/PATCH изменения, DELETE удаления — кроме операций, которые запрещены бизнес-правилами (например, подписанные договоры нельзя редактировать или удалять). Для удаления необходимо использовать HTTP DELETE, а не обычный GET.

Вложенные объекты для проверки преподавателем:

- **1:N:** `GET /api/advertisers/<id>/` — заявки рекламодателя внутри ответа;
- **1:N:** `GET /api/requests/<id>/` — строки работ с вложенными услугами и исполнителями;
- **M:N:** `GET /api/services/<id>/` — `materials` и нормы `norms` из промежуточной таблицы.

Оплата поручения выполняется сотрудником методом `POST /api/payment-orders/<id>/mark-paid/` с `{"paid_at":"2026-11-18"}` (вместо даты укажите реальную дату не ранее даты выставления). Это единственный штатный способ установить дату оплаты через API.

### Аналитические запросы

| URL `/api/reports/` | Что возвращает |
|---|---|
| `completed-works/` | Выполненные работы, дата оплаты, заказчик, код услуги, исполнитель |
| `payment-orders/` | Поручения за период с отметкой оплаты и списком услуг |
| `services/` | Прайс-лист по категориям |
| `advertiser-requests/` | Заключённые заявки заказчиков |
| `employee-workload/` | Число уникальных оплаченных заявок у каждого сотрудника |
| `quarterly/` | Стоимость работ исполнителей за последний завершённый квартал |

Период для первых, вторых, четвёртых и пятых отчётов: `?date_from=2026-07-01&date_to=2026-09-30`; для списка заявок можно добавить `&advertiser_id=1`. Для квартального отчёта: `?year=2026&quarter=3`.

Дата оплаты (`paid_at`) используется при определении выполненного заказа, дата выставления (`issued_at`) — при выборке поручений, дата подписания (`signed_at`) — при выборке заключённых заявок.

## Проверка и завершение работы

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test ad_agency -v 2
python practice_3_2/manage.py makemigrations warriors
python practice_3_2/manage.py migrate
python practice_3_2/manage.py test warriors -v 2
```

Последние три команды относятся к **отдельной учебной практике на SQLite**. Для практики 3.1 используйте среду и БД ЛР2 (см. `practice_3_1/README.md`).

Для проверки документации перейдите в корень **общего репозитория**, выполните `python students/K3340/Lyutyi_Nikita/laboratory_work_3/scripts/register_mkdocs.py`, установите MkDocs Material при необходимости (`pip install mkdocs-material`) и проверьте `python -m mkdocs build --strict`.

## Соответствие согласованной ER-схеме

В утверждённой схеме `material_usage_norm` имеет **реальный составной первичный ключ** `(service_id, material_id)`. Django 5.2 поддерживает `CompositePrimaryKey`. У всех остальных таблиц указаны именно те имена первичных ключей, которые присутствуют на ER-диаграмме (`advertiser_id`, `work_id` и т. д.), а `db_table` фиксирует исходные названия таблиц. В админке Django нормы расхода не зарегистрированы: стандартная админка Django 5.2 не поддерживает модели с составным ключом; для управления нормами доступен REST API.

**Нормы расхода:** список и создание — `/api/material-norms/`, получение, изменение и удаление отдельной нормы — `/api/material-norms/{service_id}-{material_id}/` (например, `/api/material-norms/1-2/`). Поле `key` в ответе является обозначением пары, а не столбцом в БД.

## Важные ограничения

- Деньги считают `Decimal`, округляя **каждую строку** до копеек, затем суммируя.
- `request_work`, заявка и состав работ блокируются после подписания договора.
- Договор можно оформить только при положительной сумме работ; бесплатная строка внутри платной заявки разрешена.
- Частичная оплата не поддерживается (согласованная учебная модель).
- При переходе к другой единице измерения нужно создать новую позицию каталога с другим уникальным названием.
- Для изменения уже подписанного заказа создаётся новая заявка; старые документы сохраняются.
- В админке изменения финансовых моделей намеренно отключены: требования целостности применяются в API, а не в прямом `Model.save()`.
- Не публикуйте этот учебный сервис в интернете в режиме отладки или с простой системой токенов без HTTPS и дополнительных мер безопасности.

## Swagger UI и кодировка Windows PowerShell

Для защиты запусти `python manage.py runserver` и открой:

- **Swagger UI:** `http://127.0.0.1:8000/api/docs/` (интерактивные запросы);
- **OpenAPI:** `http://127.0.0.1:8000/api/schema/` (описание интерфейса);

Шаги: раскрой `POST /auth/token/login/`, нажми **Try it out**, введи `username` и `password`, выполни запрос и скопируй `auth_token`. Нажми **Authorize** в верхней части Swagger и введи значение **`Token <токен>`** целиком. После этого можно вызывать `/api/advertisers/`, `/api/services/`, `/api/reports/quarterly/` и другие методы кнопкой **Execute**. Схема Swagger генерируется автоматически из DRF; параметры шести отчётов описаны отдельно в `ad_agency/report_schemas.py`.

В `agency/renderers.py` для JSON явно указан `charset=utf-8`: Windows PowerShell 5.1 раньше трактовал русские символы в JSON как латиницу. Сам файл `scripts/smoke.ps1` записан в UTF-8 с BOM, чтобы PowerShell 5.1 корректно прочитал русские строки и не выдавал ошибку синтаксического разбора. **Изменение не требует миграций и пересоздания PostgreSQL.**

После наложения этого обновления выполните:

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py test ad_agency -v 2
python manage.py runserver 127.0.0.1:8000
# Во втором окне:
.\scripts\smoke.ps1 -Username admin
```

В случае ошибки вида «не найдена статика Swagger» убедитесь, что в `.env` выставлено `DJANGO_DEBUG=1` для локальной демонстрации и установлен пакет `drf-spectacular-sidecar`. Нельзя включать режим отладки на публичном сервере.

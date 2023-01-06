# Разворачивание проекта на Django. <br> Стек *Nginx-Unicorn-Django* + Postgres

## Условности

[Источник](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-20-04-ru) - статья на Digitalocean

[Синтаксис сокетов](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#Specifiers) и [статья](https://habr.com/ru/post/161011/) на Хабре

`myproject` - имя проекта
`myprojectuser` - пользователь проекта
`/var/www/myproject` - папка с нашим проектом

Схема:

![Схема](doc_img/WSGI.png)

## Порядок работы

+ Устанавливаем и настраиваем недостающие пакеты Python и Postgres
+ инициализируем и настраиваем проект Django
+ создаём файлы Gunicorn для systemd
+ настраиваем проксирование Nginx.

## Донастройка интерпретатора и установка БД

Для работы проекта на Django обязательно требуется связь с базой данных. В качестве БД может использоваться SQLite, но традиционой для продуктовых систем является СУБД PostgreSQL. Установим её. Также для Python нам нужно доустановить некоторые пакеты, которые необходимы для стабильной работы среды разработки.

```shell
sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib
```
Что касается Postgres, нужно создать базу для проекта и пользователя. Для начала входим в СУБД от имени системного пользователя `postgres`:

```shell
sudo -u postgres psql
```
Не забывая про точки с запятой в конце создаём сначала базу данных, а потом пользователя.
```sql
CREATE DATABASE myproject;
CREATE USER myprojectuser WITH PASSWORD 'password';
```

Затем настраиваем пользователя. Нужно прописать следующие параметры пользователя:
+ `client_encoding` - кодировка базы
+ `default_transaction_isolation` - уровень изоляции при транзакции
+ `timezone` - временная зона

```sql
ALTER ROLE myprojectuser SET client_encoding TO 'utf8';
ALTER ROLE myprojectuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE myprojectuser SET timezone TO 'UTC';

# Выходим
\q
```

## Работа с Django

Для начала устанавливаем виртуальное окружение, а потом зависимости, среди которых будет и Django. Создадим директорию для нашего проекта. Пусть она будет находиться в `/var/www`. Установим зависимости из файла. Файл `requirements.txt`:

```text
Django==4.1.5
gunicorn==20.1.0
psycopg2-binary==2.9.5
```

```bash
cd /var/www/
mkdir myproject
cd myproject/

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Внутри папки проекта будет располагаться директория с проектом. Чтобы её создать, инициализируем проект Django следующей командой:

```shell
django-admin startproject myproject .
```

Команда создаёт каталог `myproject/` в текущей (`.`) папке. Соответственно, в итоге мы получим путь `/var/www/myproject/myproject`. Также можно задать другое имя и расположение создаваемого пакета Django. В папке будет следующий набор файлов:
```shell
~ tree myproject 
myproject
├── asgi.py
├── __init__.py
├── __pycache__
├── settings.py
├── urls.py
└── wsgi.py
```
Позднее опишем назначение каждого файла отдельно.

### Настройки проекта

В файле `/var/www/myproject/myproject/settings.py` производим следующие настройки:

**Правим** `ALLOWED_HOSTS` - разрешённые IP адреса и доменные имена, то есть те, с которых можно обратиться к скриптам. Например `ALLOWED_HOSTS = ['127.0.0.1', '192.168.2.101']`

**Переписываем подключение к базе данных.** По умолчанию имеем подключение к базе SQLite.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'myproject',
        'USER': 'myproject',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

**Прописываем путь к статике** (с точки зрения Python - это HTML, CSS и JS). 
```python
STATIC_URL = '/static/'
STATIC_ROOT = [
    BASE_DIR / "static/",
]


# есть ещё вариант
STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_ROOT = [
    BASE_DIR / "static/",
]

# после включения через модуль os у нас начинает работать команда `python manage.py collectstatic`

```



**Настраиваем и осуществляем миграции.** Это делается через скрипт `manage.py`:
```shell
python manage.py makemigrations
python manage.py migrate
```
Первая команда создаёт файлы миграции. На данном этапе у нас будут отсутствовать какие-либо изменения в файлах моделей. Вторая команда осуществляет миграции. Это означает, что Django создаст все необходимые таблицы и поля. Всякий раз при создании приложений, мы будем повторять эти команды.

**Создаём суперпользователя.** Это нужно для входа в административную панель.
```shell
python manage.py createsuperuser
```
Выскочит диалог, который запросит имя, почту и пароль.

**Переносим всю статику в нужный каталог.**
На данный момент статика имеется только для заглушки самого фреймворка.
```shell
python manage.py collectstatic
```

Также по мелочи настраиваем язык и временную зону в соответствующих константах. Если есть файервол, то нужно открыть порт, по которому мы будем обращаться к скриптам через браузер.

Проверяем работу, запустив сервер Django:

```shell
python manage.py runserver 0.0.0.0:8000
```

Проверяем через браузер по адресу `127.0.0.1`, если Django работает на локальной машине. Также следует проверить адрес `http://127.0.0.1/admin/`

## Работа с Gunicorn

Сначала проверяем работает ли сервер Gunicorn ("Green Unicorn").

```shell
gunicorn --bind 0.0.0.0:8000 myproject.wsgi
```
Если в консоли не будет ошибок и она будет занята процессом, а через браузер у нас будет доступ к странице через браузер, то это значит, что gunicorn у нас работает. Следует учитывать, что Gunicorn не работает со стилями, поэтому в админке при такой конфигурации у нас не будет работать CSS.

Если всё работает нормально, то на всякий случай проверяем где у нас находятся рабочие файлы веб-сервера Gunicorn:

```shell
which gunicorn
```

Скорее всего, нам вернётся следующий путь: `myproject/venv/bin/gunicorn` - это очень важный путь и его мы ещё будем использовать.

Сейчас мы создадим сокеты для работы с Gunicorn через systemd. Для этого сначала создаём файл сокета, а потом файл сервиса. Именем для создаваемого сервиса **будет** `gunicorn`, но если мы хотим на одной машине запускать несколько сайтов, то название создаваемого сервиса должно содержать имя проекта, чтобы мы могли запускать сервисы примерно так:

```shell
sudo systemctl start myproject1_gunicorn
sudo systemctl start myproject2_gunicorn
...
```

Причина по которой мы используем сокеты (UNIX-сокеты) - это желание уйти от использования сетевых интерфейсов, чтобы снизить нагрузку на машину. Более подробное объяснение можно посмотреть, например [здесь](https://zalinux.ru/?p=6293#:~:text=%D0%A1%D0%BE%D0%BA%D0%B5%D1%82%D1%8B%20Unix%20%E2%80%94%20%D1%8D%D1%82%D0%BE%20%D1%84%D0%BE%D1%80%D0%BC%D0%B0%20%D1%81%D0%B2%D1%8F%D0%B7%D0%B8,%D0%BA%D0%B0%D0%BA%D0%B8%D1%85%2D%D0%BB%D0%B8%D0%B1%D0%BE%20%D1%81%D0%B5%D1%82%D0%B5%D0%B2%D1%8B%D1%85%20%D0%BD%D0%B0%D0%BA%D0%BB%D0%B0%D0%B4%D0%BD%D1%8B%D1%85%20%D1%80%D0%B0%D1%81%D1%85%D0%BE%D0%B4%D0%BE%D0%B2.)

Приступим! Создаём файл сокета:
```shell
$ vim /etc/systemd/system/gunicorn.socket
```
```text
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```
Здесь мы задали описание сокета, где будет запускаться экземпляр сокета и к какому [юниту загрузки](https://sysadminium.ru/adm-serv-linux-systemd-target/) он будет привязан. Затем создаём файл сервиса:
```shell
$ cat /etc/systemd/system/gunicorn.service
```
```text 
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=p_boyko
Group=www-data
WorkingDirectory=/var/www/myproject
ExecStart=/var/www/myproject/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          mydjango.wsgi:application

[Install]
WantedBy=multi-user.target
```
Опять же прописываем описание, от какого файла зависит сервис и после достижения какой цели будет запущен сервис.

В разделе Service прописываем следующие значения директив: от имени какого пользователя будет запускаться сервис и от какой группы. Затем ВАЖНО: задаём рабочую директорию где находится исполняемый файл нашей программы, которую мы превращаем в демон. В нашем случае мы ориентируемся на местонахождения файла `/var/www/myproject/manage.py`, потому что, собственно, через него мы и работаем с Django в нашем проекте.

Следующая директива требует прописать путь к каталогу с Gunicorn, который будем использовать. Этот путь нам известен благодаря выводу `which gunicorn`. Параметры запрещают писать access log (сообщения о запросах и ответах в `journalctl`), задают количество воркеров и связывают наш работающий сокет с рабочим файлом скрипта `wsgi.py`. Последний находится в каталоге `myproject/`, в котором располагается также файл `__init__.py`, что делает данный каталог библиотекой. Поэтому мы и обращаемся к `wsgi.py` так как если бы работали  через python-терминал: `myproject.wsgi`. И обозначаем его как приложение (`:application`) 

В конце привязываем наше приложение к мультизадачному юниту.

## Запуск и проверка работы сервиса

Запуск начинается со старта и включения в автозагрузку сокета:

```shell
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket

# проверяем
sudo systemctl status gunicorn.socket
file /run/gunicorn.sock # out: /run/gunicorn.sock: socket
```

Проверяем логи:

```shell
sudo journalctl -u gunicorn.socket | tail -10
```
После запуска сокета, стартуем сервис:

```shell
sudo systemctl start gunicorn.service
sudo systemctl enable gunicorn.service

# проверяем
sudo systemctl status gunicorn.service
```

В случае чего, при перезагрузке может потребоваться перезагрузить и сам демон `systemd` - нужно смотреть внимательно за подсказками терминала.

Проверяем как наш сервис отрабатывает запросы:
```shell
curl --unix-socket /run/gunicorn.sock localhost
```

Ответом должен быть HTML. В конце смотрим что у нас есть в логах по `gunicorn.service`:

```shell
sudo journalctl -u gunicorn.service 
```

## Настройка Nginx как прокси для Gunicorn

Здесь всё должно быть знакомо. Пишем файл `/etc/nginx/sites-available/myproject.conf`:

```nginx configuration
server {
    listen 80;
    server_name domain-or-ip.com;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        root /var/www/myproject;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Навешиваем прослушку на 80 порт, по домену ` domain-or-ip.com`. Кстати, значение этого поля должно не входить в противоречие с константой `/var/www/myproject/myproject/settings.py::ALLOWED_HOSTS`, то есть если мы пишем здесь какой-то домен, его нужно добавить в список.

Затем мы отключаем логирование ответов по фав-иконке.  В следующем `location` прописываем куда должен обратиться Nginx за статикой. И в конце - даём директиву по поводу 'всех адресов': говорим подключить файл и задаём путь к проксируемому сервису.

# Работа с приложениями

Приложение - это логически обособленный файл, в котором создаётся внутренняя логика определённого функционала сайта.

Допустим, мы хотим создать приложение `welcome`. Чтобы создать приложение в Django нужно произвести следующие действия:

Выполняем **команду в терминале**
```shell
python manage.py startapp <name_app>
```

В переменной `myproject/myproject/settings.py::INSTALLED_APPS` **прописываем имя приложения**:

```python


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'welcome',
]
```

В сгенерированном каталоге приложения в файле `views.py` **создаём функции**, которые отвечают за отображение HTML-страниц. Например, нам нужно отобразить стартовую страницу приложения. Сама она будет располагаться в каталоге `templates` в каталоге приложения (`myproject/myproject/welcome/templates/index.html` например). Функция будет выглядеть так:

```python
from django.shortcuts import render

...

def index(request):
    return render(request, 'welcome/index.html')

...
```

Функция `render()` объединяет заданный шаблон с заданным контекстным словарем и возвращает объект HttpResponse с этим визуализированным кодом ([источник](https://django.fun/ru/docs/django/4.1/topics/http/shortcuts/#:~:text=render()&text=%D0%9E%D0%B1%D1%8A%D0%B5%D0%B4%D0%B8%D0%BD%D1%8F%D0%B5%D1%82%20%D0%B7%D0%B0%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D0%B9%20%D1%88%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD%20%D1%81%20%D0%B7%D0%B0%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D0%BC,%D1%83%D0%B4%D0%BE%D0%B1%D1%81%D1%82%D0%B2%D0%B0%2C%20%D1%87%D1%82%D0%BE%20%D0%B8%20render()%20.)). Здесь перечислены обязательные параметры: `request` и `template_name`. Первый - это объект запроса, который используется для генерации ответа. Второй - очевидно, что полное имя используемого для рендеринга шаблона.

Ещё немного по `request`: фактически, это массив с информацией для HTTP-запроса. В него входит информация о куках, GET и POST запросах, заголовки, какой в данном запросе метод используется, схема. Если сравнивать с PHP, то в этом объекте объединены суперглобальные массивы `$_SERVER`, `$_POST`, `$_GET`, `$_COOKIE`, `$_SESSION`.

Затем **прописываем маршруты** 

```python
from welcome.views import index

urlpatterns = [
    path('admin/', admin.site.urls), # URI админки
    path('', index, name='index')    # URI по которому будет вызываться скрипт
]
```

Как видно, в функции `path` функция из модуля `welcome` не вызывается! Если хочется экспериментов, то можно поставить скобочки за вызовом функции `index` и ... мы получим 500 ошибку сервера, потому что передадим в функцию пустой набор обязательных параметров.


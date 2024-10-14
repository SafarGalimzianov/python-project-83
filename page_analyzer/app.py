# Добавление библиотеки os для получения переменных окружения ('SESSION_KEY', 'DATABASE_URL')
import os
# Добавление библиотеки psycopg2 для работы с базой данных (app_repository.py)
import psycopg2
# Добавление библиотеки requests для отправки HTTP-запросов (make_request())
import requests
# Добавление библиотеки BeautifulSoup для парсинга HTML-кода (make_request())
from bs4 import BeautifulSoup
# Добавление библиотеки datetime для работы с датой (make_request())
from datetime import datetime
# Добавление библиотеки Flask для создания веб-приложения
from flask import (
    abort,  # Вызов ошибки
    flash,  # Отображение сообщения пользователю
    Flask,  # Создание экземпляра веб-приложения
    redirect,  # Редирект на другую страницу
    render_template,  # Рендеринг шаблона
    request,  # Получение ответа от пользователя
    url_for,  # Получение пути по имени функции
)

from dotenv import load_dotenv  # Загрузка переменных окружения из файла .env
load_dotenv()

# Добавление класса AppRepository из файла app_repository.py для работы с базой данных
from page_analyzer.app_repository import AppRepository

# Инстанцирование веб-приложения с именем __name__
# Таким образом Flask знает, где искать шаблоны и статические файлы
app = Flask(__name__)

app.config['SESSION_KEY'] = os.getenv('SESSION_KEY')  # Получение ключа сессии
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')  # Получение URL базы данных

conn = psycopg2.connect(app.config['DATABASE_URL'])  # Соединение с базой данных

repo = AppRepository(conn)  # Инстанцирование класса AppRepository


# Запрос к странице по URL вида https://www.example.com
def make_request(url: str) -> dict:  # 
    response = requests.get(url)  # 
    response_code = response.status_code  # 
    soup = BeautifulSoup(response.text, 'html.parser')  # 
    
    h1_content = soup.h1.string if soup.h1 else ''  # 
    title_content = soup.title.string if soup.title else ''  # 
    description_content = ''  # 
    if soup.find('meta', attrs={'name': 'description'}):  # 
        description_content = soup.find('meta', attrs={'name': 'description'})['content']  # 
    
    check_date = response.headers.get('Date', datetime.now().date().isoformat())  # 
    
    return {  # 
        'url': url,  # 
        'response_code': response_code,  # 
        'h1_content': h1_content,  # 
        'title_content': title_content,  # 
        'description_content': description_content,  # 
        'check_date': check_date  # 
    }  # 


# Проверка URL на доступность
def check_url(url: str) -> bool:  # 
    try:  # 
        response = requests.get(url)  # 
        return response.status_code == 200  # 
    except requests.RequestException:  # 
        return False  # 


# Отображение главной страницы
@app.get('/')  # Главная страница
def search():  # Форма поиска, поэтому search
    return render_template('search.html')


# Добавление URL
@app.post('/')  # Форма поиска находится на главной странице
def add_url():  # Заполнение формы добавляет URL в базу данных, поэтому add_url
    url = request.form['url']  # Получение URL из формы
    if not check_url(url):  # Проверка URL на доступность производится только при добавлении
        flash('URL неверный', 'error')  # Оповещение пользователя об ошибке
        return redirect(url_for('search'))  # Возврат на главную страницу

    # Если URL доступен, то производится запрос к странице по URL и получение ответа
    data = make_request(url)  # Запрос к странице по URL и получение ответа
    url_id = repo.add_url(data)  # Добавление URL в базу данных
    return redirect(url_for('get_url_info', url_id=url_id))  # Редирект на страницу с информацией об URL


# Отображение информации о сайте
@app.get('/url/<int:url_id>')  # Каждая страница имеет уникальный URL, поэтому url_id
def get_url(url_id):  # Получение id URL
    url_info = repo.get_url_info(url_id)  # Поиск информации о URL по url_id, который совпадает с идентификатором URL в базе данных
    if not url_info:  # Если URL не найден в базе данных
        abort(404) # 404.html
    checks_info = repo.get_url_checks(url_id)
    return render_template(
        'url_info.html',
        url_info=url_info,
        checks_info=checks_info
    )


# Проверка URL
@app.post('/url/<int:url_id>')  # Проверка URL производится на странице с информацией о сайте 
def check_url(url_id):  # Проверка URL, поэтому check_url
    url_address = repo.get_url_address(url_id)  # Получение информации о URL по url_id
    if not url_address:  # 
        abort(404)  # 
    data = make_request(url_address)  # 
    repo.check_url(data)  # 
    return redirect(url_for('get_url', url_id=url_id))  # 


# Отображение списка URL
@app.get('/urls')  # 
def get_urls():  # 
    urls = repo.get_urls()
    return render_template('urls.html', urls=urls)  # 
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
DATABASE = 'notes.db'

def get_db():
    """Подключение к БД с использованием row_factory для доступа по именам столбцов"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создание таблицы, если её нет"""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

@app.route('/')
def index():
    """Главная страница: вывод всех заметок"""
    db = get_db()
    notes = db.execute('SELECT * FROM notes ORDER BY created DESC').fetchall()
    db.close()
    return render_template('index.html', notes=notes)

@app.route('/note/<int:note_id>')
def view_note(note_id):
    """Просмотр одной заметки"""
    db = get_db()
    note = db.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
    db.close()
    if note is None:
        return 'Заметка не найдена', 404
    return render_template('view_note.html', note=note)

@app.route('/add', methods=['POST'])
def add_note():
    """Добавление новой заметки"""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    if not title:
        return 'Название заметки не может быть пустым', 400
    db = get_db()
    db.execute('INSERT INTO notes (title, content) VALUES (?, ?)', (title, content))
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    """Удаление заметки"""
    db = get_db()
    db.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    db.commit()
    db.close()
    return redirect(url_for('index'))

# ---------- API часть ----------
@app.route('/api/notes', methods=['GET'])
def api_get_notes():
    """API: получить список всех заметок в JSON"""
    db = get_db()
    notes = db.execute('SELECT id, title, content, created FROM notes ORDER BY created DESC').fetchall()
    db.close()
    notes_list = [dict(note) for note in notes]
    return jsonify(notes_list)

@app.route('/api/notes', methods=['POST'])
def api_create_note():
    """API: создать новую заметку (принимает JSON)"""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Не указан title'}), 400
    title = data['title'].strip()
    content = data.get('content', '').strip()
    if not title:
        return jsonify({'error': 'Название не может быть пустым'}), 400
    db = get_db()
    db.execute('INSERT INTO notes (title, content) VALUES (?, ?)', (title, content))
    db.commit()
    note_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()
    return jsonify({'id': note_id, 'title': title, 'content': content, 'created': 'now'}), 201

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
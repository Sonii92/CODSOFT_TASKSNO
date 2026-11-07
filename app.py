import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'quiz-maker-super-secret-key-2026')

# Helper: login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for current logged in user
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        with get_db() as conn:
            user = conn.execute(
                "SELECT id, username, email, full_name FROM users WHERE id = ?",
                (session['user_id'],)
            ).fetchone()
    return dict(current_user=user)

# ==================== HOME & LISTING ====================

@app.route('/')
def index():
    with get_db() as conn:
        # Platform statistics
        quiz_count = conn.execute("SELECT COUNT(*) as count FROM quizzes WHERE is_published = 1").fetchone()['count']
        question_count = conn.execute("SELECT COUNT(*) as count FROM questions").fetchone()['count']
        attempt_count = conn.execute("SELECT COUNT(*) as count FROM quiz_attempts").fetchone()['count']
        user_count = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']

        # Featured quizzes (top 6 with most attempts)
        featured_quizzes = conn.execute('''
            SELECT q.*, u.username as creator_username, u.full_name as creator_name,
                   (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count,
                   (SELECT COUNT(*) FROM quiz_attempts WHERE quiz_id = q.id) as attempt_count,
                   (SELECT ROUND(AVG(percentage), 1) FROM quiz_attempts WHERE quiz_id = q.id) as avg_score
            FROM quizzes q
            JOIN users u ON q.created_by = u.id
            WHERE q.is_published = 1
            ORDER BY attempt_count DESC, q.created_at DESC
            LIMIT 6
        ''').fetchall()

        # Categories
        categories = conn.execute('''
            SELECT category, COUNT(*) as count
            FROM quizzes
            WHERE is_published = 1
            GROUP BY category
            ORDER BY count DESC
        ''').fetchall()

    return render_template('index.html',
                           quiz_count=quiz_count,
                           question_count=question_count,
                           attempt_count=attempt_count,
                           user_count=user_count,
                           featured_quizzes=featured_quizzes,
                           categories=categories)

@app.route('/quizzes')
def quizzes():
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    difficulty_filter = request.args.get('difficulty', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()

    sql = '''
        SELECT q.*, u.username as creator_username, u.full_name as creator_name,
               (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count,
               (SELECT COUNT(*) FROM quiz_attempts WHERE quiz_id = q.id) as attempt_count,
               (SELECT ROUND(AVG(percentage), 1) FROM quiz_attempts WHERE quiz_id = q.id) as avg_score
        FROM quizzes q
        JOIN users u ON q.created_by = u.id
        WHERE q.is_published = 1
    '''
    params = []

    if search_query:
        sql += " AND (q.title LIKE ? OR q.description LIKE ? OR u.full_name LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    if category_filter and category_filter != 'All':
        sql += " AND q.category = ?"
        params.append(category_filter)

    if difficulty_filter and difficulty_filter != 'All':
        sql += " AND q.difficulty = ?"
        params.append(difficulty_filter)

    if sort_by == 'popular':
        sql += " ORDER BY attempt_count DESC, q.created_at DESC"
    elif sort_by == 'questions':
        sql += " ORDER BY question_count DESC"
    elif sort_by == 'title':
        sql += " ORDER BY q.title ASC"
    else:  # 'newest'
        sql += " ORDER BY q.created_at DESC"

    with get_db() as conn:
        quizzes_list = conn.execute(sql, params).fetchall()
        all_categories = conn.execute('''
            SELECT DISTINCT category FROM quizzes WHERE is_published = 1 ORDER BY category ASC
        ''').fetchall()

    return render_template('quizzes.html',
                           quizzes=quizzes_list,
                           categories=[c['category'] for c in all_categories],
                           search_query=search_query,
                           current_category=category_filter,
                           current_difficulty=difficulty_filter,
                           current_sort=sort_by)

# ==================== QUIZ DETAIL & TAKING ====================

@app.route('/quiz/<int:quiz_id>')
def quiz_detail(quiz_id):
    with get_db() as conn:
        quiz = conn.execute('''
            SELECT q.*, u.username as creator_username, u.full_name as creator_name,
                   (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count,
                   (SELECT COUNT(*) FROM quiz_attempts WHERE quiz_id = q.id) as attempt_count,
                   (SELECT ROUND(AVG(percentage), 1) FROM quiz_attempts WHERE quiz_id = q.id) as avg_score
            FROM quizzes q
            JOIN users u ON q.created_by = u.id
            WHERE q.id = ? AND q.is_published = 1
        ''', (quiz_id,)).fetchone()

        if not quiz:
            flash('Quiz not found.', 'error')
            return redirect(url_for('quizzes'))

        # Recent attempts/leaderboard on this quiz
        top_attempts = conn.execute('''
            SELECT qa.*, COALESCE(u.full_name, qa.guest_name, 'Anonymous') as participant_name
            FROM quiz_attempts qa
            LEFT JOIN users u ON qa.user_id = u.id
            WHERE qa.quiz_id = ?
            ORDER BY qa.percentage DESC, qa.time_taken_seconds ASC
            LIMIT 5
        ''', (quiz_id,)).fetchall()

    return render_template('quiz_detail.html', quiz=quiz, top_attempts=top_attempts)

@app.route('/quiz/<int:quiz_id>/take')
def take_quiz(quiz_id):
    with get_db() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ? AND is_published = 1', (quiz_id,)).fetchone()
        if not quiz:
            flash('Quiz not found.', 'error')
            return redirect(url_for('quizzes'))

        # Check question count
        q_count = conn.execute('SELECT COUNT(*) as cnt FROM questions WHERE quiz_id = ?', (quiz_id,)).fetchone()['cnt']
        if q_count == 0:
            flash('This quiz currently has no questions.', 'warning')
            return redirect(url_for('quiz_detail', quiz_id=quiz_id))

    return render_template('take_quiz.html', quiz=quiz, question_count=q_count)

# API: Fetch Quiz Questions & Options (Without Revealing Correct Answer)
@app.route('/api/quiz/<int:quiz_id>/data')
def get_quiz_data(quiz_id):
    with get_db() as conn:
        quiz = conn.execute('SELECT id, title, description, category, difficulty, time_limit_minutes FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404

        questions = conn.execute('''
            SELECT id, question_text, order_num
            FROM questions
            WHERE quiz_id = ?
            ORDER BY order_num ASC, id ASC
        ''', (quiz_id,)).fetchall()

        quiz_data = {
            'id': quiz['id'],
            'title': quiz['title'],
            'description': quiz['description'],
            'category': quiz['category'],
            'difficulty': quiz['difficulty'],
            'time_limit_minutes': quiz['time_limit_minutes'],
            'questions': []
        }

        for q in questions:
            options = conn.execute('''
                SELECT id, option_text, order_num
                FROM options
                WHERE question_id = ?
                ORDER BY order_num ASC, id ASC
            ''', (q['id'],)).fetchall()

            quiz_data['questions'].append({
                'id': q['id'],
                'question_text': q['question_text'],
                'order_num': q['order_num'],
                'options': [{'id': opt['id'], 'option_text': opt['option_text']} for opt in options]
            })

    return jsonify(quiz_data)

# API: Submit Quiz Attempt
@app.route('/api/quiz/<int:quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    data = request.get_json() or {}
    answers = data.get('answers', {})  # Dict mapping str(question_id) -> option_id
    time_taken = int(data.get('time_taken_seconds', 0))
    guest_name = data.get('guest_name', '').strip() or 'Guest Explorer'

    with get_db() as conn:
        quiz = conn.execute('SELECT id FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404

        questions = conn.execute('SELECT id FROM questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
        total_questions = len(questions)
        if total_questions == 0:
            return jsonify({'error': 'No questions in this quiz'}), 400

        correct_count = 0
        recorded_answers = []

        for q in questions:
            q_id = q['id']
            selected_option_id = answers.get(str(q_id))
            is_correct = 0

            if selected_option_id:
                # Check if selected option is indeed correct
                opt = conn.execute(
                    'SELECT is_correct FROM options WHERE id = ? AND question_id = ?',
                    (selected_option_id, q_id)
                ).fetchone()
                if opt and opt['is_correct'] == 1:
                    is_correct = 1
                    correct_count += 1

            recorded_answers.append({
                'question_id': q_id,
                'selected_option_id': selected_option_id,
                'is_correct': is_correct
            })

        percentage = round((correct_count / total_questions) * 100, 1)
        user_id = session.get('user_id')

        # Insert attempt
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO quiz_attempts (quiz_id, user_id, guest_name, score, total_questions, percentage, time_taken_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (quiz_id, user_id, guest_name if not user_id else None, correct_count, total_questions, percentage, time_taken))
        attempt_id = cursor.lastrowid

        # Insert detailed answers
        for ans in recorded_answers:
            cursor.execute('''
                INSERT INTO attempt_answers (attempt_id, question_id, selected_option_id, is_correct)
                VALUES (?, ?, ?, ?)
            ''', (attempt_id, ans['question_id'], ans['selected_option_id'], ans['is_correct']))

    return jsonify({
        'success': True,
        'attempt_id': attempt_id,
        'redirect_url': url_for('quiz_result', quiz_id=quiz_id, attempt_id=attempt_id)
    })

# ==================== QUIZ RESULTS ====================

@app.route('/quiz/<int:quiz_id>/result/<int:attempt_id>')
def quiz_result(quiz_id, attempt_id):
    with get_db() as conn:
        attempt = conn.execute('''
            SELECT qa.*, q.title as quiz_title, q.category, q.difficulty,
                   COALESCE(u.full_name, qa.guest_name, 'Explorer') as taker_name
            FROM quiz_attempts qa
            JOIN quizzes q ON qa.quiz_id = q.id
            LEFT JOIN users u ON qa.user_id = u.id
            WHERE qa.id = ? AND qa.quiz_id = ?
        ''', (attempt_id, quiz_id)).fetchone()

        if not attempt:
            flash('Results not found.', 'error')
            return redirect(url_for('quizzes'))

        # Fetch questions, selected options, correct options, and explanations
        questions = conn.execute('''
            SELECT q.id as question_id, q.question_text, q.explanation, q.order_num,
                   aa.selected_option_id, aa.is_correct
            FROM questions q
            JOIN attempt_answers aa ON aa.question_id = q.id
            WHERE aa.attempt_id = ?
            ORDER BY q.order_num ASC, q.id ASC
        ''', (attempt_id,)).fetchall()

        detailed_results = []
        for q in questions:
            options = conn.execute('''
                SELECT id, option_text, is_correct
                FROM options
                WHERE question_id = ?
                ORDER BY order_num ASC, id ASC
            ''', (q['question_id'],)).fetchall()

            detailed_results.append({
                'question_id': q['question_id'],
                'question_text': q['question_text'],
                'explanation': q['explanation'],
                'is_correct': bool(q['is_correct']),
                'selected_option_id': q['selected_option_id'],
                'options': options
            })

        # Calculate time format
        time_sec = attempt['time_taken_seconds']
        mins = time_sec // 60
        secs = time_sec % 60
        formatted_time = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

    return render_template('quiz_result.html',
                           attempt=attempt,
                           questions=detailed_results,
                           formatted_time=formatted_time,
                           quiz_id=quiz_id)

# ==================== QUIZ CREATION ====================

@app.route('/create-quiz')
@login_required
def create_quiz_page():
    return render_template('create_quiz.html')

@app.route('/api/create-quiz', methods=['POST'])
@login_required
def create_quiz_api():
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', 'General Knowledge').strip()
    difficulty = data.get('difficulty', 'Medium').strip()
    time_limit = int(data.get('time_limit_minutes', 0))
    questions_data = data.get('questions', [])

    # Validation
    if not title:
        return jsonify({'error': 'Quiz title is required.'}), 400
    if len(questions_data) < 1:
        return jsonify({'error': 'You must add at least one question.'}), 400

    for idx, q in enumerate(questions_data, 1):
        q_text = q.get('question_text', '').strip()
        options = q.get('options', [])
        correct_idx = q.get('correct_option_index')

        if not q_text:
            return jsonify({'error': f'Question #{idx} is missing text.'}), 400
        if len(options) < 2:
            return jsonify({'error': f'Question #{idx} must have at least 2 options.'}), 400
        if any(not opt.strip() for opt in options):
            return jsonify({'error': f'All options in Question #{idx} must have text.'}), 400
        if correct_idx is None or correct_idx < 0 or correct_idx >= len(options):
            return jsonify({'error': f'Question #{idx} must have a designated correct answer.'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO quizzes (title, description, category, difficulty, time_limit_minutes, created_by, is_published)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (title, description, category, difficulty, time_limit, session['user_id']))
        quiz_id = cursor.lastrowid

        for q_order, q in enumerate(questions_data, 1):
            cursor.execute('''
                INSERT INTO questions (quiz_id, question_text, order_num, explanation)
                VALUES (?, ?, ?, ?)
            ''', (quiz_id, q['question_text'].strip(), q_order, q.get('explanation', '').strip()))
            question_id = cursor.lastrowid

            correct_idx = int(q['correct_option_index'])
            for opt_order, opt_text in enumerate(q['options']):
                is_correct = 1 if opt_order == correct_idx else 0
                cursor.execute('''
                    INSERT INTO options (question_id, option_text, is_correct, order_num)
                    VALUES (?, ?, ?, ?)
                ''', (question_id, opt_text.strip(), is_correct, opt_order + 1))

    return jsonify({
        'success': True,
        'quiz_id': quiz_id,
        'redirect_url': url_for('quiz_detail', quiz_id=quiz_id)
    })

@app.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    with get_db() as conn:
        quiz = conn.execute('SELECT created_by FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
        if not quiz:
            flash('Quiz not found.', 'error')
            return redirect(url_for('dashboard'))
        if quiz['created_by'] != session['user_id']:
            flash('You do not have permission to delete this quiz.', 'error')
            return redirect(url_for('dashboard'))

        conn.execute('DELETE FROM quizzes WHERE id = ?', (quiz_id,))
        flash('Quiz deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

# ==================== USER DASHBOARD & LEADERBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        # Quizzes created by user
        my_quizzes = conn.execute('''
            SELECT q.*,
                   (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as question_count,
                   (SELECT COUNT(*) FROM quiz_attempts WHERE quiz_id = q.id) as attempt_count,
                   (SELECT ROUND(AVG(percentage), 1) FROM quiz_attempts WHERE quiz_id = q.id) as avg_score
            FROM quizzes q
            WHERE q.created_by = ?
            ORDER BY q.created_at DESC
        ''', (user_id,)).fetchall()

        # Quiz attempts history
        my_attempts = conn.execute('''
            SELECT qa.*, q.title as quiz_title, q.category
            FROM quiz_attempts qa
            JOIN quizzes q ON qa.quiz_id = q.id
            WHERE qa.user_id = ?
            ORDER BY qa.completed_at DESC
            LIMIT 20
        ''', (user_id,)).fetchall()

        # User stats
        quizzes_taken = len(my_attempts)
        avg_percentage = round(sum(a['percentage'] for a in my_attempts) / quizzes_taken, 1) if quizzes_taken > 0 else 0
        total_plays_on_created = sum(q['attempt_count'] for q in my_quizzes)

    return render_template('dashboard.html',
                           user=user,
                           my_quizzes=my_quizzes,
                           my_attempts=my_attempts,
                           quizzes_taken=quizzes_taken,
                           avg_percentage=avg_percentage,
                           total_plays_on_created=total_plays_on_created)

@app.route('/leaderboard')
def leaderboard():
    with get_db() as conn:
        # Top performers based on average score & completed quizzes
        top_users = conn.execute('''
            SELECT u.id, u.username, u.full_name,
                   COUNT(qa.id) as total_quizzes_taken,
                   ROUND(AVG(qa.percentage), 1) as avg_score,
                   SUM(qa.score) as total_correct_answers
            FROM users u
            JOIN quiz_attempts qa ON u.id = qa.user_id
            GROUP BY u.id
            HAVING total_quizzes_taken >= 1
            ORDER BY avg_score DESC, total_quizzes_taken DESC
            LIMIT 10
        ''').fetchall()

        # Most popular quizzes
        popular_quizzes = conn.execute('''
            SELECT q.*, u.full_name as creator_name,
                   COUNT(qa.id) as plays,
                   ROUND(AVG(qa.percentage), 1) as avg_score
            FROM quizzes q
            JOIN users u ON q.created_by = u.id
            LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id
            WHERE q.is_published = 1
            GROUP BY q.id
            ORDER BY plays DESC, q.created_at DESC
            LIMIT 5
        ''').fetchall()

    return render_template('leaderboard.html', top_users=top_users, popular_quizzes=popular_quizzes)

# ==================== AUTHENTICATION ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password or not full_name:
            flash('Please fill in all required fields.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        with get_db() as conn:
            existing = conn.execute(
                'SELECT id FROM users WHERE username = ? OR email = ?',
                (username, email)
            ).fetchone()

            if existing:
                flash('Username or email already exists. Please log in.', 'error')
                return render_template('register.html')

            hashed = generate_password_hash(password)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username, email, hashed, full_name))
            new_id = cursor.lastrowid

            session['user_id'] = new_id
            session['username'] = username
            session['full_name'] = full_name

            flash(f'Welcome, {full_name}! Your account has been created.', 'success')
            return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    next_page = request.args.get('next')

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')

        if not login_input or not password:
            flash('Please enter your username/email and password.', 'error')
            return render_template('login.html', next=next_page)

        with get_db() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? OR email = ?',
                (login_input, login_input.lower())
            ).fetchone()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']

                flash(f'Welcome back, {user["full_name"]}!', 'success')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username/email or password.', 'error')

    return render_template('login.html', next=next_page)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Online Quiz Maker on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

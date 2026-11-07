from werkzeug.security import generate_password_hash
from database import get_db, init_db

def seed():
    init_db()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        if cursor.fetchone()['cnt'] > 0:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding sample users and quizzes...")
        
        # 1. Create demo users
        demo_users = [
            ('sarah_dev', 'sarah@example.com', generate_password_hash('password123'), 'Sarah Jenkins', 'Senior Fullstack Engineer & Tech Educator'),
            ('alex_trivia', 'alex@example.com', generate_password_hash('password123'), 'Alex Rivera', 'Science Communicator & Trivia Enthusiast'),
            ('dr_alan', 'alan@example.com', generate_password_hash('password123'), 'Dr. Alan Turing', 'Computer Science Historian & Researcher')
        ]
        
        user_ids = []
        for username, email, pwd_hash, full_name, bio in demo_users:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, bio)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, pwd_hash, full_name, bio))
            user_ids.append(cursor.lastrowid)
            
        sarah_id, alex_id, alan_id = user_ids[0], user_ids[1], user_ids[2]
        
        # 2. Sample Quizzes
        quizzes = [
            {
                'title': 'Web Development & Modern JavaScript',
                'description': 'Test your knowledge on modern JavaScript concepts, ES6+ features, CSS Grid/Flexbox, and DOM manipulation.',
                'category': 'Programming',
                'difficulty': 'Medium',
                'time_limit_minutes': 5,
                'created_by': sarah_id,
                'questions': [
                    {
                        'text': 'Which of the following is true about "let" and "const" in JavaScript?',
                        'explanation': '"let" and "const" have block scope, whereas "var" is function-scoped.',
                        'options': [
                            ('They are function-scoped variables.', False),
                            ('They are block-scoped variables.', True),
                            ('They can be accessed before initialization without error.', False),
                            ('They cannot be used inside loops.', False)
                        ]
                    },
                    {
                        'text': 'What will `typeof NaN` evaluate to in JavaScript?',
                        'explanation': 'In JavaScript, NaN stands for "Not-a-Number", but its data type is technically "number".',
                        'options': [
                            ('"undefined"', False),
                            ('"nan"', False),
                            ('"number"', True),
                            ('"object"', False)
                        ]
                    },
                    {
                        'text': 'In CSS Flexbox, which property defines the alignment along the cross-axis?',
                        'explanation': 'justify-content aligns items along the main axis, while align-items aligns them along the cross axis.',
                        'options': [
                            ('justify-content', False),
                            ('align-items', True),
                            ('flex-direction', False),
                            ('align-self', False)
                        ]
                    },
                    {
                        'text': 'Which HTTP status code signifies a resource was successfully created?',
                        'explanation': 'HTTP 201 Created indicates that the request has succeeded and led to the creation of a new resource.',
                        'options': [
                            ('200 OK', False),
                            ('201 Created', True),
                            ('204 No Content', False),
                            ('301 Moved Permanently', False)
                        ]
                    },
                    {
                        'text': 'What does the JavaScript Promise method `Promise.all()` do?',
                        'explanation': 'Promise.all() waits for all promises in an iterable to fulfill, or rejects as soon as one rejects.',
                        'options': [
                            ('Resolves as soon as the first promise resolves.', False),
                            ('Resolves only after all promises have fulfilled, or rejects if any promise rejects.', True),
                            ('Runs promises in sequential series one after another.', False),
                            ('Cancels promises that take longer than 5 seconds.', False)
                        ]
                    }
                ]
            },
            {
                'title': 'Cosmos & Space Exploration Trivia',
                'description': 'Embark on an astronomical journey testing your knowledge about our solar system, distant stars, and space missions.',
                'category': 'Science',
                'difficulty': 'Easy',
                'time_limit_minutes': 4,
                'created_by': alex_id,
                'questions': [
                    {
                        'text': 'Which planet in our solar system has the most prominent ring system?',
                        'explanation': 'Saturn has the most extensive and visually prominent ring system in the solar system.',
                        'options': [
                            ('Jupiter', False),
                            ('Saturn', True),
                            ('Uranus', False),
                            ('Neptune', False)
                        ]
                    },
                    {
                        'text': 'What was the name of the first human-made satellite launched into space in 1957?',
                        'explanation': 'Sputnik 1 was launched by the Soviet Union on October 4, 1957.',
                        'options': [
                            ('Explorer 1', False),
                            ('Apollo 11', False),
                            ('Sputnik 1', True),
                            ('Vostok 1', False)
                        ]
                    },
                    {
                        'text': 'What is the hottest planet in our solar system?',
                        'explanation': 'Venus has a dense, greenhouse gas-laden atmosphere that traps heat, making its surface hotter than Mercury (~465°C).',
                        'options': [
                            ('Mercury', False),
                            ('Venus', True),
                            ('Mars', False),
                            ('Jupiter', False)
                        ]
                    },
                    {
                        'text': 'How long does light from the Sun take to reach Earth approximately?',
                        'explanation': 'Light from the Sun takes roughly 8 minutes and 20 seconds (about 500 seconds) to travel to Earth.',
                        'options': [
                            ('8 seconds', False),
                            ('8 minutes', True),
                            ('8 hours', False),
                            ('Instantaneous', False)
                        ]
                    }
                ]
            },
            {
                'title': 'Python Programming Masterclass',
                'description': 'Assess your Python proficiency including data structures, list comprehensions, decorators, and memory management.',
                'category': 'Programming',
                'difficulty': 'Hard',
                'time_limit_minutes': 6,
                'created_by': alan_id,
                'questions': [
                    {
                        'text': 'Which of the following data types in Python is IMMUTABLE?',
                        'explanation': 'Tuples, strings, and integers are immutable in Python; lists, sets, and dictionaries are mutable.',
                        'options': [
                            ('List', False),
                            ('Dictionary', False),
                            ('Tuple', True),
                            ('Set', False)
                        ]
                    },
                    {
                        'text': 'What is the output of `bool([])`, `bool([0])`, and `bool("")` in Python?',
                        'explanation': 'Empty collections and empty strings evaluate to False, while non-empty collections like `[0]` evaluate to True.',
                        'options': [
                            ('False, False, False', False),
                            ('False, True, False', True),
                            ('True, True, False', False),
                            ('False, False, True', False)
                        ]
                    },
                    {
                        'text': 'What does Python’s `@property` decorator allow you to do?',
                        'explanation': 'The @property decorator allows a method to be accessed like an attribute while maintaining getter/setter logic.',
                        'options': [
                            ('Makes a method static and callable without an instance.', False),
                            ('Defines getter and setter interface for class attributes using method syntax.', True),
                            ('Caches the return value of an expensive function.', False),
                            ('Restricts access to private variables only.', False)
                        ]
                    },
                    {
                        'text': 'In Python, what is the Global Interpreter Lock (GIL)?',
                        'explanation': 'The GIL is a mutex that prevents multiple native threads from executing Python bytecodes at the same time in CPython.',
                        'options': [
                            ('A security feature preventing unauthorized imports.', False),
                            ('A mutex that protects access to Python objects, preventing multiple threads from executing bytecodes at once.', True),
                            ('A garbage collector algorithm for circular references.', False),
                            ('A compiler optimization for vectorized math.', False)
                        ]
                    }
                ]
            },
            {
                'title': 'World Geography & Wonders',
                'description': 'Test your geographic knowledge of world capitals, highest peaks, oceans, and famous landmarks.',
                'category': 'Geography',
                'difficulty': 'Medium',
                'time_limit_minutes': 5,
                'created_by': alex_id,
                'questions': [
                    {
                        'text': 'What is the capital city of Australia?',
                        'explanation': 'Canberra was chosen as the compromise capital between Sydney and Melbourne in 1908.',
                        'options': [
                            ('Sydney', False),
                            ('Melbourne', False),
                            ('Canberra', True),
                            ('Brisbane', False)
                        ]
                    },
                    {
                        'text': 'Which is the longest river in the world?',
                        'explanation': 'The Nile River in northeastern Africa is generally recognized as the longest river (~6,650 km).',
                        'options': [
                            ('Amazon River', False),
                            ('Nile River', True),
                            ('Yangtze River', False),
                            ('Mississippi River', False)
                        ]
                    },
                    {
                        'text': 'Mount Kilimanjaro, the highest peak in Africa, is located in which country?',
                        'explanation': 'Mount Kilimanjaro is a dormant volcano in northeastern Tanzania.',
                        'options': [
                            ('Kenya', False),
                            ('Tanzania', True),
                            ('Uganda', False),
                            ('Ethiopia', False)
                        ]
                    }
                ]
            }
        ]
        
        for q_data in quizzes:
            cursor.execute('''
                INSERT INTO quizzes (title, description, category, difficulty, time_limit_minutes, created_by, is_published)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (q_data['title'], q_data['description'], q_data['category'], q_data['difficulty'], q_data['time_limit_minutes'], q_data['created_by']))
            quiz_id = cursor.lastrowid
            
            for q_idx, question in enumerate(q_data['questions'], 1):
                cursor.execute('''
                    INSERT INTO questions (quiz_id, question_text, order_num, explanation)
                    VALUES (?, ?, ?, ?)
                ''', (quiz_id, question['text'], q_idx, question['explanation']))
                question_id = cursor.lastrowid
                
                for opt_idx, (opt_text, is_corr) in enumerate(question['options'], 1):
                    cursor.execute('''
                        INSERT INTO options (question_id, option_text, is_correct, order_num)
                        VALUES (?, ?, ?, ?)
                    ''', (question_id, opt_text, 1 if is_corr else 0, opt_idx))
                    
        # 3. Add a few sample attempts so the leaderboard and stats show live data
        sample_attempts = [
            (1, sarah_id, 'Sarah Jenkins', 5, 5, 100.0, 110),
            (1, alex_id, 'Alex Rivera', 4, 5, 80.0, 145),
            (2, alan_id, 'Dr. Alan Turing', 4, 4, 100.0, 75),
            (3, sarah_id, 'Sarah Jenkins', 3, 4, 75.0, 190),
            (4, alex_id, 'Alex Rivera', 3, 3, 100.0, 60),
        ]
        
        for q_id, u_id, g_name, score, total, pct, time_sec in sample_attempts:
            cursor.execute('''
                INSERT INTO quiz_attempts (quiz_id, user_id, guest_name, score, total_questions, percentage, time_taken_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (q_id, u_id, g_name, score, total, pct, time_sec))
            
        print("Sample data successfully seeded!")

if __name__ == '__main__':
    seed()

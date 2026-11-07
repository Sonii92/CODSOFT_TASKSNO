import unittest
import json
import os
from app import app
from database import get_db, init_db
from seed_data import seed

class QuizPlatformTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
        seed()

    def test_01_home_page(self):
        """Test home page loads with featured quizzes and stats"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'QuizPulse', response.data)
        self.assertIn(b'Take a Quiz', response.data)
        self.assertIn(b'Create a Quiz', response.data)

    def test_02_quizzes_listing_and_filtering(self):
        """Test quiz listing, search and category filters"""
        # All quizzes
        res = self.client.get('/quizzes')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Web Development', res.data)

        # Search filter
        res_search = self.client.get('/quizzes?q=JavaScript')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'Web Development', res_search.data)

        # Category filter
        res_cat = self.client.get('/quizzes?category=Science')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b'Cosmos &amp; Space Exploration Trivia', res_cat.data)

    def test_03_quiz_detail_page(self):
        """Test preview page before taking a quiz"""
        res = self.client.get('/quiz/1')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Web Development &amp; Modern JavaScript', res.data)
        self.assertIn(b'Start Quiz Now', res.data)

    def test_04_quiz_data_api(self):
        """Test quiz questions API returns clean data WITHOUT leaking is_correct"""
        res = self.client.get('/api/quiz/1/data')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['id'], 1)
        self.assertGreaterEqual(len(data['questions']), 1)
        
        # Verify is_correct is NOT leaked in the payload
        first_q = data['questions'][0]
        self.assertIn('question_text', first_q)
        self.assertIn('options', first_q)
        for opt in first_q['options']:
            self.assertIn('id', opt)
            self.assertIn('option_text', opt)
            self.assertNotIn('is_correct', opt)

    def test_05_quiz_taking_and_instant_scoring(self):
        """Test submitting answers, computing score and viewing results"""
        # Fetch question 1 data to know options
        res = self.client.get('/api/quiz/1/data')
        data = json.loads(res.data)
        questions = data['questions']

        # Get the actual correct options from the database to test perfect score
        answers = {}
        with get_db() as conn:
            for q in questions:
                correct_opt = conn.execute(
                    "SELECT id FROM options WHERE question_id = ? AND is_correct = 1",
                    (q['id'],)
                ).fetchone()
                answers[str(q['id'])] = correct_opt['id']

        # Submit perfect answers
        submit_payload = {
            'answers': answers,
            'time_taken_seconds': 45,
            'guest_name': 'Test Champion'
        }
        submit_res = self.client.post('/api/quiz/1/submit',
                                      data=json.dumps(submit_payload),
                                      content_type='application/json')
        self.assertEqual(submit_res.status_code, 200)
        submit_data = json.loads(submit_res.data)
        self.assertTrue(submit_data['success'])
        attempt_id = submit_data['attempt_id']

        # View results page
        result_res = self.client.get(f'/quiz/1/result/{attempt_id}')
        self.assertEqual(result_res.status_code, 200)
        self.assertIn(b'100', result_res.data) # 100%
        self.assertIn(b'Correct Answer', result_res.data)

    def test_06_user_registration_and_login(self):
        """Test user registration and login flow"""
        import time
        unique_suffix = int(time.time() * 1000)
        uname = f'student_{unique_suffix}'
        reg_data = {
            'full_name': 'Test Student',
            'username': uname,
            'email': f'{uname}@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        reg_res = self.client.post('/register', data=reg_data, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        # Check session
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('username'), uname)

        # Logout
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

        # Login
        login_data = {
            'login_input': uname,
            'password': 'password123'
        }
        login_res = self.client.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('username'), uname)

    def test_07_custom_quiz_creation_by_user(self):
        """Test user creating a custom quiz with questions, multiple choices, and correct answer"""
        # Login first
        login_data = {'login_input': 'sarah_dev', 'password': 'password123'}
        self.client.post('/login', data=login_data, follow_redirects=True)

        new_quiz_payload = {
            'title': 'AI & Machine Learning Basics',
            'description': 'A quick test on neural networks and model evaluation metrics.',
            'category': 'Programming',
            'difficulty': 'Medium',
            'time_limit_minutes': 10,
            'questions': [
                {
                    'question_text': 'What does CNN stand for in Deep Learning?',
                    'explanation': 'CNN stands for Convolutional Neural Network, typically used in computer vision.',
                    'options': [
                        'Convolutional Neural Network',
                        'Circular Node Network',
                        'Centralized Network Node',
                        'Compute Neural Node'
                    ],
                    'correct_option_index': 0
                },
                {
                    'question_text': 'Which metric measures the proportion of actual positives correctly identified?',
                    'explanation': 'Recall (also known as sensitivity) measures true positive rate.',
                    'options': [
                        'Precision',
                        'Recall',
                        'Accuracy',
                        'F1 Score'
                    ],
                    'correct_option_index': 1
                }
            ]
        }

        res = self.client.post('/api/create-quiz',
                              data=json.dumps(new_quiz_payload),
                              content_type='application/json')
        self.assertEqual(res.status_code, 200)
        res_data = json.loads(res.data)
        self.assertTrue(res_data['success'])
        new_quiz_id = res_data['quiz_id']

        # Verify new quiz is in listing
        quiz_listing_res = self.client.get('/quizzes')
        self.assertIn(b'AI &amp; Machine Learning Basics', quiz_listing_res.data)

        # Verify quiz details
        quiz_detail_res = self.client.get(f'/quiz/{new_quiz_id}')
        self.assertEqual(quiz_detail_res.status_code, 200)
        self.assertIn(b'AI &amp; Machine Learning Basics', quiz_detail_res.data)

    def test_08_leaderboard_page(self):
        """Test community leaderboard page"""
        res = self.client.get('/leaderboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Leaderboard & Top Scorers', res.data)
        self.assertIn(b'Top Ranked Learners', res.data)

if __name__ == '__main__':
    unittest.main()

# QuizPulse - Interactive Online Quiz Platform

QuizPulse is a full-featured, mobile-responsive online quiz platform built with **Python (Flask)**, **SQLite3**, **HTML5**, **Tailwind CSS**, and **Vanilla JavaScript**. It enables users to create, browse, and take interactive multiple-choice quizzes with immediate scoring, detailed performance analytics, and community leaderboards.

---

## 🚀 Features

### 1. Home Page
- **Hero & Call-to-Actions**: Welcome headline with direct options to **"Take a Quiz"** or **"Create a Quiz"**.
- **Live Statistics**: Real-time counters showing total quizzes, questions, quizzes completed, and active members.
- **Category Explorer**: Filter by categories such as Programming, Science, Geography, History, and Trivia.
- **Featured Quizzes**: Curated grid of community quizzes with difficulty badges, play counts, and question metrics.
- **Visual Walkthrough**: 3-step guide explaining how QuizPulse works.

### 2. Quiz Creation (`/create-quiz`)
- **Metadata Studio**: Set quiz title, description, category, difficulty (Easy, Medium, Hard), and custom time limit (or untimed).
- **Dynamic Question Builder**:
  - Add unlimited questions.
  - Multi-choice options (2 to 6 choices per question).
  - One-click radio button to set the correct answer.
  - Optional solution explanations for each question so participants can learn.
  - Move questions up or down, or delete questions.
- **Live Client & Server Validation**: Guarantees question text, choices, and designated correct answers before publishing.

### 3. Quiz Taking (`/quiz/<id>/take`)
- **One-Question-at-a-Time Focus Mode**: Clean stepper presentation without cognitive overload.
- **Progress Tracking**: Real-time progress bar and "Question X of Y" indicators.
- **Dynamic Countdown Timer**: Real-time timer with amber warnings (< 2 min) and pulsing red alerts (< 30 sec). Auto-submits when time expires.
- **Interactive Option Cards**: Clean clickable choices with hover states and active selection glow.
- **Keyboard Shortcuts**: Select choices using keys `1`-`4` or `A`-`D`, and navigate using `ArrowLeft` / `ArrowRight`.
- **Question Navigator**: Drawer modal allowing users to jump directly to any question, displaying answered vs unanswered indicators.
- **Anti-Cheat Design**: Questions API strictly protects answer keys; evaluation happens securely on the server.

### 4. Immediate Results & Review (`/quiz/<id>/result/<attempt_id>`)
- **Instant Scoring & Badges**: Calculated percentage, accuracy grade (Mastery, Passed, Needs Practice), and celebratory confetti animations for high scores.
- **Time & Accuracy Metrics**: Total correct answers, time spent, and skipped questions.
- **Question-by-Question Breakdown**:
  - Highlights correct answers in emerald green with checkmarks.
  - Highlights user mistakes in crimson red with "Your Choice" tags.
  - Detailed educational explanations for why the correct answer is right.
- **Actions**: Retake Quiz, Explore Other Quizzes, or View Leaderboard.

### 5. Quiz Catalog & Filtering (`/quizzes`)
- Live keyword search across quiz titles, descriptions, and creator names.
- Dropdown filters for Category and Difficulty Level.
- Sort by Newest, Most Popular, Most Questions, or Alphabetical.

### 6. User Authentication & Personalized Experience
- User Registration (`/register`) and Secure Login (`/login`) with password hashing (`Werkzeug`).
- **User Dashboard (`/dashboard`)**:
  - View personal creator statistics.
  - Manage authored quizzes (preview, take, delete).
  - Complete history of past quiz attempts with scores and direct links to review answers.
- **Community Leaderboard (`/leaderboard`)**:
  - Ranked hall of fame showing top scorers by average accuracy.
  - Trending quizzes ranked by community plays.

### 7. Mobile Responsiveness
- Optimized for desktops, tablets, and smartphones.
- Mobile drawer navigation and touch-friendly option cards.

---

## 🛠️ Project Structure

```
d:\Sales\quiz_platform\
│
├── app.py                   # Core Flask server, routing, authentication & APIs
├── database.py              # SQLite connection helper & schema creation
├── seed_data.py             # Pre-seeded users, quizzes, questions & answers
├── test_app.py              # Automated unit tests covering all features
├── quiz_maker.db            # SQLite database file
│
├── static/
│   ├── css/
│   │   └── style.css        # Custom styles, animations & glassmorphism
│   └── js/
│       ├── quiz_taker.js    # Interactive one-at-a-time quiz taker engine
│       └── quiz_creator.js  # Dynamic quiz creation form builder
│
└── templates/
    ├── base.html            # Layout with responsive navbar, flash alerts & footer
    ├── index.html           # Home page with hero, stats & featured quizzes
    ├── quizzes.html         # Quiz catalog with search, filters & cards
    ├── quiz_detail.html     # Quiz preview & briefing room before starting
    ├── take_quiz.html       # One-by-one taking experience with timer & stepper
    ├── quiz_result.html     # Score summary, badges & question review
    ├── create_quiz.html     # Dynamic quiz builder
    ├── dashboard.html       # User profile, authored quizzes & history
    ├── leaderboard.html     # Top scorers & trending quizzes
    ├── login.html           # Sign in page
    └── register.html        # Registration page
```

---

## 💻 Running the Application

### 1. Start the Flask Server
In your terminal, run:

```powershell
cd d:\Sales\quiz_platform
python app.py
```

The application will start at:
👉 **`http://localhost:5000`**

### 2. Demo User Accounts (Pre-seeded)
You can log in immediately using any of these accounts:

| Username | Password | Role |
| :--- | :--- | :--- |
| `sarah_dev` | `password123` | Senior Fullstack Engineer |
| `alex_trivia` | `password123` | Science & Trivia Creator |
| `dr_alan` | `password123` | CS Historian & Researcher |

*Or register a new account on `/register`!*

### 3. Run Automated Tests
```powershell
cd d:\Sales\quiz_platform
python test_app.py
```

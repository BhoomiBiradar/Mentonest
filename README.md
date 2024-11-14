## MentoNest 🎓

MentoNest is a comprehensive web-based platform designed to streamline academic mentorship programs, automate meeting management, and facilitate effective mentor-mentee relationships. Like a nest that provides structure, security, and nurturing, MentoNest creates an organized and supportive environment where academic mentorship can flourish.

## 🚀 Features

- **User Management**
  - Secure authentication and role-based access
  - Automated mentor-mentee pairing
  - Profile management for mentors and mentees

- **Meeting Management**
  - Automated scheduling system
  - Real-time notifications
  - Meeting agenda and report generation

- **Communication**
  - Instant notifications
  - Meeting history tracking
  - Progress monitoring

- **Analytics Dashboard**
  - Student progress tracking
  - Mentor workload visualization
  - Meeting statistics

## 🛠️ Tech Stack

- **Frontend:** Streamlit, React components
- **Backend:** Python
- **Database:** MySQL
- **Architecture:** RESTful API

## ⚙️ Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- Node.js 14.x or higher

## 🏃‍♂️ Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mentor-mentee-system.git
   cd mentor-mentee-system
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

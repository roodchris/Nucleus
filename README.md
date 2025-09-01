# Nucleus - Radiology Opportunities Platform

A comprehensive platform connecting radiology residents and employers for job opportunities, featuring forums, compensation data, program reviews, and more.

## Features

- **Job Opportunities**: Post and browse radiology job opportunities
- **Messaging System**: Direct messaging between users
- **Forum**: Community discussions with voting system
- **Compensation Data**: Community-submitted salary and RVU data
- **Program Reviews**: Reviews and ratings for radiology residency programs
- **Knowledge Base**: Curated resources by radiology subspecialty
- **Job Reviews**: Reviews of current and past practices
- **Modern UI**: Beautiful glass morphism design with dark/light themes

## Deployment

### Railway (Recommended - Easiest)

1. **Install Railway CLI** (optional but helpful):
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy to Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect it's a Python app and deploy

3. **Set Environment Variables**:
   - Go to your project settings in Railway
   - Add these environment variables:
     ```
     SECRET_KEY=your-secret-key-here
     DATABASE_URL=sqlite:///app.db
     ```

4. **Your app will be live at**: `https://your-app-name.railway.app`

### Render

1. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - Sign up with GitHub
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn main:app`
   - Add environment variables as above

### Heroku

1. **Install Heroku CLI**:
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Windows
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Deploy to Heroku**:
   ```bash
   heroku login
   heroku create your-app-name
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key-here
   ```

## Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd radiology-moonlighting-job-board
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Visit**: `http://localhost:5000`

## Environment Variables

- `SECRET_KEY`: Flask secret key for sessions (required)
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Database**: SQLite (can be changed to PostgreSQL for production)
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with glass morphism design
- **Deployment**: Railway/Render/Heroku ready

## License

This project is for educational and professional use.

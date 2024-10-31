# Intelligent URL Analysis and Classification

A sophisticated cybersecurity system that uses machine learning to detect and classify malicious URLs in real-time. The system combines advanced feature extraction with adaptive learning capabilities to provide robust protection against evolving cyber threats.

## 🚀 Key Features

- Real-time URL analysis and classification
- Advanced feature extraction (lexical, host-based, security, domain-based)
- Machine learning-based classification with 97.8% accuracy
- Adaptive learning system with user feedback integration
- React-based web dashboard
- Chrome browser extension for real-time protection
- FastAPI backend with async processing capabilities
- Comprehensive API documentation

## 🛠️ Technology Stack

- **Backend**: Python, FastAPI, scikit-learn, pandas, numpy
- **Frontend**: React, Material-UI
- **Browser Extension**: JavaScript, Chrome Extensions API
- **Database**: MySQL
- **Machine Learning**: Decision Trees, Random Forest, GradientBoosting, XGBoost
- **API Documentation**: Swagger/OpenAPI

## 📋 Prerequisites

- Python 3.8 or higher
- Node.js 14.0 or higher
- MySQL 8.0 or higher
- Chrome Browser (for extension)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kshitijtapale/Intelligent-URL-Analysis-and-Classification.git
cd Intelligent-URL-Analysis-and-Classification
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up Database

```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE url;
```

Update the `.env` file with your database credentials:

```env
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=url
```

### 4. Set Up Frontend

```bash
cd frontend
npm install
```

### 5. Install Browser Extension

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the `browser_extension` directory

## 🚀 Running the Application

### Start Backend Server

```bash
# From project root
cd backend
uvicorn main:app --reload --port 8000
```

### Start Frontend Development Server

```bash
# From project root
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
Intelligent-URL-Analysis-and-Classification/
├── backend/
│   ├── ml/
│   ├── config/
│   └── main.py
├── frontend/
│   ├── public/
│   └── src/
└── browser_extension/
```

## 🔄 API Endpoints

- `POST /api/predict_url`: URL classification
- `POST /api/predict_with_explanation`: Detailed URL analysis
- `POST /api/feedback`: Submit user feedback
- `POST /api/retrain`: Trigger model retraining
- `GET /api/training_stats`: View model statistics

## 🧪 Running Tests

```bash
# Run backend tests
pytest backend/tests/

# Run frontend tests
cd frontend
npm test
```

## 📈 Performance Metrics

- Classification Accuracy: 97.8%
- Average Processing Time: 850ms per URL
- Request Handling: 420 requests/second

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Kshitij Tapale - kshitijtaple@gmail.com

Project Link: [https://github.com/kshitijtapale/Intelligent-URL-Analysis-and-Classification](https://github.com/kshitijtapale/Intelligent-URL-Analysis-and-Classification)

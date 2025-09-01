# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Python 3.8+
- Git

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/Tracklytic-Server.git
cd Tracklytic-Server
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create `.env` file:

```env
SECRET_KEY=django-insecure-your-secret-key
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 4. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to see your API!

## 🏦 Test OCR System

### Quick OCR Test

```bash
python test_ocr.py
```

### Test with Receipt Image

```bash
python test_ocr.py path/to/your/receipt.jpg
```

## 📱 API Quick Test

### Test OCR Endpoint

```bash
curl -X POST http://localhost:8000/api/transaction/upload/receipt/ \
  -F "receipt=@path/to/receipt.jpg" \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Test Categories Endpoint

```bash
curl -X GET http://localhost:8000/api/get/categories/ \
  -H "Authorization: Bearer <your-jwt-token>"
```

### Test Authentication

```bash
# Register a user
curl -X POST http://localhost:8000/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123","age":25,"phone_number":1234567890}'

# Login to get JWT token
curl -X POST http://localhost:8000/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

## 🔧 Common Issues

### OCR Not Working

- Ensure image is clear and well-lit
- Check file format (JPG, PNG, PDF)
- Verify file size is under 10MB

### Database Issues

- Run `python manage.py migrate`
- Check database permissions
- Verify database connection

### API Errors

- Check if server is running
- Verify endpoint URLs
- Check authentication headers
- Ensure JWT token is valid

### Authentication Issues

- Verify email and password
- Check if user is registered
- Ensure JWT token is included in Authorization header

## 📚 Next Steps

1. **Explore API Documentation** - Check the README for full API reference
2. **Test OCR with Different Receipts** - Try various receipt formats
3. **Set Up Frontend** - Connect your React/React Native app
4. **Configure Production** - Follow deployment guide for production setup

## 🆘 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review [CONFIGURATION.md](CONFIGURATION.md) for environment setup
- Create an issue on GitHub for bugs or feature requests

---

**Happy Coding! 🎉**

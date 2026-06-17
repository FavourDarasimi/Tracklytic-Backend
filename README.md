# Tracklytic - Smart Financial Tracking System

## 🎯 Overview

Tracklytic is a comprehensive financial tracking application that helps users manage their expenses, income, savings goals, and budget limits. The system features an OCR (Optical Character Recognition) system that can automatically extract transaction data from receipts.

## 🚀 Key Features

### 💰 Financial Management

- **Transaction Tracking** - Record and categorize income and expenses
- **Budget Management** - Set daily, weekly, and monthly spending limits
- **Savings Goals** - Create and track savings plans with deadlines
- **Category Management** - Organize transactions with custom categories
- **Recurring Transactions** - Set up automatic recurring transactions

### 🏦 OCR System

- **Receipt Processing** - Extract transaction data from receipt images
- **Automatic Data Extraction** - Extracts amounts, sender/receiver information
- **PDF Support** - Handles both images and PDF documents
- **Transaction Type Detection** - Automatically determines if transaction is income or expense

### 🤖 AI-Powered Insights

- **Spending Analysis** - AI-generated insights and recommendations
- **Budget Alerts** - Notifications when approaching spending limits
- **Savings Advice** - Personalized tips to reach savings goals faster

## 🛠️ Technology Stack

### Backend

- **Django** - Web framework
- **Django REST Framework** - API development
- **SQLite** - Database (default)
- **EasyOCR** - OCR engine for text extraction
- **pdf2image** - PDF to image conversion
- **Google Gemini AI** - AI-powered insights
- **Djoser** - Authentication system
- **JWT** - Token-based authentication

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git
- Virtual environment (recommended)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Tracklytic-Server.git
cd Tracklytic-Server
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key-here
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
MONO_PUBLIC_KEY=your-mono-public-key
MONO_SECRET_KEY=your-mono-secret-key
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run the Server

```bash
python manage.py runserver
```

The server will be available at `http://localhost:8000`

## 📱 API Endpoints

All API endpoints are prefixed with `/api/v1/`. Authentication endpoints use `/auth/v1/`.

### Authentication (Djoser + Custom)

- `POST /auth/v1/users/` - User registration
- `GET /auth/v1/users/me/` - Get current user profile
- `POST /auth/v1/jwt/create/` - User login (get JWT tokens)
- `POST /auth/v1/jwt/refresh/` - Refresh JWT token
- `POST /auth/v1/jwt/verify/` - Verify JWT token
- `POST /auth/v1/logout/` - Logout (clears JWT cookies)
- `POST /auth/v1/users/set_password/` - Set password
- `POST /auth/v1/users/reset_password/` - Request password reset
- `POST /auth/v1/users/reset_password_confirm/` - Confirm password reset

### Categories

- `GET /api/v1/categories/` - List user categories
- `POST /api/v1/categories/` - Create new category
- `GET /api/v1/categories/<id>/` - Get category detail
- `PUT /api/v1/categories/<id>/` - Update category
- `PATCH /api/v1/categories/<id>/` - Partial update category
- `DELETE /api/v1/categories/<id>/` - Delete category

### Transactions

- `GET /api/v1/transactions/` - List transactions (supports `?search=`, `?type=`, `?category=`, `?date_from=`, `?date_to=`, `?ordering=`)
- `POST /api/v1/transactions/` - Create transaction (supports receipt upload)
- `GET /api/v1/transactions/<id>/` - Get transaction detail
- `PUT /api/v1/transactions/<id>/` - Update transaction
- `PATCH /api/v1/transactions/<id>/` - Partial update transaction
- `DELETE /api/v1/transactions/<id>/` - Delete transaction
- `POST /api/v1/transaction/upload/receipt/` - Upload receipt for OCR parsing

### Recurring Transactions

- `GET /api/v1/recurring-transactions/` - List recurring transactions
- `POST /api/v1/recurring-transactions/` - Create recurring transaction
- `GET /api/v1/recurring-transactions/<id>/` - Get recurring transaction detail
- `PUT /api/v1/recurring-transactions/<id>/` - Update recurring transaction
- `DELETE /api/v1/recurring-transactions/<id>/` - Delete recurring transaction

### Budget Management

- `GET /api/v1/general-budgets/` - List general budgets
- `POST /api/v1/general-budgets/` - Set general spending limit
- `PUT /api/v1/general-budgets/<id>/` - Update general budget
- `DELETE /api/v1/general-budgets/<id>/` - Delete general budget
- `GET /api/v1/category-budgets/` - List category budgets
- `POST /api/v1/category-budgets/` - Set category spending limit
- `PUT /api/v1/category-budgets/<id>/` - Update category budget
- `DELETE /api/v1/category-budgets/<id>/` - Delete category budget

### Savings Plans

- `GET /api/v1/saving-plans/` - List savings plans
- `POST /api/v1/saving-plans/` - Create savings plan
- `GET /api/v1/saving-plans/<id>/` - Get savings plan detail
- `PUT /api/v1/saving-plans/<id>/` - Update savings plan
- `PATCH /api/v1/saving-plans/<id>/` - Partial update savings plan
- `DELETE /api/v1/saving-plans/<id>/` - Delete savings plan
- `GET /api/v1/check/saving/plan/status/` - Check and update all savings plan statuses
- `PUT /api/v1/renew/saving/plan/<pk>/` - Renew a savings plan with a new amount

### Dashboard & AI

- `GET /api/v1/dashboard/overview/` - Get monthly overview, expense distribution, budget summary, latest transactions
- `GET /api/v1/ai/insights/` - Get AI-powered spending insights

## 🏦 OCR System Usage

### Upload Receipt

```http
POST /api/transaction/upload/receipt/
Content-Type: multipart/form-data
Authorization: Bearer <your-jwt-token>

receipt: [image file]
```

### Supported File Formats

- **Images**: JPG, JPEG, PNG
- **Documents**: PDF (converted to images)
- **Size**: Recommended under 10MB

### Sample Response

```json
{
  "status": "success",
  "message": "Transaction data extracted successfully",
  "data": {
    "id": 123,
    "user": "username",
    "party_name": "Jane Smith",
    "amount": 50000,
    "type": "Expense",
    "transaction_date": "2024-12-15T14:30:25Z",
    "receipt": "/media/receipts/receipt.jpg"
  }
}
```

## 📊 OCR System Performance

The OCR system can extract:

- **Amounts** - Currency amounts with ₦, $, NGN symbols
- **Sender/Receiver** - Names from transaction receipts
- **Transaction Type** - Automatic detection of income/expense
- **Text Content** - Full OCR text for reference

## 🔧 Configuration

### Database Configuration

The default configuration uses SQLite. For production, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tracklytic_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### AI Configuration

Set your Gemini API key in the `.env` file:

```env
GEMINI_API_KEY=your-gemini-api-key-here
```

### Email Configuration

For email functionality, configure in `.env`:

```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## 📁 Project Structure

```
Tracklytic-Server/
├── Tracker/                 # Main app
│   ├── models.py           # Database models
│   ├── views.py            # API views
│   ├── utils.py            # OCR and utility functions
│   ├── services.py         # Business logic
│   ├── serializers.py      # API serializers
│   ├── urls.py             # URL routing
│   └── ai_client.py        # AI integration
├── Account/                # Authentication app
│   ├── models.py           # Custom user model
│   ├── views.py            # Auth views
│   ├── serializers.py      # Auth serializers
│   └── urls.py             # Auth URLs
├── Tracklytic_Backend/     # Django project
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI configuration
├── media/                  # Uploaded files
├── templates/              # HTML templates
├── manage.py               # Django management
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

1. **OCR not working**

   - Ensure image is clear and well-lit
   - Check file format (JPG, PNG, PDF)
   - Verify file size is under 10MB

2. **Authentication issues**

   - Check JWT token validity
   - Ensure proper Authorization header
   - Verify user credentials

3. **Amount not extracted**
   - Ensure amount format is clear
   - Check currency symbol visibility
   - Verify image quality

### Getting Help

- Create an issue on GitHub
- Check the documentation
- Review the test results

## 🔮 Roadmap

### Planned Features

- [ ] Enhanced OCR with bank-specific patterns
- [ ] Support for more receipt formats
- [ ] Real-time transaction notifications
- [ ] Advanced analytics dashboard
- [ ] Mobile app optimization
- [ ] Multi-language support

### Recent Updates

- ✅ Basic OCR system for receipt processing
- ✅ AI-powered financial insights
- ✅ Comprehensive budget management
- ✅ Savings goal tracking
- ✅ Recurring transaction support
- ✅ JWT authentication system

## 📞 Contact

- **Project Link**: [https://github.com/yourusername/Tracklytic-Server](https://github.com/yourusername/Tracklytic-Server)
- **Issues**: [GitHub Issues](https://github.com/yourusername/Tracklytic-Server/issues)

---

**Tracklytic** - Making financial tracking smarter and easier! 💰📱

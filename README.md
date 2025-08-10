
# 🛍️ DoleseCommerce - Advanced E-Commerce Platform

[![Django](https://img.shields.io/badge/Django-5.2.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13.5-blue.svg)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive modern e-commerce platform built with Django, featuring advanced payment systems including **Pi Coin cryptocurrency** and **M-Pesa mobile money** integration, along with traditional e-commerce functionality.

## ✨ Key Features

### 🪙 **Cryptocurrency Payments**
- **Pi Coin Integration**: Full Pi Network payment support with real-time exchange rates
- **Secure Processing**: Advanced cryptocurrency transaction handling
- **Rate Management**: Dynamic Pi to USD exchange rate system

### 📱 **Mobile Money (M-Pesa)**
- **Send Money (B2C)**: Direct transfers to any M-Pesa phone number
- **STK Push (C2B)**: Customer payment requests via mobile
- **Real-time Processing**: Instant transaction confirmation
- **Admin Dashboard**: Comprehensive payment management interface

### 🛒 **E-Commerce Core**
- Product catalog with categories and brands
- Advanced shopping cart system
- Order management and tracking
- Inventory management
- Multi-image product gallery

### 👥 **User Management**
- User registration and authentication
- Profile management with avatars
- Address book functionality
- Role-based access control

### 🎨 **Modern UI/UX**
- Responsive Bootstrap 5 design
- Professional dark navigation
- Mobile-optimized interface
- Real-time form validation

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- pip (Python package manager)
- Git

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/seludoto/dolesecommerce.git
   cd dolesecommerce
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your settings
   # Add your M-Pesa and Pi Network credentials
   ```

5. **Setup Database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

8. **Access the Application**
   - Website: http://localhost:8000/
   - Admin Panel: http://localhost:8000/admin/

## ⚙️ Configuration

### Payment System Setup

#### Pi Coin Configuration
```python
# In settings.py or .env
PI_NETWORK_API_KEY = 'your_pi_api_key'
PI_WALLET_ADDRESS = 'your_pi_wallet_address'
PI_SANDBOX_MODE = True  # False for production
PI_WEBHOOK_SECRET = 'your_webhook_secret'
```

#### M-Pesa Configuration
```python
# In settings.py or .env
MPESA_CONSUMER_KEY = 'your_consumer_key'
MPESA_CONSUMER_SECRET = 'your_consumer_secret'
MPESA_SHORTCODE = 'your_shortcode'
MPESA_PASSKEY = 'your_passkey'
MPESA_INITIATOR_NAME = 'your_initiator_name'
MPESA_SECURITY_CREDENTIAL = 'your_security_credential'
```

## 📖 Documentation

- **[Complete Project Documentation](PROJECT_DOCUMENTATION.md)** - Comprehensive technical documentation
- **[Phone Payment Guide](PHONE_PAYMENT_DOCUMENTATION.md)** - M-Pesa integration details
- **[API Documentation](#)** - Payment API reference
- **[Deployment Guide](#)** - Production deployment instructions

## 🎯 Usage Examples

### Making a Pi Coin Payment
```javascript
// Frontend Pi Payment
Pi.createPayment({
  amount: 3.14159,
  memo: "Order #1234",
  metadata: { orderId: 1234 }
});
```

### Sending Money via M-Pesa
```python
# Backend M-Pesa Payment
from payments.mpesa import mpesa_processor

result = mpesa_processor.send_money_to_phone(
    phone_number="+254712345678",
    amount=1000,
    description="Order refund"
)
```

## 🏗️ Project Structure

```
dolesecommerce/
├── 📁 core/                 # Core application logic
├── 📁 products/             # Product management
├── 📁 orders/               # Order processing
├── 📁 payments/             # Payment systems
│   ├── 📄 mpesa.py         # M-Pesa integration
│   ├── 📄 pi_network.py    # Pi Network integration
│   └── 📄 models.py        # Payment models
├── 📁 users/                # User management
├── 📁 reviews/              # Product reviews
├── 📁 shipping/             # Shipping management
├── 📁 static/               # Static files
├── 📁 media/                # User uploads
├── 📁 templates/            # HTML templates
├── 📄 requirements.txt      # Dependencies
├── 📄 manage.py            # Django management
└── 📄 README.md            # This file
```

## 🛠️ Technology Stack

- **Backend**: Django 5.2.4, Python 3.13.5
- **Frontend**: Bootstrap 5.3.0, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Payments**: Pi Network API, M-Pesa Daraja API
- **Deployment**: Heroku-ready with Procfile

## 🔧 Development

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Run linting
flake8 .

# Check for security issues
bandit -r .
```

### Database Management
```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

## 📱 API Endpoints

### Payment APIs
- `POST /payments/pay/pi/<order_id>/` - Pi Coin payment
- `POST /payments/phone/send/` - Send money to phone
- `POST /payments/phone/request/` - Request payment via STK Push
- `GET /payments/phone/dashboard/` - Payment dashboard

### Product APIs
- `GET /products/` - Product list
- `GET /products/<id>/` - Product detail
- `POST /products/<id>/review/` - Add review

## 🚢 Deployment

### Heroku Deployment
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set DJANGO_SETTINGS_MODULE=dolesecommerce.settings.production

# Deploy
git push heroku main
```

### Environment Variables
```bash
# Required for production
DJANGO_SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url
MPESA_CONSUMER_KEY=your_mpesa_key
PI_NETWORK_API_KEY=your_pi_key
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Project Documentation](PROJECT_DOCUMENTATION.md)
- **Issues**: [GitHub Issues](https://github.com/seludoto/dolesecommerce/issues)
- **Discussions**: [GitHub Discussions](https://github.com/seludoto/dolesecommerce/discussions)

## 🏆 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework for perfectionists with deadlines
- [Pi Network](https://minepi.com/) - Making cryptocurrency accessible to everyone
- [Safaricom](https://www.safaricom.co.ke/) - M-Pesa mobile money platform
- [Bootstrap](https://getbootstrap.com/) - Build fast, responsive sites

## 📊 Project Stats

- **Lines of Code**: 10,000+
- **Models**: 15+
- **Views**: 50+
- **Templates**: 30+
- **Payment Methods**: 4 (Pi Coin, M-Pesa, Credit Card, Bank Transfer)

---

⭐ **Star this repository if it helped you!**

Made with ❤️ by [seludoto](https://github.com/seludoto)

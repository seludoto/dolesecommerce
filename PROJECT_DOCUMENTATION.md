# Unique Features & Competitive Edge

## Personalized Shopping
- AI-driven recommendations and personalized content are enabled (see settings.py).

## Advanced Analytics Dashboard
- Business and product analytics are available in the Django admin (analytics app).
- Track sales, user activity, conversion funnels, and A/B tests.

## Multi-Channel Integration
- Social media shop links and sharing are available in the UI (see base.html).

## Loyalty & Referral Programs
- Users can invite friends for referral rewards (see Invite Friends in user menu).
- Loyalty program banner and logic scaffolded in UI.

## Fast, Mobile-First UI
- Responsive, modern UI with Bootstrap 5 and mobile optimizations.

## Localized Experience
- Multi-language and multi-currency support enabled (see settings.py and base.html).

## Enhanced Security & Privacy
- Security best practices enforced (see settings.py and .env.example).

## How to Access Analytics
- Log in to the Django admin panel and view the Analytics section for business metrics, user activity, and product analytics.
# Security & Performance Best Practices

## Security
- Use HTTPS for all traffic (set SECURE_SSL_REDIRECT=True in settings)
- Set strong SECRET_KEY and keep it secret (use environment variables)
- Use Django’s built-in authentication and permissions
- Enable Django security middleware (SecurityMiddleware, XFrameOptionsMiddleware, etc.)
- Set SECURE_HSTS_SECONDS, SECURE_BROWSER_XSS_FILTER, SECURE_CONTENT_TYPE_NOSNIFF
- Use secure cookies (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- Regularly update Django and dependencies
- Restrict admin access (use strong passwords, 2FA, IP allowlist)
- Validate and sanitize all user input
- Store sensitive data encrypted (passwords, payment info)
- Backup database regularly

## Performance
- Enable caching (Redis/Memcached, Django cache framework)
- Use database indexes for frequently queried fields
- Optimize database queries (select_related, prefetch_related)
- Use a CDN for static/media files
- Compress static files (gzip, brotli)
- Use async views for high-latency operations
- Monitor server and database performance (APM, logging)
- Use connection pooling for database
- Run periodic database maintenance (VACUUM, ANALYZE for Postgres)

## Deployment
- Use gunicorn/uwsgi with Nginx/Apache for production
- Run Django in DEBUG=False mode
- Set ALLOWED_HOSTS properly
- Use environment variables for all secrets and config
# dolesecommerce Django Project Documentation

## Overview
This is a comprehensive modern e-commerce web application built with Django 5.2.4. It features advanced payment systems including cryptocurrency (Pi Coin) and mobile money (M-Pesa) integration, along with traditional e-commerce functionality. The platform supports product management, user authentication, advanced payment processing, order management, reviews, shipping, and customer support features. The UI is styled with Bootstrap 5 and includes a professional dark navigation bar, logo, and modern responsive forms.

## Key Features

### 🛍️ **E-Commerce Core**
- Product catalog with categories, brands, and multiple images per product
- Advanced shopping cart with session management
- Buy Now and order management system
- Inventory tracking and stock management
- Product search and filtering

### 👥 **User Management**
- User registration, login, and profile management
- Avatar upload and personal information management
- Address book and phone number management
- User authentication and authorization

### 💳 **Advanced Payment Systems**
- **Pi Coin Cryptocurrency Payments**: Full Pi Network integration with real-time exchange rates
- **M-Pesa Mobile Money**: STK Push and direct phone number payments (B2C/C2B)
- **Traditional Payments**: Credit card and bank transfer support
- Real-time payment processing and status tracking
- Comprehensive payment administration dashboard

### 📱 **Mobile Money Features**
- Send money directly to any M-Pesa phone number
- Request payments via STK Push notifications
- Real-time transaction monitoring
- Automatic callback handling and status updates
- Phone number validation and formatting

### 🏪 **Business Management**
- Review and rating system with moderation
- Shipping management and tracking
- Admin dashboard for comprehensive management
- Customer service with live chat integration
- Email notifications for orders and registration
- Analytics and reporting tools

### 🎨 **User Experience**
- Responsive, modern UI with custom branding
- Professional navigation with user-friendly menus
- Real-time form validation and feedback
- Mobile-optimized design
- Accessibility features

## Technical Architecture

### Project Structure
```
db.sqlite3
manage.py
Procfile                      # Heroku deployment
requirements.txt              # Python dependencies
PROJECT_DOCUMENTATION.md     # This file
PHONE_PAYMENT_DOCUMENTATION.md # M-Pesa integration guide

core/                        # Home, navigation, support views
├── models.py               # Core models
├── views.py                # Main views
├── urls.py                 # URL patterns
└── templates/core/         # Core templates

products/                   # Product management
├── models.py              # Product, Category, Brand models
├── views.py               # Product views and API
├── admin.py               # Product administration
└── templates/products/    # Product templates

orders/                    # Order processing
├── models.py             # Order and order item models
├── views.py              # Order management views
└── templates/orders/     # Order templates

payments/                 # Advanced payment systems
├── models.py            # Payment, Pi, M-Pesa models
├── views.py             # Payment processing views
├── mpesa.py             # M-Pesa Daraja API client
├── pi_network.py        # Pi Network API integration
├── admin.py             # Payment administration
└── templates/payments/  # Payment UI templates

users/                   # User management
├── models.py           # User profile models
├── views.py            # User authentication views
├── forms.py            # User forms
└── templates/users/    # User interface templates

reviews/                # Product reviews
shipping/               # Shipping management
analytics/              # Business analytics
notifications/          # Notification system
promotions/             # Promotional campaigns

static/                 # Static assets
├── images/            # Site images and logos
└── css/               # Custom stylesheets

media/                 # User uploads
└── product_images/    # Product image uploads

templates/             # Shared templates
└── base.html         # Main layout template
```

### Database Models

#### **Core Models**
- **Category**: Product categorization (name, description, hierarchy)
- **Brand**: Product brands (name, description, logo)
- **Product**: Main product model (name, description, price, stock, images)
- **ProductImage**: Multiple images per product support

#### **User Models**
- **UserProfile**: Extended user information (phone, address, avatar)
- **User**: Django's built-in user model with custom extensions

#### **Order Models**
- **Order**: Order tracking (user, products, status, timestamps)
- **OrderItem**: Individual items within orders
- **Cart**: Shopping cart management

#### **Payment Models**
- **Payment**: Main payment tracking (method, status, amounts)
- **PiCoinRate**: Real-time Pi cryptocurrency exchange rates
- **PiPaymentTransaction**: Pi Network payment tracking
- **MpesaB2CTransaction**: Business-to-customer M-Pesa payments
- **MpesaC2BTransaction**: Customer-to-business M-Pesa payments
- **PhonePayment**: High-level phone payment management

#### **Supporting Models**
- **Review**: Product reviews and ratings
- **Shipping**: Order shipping and delivery tracking
- **Notification**: System notifications

### Key Templates

#### **Base Templates**
- `base.html`: Main layout with navigation, logo, and responsive design
- `admin/`: Custom admin interface templates

#### **E-Commerce Templates**
- `products/product_list.html`: Product catalog with filtering
- `products/product_detail.html`: Detailed product view with purchasing options
- `orders/order_detail.html`: Order tracking and management

#### **User Interface**
- `users/register.html`: User registration with validation
- `users/login.html`: User authentication
- `users/profile.html`: User profile management
- `users/profile_edit.html`: Profile editing interface

#### **Payment System Templates**
- `payments/pay_order_pi.html`: Pi Coin payment interface
- `payments/phone_payment_dashboard.html`: M-Pesa management dashboard
- `payments/send_money_to_phone.html`: Money transfer interface
- `payments/request_payment_from_phone.html`: STK Push request form

#### **Support Templates**
- `core/customer_service.html`: Customer support with live chat

## Payment Systems Integration

### 🪙 **Pi Coin Cryptocurrency Payments**

#### Features
- Real-time Pi to USD exchange rate management
- Secure Pi Network API integration
- Transaction validation and processing
- Admin panel for payment confirmation
- Automatic order status updates

#### Technical Implementation
```python
# Pi Network API Integration
class PiNetworkAPI:
    def create_payment(self, amount_usd, order_reference):
        # Convert USD to Pi using current exchange rate
        pi_rate = PiCoinRate.get_current_rate()
        pi_amount = amount_usd / pi_rate
        # Process payment through Pi Network
```

#### Configuration
```python
# Pi Network Settings
PI_NETWORK_API_KEY = 'your_pi_api_key'
PI_WALLET_ADDRESS = 'your_pi_wallet_address'
PI_SANDBOX_MODE = True  # Set to False for production
PI_WEBHOOK_SECRET = 'your_webhook_secret'
PI_DEFAULT_RATE = 0.314159  # Default Pi to USD rate
```

### 📱 **M-Pesa Mobile Money Integration**

#### Features
- **Send Money (B2C)**: Direct transfers to customer phone numbers
- **Request Payment (STK Push)**: Customer payment requests
- **Real-time Processing**: Instant transaction processing
- **Callback Handling**: Automatic status updates
- **Phone Validation**: Multiple format support

#### Technical Implementation
```python
# M-Pesa Daraja API Client
class MpesaDarajaAPI:
    def b2c_payment(self, phone_number, amount, remarks):
        # Send money directly to customer phone
    
    def stk_push(self, phone_number, amount, reference):
        # Request payment from customer phone
```

#### Configuration
```python
# M-Pesa Daraja API Settings
MPESA_CONSUMER_KEY = 'your_consumer_key'
MPESA_CONSUMER_SECRET = 'your_consumer_secret'
MPESA_SHORTCODE = 'your_shortcode'
MPESA_PASSKEY = 'your_passkey'
MPESA_BASE_URL = 'https://sandbox.safaricom.co.ke'

# B2C Settings
MPESA_INITIATOR_NAME = 'your_initiator_name'
MPESA_SECURITY_CREDENTIAL = 'your_encrypted_password'
SITE_URL = 'https://your-domain.com'
```

#### Phone Number Support
- `0712345678` (Kenyan format)
- `+254712345678` (International format)
- `254712345678` (Country code format)

### 💳 **Traditional Payment Methods**
- Credit/Debit card processing
- Bank transfer integration
- PayPal support
- Cryptocurrency wallet payments

## Administration Features

### 🎛️ **Payment Administration Dashboard**
- Real-time transaction monitoring
- Payment method statistics
- User payment history
- Refund and dispute management
- Financial reporting tools

### 📊 **Business Analytics**
- Sales performance tracking
- Payment method analytics
- Customer behavior insights
- Revenue reporting
- Inventory management

### 👨‍💼 **User Management**
- User account management
- Permission and role assignment
- Activity monitoring
- Support ticket management

## Security Features

### 🔒 **Payment Security**
- PCI DSS compliance measures
- Encrypted transaction data
- Secure API communication
- Fraud detection algorithms
- Transaction validation

### 🛡️ **System Security**
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure file uploads
- User input validation

### 🔐 **Authentication & Authorization**
- Multi-factor authentication support
- Role-based access control
- Session management
- Password security requirements
- Account lockout policies

## API Documentation

### Payment APIs
- **Pi Network API**: Cryptocurrency payment processing
- **M-Pesa Daraja API**: Mobile money integration
- **Internal Payment API**: Order and transaction management

### Integration Examples
```python
# Pi Payment Example
from payments.pi_network import pi_processor
result = pi_processor.create_payment(amount_usd=10.00, order_id=123)

# M-Pesa Payment Example
from payments.mpesa import mpesa_processor
result = mpesa_processor.send_money_to_phone(
    phone_number="+254712345678",
    amount=1000,
    description="Order refund"
)
```

## Deployment & Configuration

### 🚀 **Production Deployment**
- Heroku-ready with Procfile
- Environment variable configuration
- Static file management
- Database migration scripts
- SSL certificate setup

### ⚙️ **Environment Configuration**
```python
# Essential Settings
DEBUG = False  # Set to False in production
ALLOWED_HOSTS = ['your-domain.com']
SECRET_KEY = 'your-secret-key'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # ... database settings
    }
}

# Static Files
STATIC_ROOT = '/path/to/static/files'
MEDIA_ROOT = '/path/to/media/files'
```

### 📦 **Dependencies**
```
Django==5.2.4
Pillow>=10.0.0
requests>=2.31.0
python-decouple>=3.8
gunicorn>=21.2.0
whitenoise>=6.5.0
psycopg2-binary>=2.9.7
```

## Development Setup

### 🔧 **Installation**
```bash
# Clone repository
git clone <repository-url>
cd dolesecommerce

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your settings

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

### 🧪 **Testing**
```bash
# Run tests
python manage.py test

# Test specific app
python manage.py test payments

# Test with coverage
coverage run --source='.' manage.py test
coverage report
```

## Usage Guide

### 👨‍💼 **For Administrators**

1. **Access Admin Panel**
   - Navigate to `/admin/`
   - Use superuser credentials
   - Manage products, orders, users, and payments

2. **Payment Management**
   - Access "Phone Payments" from user menu
   - Send money directly to customer phones
   - Request payments via STK Push
   - Monitor all transactions in real-time

3. **Pi Coin Management**
   - Set exchange rates in admin panel
   - Confirm Pi payments manually if needed
   - Monitor Pi transaction status

### 🛒 **For Customers**

1. **Shopping Experience**
   - Browse products by category
   - Add items to cart
   - Use "Buy Now" for quick purchases

2. **Payment Options**
   - Choose Pi Coin for cryptocurrency payment
   - Use M-Pesa for mobile money payment
   - Traditional card payments available

3. **Account Management**
   - Create account and manage profile
   - Track order history
   - Leave product reviews

## Troubleshooting

### 🔧 **Common Issues**

#### **Payment Problems**
- **Pi Payment Stuck**: Check Pi Network connectivity and exchange rate
- **M-Pesa Callback Issues**: Verify callback URLs and SSL certificates
- **Transaction Timeouts**: Check API credentials and network connection

#### **System Issues**
- **Static Files 404**: Run `python manage.py collectstatic`
- **Database Errors**: Apply migrations with `python manage.py migrate`
- **Template Errors**: Ensure `{% load static %}` is included

#### **Performance Issues**
- **Slow Loading**: Optimize database queries and enable caching
- **Memory Usage**: Check for memory leaks in payment processing
- **API Timeouts**: Implement proper timeout handling

### 📞 **Support Resources**
- Django Documentation: https://docs.djangoproject.com/
- Pi Network Developer Portal: https://developers.minepi.com/
- Safaricom Daraja API: https://developer.safaricom.co.ke/
- Bootstrap Documentation: https://getbootstrap.com/

## Future Enhancements

### 🚀 **Planned Features**
- **Multi-currency Support**: Additional cryptocurrency options
- **Advanced Analytics**: Machine learning-powered insights
- **Mobile App**: React Native companion app
- **AI Chatbot**: Automated customer support
- **Inventory Automation**: Smart restocking algorithms

### 🔄 **Continuous Improvements**
- Performance optimization
- Security enhancements
- User experience improvements
- Payment method additions
- Integration expansions

## Contributing

### 📝 **Development Guidelines**
- Follow Django best practices
- Write comprehensive tests
- Document new features
- Follow PEP 8 style guidelines
- Use semantic versioning

### 🔍 **Code Review Process**
- All changes require pull requests
- Automated testing must pass
- Security review for payment features
- Performance impact assessment

---

## Contact & Support

For technical support, feature requests, or contributions:
- Project Repository: [GitHub Repository]
- Documentation: This file and PHONE_PAYMENT_DOCUMENTATION.md
- Issue Tracking: GitHub Issues
- Developer Contact: [Contact Information]


**Last Updated**: August 9, 2025
**Version**: 2.0.1
**Django Version**: 5.2.4

## Deployment & Environment Variables

### Environment Variables
For secure and production-ready deployment, set the following in your environment or `.env` file:

```
DJANGO_SECRET_KEY=your-very-secret-key
DJANGO_DEBUG=False
DATABASE_URL=your-production-database-url
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
STATIC_URL=/static/
STATIC_ROOT=/app/staticfiles
```

### Build & Run Commands
For production deployment (e.g., Heroku, Render, Railway):

```
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn dolesecommerce.wsgi
```

### Migration & Database Health
- All unnecessary files, test scripts, and cache files have been removed for a clean workspace.
- If you encounter migration errors (e.g., table already exists), use `--fake` migrations to sync the DB state:
   ```
   python manage.py migrate payments 0004_mpesab2ctransaction_mpesac2btransaction_phonepayment_and_more --fake
   python manage.py migrate
   ```

### Project Health Checklist
- [x] All migrations applied and database is in sync
- [x] No unnecessary files or cache in the repository
- [x] Static files collected and served correctly
- [x] Admin and frontend tested and working
- [x] Environment variables documented and example provided (`.env.example`)


## Pi Coin Payments Integration
To enable Pi Coin payments in your app, use the official Pi Network JS SDK. This allows users to pay with Pi directly from the Pi Wallet.

### Steps to Integrate Pi Coin Payments
1. **Add the Pi SDK to your template:**
   Add the following script tags to your main template (e.g., `base.html`):
   ```html
   <script src="https://sdk.minepi.com/pi-sdk.js"></script>
   <script>Pi.init({ version: "2.0" })</script>
   ```

2. **Authenticate the user:**
   Before requesting payments, authenticate the user:
   ```javascript
   const scopes = ['payments'];
   Pi.authenticate(scopes, function onIncompletePaymentFound(payment) {
     // Handle incomplete payments
   }).then(function(auth) {
     console.log("User authenticated for Pi payments.");
   }).catch(function(error) {
     console.error(error);
   });
   ```

3. **Request a payment:**
   Use the SDK to prompt the user for payment:
   ```javascript
   Pi.createPayment({
     amount: 3.14, // Amount of Pi
     memo: "Order #1234", // Description for the user
     metadata: { orderId: 1234 }
   }, {
     onReadyForServerApproval: function(paymentId) { /* ... */ },
     onReadyForServerCompletion: function(paymentId, txid) { /* ... */ },
     onCancel: function(paymentId) { /* ... */ },
     onError: function(error, payment) { /* ... */ }
   });
   ```

4. **Handle server-side approval/completion:**
   For advanced flows (App-to-User payments, server confirmation), refer to the [Pi Platform Docs](https://github.com/pi-apps/pi-platform-docs) and their `payments_advanced.md` and `platform_API.md` files.

### Resources
- [Pi Platform Docs](https://github.com/pi-apps/pi-platform-docs)
- [SDK Reference](https://github.com/pi-apps/pi-platform-docs/blob/master/SDK_reference.md)
- [Payments Guide](https://github.com/pi-apps/pi-platform-docs/blob/master/payments.md)

This integration allows your Django app to accept Pi Coin payments securely and easily.

## Running the Project
1. Install dependencies: `pip install -r requirements.txt`
2. Apply migrations: `python manage.py migrate`
3. Create superuser: `python manage.py createsuperuser`
4. Run server: `python manage.py runserver`
5. Access site at `http://localhost:8000/`

## Admin Access
- Login at `/admin/` with superuser credentials

## Notes
- Ensure all static and media files are correctly named and placed
- Use `{% load static %}` and `{% static 'images/logo.png' %}` in templates
- For support, check `core/customer_service.html` and related views

---

## Example Admin/User Credentials
- Admin: Use the credentials created with `python manage.py createsuperuser` to log in at `/admin/`.
- Users: Register via `/users/register/` or create users in the admin panel.

## Sample Data Creation
To quickly add sample products, categories, and brands:
1. Log in to the Django admin at `/admin/`.
2. Add categories, brands, and products using the admin interface.
3. Upload product images via the product or product image forms.
4. Create test orders and payments to see the workflow.

## Troubleshooting Common Errors
- **Static/Media 404s**: Ensure files are named correctly and placed in the right folders. Run `python manage.py collectstatic` if needed.
- **Template Errors**: Always use `{% load static %}` at the top of templates using static files.
- **NoReverseMatch**: Check that your URLs and template tags match the namespaced URL patterns.
- **Image Not Displaying**: Confirm the image path and filename match what is referenced in the template.
- **Database Issues**: Run migrations with `python manage.py migrate` and check for missing fields.

## More Details on Models and Views
- **Category/Brand/Product**: Organize products for easy browsing and filtering.
- **ProductImage**: Allows multiple images per product for better presentation.
- **UserProfile**: Stores extra user info (phone, address, avatar) for personalized experience.
- **Order/Payment/Shipping**: Handles the full purchase and delivery workflow.
- **Review**: Lets users rate and review products.
- **Customer Service**: Provides support, live chat, FAQ, and feedback forms.

## Learning Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap Documentation](https://getbootstrap.com/)
- [Django Admin Guide](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/)

---
For further customization or feature requests, contact the project maintainer.

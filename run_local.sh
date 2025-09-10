 #!/bin/bash

# Local Development Setup Script for Django Ecommerce
echo "🚀 Setting up Django Ecommerce for local development..."

# Check if virtual environment exists
if [ ! -d "env" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python3 -m venv env"
    echo "   source env/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source env/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file for local development..."
    cat > .env << EOF
# Local Development Environment Variables
SECRET_KEY=django-insecure-local-development-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Email Settings (optional)
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password

# AWS Settings (optional)
# AWS_ACCESS_KEY_ID=your-aws-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret
# AWS_STORAGE_BUCKET_NAME=your-bucket-name

# Razorpay Settings (optional)
# RAZORPAY_KEY_ID=your-razorpay-key
# RAZORPAY_KEY_SECRET=your-razorpay-secret
EOF
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create superuser (optional)
echo "👤 Do you want to create a superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python manage.py createsuperuser
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start development server
echo "🌐 Starting development server..."
echo "📍 Your site will be available at: http://localhost:8000"
echo "📍 Admin panel: http://localhost:8000/admin"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver 0.0.0.0:8000

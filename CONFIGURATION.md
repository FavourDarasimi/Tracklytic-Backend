# Environment Configuration Guide

## Required Environment Variables

Create a `.env` file in the root directory with the following variables:

### Django Settings

```
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### AI Configuration

```
GEMINI_API_KEY=your-gemini-api-key-here
```

### Email Configuration

```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Mono Integration (Optional)

```
MONO_PUBLIC_KEY=your-mono-public-key
MONO_SECRET_KEY=your-mono-secret-key
```

### CORS Settings

```
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Getting API Keys

### Google Gemini AI

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY`

### Gmail App Password

1. Go to your Google Account settings
2. Enable 2-factor authentication
3. Generate an App Password for your application
4. Add it to your `.env` file as `EMAIL_HOST_PASSWORD`

## Production Settings

For production deployment, make sure to:

1. Set `DEBUG=False`
2. Use a strong `SECRET_KEY`
3. Configure a production database (PostgreSQL recommended)
4. Set up proper `ALLOWED_HOSTS`
5. Configure email settings
6. Set up SSL/TLS certificates
7. Use environment variables for sensitive data

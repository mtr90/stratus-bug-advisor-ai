# STRATUS Bug Advisor

AI-Powered Bug Resolution System for STRATUS Products

## Overview

STRATUS Bug Advisor is a professional knowledge management system that provides AI-powered bug analysis and resolution guidance for STRATUS products including Allocator, FormsPlus, Premium Tax, and Municipal.

## Features

- **🎯 Product-Specific Analysis**: Tailored bug analysis for each STRATUS product
- **🤖 Claude AI Integration**: Powered by Anthropic's Claude for intelligent responses
- **📊 Admin Dashboard**: Complete system management and analytics
- **🔒 Secure Configuration**: Safe API key management and system monitoring
- **📱 Responsive Design**: Professional UI that works on all devices
- **⚡ Real-time Analytics**: Usage statistics and system health monitoring

## Architecture

### Frontend (React + Vite)
- Modern React application with TypeScript support
- Tailwind CSS for styling
- shadcn/ui components for professional UI
- Responsive design with dark theme

### Backend (Flask)
- RESTful API with Flask
- Claude API integration for AI responses
- SQLite database for development
- Supabase integration for production
- Rate limiting and caching support

### Deployment
- **Frontend**: Vercel hosting
- **Database**: Supabase PostgreSQL
- **Version Control**: GitHub
- **MCP Integration**: Automated deployment pipeline

## Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.11+
- Claude API key from Anthropic

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stratus-bug-advisor
   ```

2. **Setup Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Add your Claude API key to .env
   python app.py
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000

### Production Deployment

The application is configured for automatic deployment:

1. **Push to GitHub** - Triggers Vercel deployment
2. **Supabase Database** - Automatic schema migration
3. **Environment Variables** - Configured in Vercel dashboard

## Configuration

### Environment Variables

**Backend (.env)**
```
CLAUDE_API_KEY=sk-ant-api03-your-key-here
DATABASE_URL=postgresql://... (for production)
REDIS_URL=redis://... (optional)
```

**Frontend (Vercel)**
```
VITE_API_URL=https://your-backend-url.vercel.app
```

## API Endpoints

### Bug Analysis
- `POST /api/analyze` - Analyze bug reports
- `GET /api/products` - List supported products

### Admin Dashboard
- `GET /api/admin/config` - Get configuration
- `POST /api/admin/config` - Save configuration
- `GET /api/admin/status` - System health check
- `GET /api/admin/stats` - Usage analytics
- `POST /api/admin/test-claude` - Test Claude API

## Usage

### Bug Analysis Workflow

1. **Select Product**: Choose from Allocator, FormsPlus, Premium Tax, or Municipal
2. **Describe Issue**: Enter bug description or use example queries
3. **Get Analysis**: Receive structured AI-powered analysis including:
   - Root cause analysis
   - Immediate solutions
   - Files/areas to check
   - Testing steps
   - Related historical issues

### Admin Dashboard

1. **Configuration**: Set up Claude API key
2. **System Status**: Monitor database, API, and cache health
3. **Analytics**: View usage statistics and system metrics

## STRATUS Products Supported

### Allocator
- TTS tickets and geocoding issues
- Batch processing problems
- Allocation algorithm errors
- Address standardization issues

### FormsPlus
- ClickUp tickets and form tree issues
- Field validation problems
- Dynamic form generation errors
- User permission issues

### Premium Tax
- Tax calculation errors
- E-filing problems
- Rate table issues
- Compliance validation

### Municipal
- Municipal code issues
- Rate calculation problems
- Jurisdiction mapping errors
- Data import issues

## Development

### Project Structure
```
stratus-bug-advisor/
├── frontend/          # React application
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── backend/           # Flask API
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── app.py
│   └── requirements.txt
├── database/          # Database schema
│   └── schema.sql
└── README.md
```

### Adding New Features

1. **Frontend Components**: Add to `frontend/src/components/`
2. **API Endpoints**: Add to `backend/routes/`
3. **Database Changes**: Update `database/schema.sql`

## Deployment

### Vercel Deployment

The project includes Vercel configuration for automatic deployment:

1. **Connect GitHub repository** to Vercel
2. **Configure environment variables** in Vercel dashboard
3. **Deploy automatically** on git push

### Supabase Setup

1. **Create Supabase project**
2. **Run database migrations**
3. **Configure connection string**

## Support

For technical support or feature requests:
- Create GitHub issues for bugs
- Submit feature requests via GitHub discussions
- Contact STRATUS development team for urgent issues

## License

© 2024 STRATUS Bug Advisor. All rights reserved.

---

**Powered by Claude AI** | **Built with React & Flask** | **Deployed on Vercel**

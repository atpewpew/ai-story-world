# Quick Deployment Guide

## 🚀 Deploy to Cloud (Render/Railway/Fly.io)

### Prerequisites
- GitHub account
- Cloud platform account (Render/Railway/Fly.io)
- Google Gemini API key

### Steps

#### 1. Push to GitHub
```bash
git add -A
git commit -m "Prepare for deployment"
git push origin main
```

#### 2. Deploy on Render (Recommended - Free Tier)

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ai-story-world`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd ai_story && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

5. Add Environment Variables:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   API_TOKEN=123456
   VECTOR_BACKEND=memory
   ```

6. Click "Create Web Service"
7. Wait 5-10 minutes for deployment
8. Your API will be live at: `https://your-app.onrender.com`

#### 3. Alternative: Railway

1. Go to [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub"
3. Select repository
4. Add environment variables (same as above)
5. Railway auto-detects Python and deploys

#### 4. Alternative: Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch (creates fly.toml)
fly launch

# Set secrets
fly secrets set GOOGLE_API_KEY=your_key
fly secrets set API_TOKEN=123456

# Deploy
fly deploy
```

### Frontend Deployment

#### Option A: Vercel (Recommended)

1. Go to [vercel.com](https://vercel.com)
2. Import repository
3. Select `web` directory as root
4. Environment variables:
   ```
   VITE_API_BASE=https://your-backend.onrender.com
   ```
5. Deploy

#### Option B: Netlify

1. Go to [netlify.com](https://netlify.com)
2. Drag & drop `web/dist` folder (after `npm run build`)
3. Or connect GitHub and set:
   - Base directory: `web`
   - Build command: `npm run build`
   - Publish directory: `web/dist`

### Testing Deployment

```bash
# Health check
curl https://your-app.onrender.com/health

# Create session
curl -X POST https://your-app.onrender.com/create_session \
  -H "Authorization: Bearer 123456" \
  -H "Content-Type: application/json" \
  -d '{"character_name":"Alice","genre":"fantasy","tone":"adventurous"}'
```

## 📝 Notes

- **Minimal Setup**: Current requirements.txt is ~50MB (no GPU dependencies)
- **Storage**: Uses in-memory storage by default (resets on restart)
- **Database**: Redis/Neo4j optional for production
- **Scaling**: Add Redis/Neo4j when needed
- **Cost**: Free tier sufficient for portfolio demo

## 🔧 Troubleshooting

**Port issues**: Cloud platforms use `$PORT` environment variable
**Timeout**: Increase if Gemini API calls are slow
**Memory**: 512MB minimum recommended
**Cold starts**: First request may take 10-15 seconds

## 💡 Production Enhancements

When ready to scale:
1. Add external Redis (Upstash free tier)
2. Add Neo4j (Neo4j Aura free tier)
3. Enable vector storage if needed
4. Add rate limiting
5. Set up monitoring

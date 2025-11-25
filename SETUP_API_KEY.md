# 🚀 HOW TO ACTIVATE YOUR API KEY

## Follow These Steps:

### 1️⃣ **Get Your API Key** (Just Opened in Browser)
   - If browser didn't open, go to: https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click **"Create API Key"**
   - Copy the key (starts with `AIza...`)

### 2️⃣ **Add Key to .env File**
   
   Open your `.env` file and replace this line:
   ```
   GOOGLE_API_KEY=test_key_for_demo
   ```
   
   With your real key:
   ```
   GOOGLE_API_KEY=AIzaSyD-your-actual-key-paste-it-here
   ```

### 3️⃣ **Test Your API Key Works**
   
   Run this command:
   ```bash
   python main.py --demo
   ```
   
   You should see:
   - ✅ "Root Orchestrator initialized with Gemini 1.5 Pro"
   - ✅ All 4 agents working with AI analysis
   - ✅ NO warning about "test API key"

---

## ⚡ Quick Commands:

```powershell
# Open .env file in VS Code
code .env

# After adding your key, test it:
python main.py --demo

# Or scan a specific file:
python main.py --scan demo/vulnerable_code.py
```

---

## ✅ What Will Work After Adding API Key:

- 🤖 **AI-Powered Security Analysis** - Deep code understanding
- 🧠 **Policy Engine Learning** - Adaptive decision making
- 💬 **Natural Language Explanations** - AI-generated insights
- 🎯 **Context-Aware Scanning** - Smart vulnerability detection
- 📊 **Intelligent Risk Scoring** - ML-based risk assessment

---

## 🔒 Is This Safe?

✅ **YES!** Your `.env` file is:
- Already in `.gitignore` (won't be committed to Git)
- Only on your local computer
- Never shared or pushed to GitHub

---

## 🆘 Need Help?

**If you get errors:**
1. Make sure you copied the FULL API key (starts with `AIza`)
2. No extra spaces before or after the key
3. Save the `.env` file after editing

**Test it works:**
```bash
python main.py --show-config
```

Should show your API key is configured (masked for security).

---

## 🎉 You're Almost There!

Just replace `test_key_for_demo` with your real API key in `.env` and all agents will work! 🚀

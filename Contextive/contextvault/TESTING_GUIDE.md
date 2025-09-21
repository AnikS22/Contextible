# 🧪 ContextVault Testing Guide

## **✅ VERIFIED: System Works!**

The initialization just worked perfectly! Here's your complete testing guide:

---

## **🚀 Quick Test (5 minutes)**

### **1. Initialize System**
```bash
cd /Users/aniksahai/Desktop/Contextive/contextvault
PYTHONPATH=. python cli/main.py init
```
**Expected:** ✅ Success message with next steps

### **2. Add Context**
```bash
PYTHONPATH=. python cli/main.py context add "I am a software engineer who loves Python and testing"
```
**Expected:** ✅ Context entry created with ID

### **3. Set Permissions**
```bash
PYTHONPATH=. python cli/main.py permissions add mistral:latest --scope="preferences,notes"
```
**Expected:** ✅ Permission created for mistral:latest

### **4. Start Services**
```bash
# Terminal 1: Start API server
PYTHONPATH=. python cli/main.py serve &

# Terminal 2: Start proxy
PYTHONPATH=. python cli/main.py proxy &
```
**Expected:** ✅ Both services start without errors

### **5. Test Context Injection**
```bash
# Test with model that has permissions
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?", "stream": false, "options": {"num_predict": 50}}'
```
**Expected:** ✅ Model responds with personal context

---

## **🔬 Comprehensive Test Suite**

### **Test 1: Database Operations**
```bash
# Test context management
PYTHONPATH=. python cli/main.py context add "Test context entry"
PYTHONPATH=. python cli/main.py context list
PYTHONPATH=. python cli/main.py context search "test"
```

### **Test 2: Permission System**
```bash
# Test permission management
PYTHONPATH=. python cli/main.py permissions add codellama:13b --scope="work"
PYTHONPATH=. python cli/main.py permissions list
PYTHONPATH=. python cli/main.py permissions check mistral:latest --scope="preferences"
```

### **Test 3: API Endpoints**
```bash
# Test health endpoint
curl http://localhost:8000/health/

# Test context API
curl http://localhost:8000/api/context/

# Test permissions API
curl http://localhost:8000/api/permissions/
```

### **Test 4: Context Injection**
```bash
# Test with permission
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "Hello", "stream": false}'

# Test without permission
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:13b", "prompt": "Hello", "stream": false}'
```

---

## **📊 Expected Results**

### **✅ Success Indicators**
- Database initializes without errors
- Context entries are created and retrieved
- Permissions are enforced correctly
- API endpoints return 200 OK
- Proxy forwards requests to Ollama
- Context injection works (access counts increase)
- Models with permissions get personalized responses
- Models without permissions get generic responses

### **❌ Failure Indicators**
- Import errors or module not found
- Database connection failures
- Permission denied errors
- 404 or 500 HTTP errors
- Context injection not working
- Models responding identically regardless of permissions

---

## **🐛 Troubleshooting**

### **Common Issues**

**1. "Module not found" errors**
```bash
# Solution: Always use PYTHONPATH
PYTHONPATH=. python cli/main.py <command>
```

**2. "Address already in use"**
```bash
# Solution: Kill existing processes
pkill -f contextvault
```

**3. "Permission denied"**
```bash
# Solution: Check Ollama is running
curl http://localhost:11434/api/tags
```

**4. "Context injection not working"**
```bash
# Solution: Check permissions and context entries
PYTHONPATH=. python cli/main.py context list
PYTHONPATH=. python cli/main.py permissions list
```

---

## **🎯 Demo Commands**

### **Perfect Demo Sequence**
```bash
# 1. Clean start
cd /Users/aniksahai/Desktop/Contextive/contextvault
pkill -f contextvault
rm -f contextvault.db

# 2. Initialize
PYTHONPATH=. python cli/main.py init

# 3. Add context
PYTHONPATH=. python cli/main.py context add "I am a software engineer who loves Python, testing, and building local AI tools"

# 4. Set permissions
PYTHONPATH=. python cli/main.py permissions add mistral:latest --scope="preferences,notes"

# 5. Start services
PYTHONPATH=. python cli/main.py serve &
PYTHONPATH=. python cli/main.py proxy &

# 6. Test direct Ollama (should be generic)
curl -X POST "http://localhost:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?", "stream": false, "options": {"num_predict": 30}}'

# 7. Test through proxy (should be personalized)
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?", "stream": false, "options": {"num_predict": 50}}'

# 8. Test permission enforcement
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:13b", "prompt": "What do you know about me?", "stream": false, "options": {"num_predict": 30}}'
```

---

## **🎬 Recording Tips**

### **For Demo Video**
1. **Use 3 terminal windows** side by side
2. **Highlight the key difference**: port 11434 vs 11435
3. **Show the responses clearly** - pause for reading
4. **Emphasize the permission system** working
5. **Keep it under 60 seconds** total

### **Key Moments to Capture**
- ✅ Initialization success
- ✅ Context entry creation
- ✅ Permission setup
- ✅ Direct Ollama response (generic)
- ✅ Proxy response (personalized)
- ✅ Permission enforcement (denied access)

---

## **🏆 Success Criteria**

**Your system is working if:**
- ✅ All CLI commands execute without errors
- ✅ API endpoints return healthy status
- ✅ Context injection increases access counts
- ✅ Models with permissions get personalized responses
- ✅ Models without permissions get generic responses
- ✅ Permission system enforces access control

**You're ready to demo if:**
- ✅ You can run the demo sequence in under 2 minutes
- ✅ The responses show clear differences
- ✅ No error messages appear
- ✅ All services start successfully

---

## **🚀 Next Steps After Testing**

1. **Record demo video** using the demo sequence
2. **Share on Reddit** with the demo
3. **Collect user feedback**
4. **Plan first MCP integration**

**You have a working system! Time to show it to the world!** 🎉

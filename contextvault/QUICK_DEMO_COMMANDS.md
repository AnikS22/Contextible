# 🎬 Quick Demo Commands for Video Recording

## **Setup for Demo**
```bash
# Clean start
cd /Users/aniksahai/Desktop/Contextive/contextvault
pkill -f contextvault
rm -f contextvault.db

# Initialize fresh system
./contextvault-cli init
```

## **Demo Sequence**

### **1. Add Context (5 seconds)**
```bash
./contextvault-cli context add "I am a software engineer who loves Python, testing, and building local AI tools. I prefer detailed explanations and want to understand exactly how systems work."
```

### **2. Set Permissions (5 seconds)**
```bash
./contextvault-cli permissions add mistral:latest --scope="preferences,notes" --description="Personal assistant"
```

### **3. Show Direct Ollama (10 seconds)**
```bash
# Terminal 1: Start Ollama (if not running)
# Terminal 2: Test direct access
curl -X POST "http://localhost:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?", "stream": false, "options": {"num_predict": 30}}'
```

### **4. Start ContextVault (5 seconds)**
```bash
# Terminal 3: Start API server
./contextvault-cli serve &

# Terminal 4: Start proxy
./contextvault-cli proxy &
```

### **5. Show Context Injection (15 seconds)**
```bash
# Same question through proxy
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?", "stream": false, "options": {"num_predict": 50}}'
```

### **6. Show Permission System (10 seconds)**
```bash
# Test with model that has no permissions
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:13b", "prompt": "What do you know about me?", "stream": false, "options": {"num_predict": 30}}'
```

### **7. Show Management (10 seconds)**
```bash
./contextvault-cli context list
./contextvault-cli permissions list
./contextvault-cli status
```

## **Expected Results**

### **Direct Ollama Response:**
```
"I don't have any information about you..."
```

### **ContextVault Response (mistral:latest):**
```
"Based on our previous interactions, you're a software engineer who loves Python, testing, and building local AI tools..."
```

### **ContextVault Response (codellama:13b - no permissions):**
```
"I'm just an AI, I don't have access to your personal information..."
```

## **Recording Tips**

1. **Use 3-4 terminal windows** side by side
2. **Highlight the key difference**: port 11434 vs 11435
3. **Show the responses clearly** - pause for reading
4. **Emphasize the permission system** working
5. **Keep it under 60 seconds** total

## **Backup Plan**
If anything goes wrong during recording:
- Have the commands ready to copy/paste
- Record in sections and edit together
- Focus on the key moment: the response difference

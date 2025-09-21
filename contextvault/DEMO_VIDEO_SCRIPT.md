# 🎬 ContextVault Demo Video Script (60 seconds)

## **Hook (0-5 seconds)**
**Screen:** Terminal with Ollama running
**Voice:** "Your local AI models have no memory. Every conversation starts from scratch."

## **Problem (5-15 seconds)**
**Screen:** Show two identical prompts to Ollama
```
curl -X POST "http://localhost:11434/api/generate" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'
```
**Response:** "I don't have any information about you..."
**Voice:** "Same question, same generic response."

## **Solution Intro (15-25 seconds)**
**Screen:** Show ContextVault CLI
```bash
./contextvault-cli context add "I'm a Python developer who loves testing"
./contextvault-cli permissions add mistral:latest --scope="preferences"
```
**Voice:** "ContextVault gives your local AI models persistent memory while keeping your data private."

## **The Magic (25-45 seconds)**
**Screen:** Show the proxy in action
```bash
# Start proxy
./contextvault-cli proxy

# Same question through proxy
curl -X POST "http://localhost:11435/api/generate" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'
```
**Response:** "Based on our previous interactions, you're a Python developer who loves testing..."
**Voice:** "Now your AI remembers! Context injection happens automatically."

## **Key Features (45-55 seconds)**
**Screen:** Quick montage of CLI commands
```bash
./contextvault-cli context list
./contextvault-cli permissions list
./contextvault-cli status
```
**Voice:** "Full CLI control, permission system, and local-first privacy."

## **Call to Action (55-60 seconds)**
**Screen:** GitHub repo URL
**Voice:** "Try ContextVault today. Your local AI models deserve memory."

---

## **Recording Tips**

### **Setup**
- Use a dark terminal theme (looks more professional)
- Record at 1080p, 60fps
- Use a good microphone
- Screen recording software: OBS or QuickTime

### **Timing**
- Keep each command visible for 2-3 seconds
- Pause briefly after each response
- Use smooth transitions between terminal windows

### **Visual Elements**
- Highlight the key difference: port 11434 vs 11435
- Show the context injection happening in real-time
- Use terminal highlighting for important commands

### **Audio**
- Clear, confident voice
- Emphasize "local-first" and "privacy"
- Pause for dramatic effect after showing the difference

---

## **Alternative Shorter Version (30 seconds)**

### **Hook (0-5 seconds)**
**Voice:** "Your local AI has no memory. ContextVault fixes that."

### **Demo (5-25 seconds)**
**Screen:** Side-by-side comparison
- Left: Direct Ollama (generic response)
- Right: ContextVault proxy (personalized response)
**Voice:** "Add context, set permissions, get personalized responses."

### **CTA (25-30 seconds)**
**Screen:** GitHub link
**Voice:** "ContextVault: Local AI with memory. Try it now."

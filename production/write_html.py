html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Avaniko AI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0d0d0d;color:#ececec;height:100vh;display:flex;overflow:hidden}
.sidebar{width:260px;background:#171717;border-right:1px solid #2a2a2a;display:flex;flex-direction:column;flex-shrink:0}
.sidebar-header{padding:20px 16px;border-bottom:1px solid #2a2a2a}
.sidebar-header h2{font-size:16px;font-weight:700;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sidebar-header p{font-size:11px;color:#555;margin-top:3px}
.new-chat-btn{margin:12px;padding:10px;background:#6366f1;border:none;border-radius:8px;color:#fff;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:8px;font-weight:500}
.new-chat-btn:hover{background:#5558e8}
.chat-list{flex:1;overflow-y:auto;padding:8px}
.chat-item{padding:10px 12px;border-radius:8px;cursor:pointer;font-size:13px;color:#aaa;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chat-item:hover,.chat-item.active{background:#222;color:#fff}
.sidebar-footer{padding:16px;border-top:1px solid #2a2a2a}
.api-key-label{font-size:11px;color:#555;margin-bottom:6px;display:block}
.api-key-input{width:100%;background:#0d0d0d;border:1px solid #2a2a2a;border-radius:8px;padding:8px 12px;color:#ececec;font-size:12px;outline:none}
.api-key-input:focus{border-color:#6366f1}
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.topbar{padding:14px 20px;border-bottom:1px solid #2a2a2a;display:flex;align-items:center;justify-content:space-between}
.model-badge{background:#1a1a2e;border:1px solid #6366f1;border-radius:20px;padding:4px 12px;font-size:12px;color:#a78bfa}
.mode-select{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:6px 12px;color:#ececec;font-size:13px;outline:none;cursor:pointer}
.chat-area{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px}
.chat-area::-webkit-scrollbar{width:4px}
.chat-area::-webkit-scrollbar-thumb{background:#333;border-radius:4px}
.welcome{text-align:center;margin:auto;max-width:500px;padding:40px 20px}
.welcome h1{font-size:28px;font-weight:700;margin-bottom:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.welcome p{color:#666;font-size:14px;margin-bottom:24px}
.quick-btns{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.quick-btn{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:20px;padding:8px 16px;font-size:13px;color:#aaa;cursor:pointer}
.quick-btn:hover{border-color:#6366f1;color:#a78bfa}
.msg{display:flex;gap:12px;max-width:800px;width:100%;animation:fadeIn .2s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.msg.user{align-self:flex-end;flex-direction:row-reverse}
.msg-avatar{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;background:#1a1a1a;border:1px solid #333}
.msg.user .msg-avatar{background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none}
.msg-content{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;font-size:14px;line-height:1.6;max-width:680px}
.msg.user .msg-content{background:#1e1e3a;border-color:#6366f1}
.msg-meta{font-size:11px;color:#555;margin-top:6px}
pre{background:#0d0d0d;border:1px solid #333;border-radius:8px;padding:12px;overflow-x:auto;font-size:13px;margin:8px 0}
code{font-family:monospace}
.typing{display:flex;gap:4px;padding:4px 0}
.typing span{width:6px;height:6px;background:#6366f1;border-radius:50%;animation:bounce .8s infinite}
.typing span:nth-child(2){animation-delay:.15s}
.typing span:nth-child(3){animation-delay:.3s}
@keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}
.input-area{padding:16px 20px;border-top:1px solid #2a2a2a}
.input-box{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;display:flex;align-items:flex-end;gap:8px;padding:10px 14px}
.input-box:focus-within{border-color:#6366f1}
.input-box textarea{flex:1;background:none;border:none;color:#ececec;font-size:14px;resize:none;outline:none;max-height:120px;font-family:inherit;line-height:1.5}
.send-btn{background:#6366f1;border:none;border-radius:8px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0}
.send-btn:hover{background:#5558e8}
.send-btn:disabled{background:#333;cursor:not-allowed}
.file-btn{background:none;border:1px solid #333;border-radius:8px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#666}
.file-btn:hover{border-color:#6366f1;color:#a78bfa}
.input-hints{display:flex;justify-content:space-between;margin-top:8px;font-size:11px;color:#555}
.file-preview{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:8px 12px;margin-bottom:8px;display:flex;align-items:center;gap:8px;font-size:13px}
.remove{cursor:pointer;color:#f87171;margin-left:auto}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;z-index:100}
.modal.hidden{display:none}
.modal-card{background:#171717;border:1px solid #2a2a2a;border-radius:16px;padding:32px;width:100%;max-width:400px}
.modal-card h2{font-size:20px;font-weight:700;margin-bottom:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.modal-card p{color:#666;font-size:13px;margin-bottom:24px}
.form-group{margin-bottom:16px}
.form-group label{display:block;font-size:12px;color:#888;margin-bottom:6px}
.form-group input{width:100%;background:#0d0d0d;border:1px solid #2a2a2a;border-radius:8px;padding:10px 14px;color:#ececec;font-size:14px;outline:none}
.form-group input:focus{border-color:#6366f1}
.modal-btn{width:100%;padding:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:8px;color:#fff;font-size:14px;font-weight:600;cursor:pointer;margin-top:8px}
.modal-btn:disabled{opacity:.5;cursor:not-allowed}
.modal-error{color:#f87171;font-size:13px;margin-top:8px;display:none}
.modal-error.show{display:block}
.skip-btn{width:100%;padding:10px;background:none;border:1px solid #333;border-radius:8px;color:#666;font-size:13px;cursor:pointer;margin-top:8px}
.success-key{background:#0d0d0d;border:1px solid #6366f1;border-radius:8px;padding:12px;font-family:monospace;font-size:12px;color:#a78bfa;word-break:break-all;margin-top:12px}
#scrollBtn{position:fixed;bottom:100px;right:24px;width:36px;height:36px;border-radius:50%;background:#6366f1;border:none;color:#fff;font-size:18px;cursor:pointer;display:none;box-shadow:0 2px 8px rgba(0,0,0,.4);z-index:10}
</style>
</head>
<body>

<div class="modal" id="registerModal">
  <div class="modal-card">
    <h2>Avaniko AI</h2>
    <p>Get your free API key to start chatting</p>
    <div id="registerForm">
      <div class="form-group">
        <label>Your Name</label>
        <input type="text" id="regName" placeholder="John Doe"/>
      </div>
      <div class="form-group">
        <label>Email Address</label>
        <input type="email" id="regEmail" placeholder="john@company.com"/>
      </div>
      <button class="modal-btn" id="regBtn" onclick="doRegister()">Get API Key</button>
      <div class="modal-error" id="regError"></div>
      <button class="skip-btn" onclick="skipRegister()">I have an API key</button>
    </div>
    <div id="registerSuccess" style="display:none">
      <div style="text-align:center;font-size:36px;margin-bottom:12px">🎉</div>
      <p style="color:#22c55e;text-align:center">API Key Generated!</p>
      <div class="success-key" id="successKey"></div>
      <button class="modal-btn" onclick="startChat()" style="margin-top:16px">Start Chatting</button>
    </div>
  </div>
</div>

<div class="sidebar">
  <div class="sidebar-header">
    <h2>Avaniko AI</h2>
    <p>Powered by Qwen3.6 MoE</p>
  </div>
  <button class="new-chat-btn" onclick="newChat()">New Chat</button>
  <div class="chat-list" id="chatList"></div>
  <div class="sidebar-footer">
    <span class="api-key-label">API Key</span>
    <input type="password" class="api-key-input" id="sidebarApiKey"
           placeholder="sk-ava-..." oninput="saveApiKey(this.value)"/>
  </div>
</div>

<div class="main">
  <div class="topbar">
    <span class="model-badge">qwen3.6-moe</span>
    <select class="mode-select" id="modeSelect">
      <option value="chat">Chat</option>
      <option value="reason">Reasoning</option>
      <option value="code">Code</option>
      <option value="summarize">Summarize</option>
      <option value="translate">Translate</option>
    </select>
  </div>
  <div class="chat-area" id="chatArea"></div>
  <div class="input-area">
    <div id="filePreview" style="display:none" class="file-preview">
      <span>📎</span>
      <span id="fileName"></span>
      <span class="remove" onclick="removeFile()">✕</span>
    </div>
    <div class="input-box">
      <button class="file-btn" onclick="document.getElementById('fileInput').click()">📎</button>
      <input type="file" id="fileInput" style="display:none"
             accept=".pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx,.txt,.csv"
             onchange="handleFile(this)"/>
      <textarea id="msgInput" rows="1"
                placeholder="Message Avaniko AI..."
                onkeydown="handleKey(event)"
                oninput="autoResize(this)"></textarea>
      <button class="send-btn" id="sendBtn" onclick="sendMessage()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
          <path d="M2 21l21-9L2 3v7l15 2-15 2z"/>
        </svg>
      </button>
    </div>
    <div class="input-hints">
      <span>Enter to send • Shift+Enter new line</span>
      <span id="statusDot" style="color:#22c55e">● Online</span>
    </div>
  </div>
</div>

<button id="scrollBtn" onclick="scrollToBottom()">↓</button>

<script>
const BASE = "https://g9s7n0soow3h5q-2222.proxy.runpod.net";
let apiKey = localStorage.getItem("ava_api_key") || "";
let sessions = JSON.parse(localStorage.getItem("ava_sessions") || "[]");
let currentSession = null;
let selectedFile = null;
let isLoading = false;

window.onload = function() {
  if (apiKey) {
    document.getElementById("registerModal").classList.add("hidden");
    document.getElementById("sidebarApiKey").value = apiKey;
  }
  renderSessions();
  checkHealth();
  setupScroll();
  newChat();
};

function checkHealth() {
  fetch(BASE + "/health").then(function(r) {
    return r.json();
  }).then(function(d) {
    var dot = document.getElementById("statusDot");
    if (d.vllm === "ok") {
      dot.textContent = "● Online";
      dot.style.color = "#22c55e";
    } else {
      dot.textContent = "● Partial";
      dot.style.color = "#f59e0b";
    }
  }).catch(function() {
    var dot = document.getElementById("statusDot");
    dot.textContent = "● Offline";
    dot.style.color = "#ef4444";
  });
}

function setupScroll() {
  var area = document.getElementById("chatArea");
  var btn  = document.getElementById("scrollBtn");
  area.addEventListener("scroll", function() {
    var near = area.scrollHeight - area.scrollTop - area.clientHeight < 100;
    btn.style.display = near ? "none" : "flex";
  });
}

function scrollToBottom() {
  var area = document.getElementById("chatArea");
  area.scrollTop = area.scrollHeight;
  document.getElementById("scrollBtn").style.display = "none";
}

function smartScroll() {
  var area = document.getElementById("chatArea");
  var near = area.scrollHeight - area.scrollTop - area.clientHeight < 200;
  if (near) area.scrollTop = area.scrollHeight;
}

function addMsgEl(role, id, extraHtml) {
  var area = document.getElementById("chatArea");
  var div  = document.createElement("div");
  div.className = "msg " + role;
  div.id = id;
  var avatar = role === "user" ? "U" : "AI";
  div.innerHTML = '<div class="msg-avatar">' + avatar + '</div>' +
    '<div>' +
    '<div class="msg-content" id="content_' + id + '">' + extraHtml + '</div>' +
    '<div class="msg-meta" id="meta_' + id + '"></div>' +
    '</div>';
  area.appendChild(div);
  smartScroll();
  return div;
}

async function readStream(response, msgId) {
  var contentEl = document.getElementById("content_" + msgId);
  var reader    = response.body.getReader();
  var decoder   = new TextDecoder();
  var buffer    = "";
  var fullText  = "";
  var first     = true;

  while (true) {
    var result = await reader.read();
    if (result.done) break;

    buffer += decoder.decode(result.value, {stream: true});

    var newlineIdx;
    while ((newlineIdx = buffer.indexOf("\\n")) !== -1) {
      var line = buffer.slice(0, newlineIdx).trim();
      buffer   = buffer.slice(newlineIdx + 1);

      if (!line) continue;
      if (!line.startsWith("data:")) continue;

      var jsonStr = line.replace(/^data:\\s*/, "").trim();
      if (!jsonStr || jsonStr === "[DONE]") continue;

      try {
        var parsed = JSON.parse(jsonStr);
        var token  = parsed.token || parsed.content || "";
        if (token) {
          if (first) {
            contentEl = document.getElementById("content_" + msgId);
            if (contentEl) contentEl.innerHTML = "";
            first = false;
          }
          fullText += token;
          contentEl = document.getElementById("content_" + msgId);
          if (contentEl) {
            contentEl.innerHTML = formatMsg(fullText);
            smartScroll();
          }
        }
      } catch(e) {}
    }
  }
  return fullText;
}

function doRegister() {
  var name  = document.getElementById("regName").value.trim();
  var email = document.getElementById("regEmail").value.trim();
  if (!name || !email) { showRegError("Please fill all fields"); return; }
  var btn = document.getElementById("regBtn");
  btn.disabled = true;
  btn.textContent = "Generating...";
  fetch(BASE + "/admin/signup", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({user_name: name, user_email: email, daily_limit: 1000})
  }).then(function(r) {
    return r.json().then(function(d) { return {ok: r.ok, data: d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.data.detail || "Failed");
    apiKey = res.data.api_key;
    localStorage.setItem("ava_api_key", apiKey);
    document.getElementById("sidebarApiKey").value = apiKey;
    document.getElementById("successKey").textContent = apiKey;
    document.getElementById("registerForm").style.display = "none";
    document.getElementById("registerSuccess").style.display = "block";
  }).catch(function(e) {
    showRegError(e.message);
    btn.disabled = false;
    btn.textContent = "Get API Key";
  });
}

function skipRegister() {
  var key = prompt("Enter your API key (sk-ava-...):");
  if (key) {
    apiKey = key;
    localStorage.setItem("ava_api_key", key);
    document.getElementById("sidebarApiKey").value = key;
  }
  document.getElementById("registerModal").classList.add("hidden");
}

function startChat() {
  document.getElementById("registerModal").classList.add("hidden");
}

function showRegError(msg) {
  var el = document.getElementById("regError");
  el.textContent = msg;
  el.classList.add("show");
}

function saveApiKey(val) {
  apiKey = val;
  localStorage.setItem("ava_api_key", val);
}

function newChat() {
  currentSession = {
    id: Date.now().toString(),
    title: "New Chat",
    messages: [],
    mode: "chat"
  };
  sessions.unshift(currentSession);
  saveSessions();
  renderSessions();
  renderMessages();
}

function loadSession(id) {
  currentSession = sessions.find(function(s) { return s.id === id; });
  if (currentSession) {
    document.getElementById("modeSelect").value = currentSession.mode || "chat";
    renderSessions();
    renderMessages();
  }
}

function saveSessions() {
  sessions = sessions.slice(0, 20);
  localStorage.setItem("ava_sessions", JSON.stringify(sessions));
}

function renderSessions() {
  var list = document.getElementById("chatList");
  list.innerHTML = sessions.map(function(s) {
    var active = currentSession && currentSession.id === s.id ? " active" : "";
    return '<div class="chat-item' + active + '" onclick="loadSession(\'' + s.id + '\')">' + s.title + '</div>';
  }).join("");
}

function renderMessages() {
  var area = document.getElementById("chatArea");
  if (!currentSession || currentSession.messages.length === 0) {
    area.innerHTML = '<div class="welcome">' +
      '<h1>Avaniko AI Gateway</h1>' +
      '<p>Chat, Code, OCR, Reasoning and More</p>' +
      '<div class="quick-btns">' +
      '<button class="quick-btn" onclick="quickSend(\'What can you do?\')">What can you do?</button>' +
      '<button class="quick-btn" onclick="quickSend(\'Write Python hello world\')">Python code</button>' +
      '<button class="quick-btn" onclick="quickSend(\'Explain MoE architecture\')">Explain MoE</button>' +
      '<button class="quick-btn" onclick="quickSend(\'Translate Hello to Tamil\')">Translate</button>' +
      '</div></div>';
    return;
  }
  area.innerHTML = currentSession.messages.filter(function(m) { return !m._id; }).map(function(m) {
    return '<div class="msg ' + m.role + '">' +
      '<div class="msg-avatar">' + (m.role === "user" ? "U" : "AI") + '</div>' +
      '<div><div class="msg-content">' + formatMsg(m.content) + '</div>' +
      '<div class="msg-meta">' + (m.time ? "⚡ " + m.time + "ms" : "") + '</div>' +
      '</div></div>';
  }).join("");
  area.scrollTop = area.scrollHeight;
}

function formatMsg(text) {
  if (!text) return "";
  text = text.replace(/```(\\w+)?\\n?([\\s\\S]*?)```/g, "<pre><code>$2</code></pre>");
  text = text.replace(/`([^`]+)`/g, '<code style="background:#333;padding:2px 6px;border-radius:4px">$1</code>');
  text = text.replace(/\\*\\*(.*?)\\*\\*/g, "<strong>$1</strong>");
  text = text.replace(/\\n/g, "<br>");
  return text;
}

async function sendMessage() {
  if (isLoading) return;
  var input = document.getElementById("msgInput");
  var msg   = input.value.trim();
  if (!msg && !selectedFile) return;
  if (!apiKey) {
    document.getElementById("registerModal").classList.remove("hidden");
    return;
  }
  input.value = "";
  autoResize(input);
  var mode = document.getElementById("modeSelect").value;
  if (!currentSession) newChat();
  currentSession.mode = mode;
  isLoading = true;
  document.getElementById("sendBtn").disabled = true;

  if (selectedFile) {
    var fileToUpload = selectedFile;
    var fname = selectedFile.name;
    addUserMsg("📎 " + fname + "\\n" + (msg || "Extract all information"));
    removeFile();
    await handleFileUpload(fileToUpload, msg, mode);
  } else {
    addUserMsg(msg);
    await handleChat(msg, mode);
  }

  isLoading = false;
  document.getElementById("sendBtn").disabled = false;
}

function addUserMsg(content) {
  if (!currentSession) newChat();
  currentSession.messages.push({role: "user", content: content});
  if (currentSession.title === "New Chat") {
    currentSession.title = content.slice(0, 30);
  }
  saveSessions();
  var area = document.getElementById("chatArea");
  var div  = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = '<div class="msg-avatar">U</div>' +
    '<div><div class="msg-content">' + formatMsg(content) + '</div></div>';
  area.appendChild(div);
  smartScroll();
  renderSessions();
}

async function handleChat(msg, mode) {
  var startT = Date.now();
  var msgId  = "msg_" + Date.now();
  addMsgEl("assistant", msgId,
    '<div class="typing"><span></span><span></span><span></span></div>');

  try {
    var r = await fetch(BASE + "/v1/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json", "x-api-key": apiKey},
      body: JSON.stringify({
        message: msg, mode: mode,
        session_id: currentSession.id, stream: true
      })
    });
    if (!r.ok) {
      var d = await r.json();
      throw new Error(d.detail || "Error");
    }
    var fullText = await readStream(r, msgId);
    currentSession.messages.push({role: "assistant", content: fullText, time: Date.now()-startT});
    saveSessions();
    var meta = document.getElementById("meta_" + msgId);
    if (meta) meta.textContent = "⚡ " + (Date.now()-startT) + "ms";
  } catch(e) {
    var el = document.getElementById("content_" + msgId);
    if (el) el.innerHTML = "Error: " + e.message;
  }
}

async function handleFileUpload(file, question, mode) {
  var startT = Date.now();
  var msgId  = "msg_" + Date.now();
  addMsgEl("assistant", msgId,
    '<div class="typing"><span></span><span></span><span></span></div>' +
    '<div style="font-size:12px;color:#666;margin-top:6px">Processing ' + file.name + '...</div>');

  try {
    var formData = new FormData();
    formData.append("file", file);
    formData.append("question", question || "Extract all information as JSON");
    formData.append("mode", mode);
    formData.append("session_id", currentSession.id);
    formData.append("stream", "true");

    var r = await fetch(BASE + "/v1/files/ask", {
      method: "POST",
      headers: {"x-api-key": apiKey},
      body: formData
    });
    if (!r.ok) {
      var d = await r.json();
      throw new Error(d.detail || "Error");
    }
    var fullText = await readStream(r, msgId);
    currentSession.messages.push({role: "assistant", content: fullText, time: Date.now()-startT});
    saveSessions();
    var meta = document.getElementById("meta_" + msgId);
    if (meta) meta.textContent = "⚡ " + (Date.now()-startT) + "ms";
  } catch(e) {
    var el = document.getElementById("content_" + msgId);
    if (el) el.innerHTML = "Error: " + e.message;
  }
}

function handleFile(input) {
  selectedFile = input.files[0];
  if (selectedFile) {
    document.getElementById("filePreview").style.display = "flex";
    document.getElementById("fileName").textContent = selectedFile.name;
  }
}

function removeFile() {
  selectedFile = null;
  document.getElementById("filePreview").style.display = "none";
  document.getElementById("fileInput").value = "";
}

function quickSend(msg) {
  document.getElementById("msgInput").value = msg;
  sendMessage();
}

function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}
</script>
</body>
</html>"""

with open('/workspace/production/static/index.html', 'w') as f:
    f.write(html)
print("✅ index.html written successfully")

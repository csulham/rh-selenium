from flask import Flask
import threading
import time

app = Flask(__name__)
log_messages = []

def generate_logs():
    global log_messages
    while True:
        log_messages.append(f"[LOG] Selenium test running at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(5)

@app.route('/')
def view_logs():
    return "<br>".join(log_messages[-50:]) 

log_thread = threading.Thread(target=generate_logs, daemon=True)
log_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

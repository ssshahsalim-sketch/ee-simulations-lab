"""
EE Simulations Lab — Flask Server
Compatible with Render.com cloud hosting
"""

from flask import (Flask, render_template, jsonify, request,
                   send_from_directory, redirect, session)
import os, json, hashlib, datetime, re
from pathlib import Path
from functools import wraps
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

app        = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ee_sim_secret_2024_xyz")

BASE_DIR     = Path(__file__).parent
SIM_DIR      = BASE_DIR / "simulations"
UPLOAD_DIR   = BASE_DIR / "static" / "uploads"
META_FILE    = BASE_DIR / "meta.json"
CONTENT_FILE = BASE_DIR / "content.json"
CONFIG_FILE  = BASE_DIR / "config.json"
ADMIN_PASS   = "admin123"

SIM_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

if CONFIG_FILE.exists():
    try: ADMIN_PASS = json.loads(CONFIG_FILE.read_text()).get("admin_pass", ADMIN_PASS)
    except: pass

DEFAULT_CONTENT = {
    "site_title":"EE Simulations Lab","site_subtitle":"ELECTRICAL ENGINEERING SIMULATION LAB",
    "hero_title":"Interactive Circuit Simulations","hero_highlight":"Circuit",
    "hero_desc":"Explore, analyze and learn electrical engineering concepts through interactive HTML simulations.",
    "logo_text":"EESIM","logo_icon":"⚡","primary_color":"#00d4ff","accent_color":"#ff6b00",
    "hero_image":"","categories":["AC Circuits","DC Circuits","Motors & Machines",
    "Power Systems","Electronics","Signal Processing","Control Systems",
    "Electromagnetics","Transformers","Other"],"blocks":[]
}

def load_content():
    if CONTENT_FILE.exists():
        try:
            data = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))
            for k,v in DEFAULT_CONTENT.items():
                if k not in data: data[k] = v
            return data
        except: pass
    return dict(DEFAULT_CONTENT)

def save_content(data):
    CONTENT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def load_meta():
    if META_FILE.exists():
        try: return json.loads(META_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_meta(data):
    META_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def scan_simulations():
    meta = load_meta(); sims = []
    for f in sorted(SIM_DIR.glob("*.html")):
        key = f.name; m = meta.get(key,{}); st = f.stat()
        sims.append({"filename":key,
            "title":m.get("title",f.stem.replace("_"," ").replace("-"," ").title()),
            "description":m.get("description",""),"category":m.get("category","Other"),
            "tags":m.get("tags",[]),"added":m.get("added",
            datetime.datetime.fromtimestamp(st.st_ctime).strftime("%b %d, %Y")),
            "size":f"{st.st_size//1024} KB" if st.st_size>1024 else f"{st.st_size} B"})
    return sims

def admin_required(f):
    @wraps(f)
    def dec(*a,**k):
        if not session.get("admin"):
            return jsonify({"ok":False,"error":"Unauthorized"}),401
        return f(*a,**k)
    return dec

@app.route("/")
def index():
    return render_template("index.html",content=load_content(),is_admin=bool(session.get("admin")))

@app.route("/api/simulations")
def api_simulations(): return jsonify(scan_simulations())

@app.route("/api/content")
def api_content(): return jsonify(load_content())

@app.route("/sim/<filename>")
def view_simulation(filename): return send_from_directory(SIM_DIR, filename)

# ══════════════════════════════════════════════════
# TWILIO SMS — for the electrical-services.html tool.
# Credentials come ONLY from Render environment variables
# (TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM), never from the repo
# or the browser. Twilio is called server-to-server here, so
# there's no CORS proxy needed at all.
# ══════════════════════════════════════════════════
TWILIO_ERROR_HINTS = {
    20003: "Authentication failed — double-check TWILIO_SID and TWILIO_TOKEN in Render's Environment settings.",
    21211: "Invalid 'To' phone number — make sure it includes the country code, e.g. +919876543210.",
    21606: "Your Twilio 'From' number (TWILIO_FROM) isn't a valid, SMS-enabled number on this account.",
    21608: "This is a Trial account — Twilio can only send to numbers verified under Phone Numbers → Verified Caller IDs in your Twilio console. Verify this number, or upgrade the account.",
    21614: "The 'To' number isn't a valid mobile number that can receive SMS.",
    21617: "Message body is too long.",
}

def to_e164(raw):
    if not raw:
        return None
    cleaned = re.sub(r"[^\d+]", "", str(raw).strip())
    if cleaned.find("+") > 0:
        cleaned = cleaned.replace("+", "")
    if not cleaned.startswith("+"):
        return None
    digits = cleaned[1:]
    if not re.fullmatch(r"\d{8,15}", digits):
        return None
    return "+" + digits

@app.route("/api/sms-status")
def api_sms_status():
    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    from_num = to_e164(os.environ.get("TWILIO_FROM", ""))
    return jsonify({"configured": bool(sid and token and from_num)})

@app.route("/api/send-sms", methods=["POST"])
def api_send_sms():
    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    from_num = to_e164(os.environ.get("TWILIO_FROM", ""))
    if not (sid and token and from_num):
        return jsonify({"success": False, "error": "Server is missing TWILIO_SID / TWILIO_TOKEN / TWILIO_FROM environment variables. Set them in Render → Environment."}), 500

    data = request.get_json(silent=True) or {}
    to_num = to_e164(data.get("to"))
    body = (data.get("body") or "").strip()
    if not to_num:
        return jsonify({"success": False, "error": "The engineer's phone number is missing a country code. Update it in the Admin Panel (e.g. +919876543210)."}), 400
    if not body:
        return jsonify({"success": False, "error": "Message body is empty."}), 400

    try:
        client = TwilioClient(sid, token)
        msg = client.messages.create(to=to_num, from_=from_num, body=body)
        return jsonify({"success": True, "messageSid": msg.sid})
    except TwilioRestException as e:
        hint = TWILIO_ERROR_HINTS.get(e.code)
        message = f"{hint} (Twilio error {e.code})" if hint else f"{e.msg or 'Twilio rejected the request.'} (error {e.code})"
        return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    err=""
    if request.method=="POST":
        pw=request.form.get("password","")
        if hashlib.sha256(pw.encode()).hexdigest()==hashlib.sha256(ADMIN_PASS.encode()).hexdigest():
            session["admin"]=True; return redirect("/")
        err="Incorrect password."
    return render_template("login.html",error=err)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin",None); return redirect("/")

@app.route("/api/save_content",methods=["POST"])
@admin_required
def api_save_content():
    content=load_content()
    for k,v in request.json.items(): content[k]=v
    save_content(content); return jsonify({"ok":True})

@app.route("/api/save_block",methods=["POST"])
@admin_required
def api_save_block():
    import time; data=request.json; content=load_content(); blocks=content.get("blocks",[])
    bid=data.get("id")
    if bid:
        replaced=False
        for i,b in enumerate(blocks):
            if b["id"]==bid: blocks[i]=data; replaced=True; break
        if not replaced: blocks.append(data)
    else:
        data["id"]=str(int(time.time()*1000)); blocks.append(data)
    content["blocks"]=blocks; save_content(content); return jsonify({"ok":True,"id":data["id"]})

@app.route("/api/delete_block",methods=["POST"])
@admin_required
def api_delete_block():
    bid=request.json.get("id"); content=load_content()
    content["blocks"]=[b for b in content.get("blocks",[]) if b["id"]!=bid]
    save_content(content); return jsonify({"ok":True})

@app.route("/api/save_categories",methods=["POST"])
@admin_required
def api_save_categories():
    content=load_content(); content["categories"]=request.json.get("categories",[])
    save_content(content); return jsonify({"ok":True})

@app.route("/api/change_password",methods=["POST"])
@admin_required
def api_change_password():
    global ADMIN_PASS
    pw=request.json.get("password","").strip()
    if len(pw)<4: return jsonify({"ok":False,"error":"Min 4 characters"})
    ADMIN_PASS=pw; CONFIG_FILE.write_text(json.dumps({"admin_pass":pw}))
    return jsonify({"ok":True})

@app.route("/api/upload_image",methods=["POST"])
@admin_required
def api_upload_image():
    f=request.files.get("image")
    if not f: return jsonify({"ok":False})
    fname=f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{f.filename}"
    f.save(UPLOAD_DIR/fname); return jsonify({"ok":True,"url":f"/static/uploads/{fname}"})

@app.route("/admin/upload",methods=["POST"])
@admin_required
def upload_sim():
    meta=load_meta(); uploaded=[]
    for f in request.files.getlist("files"):
        if f and f.filename.endswith(".html"):
            f.save(SIM_DIR/f.filename)
            if f.filename not in meta:
                meta[f.filename]={"title":Path(f.filename).stem.replace("_"," ").replace("-"," ").title(),
                    "description":"","category":request.form.get("category","Other"),
                    "tags":[],"added":datetime.datetime.now().strftime("%b %d, %Y")}
            uploaded.append(f.filename)
    save_meta(meta); return jsonify({"ok":True,"uploaded":uploaded})

@app.route("/admin/update_meta",methods=["POST"])
@admin_required
def update_meta():
    data=request.json; meta=load_meta(); fn=data.get("filename")
    if fn:
        meta[fn]={"title":data.get("title",""),"description":data.get("description",""),
            "category":data.get("category","Other"),
            "tags":[t.strip() for t in data.get("tags","").split(",") if t.strip()],
            "added":meta.get(fn,{}).get("added",datetime.datetime.now().strftime("%b %d, %Y"))}
        save_meta(meta); return jsonify({"ok":True})
    return jsonify({"ok":False})

@app.route("/admin/delete",methods=["POST"])
@admin_required
def delete_sim():
    fn=request.json.get("filename"); target=SIM_DIR/fn
    if target.exists():
        target.unlink(); meta=load_meta(); meta.pop(fn,None); save_meta(meta)
        return jsonify({"ok":True})
    return jsonify({"ok":False})

@app.route("/admin/scan")
@admin_required
def scan_folder():
    meta=load_meta(); new=[]
    for f in SIM_DIR.glob("*.html"):
        if f.name not in meta:
            meta[f.name]={"title":f.stem.replace("_"," ").replace("-"," ").title(),
                "description":"","category":"Other","tags":[],
                "added":datetime.datetime.now().strftime("%b %d, %Y")}
            new.append(f.name)
    save_meta(meta)
    return jsonify({"ok":True,"new_files":new,"total":len(list(SIM_DIR.glob("*.html")))})

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    print(f"\n{'='*50}\n  ⚡ EE Simulations\n  http://localhost:{port}\n{'='*50}\n")
    app.run(host="0.0.0.0",port=port,debug=False)

# ⚡ EE Simulations Lab — Setup Guide

## Folder Structure
```
ee_website/
├── app.py              ← Flask server
├── START.bat           ← Double-click to start server
├── meta.json           ← Auto-created (stores titles, categories etc.)
├── templates/
│   ├── index.html      ← Public website
│   ├── admin.html      ← Admin panel
│   └── login.html      ← Admin login
└── simulations/        ← DROP YOUR HTML FILES HERE ← ← ←
    └── RC_Circuit_Simulator.html  (sample)
```

---

## Step 1 — Install & Start

1. Make sure Python is installed
2. Double-click **START.bat**
3. Open browser → http://localhost:5000

That's it! Your website is running locally.

---

## Step 2 — Adding Simulations (2 ways)

### Way A — Drop files in folder (automatic)
- Copy your `.html` simulation files into the `simulations/` folder
- Go to Admin Panel → click **🔄 Scan Folder**
- They appear on the website instantly!

### Way B — Upload through Admin Panel
- Go to http://localhost:5000/admin
- Password: **admin123** (change this in app.py!)
- Click upload zone or drag & drop `.html` files
- Choose a category → Upload

---

## Step 3 — Manage Simulations

In the Admin Panel you can:
- ✏ Edit title, description, category, tags for each simulation
- 👁 Preview any simulation
- 🗑 Delete simulations
- 🔄 Scan folder for new files

---

## Step 4 — Share on Internet (Ngrok - Free)

To share your site with anyone on the internet:

### Install Ngrok
1. Go to https://ngrok.com → Sign up free
2. Download ngrok for Windows
3. Run: `ngrok config add-authtoken YOUR_TOKEN`

### Start sharing
1. First start your server: double-click **START.bat**
2. Open a new CMD window
3. Run: `ngrok http 5000`
4. Ngrok gives you a public URL like:
   `https://abc123.ngrok-free.app`
5. Share that URL — anyone can access your simulations!

Note: Free ngrok URL changes each time you restart.
For a permanent URL, use ngrok paid plan or no-ip.com

---

## Customization

### Change admin password
Open `app.py`, find line:
```python
ADMIN_PASS = "admin123"
```
Change it to your own password.

### Change site title
Open `templates/index.html`, find:
```
EE Simulations Lab
```
Change to your preferred name.

### Add more categories
Open `app.py`, find the CATEGORIES list and add your own.

---

## Auto-refresh
The public site automatically checks for new simulations every 30 seconds.
No need to reload — new simulations appear automatically!

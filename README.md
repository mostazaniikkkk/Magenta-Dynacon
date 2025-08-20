# Magenta Dynaconn 🔌

Welcome to the magical world of **Magenta Dynaconn**!  
This library lets you manage **dynamic database connections** and **on-the-fly model generation** with SQLAlchemy, without losing your sanity.

> ⚠️ **NOTICE**: The project is still in Alpha. Use at your own risk — dragons may appear 🐉.

<a href="https://ko-fi.com/mostazaniikkkk" target="_blank">
  <img src="https://www.ko-fi.com/img/githubbutton_sm.svg">
</a>

---

## Features 🌟

- Manage multiple database instances from a single `.ini` file.  
- Safe connection handling with atomic updates and auto-refresh.  
- Dynamic class generation for tables on demand.  
- Lightweight CRUD integration.  
- MIT licensed: do whatever you want, but don’t blame me if it explodes.

---

## Why build this? 🤔

Because manually handling 20 DB connections, regenerating models, and keeping everything in sync is a **pain in the ass**.  
With **Magenta Dynaconn**, you get:

- **Order** instead of chaos.  
- **Flexibility** to plug new DBs without refactoring half your app.  
- **Speed** to prototype or build production-ready systems faster.

---

## Quickstart 🚀

### Python script
```python
from magenta_dynaconn import DatabaseRegistry

# Load from default source.ini
registry = DatabaseRegistry()

# List instances
print(registry.list_names())

# Get a handle and open a session
session = registry.new_session("my_db")

# Get a dynamic model class
Product = registry.get_db_instance("my_db", "product")

# Create and persist an object
p = Product(name="Demo", description="Test")
session.add(p)
session.commit()
```
### INI file
```ini
[my_db]
source = sqlite
username = 
password = 
host = 
port = 
base = ./myfile.db
```

---

## Goals for v1.0.0 🎯

- Full documentation & tutorials.  
- Extended validation and schema registry.  
- CI tests and PyPI package release.  
- Battle-tested in real projects (and hopefully no tears).

---

## 📣 Feedback & Contributions

Ideas? Bugs? Existential dread? Open an Issue or PR — I’ll read it, I promise.  
Let’s make this tool grow together 😄.

---

## ☕ Support the Project

If you like my work and want me to keep hacking on this, you can support me here:

<a href="https://ko-fi.com/mostazaniikkkk" target="_blank">
  <img src="https://www.ko-fi.com/img/githubbutton_sm.svg">
</a>

---

## License 📜

- **Magenta Dynaconn** is MIT licensed.  
- Use it freely in your projects, just don’t forget to credit if you feel like being nice.


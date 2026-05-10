# YouthSmartJA
The system uses Text Matching, Gap Identification and Path Optimization to serve as a skill progression engine for students. Rather than just a job board, YouthSmartJA becomes a skill progression engine

# Running YouthSmartJA Locally

## Prerequisites

Before running the project, make sure you have installed:

* Python 3.10+
* MySQL
* Git
* VS Code (recommended)

---

# 1. Clone the Repository

```bash
git clone https://github.com/gabrielle-ux/YouthSmartJA.git
```

Move into the project folder:

```bash
cd YouthSmartJA/api
```

---

# 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

Activate the virtual environment:

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

# 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 4. Create a `.env` File

Inside the `api` folder, create a file named:

```text
.env
```

Add the following configuration:

```env
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=youthsmart
DB_PORT=3306
JWT_SECRET_KEY=youthsmart
N8N_WEBHOOK_URL=http://localhost:5678/webhook/guidance-courses
```

---

# 5. Start MySQL

Make sure MySQL is running locally.

Example (macOS Homebrew):

```bash
brew services start mysql
```

Create the database:

```sql
CREATE DATABASE youthsmart;
```

---

# 6. Run the Flask Server

```bash
python app.py
```

The application should now run at:

```text
http://127.0.0.1:5000
```

---

# 7. Frontend Development (Optional)

If working only on the frontend UI:

Navigate to the frontend folder and run:

```bash
python3 -m http.server 5500
```

Then open:

```text
http://localhost:5500
```

---

# 8. Recommended VS Code Extension

Install:

* Live Server (by Ritwick Dey)

Then:

* Right-click the HTML file
* Select “Open with Live Server”

---

# Troubleshooting

## Missing Python Packages

If you encounter missing package errors:

```bash
pip install flask requests python-dotenv mysql-connector-python
```

---

## White Screen / Frontend Not Loading

* Ensure CSS and JS files are in the correct folders
* Check browser console with `F12`
* Verify static file paths are correct

---

# Tech Stack

* Frontend: HTML, CSS, JavaScript
* Backend: Python Flask
* Database: MySQL
* AI/NLP: TF-IDF + Cosine Similarity
* APIs: JSearch API

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from db_manager import CeylonDB
from nlp_processor import CeylonEngine

app = Flask(__name__)
app.secret_key = 'ceylon_guide_secret_2026' 

db = CeylonDB()
engine = CeylonEngine()


ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'ceylon123'


learning_mode = False
last_unknown = ""


# ============================================================
#  ROUTE 1: Main Landing Page
# ============================================================
@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
#  ROUTE 2: Chat Message Handler  
# ============================================================
@app.route("/get")
def get_bot_response():
    global learning_mode, last_unknown

    user_text = request.args.get('msg', '').strip()
    if not user_text:
        return "Please type a message first."

    if learning_mode:
       
        db.submit_for_review(last_unknown, user_text)
        learning_mode = False
        last_unknown = ""
        return ("Thank you! 🙏 Your suggestion has been submitted for admin review. "
                "Once approved it will become part of my knowledge base.")

    response, is_learning = engine.get_response(user_text, db)

    if is_learning:
        learning_mode = True
        last_unknown = user_text

    return response


# ============================================================
#  ROUTE 3: Admin Login Page
# ============================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid credentials. Please try again."
    return render_template("admin_login.html", error=error)


# ============================================================
#  ROUTE 4: Admin Dashboard 
# ============================================================
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    pending  = db.get_all_pending_reviews()
    learned  = db.get_all_learned_facts_with_ids()
    history  = db.get_chat_history(limit=30)
    return render_template("admin_dashboard.html",
                           pending=pending,
                           learned=learned,
                           history=history)


# ============================================================
#  ROUTE 5: Approve a pending review  
# ============================================================
@app.route("/admin/approve/<int:review_id>")
def approve_review(review_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    db.approve_fact(review_id)
    return redirect(url_for('admin_dashboard'))


# ============================================================
#  ROUTE 6: Reject / delete a pending review
# ============================================================
@app.route("/admin/reject/<int:review_id>")
def reject_review(review_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    db.reject_review(review_id)
    return redirect(url_for('admin_dashboard'))


# ============================================================
#  ROUTE 7: Delete a learned fact
# ============================================================
@app.route("/admin/delete_fact/<int:fact_id>")
def delete_fact(fact_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    db.delete_learned_fact(fact_id)
    return redirect(url_for('admin_dashboard'))


# ============================================================
#  ROUTE 8: Approve ALL pending at once  
# ============================================================
@app.route("/admin/approve_all")
def approve_all():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    pending = db.get_all_pending_reviews()
    for row in pending:
        db.approve_fact(row[0])
    return redirect(url_for('admin_dashboard'))


# ============================================================
#  ROUTE 9: Admin Logout
# ============================================================
@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


# ============================================================
if __name__ == "__main__":
    print("CeylonGuide AI Web Server starting...")
    app.run(host="0.0.0.0", port=5000, debug=True)
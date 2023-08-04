from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2

# Thông tin kết nối PostgreSQL
db_config = {
    "dbname": "phonesdb",
    "user": "phong",
    "password": "123",
    "host": "192.168.1.11",
    "port": "5432",
}

def get_data_from_db():
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM phone;")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Lỗi khi thực hiện truy vấn SELECT: {e}")
        return []

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Hãy thay đổi "your_secret_key" thành một giá trị bí mật thực tế

def is_all_digits(s):
    return s.isdigit()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone_number = request.form.get("phoneNumber")

        if not is_all_digits(phone_number):
            error = "Số điện thoại chỉ được chứa các ký tự số."
            return render_template("index.html", error=error)

        if len(phone_number) < 5 or len(phone_number) > 15:
            error = "Nhập số trong khoảng từ 5 đến 15 ký tự."
            return render_template("index.html", error=error)

        session["phone_number"] = phone_number
        return redirect(url_for("next_page"))

    return render_template("index.html")

@app.route("/next", methods=["GET", "POST"])
def next_page():
    phone_number = session.get("phone_number")

    if not phone_number:
        return redirect(url_for("login"))

    if request.method == "POST":
        data = request.form.get("data")

        # Kiểm tra nếu data đã tồn tại trong cơ sở dữ liệu
        existing_data = get_data_from_db()
        for row in existing_data:
            if row[2] == data:
                error = "Data đã tồn tại."
                return render_template("next_page.html", phone_number=phone_number, error=error)

        # Thực hiện lưu data vào cơ sở dữ liệu
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            insert_query = "INSERT INTO phone (phone_number, data) VALUES (%s, %s);"
            cursor.execute(insert_query, (phone_number, data))
            conn.commit()
            cursor.close()
            conn.close()
            print("Lưu dữ liệu thành công!")
            success = "Đã lưu thành công."
            return render_template("next_page.html", phone_number=phone_number, success=success)
        except Exception as e:
            print(f"Lỗi khi thực hiện truy vấn INSERT: {e}")
            error = "Lưu dữ liệu không thành công."
            return render_template("next_page.html", phone_number=phone_number, error=error)

    return render_template("next_page.html", phone_number=phone_number)

@app.route("/save_data", methods=["POST"])
def save_data():
    if request.method == "POST":
        phone_number = session.get("phone_number")
        data = request.json.get("data")

        if not phone_number:
            return jsonify({"success": False, "message": "Invalid phone number."}), 400

        # Check if the data already exists in the database
        existing_data = get_data_from_db()
        if existing_data is None:
            existing_data = []

        for row in existing_data:
            if row[1] == phone_number and row[2] == data:
                return jsonify({"success": False, "message": "Data already exists for this phone number."}), 409

        # Save data to the database
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO phone (phone_number, data) VALUES (%s, %s);", (phone_number, data))
            conn.commit()
            cursor.close()
            conn.close()
            print("Data saved successfully!")
            return jsonify({"success": True, "message": "Data saved successfully."}), 200
        except Exception as e:
            print(f"Error executing INSERT query: {e}")
            return jsonify({"success": False, "message": "Failed to save data."}), 500

@app.route("/check_data", methods=["POST"])
def check_data():
    data = request.json.get("data")

    # Kiểm tra nếu data đã tồn tại trong cơ sở dữ liệu
    existing_data = get_data_from_db()
    for row in existing_data:
        if row[2] == data:
            return {"exists": True}

    return {"exists": False}

@app.route("/watch_log", methods=["GET"])
def watch_log():
    phone_number = session.get("phone_number")

    if not phone_number:
        return redirect(url_for("login"))

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        select_query = "SELECT * FROM phone WHERE phone_number=%s;"
        cursor.execute(select_query, (phone_number,))
        log_data = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Lỗi khi thực hiện truy vấn SELECT: {e}")
        log_data = []  # Nếu có lỗi, trả về một danh sách rỗng

    return render_template("watch_log.html", log_data=log_data)

@app.route("/update_data", methods=["POST"])
def update_data():
    if request.method == "POST":
        data_id = request.form.get("data_id")
        new_data = request.form.get("new_data")

        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            update_query = "UPDATE phone SET data = %s WHERE id = %s RETURNING *;"
            cursor.execute(update_query, (new_data, data_id))
            updated_data = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()

            if updated_data:
                return jsonify({"success": True, "message": "Data updated successfully.", "data": updated_data}), 200
            else:
                return jsonify({"success": False, "message": "Data not found."}), 404

        except Exception as e:
            print(f"Lỗi khi thực hiện truy vấn UPDATE: {e}")
            return jsonify({"success": False, "message": "Failed to update data."}), 500

@app.route("/delete_data", methods=["POST"])
def delete_data():
    if request.method == "POST":
        data_id = request.json.get("data_id")

        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM phone WHERE id=%s;", (data_id,))
            conn.commit()
            cursor.close()
            conn.close()
            print("Xóa dữ liệu thành công!")
            return "Success"
        except Exception as e:
            print(f"Lỗi khi thực hiện truy vấn DELETE: {e}")
            return "Failed"

if __name__ == "__main__":
    app.run(debug=True)

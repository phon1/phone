from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2

# Thông tin kết nối PostgreSQL
db_config = {
    "dbname": "phone",
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
                return render_template("next_page.html", phone_number=phone_number, error="Data đã tồn tại.")

        # Thực hiện lưu data vào cơ sở dữ liệu
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO phone (phone_number, data) VALUES ('{phone_number}', '{data}');")
            conn.commit()
            cursor.close()
            conn.close()
            print("Lưu dữ liệu thành công!")
            return render_template("next_page.html", phone_number=phone_number, success="Đã lưu thành công.")
        except Exception as e:
            print(f"Lỗi khi thực hiện truy vấn INSERT: {e}")
            return render_template("next_page.html", phone_number=phone_number, error="Lưu dữ liệu không thành công.")

    return render_template("next_page.html", phone_number=phone_number)

@app.route("/save_data", methods=["POST"])
def save_data():
    if request.method == "POST":
        phone_number = session.get("phone_number")
        data = request.form.get("data")

        if not phone_number:
            return redirect(url_for("login"))

        # Kiểm tra nếu data đã tồn tại trong cơ sở dữ liệu
        existing_data = get_data_from_db()
        if existing_data is None:
            existing_data = []

        for row in existing_data:
            if row[2] == data:
                return render_template("next_page.html", phone_number=phone_number, data=data, error="Data đã tồn tại.")

        # Thực hiện lưu data vào cơ sở dữ liệu
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO phone (phone_number, data) VALUES ('{phone_number}', '{data}');")
            conn.commit()
            cursor.close()
            conn.close()
            print("Lưu dữ liệu thành công!")
            return render_template("next_page.html", phone_number=phone_number, success="Đã lưu thành công.")
        except Exception as e:
            print(f"Lỗi khi thực hiện truy vấn INSERT: {e}")
            return render_template("next_page.html", phone_number=phone_number, data=data, error="Lưu dữ liệu không thành công.")


if __name__ == "__main__":
    app.run(debug=True)


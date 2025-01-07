from flask import Flask, render_template, request, redirect, send_file , jsonify
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from reportlab.pdfgen import canvas
import pyodbc
import io
import pandas as pd
import os
import json
import joblib
import xlsxwriter
from prophet import Prophet
from flask import jsonify, request
import pandas as pd




# Initialize Flask App
app = Flask(__name__)



@app.route("/")
def home():
    # Define default dataset path
    dataset_dir = os.path.join("static", "data")
    dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")

    try:
        # Check if the uploaded dataset exists
        if not os.path.exists(dataset_path):
            raise FileNotFoundError("No uploaded dataset found. Please upload a dataset.")

        # Load the uploaded dataset
        data = pd.read_csv(dataset_path)

        # Identify numerical and categorical columns
        numerical_columns = data.select_dtypes(include=["number"]).columns.tolist()
        categorical_columns = data.select_dtypes(include=["object"]).columns.tolist()

        if len(numerical_columns) < 2:
            raise ValueError("Dataset must have at least two numerical columns for visualizations.")

        # Prepare data for bar chart (average of the first numerical column grouped by the first categorical column)
        if categorical_columns:
            first_category = categorical_columns[0]
            bar_chart_data_raw = data.groupby(first_category)[numerical_columns[0]].mean().to_dict()
        else:
            bar_chart_data_raw = {}

        # Prepare data for scatter plot (first two numerical columns)
        scatter_data = data[[numerical_columns[0], numerical_columns[1]]].rename(
            columns={numerical_columns[0]: "x", numerical_columns[1]: "y"}
        ).to_dict(orient="records")

        # Prepare data for line chart (cumulative sum of the first numerical column)
        line_chart_data_raw = data[numerical_columns[0]].cumsum().to_dict()

        # Prepare data for pie chart (distribution of the first categorical column)
        if categorical_columns:
            pie_chart_data_raw = data[first_category].value_counts().to_dict()
        else:
            pie_chart_data_raw = {}

        # Prepare data for heatmap
        heatmap_data_raw = data[numerical_columns].corr().to_dict()

        # Convert dict_keys and dict_values to lists for charts
        bar_chart_data = {"labels": list(bar_chart_data_raw.keys()), "values": list(bar_chart_data_raw.values())}
        line_chart_data = {"labels": list(line_chart_data_raw.keys()), "values": list(line_chart_data_raw.values())}
        pie_chart_data = {"labels": list(pie_chart_data_raw.keys()), "values": list(pie_chart_data_raw.values())}

    except Exception as e:
        # Handle errors by displaying a default message or asking users to upload a valid dataset
        return render_template("index.html", error=str(e))

    # Use json.dumps to ensure data is JSON serializable
    return render_template(
        "index.html",
        bar_chart_data=json.dumps(bar_chart_data),
        scatter_data=json.dumps(scatter_data),
        line_chart_data=json.dumps(line_chart_data),
        pie_chart_data=json.dumps(pie_chart_data),
        heatmap_data=json.dumps(heatmap_data_raw),
    )
@app.route("/add_card", methods=["GET", "POST"])
def add_card():
    if request.method == "POST":
        # Get form data
        title = request.form["title"]
        description = request.form["description"]
        link = request.form["link"]

        # Build the connection string
        conn_str = (
            f"DRIVER={db_config['Driver']};"
            f"SERVER={db_config['Server']};"
            f"DATABASE={db_config['Database']};"
            f"Trusted_Connection={db_config['Trusted_Connection']}"
        )
        
        # Insert data into the database
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO insights (title, description, link) VALUES (?, ?, ?)",
            (title, description, link)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Redirect back to the home page
        return redirect("/")

    # Render the form template
    return render_template("add_card.html")
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        # Get form data
        username = request.form["username"]
        email = request.form["email"]

        # Build the connection string
        conn_str = (
            f"DRIVER={db_config['Driver']};"
            f"SERVER={db_config['Server']};"
            f"DATABASE={db_config['Database']};"
            f"Trusted_Connection={db_config['Trusted_Connection']}"
        )
        
        # Insert user data into the database
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (username, email)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Redirect to a success page or home
        return redirect("/")

    # Render the user input form
    return render_template("add_user.html")

@app.route("/view_users", methods=["GET", "POST"])
def view_users():
    search_query = request.form.get("search", "")

    conn_str = (
        f"DRIVER={db_config['Driver']};"
        f"SERVER={db_config['Server']};"
        f"DATABASE={db_config['Database']};"
        f"Trusted_Connection={db_config['Trusted_Connection']}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    if search_query:
        # Fetch users matching the search query
        cursor.execute("SELECT * FROM users WHERE username LIKE ? OR email LIKE ?", (f"%{search_query}%", f"%{search_query}%"))
    else:
        # Fetch all users
        cursor.execute("SELECT * FROM users")

    rows = cursor.fetchall()
    users = [{'id': row[0], 'username': row[1], 'email': row[2]} for row in rows]

    cursor.close()
    conn.close()

    return render_template("view_users.html", users=users, search_query=search_query)

@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if request.method == "POST":
        # Get the updated data from the form
        username = request.form["username"]
        email = request.form["email"]

        # Update the user in the database
        conn_str = (
            f"DRIVER={db_config['Driver']};"
            f"SERVER={db_config['Server']};"
            f"DATABASE={db_config['Database']};"
            f"Trusted_Connection={db_config['Trusted_Connection']}"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET username = ?, email = ? WHERE id = ?",
            (username, email, user_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/view_users")

    # Fetch the current user data for the form
    conn_str = (
        f"DRIVER={db_config['Driver']};"
        f"SERVER={db_config['Server']};"
        f"DATABASE={db_config['Database']};"
        f"Trusted_Connection={db_config['Trusted_Connection']}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # Pass the current user data to the template
    return render_template("edit_user.html", user={'id': user[0], 'username': user[1], 'email': user[2]})
@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    # Delete the user from the database
    conn_str = (
        f"DRIVER={db_config['Driver']};"
        f"SERVER={db_config['Server']};"
        f"DATABASE={db_config['Database']};"
        f"Trusted_Connection={db_config['Trusted_Connection']}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/view_users")

# Route to generate and download a PDF for a specific user
@app.route("/download_user_pdf/<int:user_id>")
def download_user_pdf(user_id):
    # Build the connection string
    conn_str = (
        f"DRIVER={db_config['Driver']};"
        f"SERVER={db_config['Server']};"
        f"DATABASE={db_config['Database']};"
        f"Trusted_Connection={db_config['Trusted_Connection']}"
    )
    
    # Fetch user details from the database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT username, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return "User not found", 404

    # Generate the PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica", 12)

    # Add content to the PDF
    pdf.drawString(100, 750, f"User Report")
    pdf.drawString(100, 730, f"Name: {user[0]}")
    pdf.drawString(100, 710, f"Email: {user[1]}")

    # Finalize and save the PDF
    pdf.save()
    buffer.seek(0)

    # Return the PDF as a downloadable file
    return send_file(buffer, as_attachment=True, download_name=f"user_{user_id}_report.pdf", mimetype="application/pdf")

@app.route("/download_all_users_pdf")
def download_all_users_pdf():
    # Build the connection string
    conn_str = (
        f"DRIVER={db_config['Driver']};"
        f"SERVER={db_config['Server']};"
        f"DATABASE={db_config['Database']};"
        f"Trusted_Connection={db_config['Trusted_Connection']}"
    )
    
    # Fetch all users from the database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT username, email FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    # Generate the PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica", 12)

    # Add content to the PDF
    pdf.drawString(100, 800, "Consolidated User Report")
    pdf.drawString(100, 780, f"Total Users: {len(users)}")
    y_position = 760

    # Add each user's details
    for user in users:
        pdf.drawString(100, y_position, f"Name: {user[0]} | Email: {user[1]}")
        y_position -= 20

        # Prevent text from going off the page
        if y_position < 50:
            pdf.showPage()  # Start a new page
            pdf.setFont("Helvetica", 12)
            y_position = 800

    # Finalize and save the PDF
    pdf.save()
    buffer.seek(0)

    # Return the PDF as a downloadable file
    return send_file(buffer, as_attachment=True, download_name="consolidated_user_report.pdf", mimetype="application/pdf")



@app.route("/upload_dataset", methods=["GET", "POST"])
def upload_dataset():
    if request.method == "POST":
        if "dataset" not in request.files:
            return "No file part", 400

        file = request.files["dataset"]
        if file.filename == "":
            return "No selected file", 400

        # Ensure the 'static/data' directory exists
        dataset_dir = os.path.join("static", "data")
        os.makedirs(dataset_dir, exist_ok=True)

        # Save the uploaded file
        dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")
        file.save(dataset_path)

        try:
            # Load and validate the dataset
            data = pd.read_csv(dataset_path)
            numerical_columns = data.select_dtypes(include=["number"]).columns.tolist()

            if len(numerical_columns) < 2:
                return "Dataset must have at least two numerical columns for visualizations.", 400

            # Additional validation or preprocessing logic can be added here

        except Exception as e:
            return f"Error processing dataset: {e}", 400

        # Redirect to the charts page after successful upload
        return redirect("/charts")

    # Render the upload form
    return render_template("upload.html")


@app.route("/charts")
def charts():
    # Define the dataset directory and file path
    dataset_dir = os.path.join("static", "data")
    dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")

    # Check if the dataset exists
    if not os.path.exists(dataset_path):
        return redirect("/")  # Redirect to the home page if no dataset is found

    try:
        # Load the dataset
        data = pd.read_csv(dataset_path)

        # Identify numerical and categorical columns
        numerical_columns = data.select_dtypes(include=["number"]).columns.tolist()
        categorical_columns = data.select_dtypes(include=["object"]).columns.tolist()

        # Initialize chart data
        bar_chart_data = {"labels": [], "values": []}
        line_chart_data = {"labels": [], "values": []}
        pie_chart_data = {"labels": [], "values": []}
        scatter_data = []
        histogram_data = {}
        area_chart_data = {"labels": [], "values": []}
        pareto_chart_data = {"labels": [], "frequencies": [], "cumulative_percentage": []}
        bubble_chart_data = []
        box_plot_data = []

        # Bar Chart: Average of the first numerical column grouped by the first categorical column
        if numerical_columns and categorical_columns:
            first_category = categorical_columns[0]
            first_numerical = numerical_columns[0]
            bar_chart_grouped = data.groupby(first_category)[first_numerical].mean().to_dict()
            bar_chart_data = {"labels": list(bar_chart_grouped.keys()), "values": list(bar_chart_grouped.values())}

        # Line Chart: Cumulative sum of the first numerical column
        if numerical_columns:
            cumulative_sum = data[numerical_columns[0]].cumsum().to_dict()
            line_chart_data = {"labels": list(cumulative_sum.keys()), "values": list(cumulative_sum.values())}

        # Pie Chart: Distribution of the first categorical column
        if categorical_columns:
            category_counts = data[categorical_columns[0]].value_counts().to_dict()
            pie_chart_data = {"labels": list(category_counts.keys()), "values": list(category_counts.values())}

        # Scatter Plot: First two numerical columns
        if len(numerical_columns) > 1:
            scatter_data = data[[numerical_columns[0], numerical_columns[1]]].rename(
                columns={numerical_columns[0]: "x", numerical_columns[1]: "y"}
            ).to_dict(orient="records")

        # Histogram: Distribution of the first numerical column
        if numerical_columns:
            histogram_data = data[numerical_columns[0]].value_counts().sort_index().to_dict()

        # Box Plot: Distribution of the first numerical column
        if numerical_columns:
            box_plot_data = data[numerical_columns[0]].tolist()

        # Area Chart: Cumulative sum of the first numerical column
        if numerical_columns:
            area_chart_data = {"labels": list(cumulative_sum.keys()), "values": list(cumulative_sum.values())}

        # Pareto Chart: Use the first categorical column
        if categorical_columns:
            category_counts = data[categorical_columns[0]].value_counts()
            cumulative_percentage = category_counts.cumsum() / category_counts.sum() * 100
            pareto_chart_data = {
                "labels": category_counts.index.tolist(),
                "frequencies": category_counts.values.tolist(),
                "cumulative_percentage": cumulative_percentage.values.tolist(),
            }

        # Bubble Chart: Use the first three numerical columns
        if len(numerical_columns) > 2:
            bubble_chart_data = [
                {
                    "x": row[numerical_columns[0]],
                    "y": row[numerical_columns[1]],
                    "r": row[numerical_columns[2]] / 5  # Scale down the size (radius)
                }
                for _, row in data.iterrows()
            ]

        # Return the prepared data to the template
        return render_template(
            "charts.html",
            bar_chart_data=json.dumps(bar_chart_data),
            line_chart_data=json.dumps(line_chart_data),
            pie_chart_data=json.dumps(pie_chart_data),
            scatter_data=json.dumps(scatter_data),
            histogram_data=json.dumps(histogram_data),
            area_chart_data=json.dumps(area_chart_data),
            pareto_chart_data=json.dumps(pareto_chart_data),
            bubble_chart_data=json.dumps(bubble_chart_data),
            box_plot_data=json.dumps(box_plot_data),
        )

    except Exception as e:
        # Handle errors gracefully and provide feedback
        return render_template(
            "charts.html",
            error=f"Error processing the dataset: {str(e)}"
        )

    
@app.route("/descriptive_statistics", methods=["GET"])
def descriptive_statistics():
    # Define the path to the uploaded dataset
    dataset_dir = os.path.join("static", "data")
    dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")

    # Check if the dataset exists
    if not os.path.exists(dataset_path):
        return jsonify({"error": "No dataset uploaded. Please upload a dataset first."}), 400

    try:
        # Load the dataset
        data = pd.read_csv(dataset_path)

        # Ensure the dataset has data
        if data.empty:
            return jsonify({"error": "The uploaded dataset is empty. Please upload a valid dataset."}), 400

        # Generate descriptive statistics for numerical columns
        numerical_columns = data.select_dtypes(include=["number"]).columns.tolist()
        if numerical_columns:
            numerical_stats = data[numerical_columns].describe().to_dict()
        else:
            numerical_stats = {}

        # Generate frequency counts for categorical columns
        categorical_columns = data.select_dtypes(include=["object"]).columns.tolist()
        if categorical_columns:
            categorical_stats = {col: data[col].value_counts().to_dict() for col in categorical_columns}
        else:
            categorical_stats = {}

        # Check if either numerical or categorical stats exist
        if not numerical_stats and not categorical_stats:
            return jsonify({"error": "The dataset does not contain any numerical or categorical columns."}), 400

        # Return the statistics as JSON
        return jsonify({
            "numerical_stats": numerical_stats,
            "categorical_stats": categorical_stats,
        })

    except Exception as e:
        return jsonify({"error": f"An error occurred while processing the dataset: {str(e)}"}), 500


# Route to serve the Descriptive Statistics page
@app.route("/statistics")
def statistics():
    return render_template("statistics.html")


@app.route("/data_cleaning", methods=["GET"])
def data_cleaning():
    # Define the path to the uploaded dataset
    dataset_dir = os.path.join("static", "data")
    dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")

    # Check if the dataset exists
    if not os.path.exists(dataset_path):
        return jsonify({"error": "No dataset uploaded. Please upload a dataset first."}), 400

    try:
        # Load the dataset
        data = pd.read_csv(dataset_path)

        # Ensure the dataset has data
        if data.empty:
            return jsonify({"error": "The uploaded dataset is empty. Please upload a valid dataset."}), 400

        # Calculate the percentage of missing values for each column
        missing_values = (data.isnull().sum() / len(data) * 100).to_dict()

        # Suggest options for handling missing data
        suggestions = {
            col: "Consider filling missing values with the mean/median or dropping rows."
            if pct > 0 else "No action required."
            for col, pct in missing_values.items()
        }

        # Return the cleaning insights as JSON
        return jsonify({
            "missing_values": missing_values,
            "suggestions": suggestions,
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred while processing the dataset: {str(e)}"}), 500


# Route to serve the Data Cleaning Insights page
@app.route("/cleaning")
def cleaning():
    return render_template("cleaning.html")

@app.route("/export_excel", methods=["GET"])
def export_excel():
    # Define the path to the uploaded dataset
    dataset_dir = os.path.join("static", "data")
    dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")

    # Check if the dataset exists
    if not os.path.exists(dataset_path):
        return "No dataset uploaded. Please upload a dataset first.", 400

    try:
        # Load the dataset
        data = pd.read_csv(dataset_path)

        # Generate descriptive statistics
        descriptive_stats = data.describe(include="all").transpose()

        # Create an in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            # Write dataset
            data.to_excel(writer, index=False, sheet_name="Dataset")

            # Write descriptive statistics
            descriptive_stats.to_excel(writer, sheet_name="Descriptive Statistics")

            # Add a charts placeholder (optional for now)
            writer.sheets["Dataset"].write(0, 0, "Charts will go here!")

        output.seek(0)

        # Return the Excel file as a response
        return send_file(
            output,
            as_attachment=True,
            download_name="analysis_results.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        return f"An error occurred while exporting data: {str(e)}", 500

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@app.route("/export_pdf", methods=["GET"])
def export_pdf():
    # Define the path to the uploaded dataset
    dataset_dir = os.path.join("static", "data")
    dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")

    # Check if the dataset exists
    if not os.path.exists(dataset_path):
        return "No dataset uploaded. Please upload a dataset first.", 400

    try:
        # Load the dataset
        data = pd.read_csv(dataset_path)

        # Generate descriptive statistics
        descriptive_stats = data.describe(include="all").transpose()

        # Create an in-memory PDF file
        output = io.BytesIO()
        pdf = canvas.Canvas(output, pagesize=letter)
        pdf.setTitle("Analysis Results")

        # Add title
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(100, 750, "Analysis Results")

        # Write dataset summary (only a sample for demonstration)
        pdf.setFont("Helvetica", 10)
        y = 720
        for col, stats in descriptive_stats.iterrows():
            text = f"{col}: Mean = {stats['mean']}, Std = {stats['std']}"
            pdf.drawString(100, y, text)
            y -= 20
            if y < 50:
                pdf.showPage()
                y = 750

        pdf.save()
        output.seek(0)

        # Return the PDF file as a response
        return send_file(
            output,
            as_attachment=True,
            download_name="analysis_results.pdf",
            mimetype="application/pdf",
        )
    except Exception as e:
        return f"An error occurred while exporting data: {str(e)}", 500

    
@app.route("/forecast", methods=["GET", "POST"])
def forecast():
    # Define the path to the uploaded dataset
    dataset_dir = os.path.join("static", "data")
    dataset_path = os.path.join(dataset_dir, "uploaded_dataset.csv")

    # Check if the dataset exists
    if not os.path.exists(dataset_path):
        return redirect("/")  # Redirect to the home page if no dataset is found

    try:
        if request.method == "POST":
            # Load the dataset
            data = pd.read_csv(dataset_path)

            # Ensure a DateTime column exists
            if "Date" not in data.columns:
                return render_template("forecast.html", error="The dataset must have a 'Date' column.")

            # Convert the Date column to datetime
            data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
            if data["Date"].isnull().any():
                return render_template("forecast.html", error="The 'Date' column contains invalid date values.")

            # Ensure at least one numerical column exists for forecasting
            numerical_columns = data.select_dtypes(include=["number"]).columns.tolist()
            if not numerical_columns:
                return render_template("forecast.html", error="The dataset must contain at least one numerical column.")

            # Sort data by Date
            data = data.sort_values("Date")

            # Select the first numerical column for forecasting
            target_column = numerical_columns[0]

            # Prepare the dataset for Prophet
            df_prophet = data[["Date", target_column]].rename(columns={"Date": "ds", target_column: "y"})

            # Train the Prophet model
            model = Prophet()
            model.fit(df_prophet)

            # Create a future DataFrame for 30 days
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)

            # Prepare the forecast data for visualization
            forecast_data = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_dict(orient="records")

            return render_template("forecast.html", forecast_data=forecast_data, column=target_column)

        # Render the forecast page for GET request
        return render_template("forecast.html", forecast_data=None)
    except Exception as e:
        return render_template("forecast.html", error=f"An error occurred: {str(e)}")

def run_app():
    app.run(debug=True, use_reloader=False)

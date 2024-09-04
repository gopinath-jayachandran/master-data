import datetime
from flask import Flask, request, jsonify
import pandas as pd
import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection parameters from environment variables
db_params = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

app = Flask(__name__)


def connect_to_db():
    """Establish a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(**db_params)
        return connection
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)
        return None


@app.route('/sbu', methods=['POST'])
def upload_sbu_file():
    """Endpoint to upload a CSV file and insert data into the 'sbu' table."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            connection = connect_to_db()
            if connection:
                cursor = connection.cursor()
                for index, row in df.iterrows():
                    sbu_name = row['SBU']

                    # Insert the data into the 'sbu' table
                    query = """
                    INSERT INTO public.sbu (name, created_at)
                    VALUES (%s, %s)
                    """
                    cursor.execute(query, (sbu_name, datetime.datetime.now()))

                connection.commit()
                cursor.close()
                connection.close()
                return jsonify({'message': 'Data processed successfully'}), 200
            else:
                return jsonify({'error': 'Failed to connect to database'}), 500

        except Exception as e:
            print("An error occurred:", e)
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file format'}), 400


@app.route('/job_role', methods=['POST'])
def upload_job_role_file():
    """Endpoint to upload a CSV file and insert data into the 'job_role' table."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            connection = connect_to_db()
            if connection:
                cursor = connection.cursor()
                for index, row in df.iterrows():
                    job_role_name = row['Job Role']

                    # Insert the data into the 'job_role' table
                    query = """
                    INSERT INTO public.job_role (name, created_at)
                    VALUES (%s, %s)
                    """
                    cursor.execute(query, (job_role_name, datetime.datetime.now()))

                connection.commit()
                cursor.close()
                connection.close()
                return jsonify({'message': 'Data processed successfully'}), 200
            else:
                return jsonify({'error': 'Failed to connect to database'}), 500

        except Exception as e:
            print("An error occurred:", e)
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file format'}), 400


def expand_grades(grade):
    """Expand grades into individual values and handle ranges. Exclude specific values."""
    if grade == "Not Applicable" or "M9 & Above" in grade:
        return []
    if "MT" in grade:
        if "-" in grade:
            start, end = grade.split(" - ")
            start_num = int(start[2:])
            end_num = int(end[2:])
            return [f"MT{i}" for i in range(start_num, end_num + 1)]
        elif " & Above" in grade:
            start_num = int(grade.split(" ")[0][2:])
            return [f"MT{i}" for i in range(start_num, 19)]  # Assuming MT19 as the highest
    return [grade]


@app.route('/grade', methods=['POST'])
def upload_grade_file():
    """Endpoint to upload a CSV file and insert data into the 'grade' table."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            connection = connect_to_db()
            if connection:
                # Fetch existing grades from the database
                cursor = connection.cursor()
                cursor.execute("SELECT name FROM public.grade")
                existing_grades = set(row[0] for row in cursor.fetchall())
                cursor.close()

                # Create a set to store new unique grades
                unique_grades = set()
                for index, row in df.iterrows():
                    grade = row['Grade']
                    expanded_grades = expand_grades(grade)
                    unique_grades.update(expanded_grades)

                # Filter out grades that already exist
                new_grades = unique_grades - existing_grades

                # Insert new grades into the database
                if new_grades:
                    cursor = connection.cursor()
                    for grade_name in new_grades:
                        query = """
                        INSERT INTO public.grade (name, created_at)
                        VALUES (%s, %s)
                        """
                        cursor.execute(query, (grade_name, datetime.datetime.now()))

                    connection.commit()
                    cursor.close()

                connection.close()
                return jsonify({'message': 'Data processed successfully'}), 200
            else:
                return jsonify({'error': 'Failed to connect to database'}), 500

        except Exception as e:
            print("An error occurred:", e)
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file format'}), 400


@app.route('/job_role_grade', methods=['POST'])
def upload_job_role_grade_file():
    """Endpoint to upload a CSV file and map job roles to grades."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            connection = connect_to_db()
            if connection:
                # Create the 'job_role_grade' table if it does not exist
                # create_table_job_role_grade(connection)

                # Fetch existing job roles and grades from the database
                cursor = connection.cursor()
                cursor.execute("SELECT id, name FROM public.job_role")
                job_roles = {row[1]: row[0] for row in cursor.fetchall()}

                cursor.execute("SELECT id, name FROM public.grade")
                grades = {row[1]: row[0] for row in cursor.fetchall()}
                cursor.close()

                # Prepare data for insertion
                to_insert = []
                for index, row in df.iterrows():
                    job_role_name = row['Job Role']
                    grade = row['Grade']

                    # Expand grades and filter out invalid entries
                    expanded_grades = expand_grades(grade)

                    if job_role_name in job_roles:
                        job_role_id = job_roles[job_role_name]
                        for expanded_grade in expanded_grades:
                            if expanded_grade in grades:
                                grade_id = grades[expanded_grade]
                                to_insert.append((job_role_id, grade_id))

                # Insert new mappings into the database
                if to_insert:
                    cursor = connection.cursor()
                    query = """
                    INSERT INTO public.job_role_grade (job_role_id, grade_id, created_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (job_role_id, grade_id) DO NOTHING
                    """
                    cursor.executemany(query,
                                       [(job_role_id, grade_id, datetime.datetime.now()) for job_role_id, grade_id in
                                        to_insert])
                    connection.commit()
                    cursor.close()

                connection.close()
                return jsonify({'message': 'Data processed successfully'}), 200
            else:
                return jsonify({'error': 'Failed to connect to database'}), 500

        except Exception as e:
            print("An error occurred:", e)
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file format'}), 400


if __name__ == '__main__':
    app.run(debug=True)

import os
import sqlite3
import argparse

def create_database():
    if not os.path.exists('jobs.db'):
        conn = sqlite3.connect('jobs.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE scraped_jobs
                     (job_id TEXT PRIMARY KEY, title TEXT, link TEXT, keyword TEXT)''')
        conn.commit()
        conn.close()


def remove_job_from_db(job_id):
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()

    # Check if the job exists in the database
    c.execute("SELECT * FROM scraped_jobs WHERE job_id = ?", (job_id,))
    entry = c.fetchone()

    if entry:
        # If the job exists, delete it from the database
        c.execute("DELETE FROM scraped_jobs WHERE job_id = ?", (job_id,))
        conn.commit()
        print("Job removed successfully.")
    else:
        print("Job not found in the database.")

    conn.close()

def clear_database():
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute("DELETE FROM scraped_jobs")
    conn.commit()
    conn.close()

def is_job_scraped(job_id, keyword):
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute("SELECT job_id FROM scraped_jobs WHERE job_id = ?", (job_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_job_as_scraped(job_id, title, link, keyword):
    global conn
    try:
        conn = sqlite3.connect('jobs.db')
        c = conn.cursor()
        c.execute("SELECT job_id FROM scraped_jobs WHERE job_id = ?", (job_id,))
        result = c.fetchone()
        if result is None:
            c.execute("INSERT INTO scraped_jobs (job_id, title, link, keyword) VALUES (?, ?, ?, ?)", (job_id, title, link, keyword))
            conn.commit()
            print(f"Job {job_id} marked as scraped for keyword: {keyword}")
        else:
            print(f"Job {job_id} already scraped for keyword: {keyword}")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage scraped job database")
    parser.add_argument("-c", "--clear", action="store_true", help="Clear the entire database")
    parser.add_argument("-s", "--remove", type=str, help="Remove a single entry by job_id")
    args = parser.parse_args()

    if args.clear:
        clear_database()
        print("Database cleared successfully.")

    if args.remove:
        remove_job_from_db(args.remove)
        print(f"Entry with job_id '{args.remove}' removed successfully.")

import psycopg2

# ================= SUPABASE CREDENTIALS =================
HOST = "aws-1-eu-west-1.pooler.supabase.com"
PORT = 6543
DATABASE = "postgres"

# ⚠️ Replace with your real values
USER = "postgres.hlfsfmjzefhjjtovdkwu"
PASSWORD = "uns91QMI6xnAHpug"
# =======================================================


def test_connection():

    print(f"Connecting to {HOST} as {USER}...")

    try:
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DATABASE,
            user=USER,
            password=PASSWORD,
            sslmode="require",
            connect_timeout=10
        )

        cur = conn.cursor()

        # Run test query
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]

        print("\n✅ SUCCESS: Connected to Supabase!")
        print("PostgreSQL version:")
        print(version)

        cur.close()
        conn.close()

    except Exception as e:

        print("\n❌ CONNECTION FAILED")
        print("Error:", e)

        print("\nCheck the following:")
        print("1. Username is correct")
        print("2. Password has no spaces")
        print("3. SSL is enabled")
        print("4. Port is 6543 (session pooler)")
        print("5. IP is not blocked")


# ================= RUN TEST =================

if __name__ == "__main__":
    test_connection()
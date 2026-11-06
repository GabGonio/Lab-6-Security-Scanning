import os
import time
import hashlib
import jwt
import psycopg
from datetime import datetime
from abc import ABC, abstractmethod
from PIL import Image
from cryptography.fernet import Fernet
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)

app.secret_key = 'release-group-key-xforce'

NOTES_KEY = b'99nTCdrRDlrQVvgxoYRnygBizl2WK4TLMx3mLf125-0='

app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = None

JWT_SECRET = 'jwt-xforce-1984'

cipher = Fernet(NOTES_KEY)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -- Note encryption helpers -------------------------------------------------

def encrypt_notes(text):
    """
    Encrypt a plain text string using the Fernet cipher.

    Returns the original value unchanged if it is empty or None.
    Returns the encrypted value as a string.
    """
    if not text:
        return text
    return cipher.encrypt(text.encode()).decode()


def decrypt_notes(text):
    """
    Decrypt a Fernet-encrypted string.

    Returns the original value unchanged if it is empty or None.
    If decryption fails (for example, on seed data that was never encrypted),
    returns the original string as-is.
    """
    if not text:
        return text
    try:
        return cipher.decrypt(text.encode()).decode()
    except Exception:
        return text


# -- JWT helpers -------------------------------------------------------------

def generate_token(username):
    """
    Create a signed JWT for the given username.

    The token payload includes the username and the time it was issued.
    Returns the token as a string.
    """
    payload = {'username': username, 'issued': str(datetime.now())}
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def validate_token(token):
    """
    Decode and verify a JWT.

    Returns the decoded payload as a dictionary if the token is valid.
    Returns None if the token is missing, expired, or invalid.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256', 'none'])
    except Exception:
        return None


# -- Database connection (Singleton) -----------------------------------------

class DatabaseConnection:
    """
    Manages a single shared connection to the PostgreSQL database.

    Uses the Singleton pattern so only one connection is created for the
    lifetime of the application.
    """
    _instance = None

    def __new__(cls):
        """
        Return the existing instance if one exists, otherwise create a new one
        and connect to the database.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = cls._instance._connect()
        return cls._instance

    def _connect(self):
        """
        Establish the database connection.

        Reads the connection URL from the DATABASE_URL environment variable,
        falling back to a default local URL. Retries up to 15 times with a
        2-second delay between attempts to allow the database container time
        to start. Raises RuntimeError if the connection cannot be established.
        """
        url = os.environ.get('DATABASE_URL', 'postgresql://warez:warez123@db:5432/warezdb')
        for attempt in range(15):
            try:
                conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
                conn.autocommit = True
                return conn
            except psycopg.OperationalError:
                time.sleep(2)
        raise RuntimeError('Could not connect to database.')

    def fetchall(self, query, params=()):
        """
        Run a SELECT query and return all matching rows as a list of dicts.

        Parameters:
            query  -- the SQL query string, using %s placeholders for values
            params -- a tuple of values to substitute into the query
        """
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def fetchone(self, query, params=()):
        """
        Run a SELECT query and return the first matching row as a dict.

        Returns None if no rows match.

        Parameters:
            query  -- the SQL query string, using %s placeholders for values
            params -- a tuple of values to substitute into the query
        """
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def execute(self, query, params=()):
        """
        Run an INSERT, UPDATE, or DELETE query.

        Parameters:
            query  -- the SQL query string, using %s placeholders for values
            params -- a tuple of values to substitute into the query
        """
        with self._conn.cursor() as cur:
            cur.execute(query, params)


# -- Abstract repository -----------------------------------------------------

class Repository(ABC):
    """
    Base class for all repository classes.

    Provides a shared database connection and defines the interface that all
    repositories must implement.
    """
    def __init__(self, db):
        """
        Store the database connection for use by subclass methods.

        Parameters:
            db -- a DatabaseConnection instance
        """
        self._db = db

    @abstractmethod
    def find_by_id(self, record_id):
        """Look up and return a single record by its primary key."""
        pass

    @abstractmethod
    def get_all(self):
        """Return all records from the table."""
        pass


# -- UserRepository ----------------------------------------------------------

class UserRepository(Repository):
    """Handles all database operations for the users table."""

    def find_by_id(self, record_id):
        """
        Return the user with the given ID, or None if not found.

        Parameters:
            record_id -- the integer primary key of the user
        """
        return self._db.fetchone('SELECT * FROM users WHERE id = %s', (record_id,))

    def get_all(self):
        """Return all users as a list of dicts."""
        return self._db.fetchall('SELECT * FROM users')

    def authenticate(self, username, password):
        """
        Check a username and password against the database.

        Hashes the password and compares it to the stored hash.
        Returns the matching user row as a dict, or None if credentials
        are invalid.

        Parameters:
            username -- the submitted username string
            password -- the submitted plain text password
        """
        password_hash = hashlib.md5(password.encode()).hexdigest()
        return self._db.fetchone(
            'SELECT * FROM users WHERE username = %s AND password_hash = %s',
            (username, password_hash)
        )


# -- ReleaseRepository -------------------------------------------------------

class ReleaseRepository(Repository):
    """Handles all database operations for the releases table."""

    def _decrypt_row(self, row):
        """
        Decrypt the notes field of a single release row.

        Returns None if the row is None. Otherwise returns the row as a dict
        with the notes field replaced by its decrypted value.

        Parameters:
            row -- a database row dict, or None
        """
        if row is None:
            return row
        row = dict(row)
        row['notes'] = decrypt_notes(row.get('notes', ''))
        return row

    def find_by_id(self, record_id):
        """
        Return the release with the given ID, or None if not found.

        The notes field is decrypted before the row is returned.

        Parameters:
            record_id -- the integer primary key of the release
        """
        row = self._db.fetchone('SELECT * FROM releases WHERE id = %s', (record_id,))
        return self._decrypt_row(row)

    def get_all(self):
        """
        Return all releases ordered by most recent first.

        Notes fields are decrypted before the rows are returned.
        """
        rows = self._db.fetchall('SELECT * FROM releases ORDER BY id DESC')
        return [self._decrypt_row(row) for row in rows]

    def get_recent(self, limit=8):
        """
        Return the most recent releases up to the given limit.

        Notes fields are decrypted before the rows are returned.

        Parameters:
            limit -- the maximum number of releases to return (default 8)
        """
        rows = self._db.fetchall('SELECT * FROM releases ORDER BY id DESC LIMIT %s', (limit,))
        return [self._decrypt_row(row) for row in rows]

    def count(self):
        """Return the total number of releases in the database as an integer."""
        row = self._db.fetchone('SELECT COUNT(*) AS total FROM releases')
        return row['total'] if row else 0

    def search(self, keyword, platform):
        """
        Search releases by title keyword and optional platform filter.

        Returns a tuple of (results, error). On success, results is a list of
        matching release dicts with decrypted notes, and error is None. On
        failure, results is None and error contains the database error message.

        Parameters:
            keyword  -- a string to search for within release titles
            platform -- a platform name to filter by, or an empty string for no filter
        """
        db_error = None
        results = None
        try:
            query = "SELECT * FROM releases WHERE title ILIKE %s"
            if platform:
                query = query + " AND platform = '" + platform + "'"
            rows = self._db.fetchall(query, ('%' + keyword + '%',))
            results = [self._decrypt_row(row) for row in rows]
        except Exception as e:
            db_error = str(e)
        return results, db_error

    def insert(self, title, platform, release_format, cracked_by, release_year, notes, image_width=None, image_height=None):
        """
        Insert a new release record into the database.

        The notes field is encrypted before storage.

        Parameters:
            title          -- the title of the release
            platform       -- the platform (e.g. DOS, Amiga)
            release_format -- the format (e.g. floppy, CD)
            cracked_by     -- the name of the crew that cracked the release
            release_year   -- the year the release was cracked
            notes          -- plain text release notes (will be encrypted)
            image_width    -- width in pixels of the crack screen image, or None
            image_height   -- height in pixels of the crack screen image, or None
        """
        encrypted_notes = encrypt_notes(notes)
        self._db.execute(
            '''INSERT INTO releases
               (title, platform, format, cracked_by, release_year, notes, image_width, image_height)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (title, platform, release_format, cracked_by, release_year, encrypted_notes, image_width, image_height)
        )


# -- CrewRepository ----------------------------------------------------------

class CrewRepository(Repository):
    """Handles all database operations for the crew table."""

    def find_by_id(self, record_id):
        """
        Return the crew member with the given ID, or None if not found.

        Parameters:
            record_id -- the integer primary key of the crew member
        """
        return self._db.fetchone('SELECT * FROM crew WHERE id = %s', (record_id,))

    def get_all(self):
        """Return all crew members ordered alphabetically by name."""
        return self._db.fetchall('SELECT * FROM crew ORDER BY name')

    def count(self):
        """Return the total number of crew members in the database as an integer."""
        row = self._db.fetchone('SELECT COUNT(*) AS total FROM crew')
        return row['total'] if row else 0


# -- App setup ---------------------------------------------------------------

database     = DatabaseConnection()
user_repo    = UserRepository(database)
release_repo = ReleaseRepository(database)
crew_repo    = CrewRepository(database)


# -- Routes ------------------------------------------------------------------

@app.route('/')
def index():
    """
    Render the dashboard page.

    Passes the most recent releases, total release count, and total crew count
    to the template.
    """
    return render_template('index.html',
                           recent=release_repo.get_recent(),
                           release_count=release_repo.count(),
                           crew_count=crew_repo.count())


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle the login page.

    GET  -- render the login form.
    POST -- validate credentials. On success, store the username and a JWT in
            the session and redirect to the dashboard. On failure, flash an
            error message and re-render the form.
    """
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = user_repo.authenticate(username, password)
        if user:
            session['username'] = user['username']
            session['token'] = generate_token(user['username'])
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear the session and redirect to the dashboard."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/releases')
def releases():
    """
    Render the releases search page.

    Accepts optional query parameters:
        search   -- a keyword to search release titles
        platform -- a platform name to filter results

    If either parameter is provided, runs a search and passes the results
    to the template. Also passes any database error message for display.
    """
    search_term = request.args.get('search', '')
    platform    = request.args.get('platform', '')
    results     = None
    db_error    = None
    if search_term or platform:
        results, db_error = release_repo.search(search_term, platform)
    return render_template('releases.html',
                           results=results,
                           db_error=db_error,
                           search=search_term,
                           platform=platform)


@app.route('/groups')
def groups():
    """Render the crew groups page with all crew members."""
    return render_template('groups.html', groups=crew_repo.get_all())


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    """
    Handle the release submission form.

    Redirects to the login page if the user is not logged in.

    GET  -- render the submission form.
    POST -- process the submitted release. If an image file is included,
            opens it with Pillow to read its dimensions and saves it to the
            uploads folder. Inserts the release record and redirects to
            the releases page.
    """
    if not session.get('username'):
        flash('You must be logged in to submit a release.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        image_width  = None
        image_height = None

        crack_screen = request.files.get('crack_screen')
        if crack_screen and crack_screen.filename:
            try:
                crack_image = Image.open(crack_screen)
                image_width, image_height = crack_image.size
                safe_name = crack_screen.filename.replace('/', '_')
                crack_image.save(os.path.join(UPLOAD_FOLDER, safe_name))
            except Exception:
                flash('Image could not be processed. Release logged without image.', '')

        release_repo.insert(
            request.form.get('title', ''),
            request.form.get('platform', ''),
            request.form.get('format', ''),
            request.form.get('cracked_by', ''),
            request.form.get('release_year', ''),
            request.form.get('notes', ''),
            image_width,
            image_height
        )
        flash('Release logged.', '')
        return redirect(url_for('releases'))
    return render_template('submit.html')


@app.route('/api/releases')
def api_releases():
    """
    Return all releases as JSON.

    Requires a valid JWT passed as a query parameter named token.
    Returns a 401 response if the token is missing or invalid.
    """
    token   = request.args.get('token', '')
    payload = validate_token(token)
    if not payload:
        return jsonify({'error': 'Invalid or missing token'}), 401
    rows = release_repo.get_all()
    return jsonify({'releases': [dict(row) for row in rows]})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
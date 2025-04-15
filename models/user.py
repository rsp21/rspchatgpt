class User:
    def __init__(self, username, password, actual_id):
        self.username = username
        self.password = password  # Plaintext for now
        self.actual_id = actual_id  # This is used to fetch data from 8x8

    def check_password(self, password):
        return self.password == password

    def get_id(self):
        return self.username  # Used for session identity

    def get_actual_id(self):
        return self.actual_id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

def load_users_from_file(filepath="users.txt"):
    users = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) >= 3:
                username, password, actual_id = map(str.strip, parts[:3])
                users[username] = User(username, password, actual_id)
    return users

users = load_users_from_file()

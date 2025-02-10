class Comment:
    def __init__(self, text, likes, replies, timestamp, username):
        self.text = text
        self.likes = likes
        self.replies = replies
        self.sentiment = None
        self.topic = None
        self.url = None
        self.timestamp = timestamp
        self.username = username

class User:
    def __init__(self, username):
        self.username = username
        self.comments = []

    def add_comment(self, comment):
        self.comments.append(comment)

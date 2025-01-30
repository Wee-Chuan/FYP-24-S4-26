class Comment:
    def __init__(self, text, likes, replies_count, comment_id, timestamp):
        self.text = text
        self.likes = likes
        self.replies_count = replies_count  # Use replies_count instead of replies list
        self.sentiment = None
        self.topic = None
        self.comment_id = comment_id
        self.parent_id = None
        self.username = None
        self.timestamp = timestamp  # Add timestamp attribute

    def to_dict(self, visited_ids=None):
        """
        Convert the Comment object into a dictionary for JSON serialization.
        Prevent infinite recursion by using the visited_ids set.
        Include timestamp in the output.
        """
        if visited_ids is None:
            visited_ids = set()  # Initialize the set if it's not passed
        
        if self.comment_id in visited_ids:
            # If we've already visited this comment, avoid infinite recursion
            return None
        
        # Mark the current comment as visited
        visited_ids.add(self.comment_id)

        return {
            'text': self.text,
            'likes': self.likes,
            'replies_count': self.replies_count,  # Include replies_count
            'sentiment': self.sentiment,
            'topic': self.topic,
            'comment_id': self.comment_id,
            'parent_id': self.parent_id if self.parent_id else None,
            'timestamp': self.timestamp  # Include timestamp in the dictionary
        }


class User:
    def __init__(self, username):
        self.username = username
        self.comments = []

    def add_comment(self, comment):
        self.comments.append(comment)

    def to_dict(self):
        """
        Convert the User object into a dictionary for JSON serialization.
        """
        return {
            'username': self.username,
            'comments': [comment.to_dict() for comment in self.comments]
        }

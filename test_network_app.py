from flask import Flask, render_template

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Dummy data for testing
dummy_user = {"username": "test_user"}
dummy_ai_summary = (
    "Overall AI Summary: Social media activity is moderate with key trends identified. "
    "Top active users are test_user1, test_user2, and test_user3. "
    "Engagement is mixed, with predominantly positive sentiment and some neutral responses. "
    "Recommendations include focusing on interactive content and more personalized engagement. "
    "This summary is generated using the fallback summarizer."
)

@app.route('/')
def test_network():
    # Render the network.html template with dummy data
    return render_template(
        'dashboard/influencer_menu/network.html',
        user_id="test_user",
        user=dummy_user,
        ai_summary=dummy_ai_summary
    )

if __name__ == '__main__':
    app.run(debug=True)


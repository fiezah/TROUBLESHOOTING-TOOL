from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management (replace with a random key)

WEBEX_API_BASE = "https://api.ciscospark.com/v1"  # Base URL for Webex API

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        access_token = request.form.get('access_token')
        if validate_token(access_token):  # Validate token before storing it
            session['token'] = access_token
            flash("Token entered successfully!", "success")  # Flash success message
            return redirect(url_for('menu'))
        else:
            flash("Invalid access token. Please try again.", "error")  # Flash error message
            return redirect(url_for('index'))  # Redirect back to the index page
    return render_template('index.html')

# Function to validate the access token
def validate_token(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{WEBEX_API_BASE}/people/me", headers=headers)
    return response.status_code == 200

# Route to render the main menu page
@app.route('/menu')
def menu():
    return render_template('menu.html')

# Route to test the Webex connection using the token
@app.route('/test_connection', methods=['POST'])
def test_connection():
    token = session.get('token')  # Retrieve the token from the session
    
    if not token:
        flash("No token found! Please enter your token first.", "error")
        return redirect(url_for('menu'))

    headers = {'Authorization': f'Bearer {token}'}  # Authorization headers with the token
    response = requests.get(f"{WEBEX_API_BASE}/people/me", headers=headers)
    
    if response.status_code == 200:
        flash("Connection successful!", "success")  # Flash success message
    elif response.status_code == 401:  # Unauthorized error
        flash("Invalid token! Please enter a valid token.", "error")  # Flash error message
        session.pop('token', None)  # Clear the invalid token from session
    else:
        flash("Connection failed! Check your token.", "error")  # Flash error message

    return redirect(url_for('connection_status'))  # Redirect to connection status page

# Route to show the connection status page
@app.route('/connection_status')
def connection_status():
    return render_template('connection_status.html')

# Route to get and display user information from Webex API
@app.route('/user_info')
def user_info():
    token = session.get('token')
    
    if not token:
        flash("No token found. Please enter a token.", "error")
        return redirect(url_for('menu'))
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(WEBEX_API_BASE + '/people/me', headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        user = {
            'avatar': user_data.get('avatar', 'default-avatar.png'),
            'displayName': user_data.get('displayName', 'N/A'),
            'email': user_data.get('emails', ['N/A'])[0],
            'orgId': user_data.get('orgId', 'N/A')
        }
        return render_template('user_info.html', user=user)
    elif response.status_code == 401:  # Unauthorized error
        flash("Invalid token! Please enter a valid token.", "error")  # Flash error message
        session.pop('token', None)  # Clear the invalid token from session
    else:
        flash("Failed to fetch user information. Please try again.", "error")

    return redirect(url_for('menu'))  # Redirect to menu

# Route to fetch and display all rooms
@app.route('/rooms')
def rooms():
    token = session.get('token')
    
    if not token:
        flash("No token found. Please enter a token.", "error")
        return redirect(url_for('menu'))
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(WEBEX_API_BASE + '/rooms', headers=headers)
    
    if response.status_code == 200:
        rooms_data = response.json().get('items', [])
        return render_template('rooms.html', rooms=rooms_data)
    elif response.status_code == 401:  # Unauthorized error
        flash("Invalid token! Please enter a valid token.", "error")  # Flash error message
        session.pop('token', None)  # Clear the invalid token from session
    else:
        flash("Failed to fetch rooms. Please try again.", "error")

    return redirect(url_for('menu'))  # Redirect to menu

# Route to create a new room
@app.route('/create_room', methods=['GET', 'POST'])
def create_room():
    if request.method == 'POST':
        title = request.form['room_name']  # Get room name from the form
        token = session.get('token')
        
        if not token:
            flash("No token found. Please enter a token.", "error")
            return redirect(url_for('create_room'))

        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        data = {"title": title}  # Room creation data
        response = requests.post(WEBEX_API_BASE + '/rooms', headers=headers, json=data)

        if response.status_code == 200:
            flash("Room created successfully!", "success")  # Flash success message
        else:
            error_message = response.json().get('message', 'Failed to create room. Please try again.')
            flash(error_message, "error")  # Flash error message
        
        return redirect(url_for('create_room'))  # Redirect to stay on the same page

    return render_template('create_room.html')

# Route to send a message to a room based on its name
@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    token = session.get('token')

    if not token:
        flash("No token found. Please enter a token.", "error")
        return redirect(url_for('send_message'))

    headers = {'Authorization': f'Bearer {token}'}
    rooms_response = requests.get(WEBEX_API_BASE + '/rooms', headers=headers)

    if rooms_response.status_code == 200:
        rooms_data = rooms_response.json().get('items', [])
    else:
        flash("Failed to fetch rooms. Please try again.", "error")
        rooms_data = []  # No rooms available

    if request.method == 'POST':
        room_id = request.form['room_id']  # Get selected room ID from the form
        message = request.form['message']  # Get message content from the form

        # Send the message to the selected room
        message_headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        data = {"roomId": room_id, "text": message}  # Message data
        message_response = requests.post(WEBEX_API_BASE + '/messages', headers=message_headers, json=data)

        if message_response.status_code == 200:
            flash("Message sent successfully!", "success")  # Flash success message
        else:
            error_message = message_response.json().get('message', 'Failed to send message. Please try again.')
            flash(error_message, "error")  # Flash error message

        return redirect(url_for('send_message'))  # Redirect to stay on the same page

    return render_template('send_message.html', rooms=rooms_data)  # Pass rooms data to the template

if __name__ == '__main__':
    app.run(debug=True)  # Start the Flask app in debug mode

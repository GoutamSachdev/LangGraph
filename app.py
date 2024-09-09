import streamlit as st
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import datetime
import pickle
from datetime import datetime , timedelta
import pytz
from groq import Groq

# Initialize the client
client = Groq()

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Load credentials from `credentials.json`
def initialize_google_calendar():
    creds = None
    # Check if the token.pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)  # Open a local server for authentication
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

if 'service' not in st.session_state:
    st.session_state.service = initialize_google_calendar()

service = st.session_state.service

# Initialize conversation history
def get_today_and_tomorrow():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    today_str = today.strftime('%A, %Y-%m-%d')
    tomorrow_str = tomorrow.strftime('%A, %Y-%m-%d')
    return f"Today is  {today_str}", f"Tomorrow is {tomorrow_str}"

def check_availability(calendar_id='primary', start_time=None, end_time=None):
    if start_time is None:
        start_time = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    if end_time is None:
        end_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        return f"You're free from {start_time} to {end_time}."
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            return f"You have an event from {start} to {end}."

def list_all_events(calendar_id='primary'):
    events_list = []
    page_token = None

    while True:
        events_result = service.events().list(
            calendarId=calendar_id,
            pageToken=page_token,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            break

        for event in events:
            # Get the event start time
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            
            # Parse the start time string into a datetime object
            start_datetime = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            
            # Format the datetime object into a more readable string
            formatted_start = start_datetime.strftime('%A, %Y-%m-%d %I:%M %p')
            
            summary = event.get('summary', 'No title')
            events_list.append(f"{summary} at {formatted_start}")

        page_token = events_result.get('nextPageToken')
        if not page_token:
            break

    if not events_list:
        return "No upcoming events found."
    else:
        return '\n'.join(events_list)
    
list_all = list_all_events()
print(list_all)
today_str, tomorrow_str = get_today_and_tomorrow()
SystemPrompt = f"""You are an appointment scheduling assistant. Your role is to help users book appointments based on the following calendar availability. You are not available on Sundays but are available on Mondays and other weekdays. Here is the calendar availability for the owner:
{today_str} and  {tomorrow_str}
- Monday: 9:00 AM, 11:00 AM, 2:00 PM
- Tuesday: 10:00 AM, 1:00 PM, 3:00 PM
- Wednesday: 11:00 AM, 2:00 PM
- Thursday: 9:00 AM, 12:00 PM, 4:00 PM
- Friday: 10:00 AM, 12:00 PM
- Saturday: 11:00 AM
- Sunday: No availability
- BUSY Schedule of all event list: """ + list_all + "\nYou respond only with scheduling-related information and adjust your responses based on the availability. If the user asks an unrelated question, respond with 'I'm an appointment scheduling assistant. I only help with scheduling appointments.'"

conversation_history = [
    {"role": "system", "content": f"{SystemPrompt}"},
    {"role": "user", "content": "Can we schedule a meeting at 2 PM this Wednesday?"},
    {"role": "assistant", "content": "Hi! I checked my schedule, and I’m free at 2 PM this Wednesday. I’ve booked the appointment for you. Let me know if you need any changes!"},
    {"role": "user", "content": "Are you available for an interview at 10 AM on Friday?"},
    {"role": "assistant", "content": "I'm sorry, but I have another event scheduled at 10 AM this Friday. Could we try a different time?"},
    {"role": "user", "content": "Can we have a meeting at 11 AM on Monday?"},
    {"role": "assistant", "content": "I’m available at 11 AM this Monday. I’ve scheduled the meeting for that time."},
    {"role": "user", "content": "Can we have a meeting tomorrow?"},
    {"role": "assistant", "content": "I’m available tomorrow at 4 PM. Does that time work for you?"},
    {"role": "user", "content": "Can we meet on Sunday?"},
    {"role": "assistant", "content": "I'm not available on Sundays. Could we pick another day?"},
    {"role": "user", "content": "Can we schedule a call next Monday at 2 PM?"},
    {"role": "assistant", "content": "I’m available next Monday at 2 PM. I’ve scheduled the call for that time."},
    {"role": "user", "content": "What's your favorite movie?"},
    {"role": "assistant", "content": "I'm an appointment scheduling assistant. I only help with scheduling appointments."},
    {"role": "user", "content": "Can we meet at 5 PM tomorrow?"},
    {"role": "assistant", "content": "I'm available tomorrow at 5 PM. I'll book the meeting."},
    {"role": "user", "content": "Can we schedule something at any time on Sunday?"},
    {"role": "assistant", "content": "I don’t schedule meetings on Sundays. Could we pick another day for the meeting?"}
]

# Title of the app
st.title("Task : appointment scheduling assistant")

# Ensure session state attributes are initialized
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Function to handle sending messages
def send_message():
    user_message = st.session_state.input_text
    if user_message:
        st.session_state.messages.append({'text': user_message, 'is_user': True})
        st.session_state.input_text = ''  # Clear input field
        # Simulate a bot response
        conversation_history.append({"role": "user", "content": user_message})
        
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=conversation_history,  # Pass the full conversation history
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        # Collect the assistant's response
        assistant_response = ""
        for chunk in completion:
            assistant_chunk = chunk.choices[0].delta.content or ""
            assistant_response += assistant_chunk
        bot_message = f'"{assistant_response}"'
        conversation_history.append({"role": "assistant", "content": assistant_response})
        st.session_state.messages.append({'text': bot_message, 'is_user': False})

# Display chat messages
st.markdown("""
<style>
.message {
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 5px;
    max-width: 70%;
    position: relative;
    word-wrap: break-word;
}
.message.user {
    align-self: flex-start; /* Align user messages to the left */
    background-color: #e1ffc7;
    text-align: left; /* Align user text to the left */
}
.message.bot {
    align-self: flex-end; /* Align bot messages to the right */
    background-color: #f1f1f1;
    text-align: right; /* Align bot text to the right */
}
.message:before {
    content: '';
    position: absolute;
    top: 10px;
    width: 0;
    height: 0;
    border: 10px solid transparent;
}
.message.user:before {
    left: -10px; /* Position the user message arrow to the left */
    border-right-color: #e1ffc7; /* Match the user message background color */
    border-width: 10px 0 10px 10px;
}
.message.bot:before {
    right: -10px; /* Position the bot message arrow to the right */
    border-left-color: #f1f1f1; /* Match the bot message background color */
    border-width: 10px 10px 10px 0;
}
</style>
""", unsafe_allow_html=True)

# Create chat container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.messages:
    if message['is_user']:
        st.markdown(f'<div class="message user">{message["text"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="message bot">{message["text"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input field and send button
st.text_input('Type your message:', key='input_text')
st.button('Send', on_click=send_message)

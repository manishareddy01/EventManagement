from flask import Flask, render_template, request, redirect, session,url_for,flash
from pymongo import MongoClient
from datetime import datetime,timedelta
import pandas as pd
from bson import ObjectId

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['Event_Management']
organizers_collection = db['Organizer']
attendees_collection = db['Attendees']
events_collection = db['Events']
tickets_collection = db['Tickets']
bookings_houses = db['Bookings']
feedback_collection = db['Feedback']
payments_collection=db['Payments']
id_counters = db['id_counters']
bookings_collection = db['Bookings']

# Configure MongoDB URI
app.config['MONGO_URI'] = 'mongodb://localhost:27017/'
app.secret_key = 'Dinesh'
# Get the current date
current_date = datetime.now()

# Format the date as dd/mm/yy
formatted_date = current_date.strftime("%d/%m/%y")

@app.route('/')
def home():
    return render_template('home.html')

# View Events Page for Guests
@app.route('/view_events')
def view_events():
    events = get_events()  # Replace with your actual function
    print(events)
    return render_template('view_events.html', events=events)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = organizers_collection.find_one({'Email': email})
        print(user)
        if not user:
            flash('Invalid credentials', 'error')
            return render_template('login.html')
        if user['Email'] ==email and user['Password']==password:
            session['email'] = email
            return redirect('/event_details')
        else:
            # Invalid credentials
            flash('Invalid credentials', 'error')

    return render_template('login.html')

'''Organizer Code Block Starts'''

@app.route('/event_details', methods=['GET', 'POST'])
def event_details():
    # Check if the user is logged in
    if 'email' not in session:
        return redirect(url_for('login'))

    # Get the userId using the email from the session
    user_email = session['email']
    print("user_email",user_email)
    user_id = get_user_id_from_email(user_email)  # Replace with your actual function
    session['user_id']=user_id
    print("user_id",user_id)
    # Get events associated with the userId
    events = get_user_events(user_id)  # Replace with your actual function
    print(events)
    return render_template('event_details.html', events=events)

def get_user_id_from_email(email):
    """
    Get the userId associated with the given email.
    """
    user = organizers_collection.find_one({'Email': email})
    if user:
        return user['UserId']
    else:
        return None

def get_events():
    """
    Get events associated with the given userId.
    """

    events = list(events_collection.find())
    print(events)
    columns = ['EventId', 'EventName', 'Description', 'Date', 'Time',
       'Address', 'Location', 'OrganiserId',
       'Ticket_Type', 'Price', 'Status', 'Tickets_Available',
       'Sale_Start_Date', 'Sale_End_Date']
    df = pd.DataFrame(columns=columns)
    if not events:
        return "No Events Avilable for the Current User. Please Create a New Event if needed"

    # for event in events:
    #     print(event)
    #     event_id = event['EventId']
    #     tickets = tickets_collection.find({'EventId':event_id})
    #     df1 = pd.DataFrame.from_dict(event, orient='index').T
    #     df2 = pd.DataFrame.from_dict(tickets)
    #     df1 = df1.merge(df2,how='inner',on='EventId')
    #     df1 = df1[['EventId', 'EventName', 'Description', 'Date', 'Time',
    #    'Address', 'Location', 'OrganiserId',
    #    'Ticket_Type', 'Price', 'Status', 'Tickets_Available',
    #    'Sale_Start_Date', 'Sale_End_Date']]
    #     df = pd.concat([df, df1], ignore_index=True)
    tickets = list(tickets_collection.find())
    print("tickets are",tickets)
    # df1 = pd.DataFrame.from_dict(events, orient='index').T
    df1 = pd.DataFrame(events)
    print(df1.head())
    df2 = pd.DataFrame.from_dict(tickets)
    print(df2.head())
    df1 = df1.merge(df2, how='inner', on='EventId')
    df1 = df1[['EventId', 'EventName', 'Description', 'Date', 'Time',
               'Address', 'Location', 'OrganiserId',
               'Ticket_Type', 'Price', 'Status', 'Tickets_Available',
               'Sale_Start_Date', 'Sale_End_Date']]
    print(df1.columns)

    list_of_dicts = df1.to_dict(orient='records')

    return list_of_dicts
def get_user_events(user_id):
    """
    Get events associated with the given userId.
    """

    events = list(events_collection.find({'OrganiserId': user_id}))
    print(events)
    columns = ['EventId', 'EventName', 'Description', 'Date', 'Time',
       'Address', 'Location', 'OrganiserId',
       'Ticket_Type', 'Price', 'Status', 'Tickets_Available',
       'Sale_Start_Date', 'Sale_End_Date']
    df = pd.DataFrame(columns=columns)
    if not events:
        return {}
    for event in events:
        event_id = event['EventId']
        print(event,event_id)
        tickets = tickets_collection.find({'EventId':event_id})
        df1 = pd.DataFrame.from_dict(event, orient='index').T
        df2 = pd.DataFrame.from_dict(tickets)
        df1 = df1.merge(df2,how='inner',on='EventId')
        df1 = df1[['EventId', 'EventName', 'Description', 'Date', 'Time',
       'Address', 'Location', 'OrganiserId',
       'Ticket_Type', 'Price', 'Status', 'Tickets_Available',
       'Sale_Start_Date', 'Sale_End_Date']]
        df = pd.concat([df, df1], ignore_index=True)
    print(df.columns)
    session['Events'] = list(df1['EventId'])
    print(session['Events'])
    list_of_dicts = df.to_dict(orient='records')

    return list_of_dicts

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        sorted_events = list(events_collection.find().sort('EventId', 1))
        highest_event_id = sorted_events[-1]['EventId']
        next_id_number = int(highest_event_id[1:]) + 1
        event_id = f'E{next_id_number:03d}'
        print("Event Id is",event_id)
        # Extract form data
        event_data = {
            'EventId':event_id,
            'EventName': request.form['EventName'],
            'Description': request.form['Description'],
            'Date': request.form['Date'],
            'Time': request.form['Time'],
            'Address': request.form['Address'],
            'Location': request.form['Location'],
            'OrganiserId': session['user_id']
        }

        # Insert event data into the Events collection
        events_collection.insert_one(event_data)

        # Insert ticket data into the Tickets collection
        ticket_data = {
            'TicketId':"T106",
            'EventId': event_id,
            'Ticket_Type': request.form['Ticket_Type'],
            'Price': float(request.form['Price']),
            'Status': request.form['Status'],
            'Tickets_Available': int(request.form['Tickets_Available']),
            'Sale_Start_Date': request.form['Sale_Start_Date'],
            'Sale_End_Date': request.form['Sale_End_Date']
        }

        print("Ticket data is",ticket_data)

        tickets_collection.insert_one(ticket_data)

        return redirect(url_for('event_details'))  # Redirect to event details page

    return render_template('create_event.html')

@app.route('/update_event', methods=['GET', 'POST'])
def update_event():
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        field_to_update = request.form.get('field_to_update')
        new_value = request.form.get('new_value')
        ticket_type=request.form.get('ticket_type')
        if event_id not in session['Events']:
            flash('Permission Denied as the ,Event not created by current user', 'error')
            return redirect(url_for('update_event'))
        # Check if the field to update is in either events or tickets collection
        if field_to_update in ['EventName', 'Description', 'Date', 'Time', 'Address', 'Location', 'OrganiserId']:
            # Update the field in the events collection
            events_collection.update_one({'EventId': event_id}, {'$set': {field_to_update: new_value}})
        else:
            # Update the field in the tickets collection
            tickets_collection.update_one({'EventId': event_id,'Ticket_Type':ticket_type}, {'$set': {field_to_update: new_value}})
        return redirect(url_for('event_details'))
    # Render the update event page
    return render_template('update_event.html')

@app.route('/delete_event', methods=['GET', 'POST'])
def delete_event():
    if request.method == 'POST':
        event_id = request.form.get('event_id')

        # Check if the event exists
        event_exists = events_collection.find_one({'EventId': event_id,'OrganiserId':session['user_id']})
        if not event_exists:
            flash(('Permission Denied with current user with user_Id {0} for the given event').format(session['user_id']), 'error')
            return redirect(url_for('delete_event'))
        # Delete the event from the events collection
        events_collection.delete_one({'EventId': event_id})

        # Delete corresponding tickets from the tickets collection
        tickets_collection.delete_many({'EventId': event_id})

        # Redirect to the events page after successful deletion
        return redirect(url_for('event_details'))

    # Render the delete event page for GET requests
    return render_template('delete_event.html')

'''Organizer Code Block Ends'''

'''Attendees Code Block Starts'''

from flask import render_template, request

# ... (other imports and code) ...

@app.route('/book_event/<event_id>/<ticket_type>', methods=['GET', 'POST'])
def book_event(event_id, ticket_type):
    # Retrieve event details using event_id and ticket_type
    print("event_id, ticket_type are",event_id, ticket_type)
    event_details = get_event_details(event_id, ticket_type)  # Implement this function to get event details
    print(event_details)
    if request.method == 'POST':
        # Process the booking (reduce tickets available, update status, etc.)
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        ticket_quantity = int(request.form.get('ticket_quantity'))
        payment_method = request.form.get('payment_method')

        # Assuming 'events' collection has columns like 'EventId', 'EventName', 'Ticket_Type', 'Tickets_Available', 'Price'
        event_details = tickets_collection.find_one({'EventId': event_id, 'Ticket_Type': ticket_type})
        events = events_collection.find_one({'EventId': event_id})
        if event_details:
            # Check if enough tickets are available
            if event_details['Tickets_Available'] >= ticket_quantity:
                # Generate Booking ID and Payment ID (You might need to implement a proper ID generation mechanism)
                booking_id = generate_booking_id()
                payment_id = generate_payment_id()
                # Update 'tickets' collection
                tickets_collection.update_one(
                    {'EventId': event_id, 'Ticket_Type': ticket_type},
                    {'$inc': {'Tickets_Available': -ticket_quantity}}
                )
                available_tickets = tickets_collection.find_one({'EventId': event_id, 'Ticket_Type': ticket_type})
                if available_tickets['Tickets_Available']==0:
                    tickets_collection.update_one({'EventId': event_id,'Ticket_Type': ticket_type},  {'$set': {'Status': 'Not Available'}})
                # Insert into 'bookings' collection
                booking_data = {
                    'BookingId': booking_id,
                    'EventId': event_id,
                    'EventName': events['EventName'],
                    'CustomerName': name,
                    'TicketQuantity': ticket_quantity,
                    'PaymentStatus': 'Success'  # You can set an initial status
                }
                bookings_collection.insert_one(booking_data)
                # Insert into 'payments' collection
                payment_data = {
                    'PaymentId': payment_id,
                    'AttendeeId': email,
                    'AmountPaid': event_details['Price'] * ticket_quantity,
                    'PaymentMethod': payment_method
                }
                attendees_data = {
                    'AttendeeId': email,
                    'UserId':"Guest",
                    'EventId': event_id,
                    'TicketId': 'T101'
                }
                payments_collection.insert_one(payment_data)
                attendees_collection.insert_one(attendees_data)
                booking_data = bookings_collection.find_one({'BookingId': booking_id})
                return render_template('booking_details.html', booking_data=booking_data)
            else:
                flash('Not enough tickets available.')
                return redirect(url_for('view_events'))
        else:
            flash('Event not found.')
            return redirect(url_for('view_events'))
        return redirect(url_for('booking_details'))

    return render_template('booking_page.html', event_details=event_details)
@app.route('/booking_details/<booking_id>')
def booking_details(booking_id):
    # Retrieve booking details from the 'bookings' collection
    booking_data = bookings_collection.find_one({'BookingId': booking_id})

    if booking_data:
        # Render the booking details page
        return render_template('booking_details.html', booking_data=booking_data)
    else:
        flash('Booking not found.')
        return redirect(url_for('home'))
def get_event_details(event_id, ticket_type) :
    # Replace this with your actual function to retrieve event details
    # from the database based on the provided EventId
    event = tickets_collection.find_one({'EventId': event_id,'Ticket_Type':ticket_type})
    return event

def update_event_after_payment(event_id,ticket_type):
    # in the database after a successful payment
    events_collection.update_one({'EventId': event_id}, {'$inc': {'Tickets_Available': -1}})
    updated_event = get_event_details(event_id, ticket_type)
    if updated_event['Tickets_Available'] == 0:
        events_collection.update_one({'EventId': event_id}, {'$set': {'Status': 'Not Available'}})

# Helper function to generate a unique booking ID (You might need to implement a proper ID generation mechanism)
def generate_booking_id():
    return 'BOOK' + str(ObjectId())

# Helper function to generate a unique payment ID (You might need to implement a proper ID generation mechanism)
def generate_payment_id():
    return 'PAY' + str(ObjectId())

@app.route('/booking_search', methods=['GET', 'POST'])
def booking_search():
    if request.method == 'POST':
        # Retrieve Booking ID from the form
        booking_id = request.form.get('booking_id')

        # Check if the Booking ID exists
        if booking_id:
            # Fetch booking details based on booking_id
            booking_data = bookings_collection.find_one({'BookingId':booking_id})
            print(booking_data)
            # Check if booking_data is not None
            if booking_data:
                return render_template('booking_details.html', booking_data=booking_data)
            else:
                flash(f'Booking ID {booking_id} not found.', 'error')
        else:
            flash('Please enter a Booking ID.', 'error')

    return render_template('booking_search.html')
'''Attendees Code Block Ends'''

'''Sign Up Page'''


@app.route('/organiser_signup', methods=['GET', 'POST'])
def organiser_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')

        sorted_events = list(organizers_collection.find().sort('UserId', 1))
        highest_event_id = sorted_events[-1]['UserId']
        next_id_number = int(highest_event_id[1:]) + 1
        event_id = f'U{next_id_number:03d}'
        print("Event Id is",event_id)
        data = {  "UserId": event_id,
                  "First Name": first_name,
                  "Last Name": last_name,
                  "Email": email,
                  "Password": password,
                  "ContactNumber": contact_number,
                  "Address": address,
                  "Registration Date": formatted_date}

        # Check if password matches confirm_password
        if password != confirm_password:
            flash('Password and Confirm Password do not match.', 'error')
            return redirect(url_for('organiser_signup'))

        # Check if email is already in use
        if organizers_collection.find_one({'email': email}):
            flash('Email is already in use. Please choose another email.', 'error')
            return redirect(url_for('organiser_signup'))

        # Insert new organiser data
        organizers_collection.insert_one(data)

        # Redirect to a success page or login page
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))  # Replace with your login endpoint

    return render_template('signup.html')

'''Feedback Code Starts'''
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        email = request.form.get('email')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')
        submission_date = datetime.now()

        # Assuming you have a Feedback model
        feedback_data = {
            'EventID': event_id,
            'AttendeeId': email,
            'Rating': rating,
            'Comment': comment,
            'SubmissionDate': submission_date
        }
        print(f"Event Id is{event_id} and email is {email}" )
        # Check if the user attended the event
        attendee = attendees_collection.find_one({'EventId': event_id, 'AttendeeId': email})
        print(attendee)
        if not attendee:
            flash("You did not attend this event. Feedback submission not allowed.", "error")
            return redirect(url_for('feedback'))

        # Insert the feedback into the Feedback collection
        feedback_collection.insert_one(feedback_data)
        flash("Feedback submitted successfully.Proceed to Submit another Feedback", "success")
        return redirect(url_for('feedback'))

    return render_template('feedback_form.html')

    '''FeedBack Code Ends'''

if __name__ == '__main__':
    app.run(debug=True)
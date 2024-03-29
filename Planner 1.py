import datetime
import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox, simpledialog
import bcrypt
import mysql.connector
from PIL import ImageTk, Image
from tkcalendar import Calendar
from tkcalendar import DateEntry
import random
from random import randint


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # configure the root window
        self.title('Heiwa - Wellbeing Planner')
        self.geometry("1490x750")
        self.resizable(False, False)
        # Create the frames
        #create dictionary called frames
        self.frames = {}
        #each frame is stored in the dictionary with their name as a key and stacked
        for F in (Login, Homepage, CalendarFrame, AgendaFrame):
            frame = F(self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        # first frame raised on top of stack
        # Show the first frame
        self.show_frame(Login.__name__)

    def show_frame(self, frame_name, beans=None, coffee=None):
        # Hide the current frame
        # requested frame is taken from dictionary frames as current_frame
        current_frame = self.frames[frame_name]
        #frame is stacked on top
        current_frame.tkraise()
        if frame_name == Homepage.__name__:
            # if Homepage is the frame, coffee and bean are returned as parameters
            self.frames[Homepage.__name__].update_beans(beans)
            self.frames[Homepage.__name__].update_coffee(coffee)


class AnimatedGIF(Label):
    def __init__(self, container, path, duration=None):
        # Store the container widget and path of the GIF file
        self.container = container
        self.path = path

        # Open the GIF file and create an empty list for storing the frames
        self.image = Image.open(self.path)
        self.frames = []

        # Load all the frames of the GIF into the list
        self.load_frames()

        # Get the delay time and initialize variables for tracking the current frame and animation duration
        self.delay = self.image.info.get('duration', 100)
        self.index = 0
        self.duration = duration

        # Set the anchor point for the Label and initialize its size based on the dimensions of the first frame
        self.anchor = 'center'
        self.width, self.height = self.image.size
        Label.__init__(self, self.container, width=self.width, height=self.height)
        self.grid()

        # Start the animation
        self.start_animation()

    def load_frames(self):
        # Loop through all the frames of the GIF file, adding each one to the list of frames
        try:
            while True:
                self.frames.append(ImageTk.PhotoImage(self.image))
                self.image.seek(len(self.frames))  # skip to next frame
        except EOFError: # catch the end of file error
            # If the end of the file is reached, go back to the beginning of the file
            self.image.seek(0)

    def start_animation(self):
        # Begin showing frames
        self.show_frame()

    def stop_animation(self):
        # Stop the animation by canceling the after() method and removing the Label from the container
        self.after_cancel(self.anim)
        self.grid_forget()
        self.container.destroy()

    def show_frame(self):
        # Set the Label's image to the current frame and update the container widget
        self.config(image=self.frames[self.index])
        self.master.update()

        # Move to the next frame and reset to the first frame if the end is reached
        self.index += 1
        if self.index == len(self.frames):
            self.index = 0

            # If a duration was set, stop the animation after that duration
            if self.duration is not None:
                self.after(self.duration, self.stop_animation)

        # Use the delay time to schedule the next call to show_frame()
        self.anim = self.after(self.delay, self.show_frame)


class Database:
    def __init__(self, host, user, password, database):
        #store the host user password and database
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        #establish the connection to the database
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        #creates cursor for connection
        self.cursor = self.connection.cursor()

    #checks if username us already taken
    def is_username_taken(self, username):
        #all username with "username" are retrieved
        query = "SELECT * FROM users WHERE username = %s"
        #executes the query
        self.cursor.execute(query, (username,))
        #result of query is saved as result
        result = self.cursor.fetchone()
        #return True if result is not None and return False if result is None
        return result is not None

    def create_account(self, username, password):
        #password is hashed using utf-8 encoding and salted
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        #if username already exists, return False
        if self.is_username_taken(username):
            return False
        #otherwise, insert the hashed password and username into table users
        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        self.cursor.execute(query, (username, hashed_password))
        self.connection.commit()
        return True

    def login(self, username, password):
        #all users with username "username" are retrieved
        query = "SELECT password FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        #if there is a result
        if result is not None:
            #hashed password retrieved is encoded to bytes using utf-8 encoding
            hashed_password = result[0].encode('utf-8')
            #hashed password is compared with input password
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                #if equal, return True
                return True
            else:
                #otherwise, return False
                return False

    # retrieves number of beans from a specific user from users table
    def retrieve_beans(self, username):
        query = "SELECT beans FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        beans_number = self.cursor.fetchone()
        return beans_number

    # retrieves number of coffee from a specific user from users table
    def retrieve_coffee(self, username):
        query = "SELECT coffee FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        coffee_number = self.cursor.fetchone()
        return coffee_number

    # retrieves user_id from a specific user from users table
    def retrieve_userID(self, username):
        query = "SELECT id_users FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        id_users = self.cursor.fetchone()
        return id_users

    # retrieves level from a specific user from users table
    def retrieve_level(self, username):
        query = "SELECT level FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        level = self.cursor.fetchone()
        return level

    def add_event(self, id_users, title, description, start_date, start_time, end_date, end_time, category):
        query = "INSERT INTO events (id_users, title, description, start_date, end_date, category) VALUES (%s, %s, %s, %s, %s, %s)"
        # params holds list of parameters to be passed to the query
        params = [
            id_users[0],  # extract integer from tuple
            title,
            description,
            datetime.datetime.combine(start_date, start_time), #start_time and start_date are conbined to form datetime object
            datetime.datetime.combine(end_date, end_time),
            category
        ]
        self.cursor.execute(query, params)
        self.connection.commit() # this methods commits the changes to the database

    def add_task(self, id_users, title, description, start_date, start_time, end_date, end_time, category):
        query = "INSERT INTO tasks (id_users, title, description, start_date, end_date, category) VALUES (%s, %s, %s, %s, %s, %s)"
        params = [
            id_users[0],  # extract integer from tuple
            title,
            description,
            datetime.datetime.combine(start_date, start_time),
            datetime.datetime.combine(end_date, end_time),
            category
        ]
        self.cursor.execute(query, params)
        self.connection.commit()

    def add_activity(self, id_users, title, description, start_date, start_time, end_date, end_time, category):
        query = "INSERT INTO activity (id_users, title, description, start_date, end_date, category) VALUES (%s, %s, %s, %s, %s, %s)"
        params = [
            id_users[0],
            title,
            description,
            datetime.datetime.combine(start_date, start_time),
            datetime.datetime.combine(end_date, end_time),
            category
        ]
        self.cursor.execute(query, params)
        self.connection.commit()

    def get_customised_events(self, id_users, start_date, end_date, category):
        # Define a SQL query to select events with specific conditions
        query = "SELECT title, start_date, end_date, rewarded, category, description FROM events WHERE id_users = %s AND start_date BETWEEN %s AND %s AND category=%s "
        # Define the query parameters
        params = (id_users[0], start_date, end_date, category)
        # Execute the query with the provided parameters
        self.cursor.execute(query, params)
        # Fetch all the rows returned by the query
        rows = self.cursor.fetchall()
        # Initialize an empty list to store the events
        events = []
        # Loop through each row and extract the relevant information to create an event dictionary
        for row in rows:
            event = {
                "title": row[0],  # Extract title from row and add to dictionary
                "start_date": row[1].date(),
                # Extract start date from row, convert to date object, and add to dictionary
                "end_date": row[2].date(),  # Extract end date from row, convert to date object, and add to dictionary
                "rewarded": row[3],  # Extract rewarded status from row and add to dictionary
                "category": row[4],  # Extract category from row and add to dictionary
                "description": row[5]
            }
            # Append the event dictionary to the list of events
            events.append(event)
        # Return the list of events
        return events
    #this process is repeated for tasks and activity
    def get_customised_tasks(self, id_users, start_date, end_date, category):
        query = "SELECT title, start_date, end_date, rewarded, category, description FROM tasks WHERE id_users = %s AND start_date BETWEEN %s AND %s AND category=%s "
        params = (id_users[0], start_date, end_date, category)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        tasks = []
        for row in rows:
            task = {
                "title": row[0],
                "start_date": row[1].date(),
                "end_date": row[2].date(),
                "rewarded": row[3],
                "category": row[4],
                "description": row[5]
            }
            tasks.append(task)
        return tasks

    def get_customised_activities(self, id_users, start_date, end_date, category):
        query = "SELECT title, start_date, end_date, rewarded, category, description FROM activity WHERE id_users = %s AND start_date BETWEEN %s AND %s AND category=%s "
        params = (id_users[0], start_date, end_date, category)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        activities = []
        for row in rows:
            activity = {
                "title": row[0],
                "start_date": row[1].date(),
                "end_date": row[2].date(),
                "rewarded": row[3],
                "category": row[4],
                "description": row[5]
            }
            activities.append(activity)
        return activities

    def get_events(self, id_users, start_date, end_date):
        query = "SELECT title, start_date, end_date, rewarded, category, description FROM events WHERE id_users = %s AND start_date BETWEEN %s AND %s "
        params = (id_users[0], start_date, end_date)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        events = []
        for row in rows:
            event = {
                "title": row[0],
                "start_date": row[1].date(),
                "end_date": row[2].date(),
                "rewarded": row[3],
                "category": row[4],
                "description" : row[5]
            }
            events.append(event)
        return events

    def get_tasks(self, id_users, start_date, end_date):
        query = "SELECT title, start_date, end_date, rewarded, category, description FROM tasks WHERE id_users = %s AND start_date BETWEEN %s AND %s "
        params = (id_users[0], start_date, end_date)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        tasks = []
        for row in rows:
            task = {
                "title": row[0],
                "start_date": row[1].date(),
                "end_date": row[2].date(),
                "rewarded": row[3],
                "category": row[4],
                "description": row[5]
            }
            tasks.append(task)
        return tasks

    def get_activity(self, id_users, start_date, end_date):
        query = "SELECT title, start_date, end_date, rewarded, category, description FROM activity WHERE id_users = %s AND start_date BETWEEN %s AND %s AND rewarded=0"
        params = (id_users[0], start_date, end_date)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        activities = []
        for row in rows:
            activity = {
                "title": row[0],
                "start_date": row[1].date(),
                "end_date": row[2].date(),
                "rewarded": row[3],
                "category": row[4],
                "description": row[5]
            }
            activities.append(activity)
        return activities

   # updates the table with new category
    def change_category(self, table, id_users, start_date, end_date, new_category):
        query = f"UPDATE {table} SET category = %s WHERE id_users = %s AND start_date = %s AND end_date = %s"
        self.cursor.execute(query, (new_category, id_users[0], start_date, end_date))
        self.connection.commit()

    # updates coffee and beans in userws table by incrementing of one
    def update_reward(self, id_users):
        query = "UPDATE users SET coffee = coffee + 1 , beans = beans+1 WHERE id_users = %s"
        self.cursor.execute(query, (id_users[0],))
        self.connection.commit()

    # changes the rewarded value of table events to True
    def event_achieved(self, id_users, title, start_date, end_date):
        query = "UPDATE events SET rewarded = True WHERE id_users=%s AND title=%s AND start_date=%s AND end_date=%s"
        self.cursor.execute(query, (id_users[0], title, start_date, end_date))
        self.connection.commit()

    # changes the rewarded value of table tasks to True
    def task_achieved(self, id_users, title, start_date, end_date):
        query = "UPDATE tasks SET rewarded = True WHERE id_users=%s AND title=%s AND start_date=%s AND end_date=%s"
        self.cursor.execute(query, (id_users[0], title, start_date, end_date))
        self.connection.commit()

    # changes the rewarded value of table activity to True
    def activity_achieved(self, id_users, title, start_date, end_date):
        query = "UPDATE activity SET rewarded = True WHERE id_users=%s AND title=%s AND start_date=%s AND end_date=%s"
        self.cursor.execute(query, (id_users[0], title, start_date, end_date))
        self.connection.commit()

    # reduces of one the bean value in users table
    def reduce_bean(self, id_users):
        query = "UPDATE users SET beans = beans - 1 WHERE id_users=%s"
        self.cursor.execute(query, (id_users[0],))
        self.connection.commit()

    # reduces of one the bean value in users table
    def reduce_coffee(self, id_users):
        query = "UPDATE users SET coffee = coffee - 1 WHERE id_users=%s"
        self.cursor.execute(query, (id_users[0],))
        self.connection.commit()

    # counts the number of logs from a specific table that were rewarded
    def count_rewarded(self, table, id_users):
        query = f"SELECT COUNT(rewarded) FROM {table}  WHERE rewarded=0 AND id_users=%s"
        self.cursor.execute(query, (id_users[0],))
        count = self.cursor.fetchall()
        return count

    def level_check(self, id_users):
        # counts number of rewarded events
        query = "SELECT COUNT(rewarded) FROM events WHERE rewarded = 1 and id_users=%s"
        self.cursor.execute(query, (id_users[0],))
        count = self.cursor.fetchone()[0]
        # counts number of rewarded tasks
        query2 = "SELECT COUNT(rewarded) FROM tasks WHERE rewarded = 1 and id_users=%s"
        self.cursor.execute(query2, (id_users[0],))
        count2 = self.cursor.fetchone()[0]
        # counts number of rewarded activity
        query3 = "SELECT COUNT(rewarded) FROM activity WHERE rewarded = 1 and id_users=%s"
        self.cursor.execute(query3, (id_users[0],))
        count3 = self.cursor.fetchone()[0]
        # all counts are added together
        sum = count + count2 + count3
        # if its between 30 included and 49, user is set to level 2
        if sum >= 30 and sum < 50:
            query = "UPDATE users SET level = level + 1 WHERE id_users = %s"
            self.cursor.execute(query, (id_users[0],))
            self.connection.commit()
            return 2
        # if its greater than 50, user is set to level 3
        if sum >= 50:
            query = "UPDATE users SET level = level + 1 WHERE id_users = %s"
            self.cursor.execute(query, (id_users[0],))
            self.connection.commit()
            return 3
        else:
            return 1

#connected to database
db = Database("LAPTOP-**********", "HIna", "*********", "users")


class Login(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)

        self.container = container
        self.buttonimage = PhotoImage(file="bgbutton.png")
        # background
        self.bg = PhotoImage(file="bglogin.png")
        self.label = ttk.Label(self, image=self.bg)
        self.label.grid(row=0, column=0)

        # text welcome to Heiwa
        self.canvas = tk.Canvas(self, width=385, height=100, bd=0, highlightthickness=0)
        self.canvas.place(x=1000, y=120)
        self.bgcanvas = PhotoImage(file="bgcanvas.png")
        self.canvas.create_image(0, 0, image=self.bgcanvas, anchor="nw")
        self.canvas.create_text(182, 50, text="Welcome To Heiwa", font=("Delight Coffee", 28))

        self.firstscreen()

    def changepage(self):
        # destoys sign in and create button for sign in and create an account screen
        self.signin_button.destroy()
        self.signin_text.destroy()
        self.createaccount_text.destroy()
        self.createaccount_button.destroy()

    def account_page(self):
        self.changepage()
        # username - password text
        self.username_text = ttk.Label(self, text="Username", font=("Vanilla Caramel", 20), background="#c8bfe7")
        self.username_text.place(x=1000, y=305)
        self.password_text = ttk.Label(self, text="Password", font=("Vanilla Caramel", 20), background="#c8bfe7")
        self.password_text.place(x=1000, y=380)
        # username textbox
        self.username_line = tk.Canvas(self, width=200, height=2, bg="#000000", highlightthickness=0)
        self.username_line.place(x=1125, y=338)
        self.username_entry = tk.Entry(self.container, width=15, highlightthickness=0, bg="#c8bfe7", relief=FLAT,
                                       font=(12))
        self.username_entry.place(x=1125, y=310)
        # password textbox
        self.password_line = tk.Canvas(self, width=200, height=2, bg="#000000", highlightthickness=0)
        self.password_line.place(x=1125, y=412)
        self.password_entry = tk.Entry(self.container, width=15, highlightthickness=0, bg="#c8bfe7", relief=FLAT,
                                       font=(12))
        self.password_entry.place(x=1125, y=385)
        # button
        self.createaccount_button = tk.Button(self, image=self.buttonimage, bg="#c8bfe7", highlightthickness=0,
                                              relief="flat", command=self.validation)
        self.createaccount_button.place(x=980, y=450)
        self.createaccount_text = ttk.Label(self, text="Create An Account", font=("Vanilla Caramel", 25),
                                            background="#ffffff")
        self.createaccount_text.place(x=1060, y=465)

    def validation(self):
        # input in username and password is retrieved
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        # error message if input is less than 8 characters
        if  len(self.username) < 8 or len(self.password) < 8:
            self.invalid_text = ttk.Label(self, text="*The username or password cannot be less that 8 characters",
                                          font=("Delight Coffee", 10), background="#c8bfe7")
            self.invalid_text.place(x=960, y=530)
        # username is checked if it already exists
        elif not db.create_account(self.username, self.password):
            self.account_exists_text()
        else:
            self.loginpage()

    # error message that user already exists in create an account
    def account_exists_text(self):
        self.accountexists_text = ttk.Label(self, text="*The username is already taken", font=("Delight Coffee", 10),
                                            background="#c8bfe7")
        self.accountexists_text.place(x=1020, y=560)


    # widgets are created for sign in page
    def loginpage(self):
        self.changepage()
        # username - password text
        self.username_text = ttk.Label(self, text="Username", font=("Vanilla Caramel", 20), background="#c8bfe7")
        self.username_text.place(x=1000, y=305)
        self.password_text = ttk.Label(self, text="Password", font=("Vanilla Caramel", 20), background="#c8bfe7")
        self.password_text.place(x=1000, y=380)
        # username textbox
        self.username_line = tk.Canvas(self, width=200, height=2, bg="#000000", highlightthickness=0)
        self.username_line.place(x=1125, y=338)
        self.username_entry = tk.Entry(self.container, width=15, highlightthickness=0, bg="#c8bfe7", relief=FLAT,
                                       font=(12))
        self.username_entry.place(x=1125, y=310)
        # password textbox
        self.password_line = tk.Canvas(self, width=200, height=2, bg="#000000", highlightthickness=0)
        self.password_line.place(x=1125, y=412)
        self.password_entry = tk.Entry(self.container, width=15, highlightthickness=0, bg="#c8bfe7", relief=FLAT,
                                       font=(12))
        self.password_entry.place(x=1125, y=385)

        # loginbutton
        self.login_button = tk.Button(self, image=self.buttonimage, bg="#c8bfe7", highlightthickness=0, relief="flat",
                                      command=self.loginvalidation)
        self.login_button.place(x=980, y=450)
        self.login_text = ttk.Label(self, text="Login", font=("Vanilla Caramel", 25), background="#ffffff")
        self.login_text.place(x=1150, y=465)

    def loginvalidation(self):
        # retrieve input for username and password
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        #check if the entries are valid
        if len(self.username) < 8 or len(self.password) <8 :
            self.invalid_text2 = ttk.Label(self, text="*The username or password cannot be less that 8 characters",
                                           font=("Delight Coffee", 10), background="#c8bfe7")
            self.invalid_text2.place(x=960, y=530)
        else:
            # check if password is the same as the one stored in the database
            if not db.login(self.username, self.password):
                # error message
                self.invalid_password()
            else:
                # assign id_users, beans retrieved and coffee retrieved as global variables
                global beans_retrieved
                global coffee_retrieved
                global level
                global id_users
                # retrieves each variable from database
                level = db.retrieve_level(self.username)
                beans_retrieved = db.retrieve_beans(self.username)
                coffee_retrieved = db.retrieve_coffee(self.username)
                id_users = db.retrieve_userID(self.username)
                # Homepage frame is on top of stack
                self.container.show_frame(Homepage.__name__, beans_retrieved, coffee_retrieved)

    # invalid password message
    def invalid_password(self):
        self.invalid_password_text = ttk.Label(self, text="*The username or password is wrong",
                                               font=("Delight Coffee", 10),
                                               background="#c8bfe7")
        self.invalid_password_text.place(x=1020, y=560)

    def signin_button(self):
        self.signin_button = tk.Button(self, image=self.buttonimage, bg="#c8bfe7", highlightthickness=0, relief="flat",
                                       command=self.loginpage)
        self.signin_button.place(x=980, y=300)
        self.signin_text = ttk.Label(self, text="Sign In", font=("Vanilla Caramel", 22), background="#ffffff")
        self.signin_text.place(x=1130, y=317)

    def createaccount_button(self):
        self.createaccount_button = tk.Button(self, image=self.buttonimage, bg="#c8bfe7", highlightthickness=0,
                                              relief="flat", command=self.account_page)
        self.createaccount_button.place(x=980, y=380)
        self.createaccount_text = ttk.Label(self, text="Create Account", font=("Vanilla Caramel", 25),
                                            background="#ffffff")
        self.createaccount_text.place(x=1080, y=392)

    def firstscreen(self):
        self.signin_button()
        self.createaccount_button()


class Homepage(ttk.Frame):
    def __init__(self, container, beans=None, coffee=None):
        super().__init__(container)
        self.container = container
        self.beans = beans
        self.coffee = coffee
        #background
        self.bg = PhotoImage(file="bghome.png")
        self.label = ttk.Label(self, image=self.bg)
        self.label.grid(row=0, column=0)
        self.studygif()
        self.buttons()
        self.feedbutton()
        self.randombut()

    # updates the beans parameter
    def update_beans(self, beans):
        if beans is not None:
            global n_of_beans
            n_of_beans = beans
            self.beans_display = ttk.Label(self, text=n_of_beans, font=("Delight Coffee", 25), background="#fcfee4")
            self.beans_display.place(x=320, y=25)
    # updates the coffee parameter
    def update_coffee(self, coffee):
        if coffee is not None:
            global n_of_coffee
            n_of_coffee = coffee
            self.coffee_display = ttk.Label(self, text=n_of_coffee, font=("Delight Coffee", 25), background="#fcfee4")
            self.coffee_display.place(x=130, y=25)

    # the gif with name study.gif is animated
    def studygif(self):
        self.gif_frame = tk.Frame(self)
        self.gif_frame.place(x=170, y=162)
        gif = AnimatedGIF(self.gif_frame, 'study.gif')

    # the previous step is repeated with other gifs, however these have a duration
    def sleeping(self):
        self.gif_frame4 = tk.Frame(self)
        self.gif_frame4.place(x=190, y=170)
        self.netflixgif = AnimatedGIF(self.gif_frame4, "sleeping.gif", 2000)

    def knitting(self):
        self.gif_frame5 = tk.Frame(self)
        self.gif_frame5.place(x=190, y=170)
        self.netflixgif = AnimatedGIF(self.gif_frame5, "knitting.gif", 2000)

    def watermelon(self):
        self.gif_frame1 = tk.Frame(self)
        self.gif_frame1.place(x=186, y=162)
        self.watermelongif = AnimatedGIF(self.gif_frame1, "watermelon.gif", 2000)

    def popcorn(self):
        self.gif_frame2 = tk.Frame(self)
        self.gif_frame2.place(x=180, y=180)
        self.popcorngif = AnimatedGIF(self.gif_frame2, "popcorn.gif", 2000)

    def noodles(self):
        self.gif_frame3 = tk.Frame(self)
        self.gif_frame3.place(x=180, y=165)
        self.noodlesgif = AnimatedGIF(self.gif_frame3, "noodles.gif", 2000)

    def gym(self):
        self.gif_frame1 = tk.Frame(self)
        self.gif_frame1.place(x=186, y=162)
        self.gymgif = AnimatedGIF(self.gif_frame1, "gym.gif", 2000)

    #sets up button in homepage
    def buttons(self):
        self.springbut = PhotoImage(file="spring.png")
        self.arcadebut = tk.Button(self, image=self.springbut, bg="#e7d6b9", highlightthickness=0, relief="flat", command=SudokuGameWindow)
        self.arcadebut.place(x=1050, y=150)
        self.summerbut = PhotoImage(file="summer.png")
        self.calendarbut = tk.Button(self, image=self.summerbut, bg="#e7d6b9", highlightthickness=0, relief="flat",
                                     command=self.calendarscreen)
        self.calendarbut.place(x=1050, y=280)
        self.autumnbut = PhotoImage(file="autumn.png")
        self.agendabut = tk.Button(self, image=self.autumnbut, bg="#e7d6b9", highlightthickness=0, relief="flat",
                                   command=self.agendascreen)
        self.agendabut.place(x=1050, y=410)
        self.winterbut = PhotoImage(file="winter.png")
        self.logoutbut = tk.Button(self, image=self.winterbut, bg="#e7d6b9", highlightthickness=0, relief="flat", command=self.open_sudoku_game_window)
        self.logoutbut.place(x=1050, y=540)
        self.login_text = ttk.Label(self, text="What would you like to do?", font=("Vanilla Caramel", 30),
                                    background="#c8bfe7")
        self.login_text.place(x=1040, y=30)

    #opens sudoku
    def open_sudoku_game_window(self):
        new_window = tk.Toplevel()
        SudokuGameWindow()

    #chocolate bar button is set up
    def feedbutton(self):
        self.chocolatebar = PhotoImage(file="chocalatebar.png")
        self.feedbut = tk.Button(self, image=self.chocolatebar, bg="#fcfee4", highlightthickness=0, relief="flat",
                                 command=self.feed_animation)
        self.feedbut.place(x=835, y=445)

    #game button is set up
    def randombut(self):
        self.gamepad = PhotoImage(file="gamepad.png")
        self.gamepadbut = tk.Button(self, image=self.gamepad, highlightthickness=0, relief="flat",
                                    command=self.knitting)
        self.gamepadbut.place(x=835, y=575)

    #animation is filtered
    def feed_animation(self):
        global n_of_beans
        # n_of_beans is originally a tuple, so i had to change it to list
        n_of_beans_list = list(n_of_beans)
        # if n of beans is zero, no animation will start and a messagebox would appear
        if n_of_beans_list[0] == 0:
            messagebox.showerror("Error", "Insufficient Number of Beans")
        else:
            #otherwise, the levl of the user is checked. According to the level, a different animation will run
            n_level = list(level)
            if n_level[0] == 1:
                n_of_beans_list[0] -= 1
                db.reduce_bean(id_users)
                self.watermelon()
            elif n_level[0] == 2:
                n_of_beans_list[0] -= 1
                db.reduce_bean(id_users)
                self.noodles()
            elif n_level[0] == 3:
                n_of_beans_list[0] -= 1
                db.reduce_bean(id_users)
                self.popcorn()
        n_of_beans = tuple(n_of_beans_list)
        #the n_of_beans is updated with the new value

    #this has the same structure as the feed_animation
    def leisure_animation(self):
        global n_of_beans
        n_of_beans_list = list(n_of_beans)
        if n_of_beans_list[0] <= 0:
            messagebox.showerror("Error", "Insufficient Number of Beans")
        else:
            n_level = list(level)
            if n_level[0] == 1:
                n_of_beans_list[0] -= 1
                db.reduce_bean(id_users)
                self.gym()
            elif n_level[0] == 2:
                n_of_beans_list[0] -= 1
                db.reduce_bean(id_users)
                self.sleeping()
            elif n_level[0] == 3:
                n_of_beans_list[0] -= 1
                db.reduce_bean(id_users)
                self.knitting()
        n_of_beans = tuple(n_of_beans_list)


    def calendarscreen(self):
        self.container.show_frame(CalendarFrame.__name__)

    def agendascreen(self):
        self.container.show_frame(AgendaFrame.__name__)


class CalendarFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.mindate = datetime.date(2000, 1, 1)
        self.maxdate = datetime.date(2050, 12, 30)
        self.current_date = datetime.date.today()
        self.container = container
        #creates calendar object
        self.calendar = Calendar(self,
                                 style="SwitchButton",
                                 mindate=self.mindate,
                                 maxdate=self.maxdate,
                                 showweeknumbers=False,
                                 showothermonthdays=False,
                                 foreground="white",
                                 normalbackground="#d5c5d0",
                                 weekendbackground="#745d75",
                                 selectbackground="#614257",
                                 background="#614257",
                                 bordercolor="#614257",
                                 headersbackground="#d5c5d0",
                                 borderwidthint=0)

        self.calendar.pack(fill="both", expand=True)
        self.calendar.config(font=("Delight Coffee", 16))
        self.addlogbut()
        self.arrow_button()
        self.back_arrow()

    def back_arrow(self):
        self.back_image = PhotoImage(file="back.png")
        self.back = tk.Button(self, image=self.back_image, relief="flat", highlightthickness=0, bg="#614257",
                              command=self.back_to_login)
        self.back.place(x=1205, y=1)

    def back_to_login(self):
        self.container.show_frame(Homepage.__name__, beans_retrieved, coffee_retrieved)

    def arrow_button(self):
        self.arrow_image = PhotoImage(file="arrow.png")
        self.arrow_but = tk.Button(self, image=self.arrow_image, bg="#d5c5d0", highlightthickness=0,
                                   relief="flat", command=self.display_log)
        self.arrow_but.place(x=230, y=2)

    def display_log(self):
        # events, tasks, and activities are retrieved from database
        self.events = db.get_events(id_users, self.mindate, self.maxdate)
        self.tasks = db.get_tasks(id_users, self.mindate, self.maxdate)
        self.activity = db.get_activity(id_users, self.mindate, self.maxdate)
        current_date = datetime.date.today()
        #level is retrieved
        self.level=db.level_check(id_users)
        # corresponding to the level, a message would appear informing the user of the level
        if self.level == 1:
            messagebox.showinfo("Current Level", "You are currently in level 1")
        elif self.level == 2:
            messagebox.showinfo("Current Level", "You are currently in level 2")
        elif self.level == 3:
            messagebox.showinfo("Current Level", "You are currently in level 3")
        for event in self.events:
            start_date = event['start_date']
            end_date = event['end_date']
            rewarded = event["rewarded"]
            title = event['title']
            #if end date is before of the current day and it has not been already rewarded
            if end_date < current_date and rewarded == False:
                # coffee and bean count is incremented of one
                db.update_reward(id_users)
                # rewarded is changed to true
                db.event_achieved(id_users, title, start_date, end_date)
                #message box showing how the user was rewarded
                messagebox.showinfo("Success", "Reward Updated")
                #if start date is equal to end date, the event is created in thecalendar with the start day
            if start_date == end_date:
                tag_name = 'event'
                self.calendar.calevent_create(start_date, title, tag_name)
                self.calendar.tag_config(tag_name, background='#260a18')
            else:
                #if they are not equal:
                #counts number of days from first day to end date
                num_days = (end_date - start_date).days
                tag_name = 'event'
                self.calendar.calevent_create(start_date, title, tag_name)
                self.calendar.tag_config(tag_name, background='#260a18')
                #number of days is used in loop, to add event in those days in the calendar
                for day in range(0, num_days + 1):
                    #creates new date for day after
                    date = start_date + datetime.timedelta(days=day)
                    self.calendar.calevent_create(date, title, tag_name)
                    self.calendar.tag_config(tag_name, background='#260a18')
        #process repeated for tasks and activity
        for task in self.tasks:
            start_date = task['start_date']
            end_date = task['end_date']
            rewarded = task["rewarded"]
            title = task['title']
            if end_date < current_date and rewarded == False:
                db.update_reward(id_users)
                db.task_achieved(id_users, title, start_date, end_date)
                messagebox.showinfo("Success", "Reward Updated")
            if start_date == end_date:
                tag_name = 'task'
                self.calendar.calevent_create(start_date, title, tag_name)
                self.calendar.tag_config(tag_name, background='#423e40')
            else:
                num_days = (end_date - start_date).days
                tag_name = 'task'
                self.calendar.calevent_create(start_date, title, tag_name)
                self.calendar.tag_config(tag_name, background='#423e40')
                for day in range(0, num_days + 1):
                    date = start_date + datetime.timedelta(days=day)
                    self.calendar.calevent_create(date, title, tag_name)
                    self.calendar.tag_config(tag_name, background='#423e40')

        for activity in self.activity:
            start_date = activity['start_date']
            end_date = activity['end_date']
            rewarded = activity["rewarded"]
            title = activity['title']
            if end_date < current_date and rewarded == 0:
                db.update_reward(id_users)
                db.activity_achieved(id_users, title, start_date, end_date)
                messagebox.showinfo("Success", "Reward Updated")
            if start_date == end_date:
                title = activity['title']
                tag_name = 'activity'
                self.calendar.calevent_create(start_date, title, tag_name)
                self.calendar.tag_config(tag_name, background='#b66fd6')
            else:
                num_days = (end_date - start_date).days
                title = activity['title']
                tag_name = 'activity'
                self.calendar.calevent_create(start_date, title, tag_name)
                self.calendar.tag_config(tag_name, background='#b66fd6')
                for day in range(0, num_days + 1):
                    date = start_date + datetime.timedelta(days=day)
                    self.calendar.calevent_create(date, title, tag_name)
                    self.calendar.tag_config(tag_name, background='#b66fd6')

    def addlogbut(self):
        self.addlogbutton = tk.Button(self,
                                      bg="#614257",
                                      highlightthickness=0,
                                      relief="flat",
                                      text="Add Log",
                                      font=("Delight Coffee", 12),
                                      command=log_window)
        self.addlogbutton.place(x=1250, y=1)


class log_window(Toplevel):
    #style not created
    style_created = False

    def __init__(self):
        super().__init__()
        self.title("Add Log")
        self.geometry("400x400")
        # background
        self.logbg = PhotoImage(file="logbg.png")
        self.bg = ttk.Label(self, image=self.logbg)
        self.bg.grid(row=0, column=0)
        #style is not created unless it was not already created
        if not log_window.style_created:
            log_window.style_created = True
            self.style = ttk.Style(self)
            self.style.theme_create('customstyle', parent='alt', settings={
                "TCombobox": {
                    "configure": {"foreground": "black", "background": "#d5c5d0", "font": ("Arial", 15)},
                    "selectbackground": "#d5c5d0",
                    "fieldbackground": "#d5c5d0",
                    "arrowcolor": "black",
                    "relief": "flat"}})
            self.style.theme_use('customstyle')
        self.mindate = datetime.date(2000, 1, 1)
        self.maxdate = datetime.date(2050, 12, 30)
        self.select_box()
        self.event_task_activity_layout()

    # select box
    def select_box(self):
        option = ["Event", "Task", "Activity"]
        self.select_text = ttk.Label(self, text="Select                          :",
                                     font=("Delight Coffee", 15),
                                     background="#d5c5d0")
        self.logoption = ttk.Combobox(self,
                                      values=option,
                                      style="customstyle.TCombobox",
                                      width=20)
        self.select_text.place(x=15, y=10)
        self.logoption.place(x=100, y=15)

    #all widgets are initiated
    def event_task_activity_layout(self):
        self.title_widget()
        self.description_widget()
        self.date_widget()
        self.time_widget()
        self.add_button()
        self.category_widget()

    def add_button(self):
        self.add_image = PhotoImage(file="add.png")
        self.addevent = tk.Button(self, image=self.add_image, bg="#d5c5d0", highlightthickness=0,
                                  relief="flat", command=self.add_event_task_activity)
        self.addevent.place(x=175, y=320)

    def title_widget(self):
        self.title_text = ttk.Label(self, text="Title:", font=("Delight Coffee", 15), background="#d5c5d0")
        self.title_text.place(x=20, y=100)
        self.title_line = tk.Canvas(self, width=200, height=2, bg="#000000", highlightthickness=0)
        self.title_line.place(x=110, y=130)
        self.title_entry = tk.Entry(self, width=20, highlightthickness=0, bg="#d5c5d0", relief=FLAT,
                                    font=(12))
        self.title_entry.place(x=110, y=100)

    def description_widget(self):
        self.description_text = ttk.Label(self, text="Description:", font=("Delight Coffee", 10),
                                          background="#d5c5d0")
        self.description_text.place(x=20, y=160)
        self.description_box = tk.Text(self, width=25, height=3, highlightthickness=0)
        self.description_box.place(x=110, y=160)

    def date_widget(self):
        self.start_date_text = ttk.Label(self, text="Start Date:", font=("Delight Coffee", 10),
                                         background="#d5c5d0")
        self.start_date_text.place(x=20, y=230)
        self.start_date_box = DateEntry(self, width=12,
                                        mindate=self.mindate,
                                        maxdate=self.maxdate,
                                        showweeknumbers=False,
                                        showothermonthdays=False,
                                        foreground="white",
                                        normalbackground="#d5c5d0",
                                        weekendbackground="#745d75",
                                        selectbackground="#614257",
                                        background="#614257",
                                        bordercolor="#614257",
                                        headersbackground="#d5c5d0",
                                        borderwidthint=0,
                                        date_pattern='dd/mm/yyyy')
        self.start_date_box.place(x=110, y=230)
        self.end_date_text = ttk.Label(self, text="End Date:", font=("Delight Coffee", 10),
                                       background="#d5c5d0")
        self.end_date_text.place(x=200, y=230)
        self.end_date_box = DateEntry(self, width=12,
                                      mindate=self.mindate,
                                      maxdate=self.maxdate,
                                      showweeknumbers=False,
                                      showothermonthdays=False,
                                      foreground="white",
                                      normalbackground="#d5c5d0",
                                      weekendbackground="#745d75",
                                      selectbackground="#614257",
                                      background="#614257",
                                      bordercolor="#614257",
                                      headersbackground="#d5c5d0",
                                      borderwidthint=0,
                                      date_pattern='dd/mm/yyyy')
        self.end_date_box.place(x=270, y=230)

    def time_widget(self):
        self.start_hour_var = tk.StringVar()
        self.start_hour_var.set('00')
        self.start_minute_var = tk.StringVar()
        self.start_minute_var.set('00')
        self.end_hour_var = tk.StringVar()
        self.end_hour_var.set('00')
        self.end_minute_var = tk.StringVar()
        self.end_minute_var.set('00')
        # start time
        self.starthour_box = tk.Spinbox(self, from_=0, to=23, width=2, textvariable=self.start_hour_var)
        self.starthour_box.place(x=110, y=250)
        self.start_time = ttk.Label(self, text=":", font=("Delight Coffee", 10),
                                    background="#d5c5d0")
        self.start_time.place(x=140, y=250)
        self.startminute_box = tk.Spinbox(self, from_=0, to=59, width=2, textvariable=self.start_minute_var)
        self.startminute_box.place(x=150, y=250)
        # end time
        self.endhour_box = tk.Spinbox(self, from_=0, to=23, width=2, textvariable=self.end_hour_var)
        self.endhour_box.place(x=270, y=250)
        self.end_time = ttk.Label(self, text=":", font=("Delight Coffee", 10),
                                  background="#d5c5d0")
        self.end_time.place(x=300, y=250)
        self.endminute_box = tk.Spinbox(self, from_=0, to=59, width=2, textvariable=self.end_minute_var)
        self.endminute_box.place(x=310, y=250)

    def category_widget(self):
        self.category_text = ttk.Label(self, text="Category:", font=("Delight Coffee", 10), background="#d5c5d0")
        self.category_text.place(x=20, y=280)
        self.category_line = tk.Canvas(self, width=200, height=2, bg="#000000", highlightthickness=0)
        self.category_line.place(x=110, y=305)
        self.category_entry = tk.Entry(self, width=20, highlightthickness=0, bg="#d5c5d0", relief=FLAT, font=(12))
        self.category_entry.place(x=110, y=275)

    def add_event_task_activity(self):
        # Validate inputs
        if not self.title_entry.get():
            # Show an error message if the title is empty
            messagebox.showerror("Error", "Title cannot be empty")
            return
        try:
            # Convert input values into appropriate data types
            start_time = datetime.time(
                hour=int(self.start_hour_var.get()),
                minute=int(self.start_minute_var.get())
            )
            end_time = datetime.time(
                hour=int(self.end_hour_var.get()),
                minute=int(self.end_minute_var.get())
            )
            start_date = datetime.datetime.strptime(self.start_date_box.get(), '%d/%m/%Y').date()
            end_date = datetime.datetime.strptime(self.end_date_box.get(), '%d/%m/%Y').date()
        except ValueError:
            # Show an error message if any of the input values are invalid
            messagebox.showerror("Error", "Invalid date or time")
            return

        if self.logoption.get() == "Event":
            try:
                #adds event to database
                db.add_event(
                    id_users,
                    self.title_entry.get(),
                    self.description_box.get("1.0", tk.END),
                    start_date,
                    start_time,
                    end_date,
                    end_time,
                    self.category_entry.get()
                )
                #informs the user the event was added
                messagebox.showinfo("Success", "Event added")
                #window closes
                self.destroy()
            except Exception as e:
                #if it fails, this message pops up
                messagebox.showerror("Error", "Unable to add event to database")
                return
        if not self.logoption.get():
            #if events, activity and tasks were not selected, an error pop up would appear
            messagebox.showerror("Error", "Nothing was selected")
            return
        if self.logoption.get() == "Task":
            #same process is repeated with tasks
            try:
                db.add_task(
                    id_users,
                    self.title_entry.get(),
                    self.description_box.get("1.0", tk.END),
                    start_date,
                    start_time,
                    end_date,
                    end_time,
                    self.category_entry.get()
                )
                messagebox.showinfo("Success", "Task added")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", "Unable to add event to database")
                return
        #same process is repeated with activity
        if self.logoption.get() == "Activity":
            try:
                db.add_activity(
                    id_users,
                    self.title_entry.get(),
                    self.description_box.get("1.0", tk.END),
                    start_date,
                    start_time,
                    end_date,
                    end_time,
                    self.category_entry.get()
                )
                messagebox.showinfo("Success", "Activity added")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", "Unable to add event to database")
                return


class AgendaFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.container = container
        #background
        self.bg = PhotoImage(file="bgagenda.png")
        self.bglabel = ttk.Label(self, image=self.bg)
        self.bglabel.place(x=0, y=0)
        self.mindate = datetime.date(2000, 1, 1)
        self.maxdate = datetime.date(2050, 12, 30)
        #creates listbox
        self.log_listbox = tk.Listbox(self, height=10, bg='#D1C8C0', font=('Palatino Linotype', 15),
                                      highlightthickness=4, highlightcolor="#000000", highlightbackground="#000000",
                                      borderwidth=2)

        self.log_listbox.place(x=50, y=120, width=1400, height=550)
        #creates scrollbar for listbox
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.log_listbox.yview)
        scrollbar.place(x=1450, y=120, height=550)
        self.log_listbox.config(yscrollcommand=scrollbar.set)
        self.agenda_arrow = PhotoImage(file="agendaarrow.png")
        self.layout()

    #displays number of logs uncompleted
    def reward_message(self):
        self.rewards_missing = db.count_rewarded(self.logoption.get(), id_users)
        count = self.rewards_missing[0][0]  # access the count value and remove the brackets
        self.message = "You have " + str(count) + " uncompleted logs"
        self.message_label = ttk.Label(self, text=self.message)
        self.message_label.place(x=1200, y=40)

    #sets up layout of widgets
    def layout(self):
        self.back_arrow()
        self.category_widget()
        self.select_widget()
        self.action_button = tk.Button(self, image=self.agenda_arrow, bg="#D1C8C0", highlightthickness=0,
                                       relief="flat", command=self.display_log)
        self.action_button.place(x=750, y=80)
        self.edit_widget()
        self.addlogbut()



    def addlogbut(self):
        self.addlogbutton = tk.Button(self,
                                      bg="#D1C8C0",
                                      highlightthickness=0,
                                      relief="flat",
                                      text="Add Log",
                                      font=("Delight Coffee", 12),
                                      command=log_window)
        self.addlogbutton.place(x=1320, y=80)

    def edit_widget(self):
        self.add = PhotoImage(file="add.png")
        self.add_but = tk.Button(self, image=self.add, bg="#D1C8C0", highlightthickness=0,
                                 relief="flat", command=self.edit)
        self.add_but.place(x=1420, y=65)

    def back_arrow(self):
        self.back_image = PhotoImage(file="back.png")
        self.back = tk.Button(self, image=self.back_image, relief="flat", highlightthickness=0, bg="#D1C8C0",
                              command=self.back_to_login)
        self.back.place(x=1, y=1)

    def select_widget(self):
        option = ["events", "tasks", "activity"]
        self.select_text = ttk.Label(self, text="Select:",
                                     font=("Delight Coffee", 15),
                                     background="#D1C8C0")
        self.logoption = ttk.Combobox(self,
                                      values=option,
                                      width=20)
        self.select_text.place(x=500, y=80)
        self.logoption.place(x=600, y=85)

    def back_to_login(self):
        self.container.show_frame(Homepage.__name__, beans_retrieved, coffee_retrieved)

    def category_widget(self):
        self.category_text = ttk.Label(self, text="Category:", font=("Delight Coffee", 12), background="#D1C8C0")
        self.category_text.place(x=20, y=80)
        self.category_line = tk.Canvas(self, width=200, height=2, bg="#000000", highlightthickness=0)
        self.category_line.place(x=130, y=110)
        self.category_entry = tk.Entry(self, width=20, highlightthickness=0, bg="#D1C8C0", relief=FLAT, font=(12))
        self.category_entry.place(x=130, y=80)

    def display_log(self):
        if self.logoption.get() == "events":
            self.display_events()
            self.reward_message()
        elif self.logoption.get() == "tasks":
            self.display_tasks()
            self.reward_message()
        elif self.logoption.get() == "activity":
            self.display_activity()
            self.reward_message()
        else:
            messagebox.showerror("Error", "Nothing was selected")

    def display_events(self):
        # Get category from input
        category = self.category_entry.get().strip()

        # Get events based on category and date range
        if len(category) == 0:
            events = db.get_events(id_users, self.mindate, self.maxdate)
        else:
            events = db.get_customised_events(id_users, self.mindate, self.maxdate, category)

        # Display events in GUI listbox
        if events:
            # Clear existing entries in listbox
            self.log_listbox.delete(0, tk.END)

            # Iterate through events and insert each one into listbox
            for event in events:
                title = event['title']
                start_date = event['start_date']
                end_date = event['end_date']
                category = event["category"]
                description = event["description"]
                item_text = f"{title}|{start_date}|{end_date}|{category}|{description}"
                self.log_listbox.insert(tk.END, item_text)
        else:
            # Display error message if no events found
            messagebox.showerror("Error", "No events found.")

    #the process is repeated through display_tasks and display_activity

    def display_tasks(self):
        category = self.category_entry.get().strip()
        if len(category) == 0:
            tasks = db.get_tasks(id_users, self.mindate, self.maxdate)
        else:
            tasks = db.get_customised_tasks(id_users, self.mindate, self.maxdate, category)
        if tasks:
            self.log_listbox.delete(0, tk.END)
            for task in tasks:
                title = task['title']
                start_date = task['start_date']
                end_date = task['end_date']
                category = task["category"]
                description = task["description"]
                item_text = f"{title}|{start_date}|{end_date}|{category}|{description}"
                self.log_listbox.insert(tk.END, item_text)
        else:
            messagebox.showerror("Error", "No task found.")

    def display_activity(self):
        category = self.category_entry.get().strip()
        if len(category) == 0:
            activities = db.get_activity(id_users, self.mindate, self.maxdate)
        else:
            activities = db.get_customised_activities(id_users, self.mindate, self.maxdate, category)
        if activities:
            self.log_listbox.delete(0, tk.END)
            for activity in activities:
                title = activity['title']
                start_date = activity['start_date']
                end_date = activity['end_date']
                category = activity["category"]
                description = activity["description"]
                item_text = f"{title}|{start_date}|{end_date}|{category}|{description}"
                self.log_listbox.insert(tk.END, item_text)
        else:
            messagebox.showerror("Error", "No activity found.")



    def edit(self):
        # Assume the event to be edited is selected in the events_listbox widget, otherwise an error message box appears
        selected_event = self.log_listbox.get(tk.ACTIVE)
        if selected_event:
            # Parse the selected event to extract the start date, end date, and current category
            event_parts = selected_event.split("|")
            start_date = event_parts[1]
            end_date = event_parts[2]
            current_category = event_parts[3]

            # Prompt the user for the new category
            new_category = simpledialog.askstring("Change Category",
                                                  f"Enter new category for event from {start_date} to {end_date}:",
                                                  initialvalue=current_category)

            # Call the change_category method to update the category in the database
            db.change_category(self.logoption.get(), id_users, start_date, end_date, new_category)

class SudokuGameWindow(Toplevel):
    def __init__(self):
        super().__init__()
        self.geometry("600x600")
        self.title("Sudoku Game")
        self.resizable(False,False)
        # background
        self.bg=PhotoImage(file="sudokubg.png")
        self.bglabel=ttk.Label(self, image=self.bg)
        self.bglabel.grid()
        #set up buttons
        self.check_button = tk.Button(self, text="Check", command=self.check_answers)

        self.start_image=PhotoImage(file="start.png")
        self.new_button = tk.Button(self, image=self.start_image, command=self.new_game, bg="#94E6C9", highlightthickness=0,
                                 relief="flat" )
        self.new_button.place(x=500, y=20)

        self.tick_image=PhotoImage(file="greentick.png")
        self.tick_button = tk.Button(self, image=self.tick_image, bg="#94E6C9", highlightthickness=0,
                                 relief="flat", state=tk.DISABLED, command=self.check_answers)
        self.tick_button.place(x=520, y=520)
        self.grid = [[0 for i in range(9)] for j in range(9)]
        self.sudoku_text = ttk.Label(self, text="Welcome to Sudoku!!", font=("Vanilla Caramel", 30),
                                    background="#94E6C9")
        self.sudoku_text.place(x=30, y=30)

        self.n_of_coffee = coffee_retrieved

    def animatedGIF(self):
        self.gif_frame = tk.Frame(self)
        self.gif_frame.place(x=200, y=180)
        self.gogif = AnimatedGIF(self.gif_frame, "go.gif", 1000)


    def new_game(self):
        # n of coffee is a tuple so i had to change it to a list
        n_of_coffee_list=list(self.n_of_coffee)
        # if n of coffee is zero, no animation will start and pop up will inform the user of the error
        if n_of_coffee_list[0] == 0:
            messagebox.showerror("Error", "Insufficient Number of Coffee")
            self.destroy()
        else:
            # otherwise, the coffee number is reduced in the database and local variable
            n_of_coffee_list[0] -= 1
            db.reduce_coffee(id_users)
        self.n_of_coffee = tuple(n_of_coffee_list)
        global coffee_retrieved
        coffee_retrieved= self.n_of_coffee
        #activates the check button
        self.tick_button.config(state=tk.NORMAL)
        #creates the grid
        self.create_gridIU()
        self.animatedGIF()
        # Generate a new Sudoku puzzle
        self.fillGrid()
        # saves the solved grid in a new list
        global solved_grid
        solved_grid = [[self.grid[i][j] for j in range(9)] for i in range(9)]
        self.remove_numbers()
        puzzle = self.grid


        # Populate the cells with the initial values of the puzzle
        for i in range(9):
            for j in range(9):
                if puzzle[i][j] != 0:
                    self.cells[i][j].delete(0, tk.END)
                    self.cells[i][j].insert(0, str(puzzle[i][j]))
                    self.cells[i][j].config(state=tk.DISABLED, disabledbackground='#f0f0f0')


    #creates grid
    def create_gridIU(self):
        self.frame = tk.Frame(self, width=500, height=500)
        self.frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.cells = []
        for i in range(9):
            row = []
            for j in range(9):
                cell = tk.Entry(self.frame, width=2, font=('Arial', 16), justify='center')
                cell.grid(row=i, column=j, ipady=10, ipadx=10)
                cell.bind('<Button-1>', lambda event, cell=cell: self.select_number(event, cell))
                row.append(cell)
            self.cells.append(row)

    def select_number(self, event, cell):
        if cell.get() != '':  # Check if cell already has a value
            return  # If it does, do nothing

        # Create a popup menu with the numbers 1 to 9
        popup_menu = tk.Menu(self, tearoff=0)
        for i in range(1, 10):
            popup_menu.add_command(label=str(i), command=lambda value=i, cell=cell: self.set_cell_value(value, cell))
        popup_menu.post(event.x_root, event.y_root)

    def set_cell_value(self, value, cell):
        # Set the value of the selected cell to the selected number
        cell.delete(0, tk.END)
        cell.insert(0, str(value))


    # A backtracking/recursive function to check all possible combinations of numbers until a solution is found
    def fillGrid(self):
        number_list=[1,2,3,4,5,6,7,8,9]
        random.shuffle(number_list)
        # Find next empty cell
        for i in range(0, 81):
            row = i // 9
            col = i % 9
            if self.grid[row][col] == 0:
                for value in number_list:
                    # Check that this value has not already been used on this row
                    if not (value in self.grid[row]):
                        # Check that this value has not already been used on this column
                        if not value in (
                                self.grid[0][col], self.grid[1][col], self.grid[2][col], self.grid[3][col],
                                self.grid[4][col], self.grid[5][col],
                                self.grid[6][col], self.grid[7][col], self.grid[8][col]):
                            # Identify which of the 9 squares we are working on
                            square = []
                            if row < 3:
                                if col < 3:
                                    square = [self.grid[i][0:3] for i in range(0, 3)]
                                elif col < 6:
                                    square = [self.grid[i][3:6] for i in range(0, 3)]
                                else:
                                    square = [self.grid[i][6:9] for i in range(0, 3)]
                            elif row < 6:
                                if col < 3:
                                    square = [self.grid[i][0:3] for i in range(3, 6)]
                                elif col < 6:
                                    square = [self.grid[i][3:6] for i in range(3, 6)]
                                else:
                                    square = [self.grid[i][6:9] for i in range(3, 6)]
                            else:
                                if col < 3:
                                    square = [self.grid[i][0:3] for i in range(6, 9)]
                                elif col < 6:
                                    square = [self.grid[i][3:6] for i in range(6, 9)]
                                else:
                                    square = [self.grid[i][6:9] for i in range(6, 9)]
                            # Check that this value has not already been used on this 3x3 square
                            if not value in (square[0] + square[1] + square[2]):
                                self.grid[row][col] = value
                                if self.is_grid_full(self.grid):
                                    return True  # Solution found
                                else:
                                    if self.fillGrid():
                                        return True  # Solution found
                break
        else:
            return True  # Solution found (no empty cells left)
        self.grid[row][col] = 0  # Reset the cell
        # No valid value found, backtrack to previous

    def is_grid_full(self, grid):
        for row in range(0,9):
            for col in range(0,9):
                if grid[row][col]==0:
                    return False
        return True

    def solveGrid(self, grid):
        global counter
        # Find next empty cell
        for i in range(0, 81):
            row = i // 9
            col = i % 9
            if grid[row][col] == 0:
                for value in range(1, 10):
                    # Check that this value has not already been used on this row
                    if not (value in grid[row]):
                        # Check that this value has not already been used on this column
                        if not value in (
                        grid[0][col], grid[1][col], grid[2][col], grid[3][col], grid[4][col], grid[5][col],
                        grid[6][col], grid[7][col], grid[8][col]):
                            # Identify which of the 9 squares we are working on
                            square = []
                            if row < 3:
                                if col < 3:
                                    square = [grid[i][0:3] for i in range(0, 3)]
                                elif col < 6:
                                    square = [grid[i][3:6] for i in range(0, 3)]
                                else:
                                    square = [grid[i][6:9] for i in range(0, 3)]
                            elif row < 6:
                                if col < 3:
                                    square = [grid[i][0:3] for i in range(3, 6)]
                                elif col < 6:
                                    square = [grid[i][3:6] for i in range(3, 6)]
                                else:
                                    square = [grid[i][6:9] for i in range(3, 6)]
                            else:
                                if col < 3:
                                    square = [grid[i][0:3] for i in range(6, 9)]
                                elif col < 6:
                                    square = [grid[i][3:6] for i in range(6, 9)]
                                else:
                                    square = [grid[i][6:9] for i in range(6, 9)]
                            # Check that this value has not already been used on this 3x3 square
                            if not value in (square[0] + square[1] + square[2]):
                                grid[row][col] = value
                                if self.is_grid_full(grid):
                                    counter += 1
                                    break
                                else:
                                    if self.solveGrid(grid):
                                        return True
                grid[row][col] = 0
                return False
        return True

    def remove_numbers(self):
        global counter
        self.level=db.level_check(id_users)
        attempts=1
        if self.level == 1:
            attempts=1
        elif self.level == 2:
            attempts=3
        elif self.level == 3:
            attempts=5
        counter = 1
        while attempts > 0:
            # Select a random cell that is not already empty
            row = randint(0, 8)
            col = randint(0, 8)
            while self.grid[row][col] == 0:
                row = randint(0, 8)
                col = randint(0, 8)
            # Remember its cell value in case we need to put it back
            backup = self.grid[row][col]
            self.grid[row][col] = 0

            # Take a full copy of the grid
            copyGrid = []
            for r in range(0, 9):
                copyGrid.append([])
                for c in range(0, 9):
                    copyGrid[r].append(self.grid[r][c])

            # Count the number of solutions that this grid has (using a backtracking approach implemented in the solveGrid() function)
            counter = 0
            self.solveGrid(copyGrid)
            # If the number of solution is different from 1 then we need to cancel the change by putting the value we took away back in the grid
            if counter != 1:
                self.grid[row][col] = backup
                attempts -= 1

    def check_answers(self):
        #compares the solved grid and input from users
        for i in range(9):
            for j in range(9):
                cell_value = self.cells[i][j].get()
                grid_value = solved_grid[i][j]
                if cell_value != str(grid_value):
                    #in case they are not equal, gives error
                    messagebox.showerror("Error","You did something wrong")
                    return
        #if no error was given, congratulation ,essage appears
        messagebox.showinfo("Congratulations!", "You got everything right")




if __name__ == "__main__":
    app = App()
    app.mainloop()

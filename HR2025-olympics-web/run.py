from app import create_app, db

# Create an instance of the app
app = create_app()

# Initialize the database
with app.app_context():
    db.create_all()  # This will create the tables in the database if they don't exist



# To call this function and add data to the database


if __name__ == "__main__":
    app.run(debug=True)

#Author: Tyce Xiong
#Uses Flask to connect routing.py to html
#see README.md for credits

#imports necessary routing and files
from flask import Flask, jsonify, request, render_template
import routing

#creates app
app = Flask(__name__)

#serve html form on open
@app.route('/')
def home():
    return render_template('index.html')

#returns json string as dictionary
@app.route('/get-route', methods=['GET'])
def get_route():
    # Grab parameters from the frontend request URL query params
    street = request.args.get('street')
    city = request.args.get('city')
    state = request.args.get('state')
    zip_code = request.args.get('zip')
    distance = float(request.args.get('distance', 0))
    
    # Call your method
    json_string = routing.route_as_json(street, city, state, zip_code, distance)
    
    # Convert the JSON string back to a Python dict so Flask can serialize it cleanly, 
    # or return json_string directly with mimetype='application/json'
    return app.response_class(
        response=json_string,
        status=200,
        mimetype='application/json'
    )

#runs app
if __name__ == '__main__':
    app.run(debug=True)
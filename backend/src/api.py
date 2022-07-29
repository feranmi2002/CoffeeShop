import os
from flask import Flask, request, jsonify, abort, redirect, url_for
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth



def create_app():
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/*": {"origins": "*"}})

    db_drop_and_create_all()

    @app.route('/')
    def index():
        return redirect(url_for('get_drinks'))

    @app.route('/drinks', methods = ['GET'])
    def get_drinks():
        """ Get all drinks """
        drinks = Drink.query.all()
        formatted_drinks = [drink.short() for drink in drinks]
        return jsonify({
            'success':True,
            'drinks': formatted_drinks

        }), 200

   
    @app.route('/drinks-detail', methods = ['GET'])
    @requires_auth('get:drinks-detail')
    def get_drinks_detail(auth):
        """ Get drinks details """
        drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in drinks]
        return jsonify({
            'success': True,
            'drinks': formatted_drinks
        }), 200


    @app.route('/drinks', methods = ['POST'])
    @requires_auth('post:drinks')
    def post_drinks(auth):
        request_body = request.get_json()

        """ Get parameters"""
        if 'title' and 'recipe' not in request_body:
            abort(422)

        recipe = request_body['recipe']
        if isinstance(recipe, dict):
            recipe = [recipe]

        
        """ Add a new drink """
        try:
            title = request_body['title']
            
            recipe_json = json.dumps(recipe)

            drink = Drink(title = title, recipe = recipe_json)

            drink.insert()

            result = [drink.long()]
        except():
            abort(400)
        return jsonify({
                'success': True,
                'drinks':result
            }), 200


    @app.route('/drinks/<int:id>', methods = ['PATCH'])
    @requires_auth('patch:drinks')
    def updateDrink(auth, id):
        """ Get specified drink"""

        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink is None:
            """Drink does not exist in database """
            abort(404)

        request_body = request.get_json()
        
        try:
            title = request_body.get('title')
            recipe = request_body.get('recipe')
            
            """ Update the drink """
            if title:
                drink.title = title

            if recipe:
                drink.recipe = json.dumps(recipe)
            
            drink.update()
            result = [drink.long()]
        except():
            abort(400)
        return jsonify({
                'success':True,
                'drinks':result
            }), 200

 
    @app.route('/drinks/<int:id>', methods = ['DELETE'])
    @requires_auth('delete:drinks')
    def delete_drink(auth, id):
        """ Get specified drink """
        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink is None:
            """ Specified drink not found """
            return({
                'success': False,
                'drinks': 'Drink with ID {} does not exist'.format(id)
            }), 404
            
        try:
            """ Delete spsecified drink"""
            drink.delete()
           
        except():
            abort(500)

        return jsonify({
                'success':True,
                'drinks': id
            })

    """ Tests Auth0 Login """
    @app.route('/login-response', methods=['GET'])
    def auth0_result():
        return jsonify({
            'message': 'login successful'
        })
    
    """ Error Handlers"""

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422


    @app.errorhandler(404)
    def resourceNotFound(error):
            return jsonify({
                "success": False,
                "error": 404,
                "message": "Resource not found"
            }), 404

   
    @app.errorhandler(400)
    def authError(error):
            return jsonify({
                "success": False,
                "error": 400,
                "message": "Authentication error"
            }), 400
    

    @app.errorhandler(405)
    def methodNotAllowed(error):
            return jsonify({
                "sucess": False,
                "error": 405,
                "message": "Method not allowed"
            }), 405

    @app.errorhandler(AuthError)
    def auth_error(error):
        return jsonify({
            'success': False,
            'error': error.error,
            'message': error.status_code,
        }), error.status_code

    return app
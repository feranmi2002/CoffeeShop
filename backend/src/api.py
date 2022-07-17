import os
from flask import Flask, request, jsonify, abort
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

    @app.route('/drinks', methods = ['GET'])
    def get_drinks():
        """ Get all drinks """
        drinks = Drink.query.all()
        formatted_drinks = [drink.short() for drink in drinks]
        return jsonify({
            'success':True,
            'drinks': formatted_drinks
        })

   
    @app.route('/drinks-detail', methods = ['GET'])
    def get_drinks_detail():
        """ Get drinks details """
        drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in drinks]
        return jsonify({
            'success': True,
            'drinks': formatted_drinks
        })


    @app.route('/drinks', methods = ['POST'])
    def post_drinks():
        request_body = request.get_json()
        """ Add a new drink """
        drink = Drink(title = request_body.get('title'), recipe = request_body.get('recipe'))
        try:
            drink.insert()
            result = [drink.long()]
            return jsonify({
                'success': True,
                'drinks':result
            })
        except():
            abort(500)


    @app.route('/drinks/<int:id>', methods = ['PATCH'])
    def updateDrink(id):
        """ Get specified drink"""
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            """Drink does not exist in database """
            abort(404)
        request_body = request.get_json()
        drink.title = request_body.get('title')
        drink.recipe = request_body.get('recipe')
        try:
            """ Update the drink """
            drink.update()
            result = [drink.long()]
            return jsonify({
                'success':True,
                'drinks':result
            })
        except():
            abort(500)

 
    @app.route('/drinks/<int:id>', methods = ['DELETE'])
    def delete_drink(id):
        """ Get specified drink """
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            """ Specified drink not found """
            abort(404)
        try:
            """ Delete spsecified drink"""
            drink.delete()
            result = [drink.long()]
            return jsonify({
                'success':True,
                'drinks':result
            })
        except():
            abort(500)
    
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
                "sucess": False,
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

    return app
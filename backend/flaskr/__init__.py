import os
from select import select
from sre_constants import SUCCESS
from traceback import print_tb
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''
    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        try:
            data = {}
            for category in categories:
                data[category.id] = category.type

            if data == 0:
                abort(404)  # not found

            return jsonify({
                "success": True,
                "categories": data,
                "total_categories": len(categories)
            }), 200
        except:
            abort(422)

    '''
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.


    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''

    QUESTIONS_PER_PAGE = 10

    def paginate_question(request, selection):
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        formatted_question = [question.format() for question in selection]
        current_questions = formatted_question[start:end]
        return current_questions

    @app.route('/questions')
    def retrieve_questions():
        categories = Category.query.order_by(Category.id).all()

        data = {}
        for category in categories:
            data[category.id] = category.type

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_question(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "questions": current_questions,
            "categories": data,
            "total_questions": len(selection)
        })

    '''
        @TODO:
        Create an endpoint to DELETE question using a question ID.

        TEST: When you click the trash icon next to a question, the question will be removed.
        This removal will persist in the database and when you refresh the page.
    '''

    @app.route('/questions/<int:question_id>', methods=["DELETE"])
    def delete_question(question_id):

        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            print(question)
            if question is None:
                abort(404)

            question.delete()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_question(request, selection)

            return jsonify({
                "success": True,
                "questions": current_questions,
                "question deleted": question_id,
                "total_question": len(selection)

            })
        except:
            abort(404)

    '''
        @TODO:
        Create an endpoint to POST a new question,
        which will require the question and answer text,
        category, and difficulty score.
        
    '''

    @app.route('/questions', methods=['POST'])
    def add_question():

        body = request.get_json()

        question = body.get('question', None)
        answer = body.get('answer', None)
        difficulty = body.get('difficulty', None)
        category = body.get('category', None)

        try:
            question = Question(
                question=question, answer=answer, difficulty=difficulty, category=category)

            question.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_question(request, selection)

            return jsonify({
                "success": True,
                'questions': current_questions,
                'questions_id': question.id,


            })
        except:
            abort(422)

    ''' Create a POST endpoint to get questions based on a search term.
        It should return any questions for whom the search term
        is a substring of the question.
    '''

    @app.route('/questions/search', methods=['POST'])
    def search():

        body = request.get_json()
        try:
            search = body.get('searchTerm', None)

            selection = Question.query.order_by(
                Question.id).filter(Question.question.ilike(f'%{search}%')).all()

            searched_questions = paginate_question(request, selection)

            return jsonify({
                "success": True,
                "questions": searched_questions,
                "total_questions": len(selection)

            })
        except:
            abort(404)

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''

    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):

        try:
            category = Category.query.filter_by(
                id=id).one_or_none()
            # print(category)

            def find_question(id):
                global questions

                questions = Question.query.filter_by(
                    category=str(id)).all()

                formatted_question = []

                for question in questions:
                    formatted_question.append(question.format())

                return formatted_question

            return jsonify({
                'success': True,
                'questions': find_question(id),
                'total_questions': len(questions),
                'current_category': category.type
            })
        except:
            abort(422)
    '''
        # @TODO:
        # Create a POST endpoint to get questions to play the quiz.
        # This endpoint should take category and previous question parameters
        # and return a random questions within the given category,
        # if provided, and that is not one of the previous questions.
        # TEST: In the "Play" tab, after a user selects "All" or a category,
        # one question at a time is displayed, the user is allowed to answer
        # and shown whether they were correct or not.
        # '''
    @app.route('/quizzes', methods=['POST'])
    def get_random_questions():

        body = request.get_json()
        category = body.get('quiz_category', None)  # dict
        previous_question = body.get('previous_questions', None)  # list

        # for k in category.items():
        #     print(k)
        try:
            # for all category, type==click
            if category["type"] == "click":
                questions = Question.query.all()
                # print(questions)

            else:
                category_id = category.get("id")
                # print("this is id:", category_id)
                questions = Question.query.filter_by(
                    category=category_id).all()

            random_question_id = random.randrange(0, len(questions), 1)

            while random_question_id not in previous_question:
                selected_question = questions[random_question_id]

                return jsonify({
                    "success": True,
                    "question": selected_question.format()
                })
        except:
            abort(422)

    '''
            @TODO:
            Create error handlers for all expected errors
            including 404 and 422.
    '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(405)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    return app

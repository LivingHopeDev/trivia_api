import os
from select import select
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
            abort(422)

    '''
        @TODO:
        Create an endpoint to POST a new question,
        which will require the question and answer text,
        category, and difficulty score.

        AND

         Create a POST endpoint to get questions based on a search term.
        It should return any questions for whom the search term
        is a substring of the question.
    '''

    @app.route('/questions', methods=['POST'])
    def add_question():

        body = request.get_json()

        # curl -X POST -H "Content-Type: application/json" -d '{"search":"autobiography"}' http://127.0.0.1:5000/questions

        if (body.get('searchTerm', None)):

            search = body.get('searchTerm', None)

            selection = Question.query.order_by(
                Question.id).filter(Question.question.ilike(f'%{search}%')).all()

            # print(selection)
            # print(search)

            searched_questions = paginate_question(request, selection)

            if(len(selection) == 0):
                abort(404)

            return jsonify({
                "success": True,
                "questions": searched_questions,
                "total_questions": len(selection)

            })

        else:
            question = body.get('question', None)
            answer = body.get('answer', None)
            difficulty = body.get('difficulty', None)
            category = body.get('category', None)

            if(question == None) or (answer == None) or (difficulty == None) or (category == None):
                abort(422)

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
                    "categories": question.category,
                    'total_questions': len(selection)

                })
            except:
                abort(422)

    # '''
    # # @TODO:
    # # Create a GET endpoint to get questions based on category.
    # # TEST: In the "List" tab / main screen, clicking on one of the
    # # categories in the left column will cause only questions of that
    # # category to be shown.
    # # '''
    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):

        try:
            category = Category.query.filter_by(
                id=id).one_or_none()
            # print(category)

            if category is None:
                abort(404)

            selections = Question.query.filter_by(
                category=str(id)).all()
            # print(type(selections))

            data = []
            for selection in selections:
                data.append(selection)
            current_questions = paginate_question(request, data)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selections),
                'current_category': category.type
            })
        except Exception as e:
            print(e)
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
        # questions = Question.query.all()
        category = body.get('quiz_category', None)  # dict
        previous_question = body.get('previous_questions', None)  # list

        # print(type(category), type(previous_question))
        if(category == None) or (previous_question == None):
            abort(422)

        # if no category selected, then all is selected
        if(category['id'] == 0):
            questions = Question.query.all()

        else:
            questions = Question.query.filter(
                Question.category == category['id']).all()
        total = len(questions)

        # function for random questions
        def random_questions():
            random_question = questions[random.randrange(0, len(questions), 1)]
            return random_question
    # function for checking previous questions

        def check_if_previous_question(random_question):
            for question_id in previous_question:
                if (question_id == random_question.id):
                    return True
                else:
                    return False

        random_question = random_questions()

        while (check_if_previous_question(random_question)):
            random_question = random_questions()

            if (len(previous_question) == total):
                return jsonify({
                    'success': True
                })

        # return the question
        return jsonify({
            'success': True,
            'question': random_question.format()
        })

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
            "message": "Method not allowed"
        }), 405

    return app

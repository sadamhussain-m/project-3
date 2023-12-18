from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets
import random
from secrets import randbelow
import click
from sqlalchemy import and_
from flask_restful import Api, Resource
# from flask_whooshalchemy3 import whoosh_index, register_whoosh, search
# from sqlalchemy import between
from sqlalchemy_searchable import search
from sqlalchemy import or_


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///post.db'  # Use SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WHOOSH_BASE'] = 'whoosh_index'
api=Api(app)
db = SQLAlchemy(app)


# register_whoosh(db)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    timestamp = db.Column(db.String(30), nullable=False)
    msg = db.Column(db.String(255), nullable=False)

@app.get("/random/<int:sides>")
def roll(sides):
    if sides <= 0:
        return { 'err': 'need a positive number of sides' }, 400
    
    return { 'num': randbelow(sides) + 1 }

def generate_key():
    # Generating a secure random key using secrets module
    return secrets.token_urlsafe(32)



# Endpoint to create a new post
@app.route('/post', methods=['POST'])
def create_post():
    try:
        data = request.get_json()

        if not isinstance(data, dict) or 'msg' not in data or not isinstance(data['msg'], str):
            return jsonify({"error": "Bad Request. 'msg' field missing or not a string."}), 400

        post = Post(
            key=generate_key(),
            timestamp=datetime.now().replace(microsecond=0).isoformat(),
            msg=data['msg']
        )

        db.session.add(post)
        db.session.commit()

        response = {
            "id": post.id,
            "key": post.key,
            "timestamp": post.timestamp
        }

        return jsonify(response)

    except Exception as e:
            return jsonify({e: "Internal Server Error"}), 500

# Endpoint to get a post by ID
@app.route('/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)

    if post:
        response = {
            "id": post.id,
            "timestamp": post.timestamp,
            "msg": post.msg
        }
        return jsonify(response)
    else:
        return jsonify({"error": "Post not found"}), 404

# Endpoint to delete a post by ID and key
@app.route('/post/<int:post_id>/delete/<string:key>', methods=['DELETE'])
def delete_post(post_id, key):
    post = Post.query.get(post_id)

    if post:
        if key == post.key:
            db.session.delete(post)
            db.session.commit()

            response = {
                "id": post.id,
                "key": generate_key(),
                "timestamp": post.timestamp
            }

            return jsonify(response)
        else:
            return jsonify({"error": "Forbidden. Invalid key"}), 403
    else:
        return jsonify({"error": "Post not found"}), 404

@app.route('/search', methods=['GET'])
def search_posts():
    try:
        start_datetime_str = request.args.get('start_datetime')
        end_datetime_str = request.args.get('end_datetime')

        start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M:%S') if start_datetime_str else None
        end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M:%S') if end_datetime_str else None

        filtered_posts = []

        # if start_datetime and end_datetime:
        #     from sqlalchemy import between
        #     filtered_posts = Post.query.filter(Post.timestamp.between(start_datetime, end_datetime)).all()
        # elif start_datetime:
        #     filtered_posts = Post.query.filter(Post.timestamp >= start_datetime).all()
        # elif end_datetime:
        #     filtered_posts = Post.query.filter(Post.timestamp <= end_datetime).all()
        # else:
        #     return jsonify({"error": "Invalid search parameters"}), 400
        query = Post.query
        if start_datetime and end_datetime:
            filtered_posts = query.filter(and_(Post.timestamp >= start_datetime, Post.timestamp <= end_datetime)).all()
        elif start_datetime:
            filtered_posts = query.filter(Post.timestamp >= start_datetime).all()
        elif end_datetime:
            filtered_posts = query.filter(Post.timestamp <= end_datetime).all()

        # filtered_posts = query.all()
        # query = Post.query
        # if start_datetime:
        #     query = query.filter(Post.timestamp >= start_datetime)
        # if end_datetime:
        #     query = query.filter(Post.timestamp <= end_datetime)

        # filtered_posts = query.all()


        response = [
            {
                "id": post.id,
                "timestamp": post.timestamp,
                "msg": post.msg
            } for post in filtered_posts
        ]

        return jsonify({"posts": response}), 200

    except ValueError:
        return jsonify({"error": "Invalid date/time format"}), 40

class FullTextSearchResource(Resource):
    def get(self):
        try:
            search_query = request.args.get('query')

            if not search_query:
                return jsonify({"error": "Query parameter 'query' is required"}), 400

            # Perform a full-text search using SQLAlchemy
            search_results = Post.query.filter(or_(Post.msg.ilike(f"%{search_query}%"))).all()

            # Format the results
            search_response = [
                {
                    "id": result.id,
                    "timestamp": result.timestamp,
                    "msg": result.msg,
                } for result in search_results
            ]

            return jsonify({"posts": search_response})

        except Exception as e:
            return jsonify({"error": "Internal Server Error"})


api.add_resource(FullTextSearchResource, '/fulltextsearch')

@app.before_request
def create_tables():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import secrets
import random
from secrets import randbelow
import click

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///post.db'  # Use SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



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

            return jsonify(response), 200
        else:
            return jsonify({"error": "Forbidden. Invalid key"}), 403
    else:
        return jsonify({"error": "Post not found"}), 404


@app.before_request
def create_tables():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)

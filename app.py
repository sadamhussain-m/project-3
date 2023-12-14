from flask import Flask,jsonify,request

import secrets

from secrets import randbelow
from datetime import datetime

app = Flask(__name__)

posts=[]

@app.get("/random/<int:sides>")
def roll(sides):
    if sides <= 0:
        return { 'err': 'need a positive number of sides' }, 400
    
    return { 'num': randbelow(sides) + 1 }

def generate_key():
    # Generating a secure random key using secrets module
    return secrets.token_urlsafe(32)

@app.post("/post")
def post():
    try:
        data = request.get_json()

        # Check if the request body is a JSON object and contains the 'msg' field
        if not isinstance(data, dict) or 'msg' not in data or not isinstance(data['msg'], str):
            return jsonify({"error": "Bad Request. 'msg' field missing or not a string."}), 400

        # Generate unique id
        post_id = len(posts) + 1

        # Generate a unique random key
        key = generate_key()

        # Get the current timestamp in ISO 8601 format
        timestamp = datetime.utcnow().isoformat()

        # Create the post
        post = {
            "id": post_id,
            "key": key,
            "timestamp": timestamp,
            "msg": data['msg']
        }

        # Add the post to the list
        posts.append(post)

        # Return the response
        response = {
            "id": post_id,
            "key": key,
            "timestamp": timestamp
        }

        return jsonify(response), 201

    except Exception as e:
        return jsonify({"error": "Internal Server Error","error":e}), 500
    

@app.get('/post/<int:post_id>')
def get_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if post:
        # Return the response without the key
        response = {
            "id": post['id'],
            "timestamp": post['timestamp'],
            "msg": post['msg']
        }
        return jsonify(response)
    else:
        return jsonify({"error": "Post not found"}), 404
    
@app.route('/post/<int:post_id>/delete/<string:key>', methods=['DELETE'])
def delete_post(post_id, key):
    global posts

    # Find the post by ID
    post = next((p for p in posts if p['id'] == post_id), None)

    if post:
        # Check if the provided key matches the key associated with the post
        if key == post['key']:
            # Delete the post
            posts = [p for p in posts if p['id'] != post_id]
            
            # Return the same information as in the POST response
            response = {
                "id": post['id'],
                "key": generate_key(),  # Generate a new key after deletion
                "timestamp": post['timestamp']
            }

            return jsonify(response), 200
        else:
            # Key mismatch, return forbidden error
            return jsonify({"error": "Forbidden. Invalid key"}), 403
    else:
        # Post not found, return not found error
        return jsonify({"error": "Post not found"}), 404
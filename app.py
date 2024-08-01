# Flask application for generating and displaying storybooks
# Main components:
# - Index route ('/'): Displays form for story generation and list of existing storybooks
# - generate_story(): Generates a new story based on user input
# - view_storybook(): Displays an existing storybook
# - Helper functions: load_storybooks(), save_storybook(), get_all_file_paths()
# - Error handling for rate limiting

import os
import json
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_caching import Cache
from flask_cors import CORS, cross_origin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from story_generator import generate_content, process_text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fallback_secret_key'
app.config['CACHE_TYPE'] = 'simple'
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

cache = Cache(app)
#limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

STORYBOOKS_FILE = 'storybooks.json'

@app.before_first_request
def initialize_app():
    '''
    - Runs before the first request to the app
    - Creates 'storybooks.json' if it doesn't exist
    - Logs the creation or existence of the file
    '''
    if not os.path.exists(STORYBOOKS_FILE):
        with open(STORYBOOKS_FILE, 'w') as file:
            json.dump({'storybooks': []}, file)
        app.logger.info(f'{STORYBOOKS_FILE} created.')
    else:
        app.logger.info(f'{STORYBOOKS_FILE} already exists.')

@cache.memoize(timeout=300)
def load_storybooks():
    '''
    - Cached function to reduce file I/O
    - Reads and parses the 'storybooks.json' file
    - Returns an empty list if there's an error
    '''
    try:
        with open(STORYBOOKS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('storybooks', [])
    except (IOError, json.JSONDecodeError) as e:
        app.logger.error(f"Error loading storybooks: {str(e)}")
        return []

def save_storybook(title, output_dir,all_images):
    '''
    - Loads existing storybooks
    - Adds new storybook with title, path, and image paths
    - Writes updated data back to 'storybooks.json'
    '''
    try:
        storybooks = load_storybooks()
        relative_path = os.path.relpath(output_dir, app.static_folder)
        storybooks.append({'title': title, 'path': relative_path, 'all_images':all_images})
        with open(STORYBOOKS_FILE, 'w') as f:
            json.dump({'storybooks': storybooks}, f)
        app.logger.info(f"Storybook '{title}' saved successfully.")
    except Exception as e:
        app.logger.error(f"Error saving storybook: {str(e)}")

@app.route('/', methods=['GET', 'POST']) 
def index():
    '''
    - Processes POST requests for story generation
    - Displays existing storybooks for GET requests
    - Validates the user's input prompt
    '''
    if request.method == 'POST':
        prompt = request.form['prompt']
        if not prompt or len(prompt.split()) <= 1:
            flash('Please enter a story prompt.', 'error')
            return redirect(url_for('index'))
        return generate_story(prompt)
    storybooks = load_storybooks()
    print(storybooks)
    return render_template('index.html', storybooks=storybooks)

def get_all_file_paths(directory):
    '''
    - Walks through the directory tree
    - Collects all file paths
    - Returns a list of file paths
    '''
    try:
        file_paths = []
        for root, _, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)
        return file_paths
    except Exception as e:
        app.logger.error(f"Error getting file paths: {str(e)}")
        return []

@cache.memoize(timeout=300)
def generate_story(prompt):
    '''
    - Cached function to avoid regenerating the same story
    - Calls generate_content() and process_text()
    - Saves the generated storybook
    - Renders the story template with generated content
    '''
    try:
        text = generate_content(prompt)
        try:
            content = json.loads(text)
        except json.JSONDecodeError:
            content = {"title": "Generated Story", "story": text}

        result, output_dir, title = process_text(text)
        if not output_dir or not os.path.exists(output_dir):
            raise ValueError("Invalid output directory")

        image_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
        image_paths = [os.path.join(os.path.basename(output_dir), f) for f in image_files]
        

        al_image_complete_paths = get_all_file_paths(output_dir)
        save_storybook(title,output_dir, al_image_complete_paths )
        
        return render_template('story.html', title=title, images=al_image_complete_paths)
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        flash(f"An error occurred while generating the story: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/storybook/<path:relative_path>')
def view_storybook(relative_path):
    '''
    - Finds the storybook data in 'storybooks.json'
    - Retrieves images and title for the storybook
    - Renders the story template with the storybook data
    '''
    try:
        def find_dict_by_path(file_path, search_value):
            with open(STORYBOOKS_FILE, 'r') as f:
                data = json.load(f)
                

            for item in data.get('storybooks', []):
                if item.get('path') == search_value:
                    return item["all_images"] ,item['title'],item["path"]
                
        images , title , path = find_dict_by_path(STORYBOOKS_FILE , relative_path)
        
        return render_template('story.html', title=title, images= images)
    except Exception as e:
        app.logger.error(f"Error viewing storybook: {str(e)}")
        flash("An error occurred while viewing the storybook. Please try again.", 'error')
        return redirect(url_for('index'))
    
@app.errorhandler(429)
def ratelimit_handler(e):
    '''- Returns a JSON response for rate limit exceeded errors'''
    return jsonify(error="Rate limit exceeded. Please try again later."), 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

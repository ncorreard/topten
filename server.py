from flask import Flask, render_template, jsonify, request, redirect, url_for
import random

app = Flask(__name__)

# Store multiple games: {game_id: {'cards': [...], 'revealed': [...], 'players': {name: card_or_None}}}
games = {}

# Word lists for human-readable game keys
adjectives = ['red', 'blue', 'green', 'happy', 'bright', 'swift', 'calm', 'bold', 'wise', 'kind']
animals = ['tiger', 'eagle', 'wolf', 'bear', 'fox', 'lion', 'hawk', 'shark', 'deer', 'owl']
objects = ['mountain', 'river', 'castle', 'bridge', 'tower', 'garden', 'forest', 'valley', 'ocean', 'star']

def generate_game_key():
    adj = random.choice(adjectives)
    animal = random.choice(animals)
    obj = random.choice(objects)
    return f"{adj}-{animal}-{obj}"

def create_new_game():
    return {
        'cards': list(range(1, 11)),
        'players': {},
        'drawn_order': [],
        'is_revealed': False
    }

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    game_key = generate_game_key()
    while game_key in games:
        game_key = generate_game_key()
    player_name = request.form.get('player_name', '').strip() or 'Anonymous'
    games[game_key] = create_new_game()
    games[game_key]['players'][player_name] = None
    return redirect(url_for('game', game_key=game_key, player=player_name))

@app.route('/join/<game_key>')
def join_page(game_key):
    if game_key not in games:
        return render_template('home.html', error=f"Game '{game_key}' not found!")
    game_data = games[game_key]
    full = len(game_data['players']) >= 10
    return render_template('join.html', game_key=game_key, players=game_data['players'], full=full)

@app.route('/join_game', methods=['POST'])
def join_game():
    game_key = request.form.get('game_key', '').strip()
    player_name = request.form.get('player_name', '').strip() or 'Anonymous'
    if game_key in games:
        if len(games[game_key]['players']) >= 10:
            return render_template('join.html', game_key=game_key, players=games[game_key]['players'], full=True, error='This game is full (10 players max).')
        games[game_key]['players'][player_name] = None
        return redirect(url_for('game', game_key=game_key, player=player_name))
    else:
        return render_template('home.html', error=f"Game '{game_key}' not found!")

@app.route('/game/<game_key>')
def game(game_key):
    if game_key not in games:
        return redirect(url_for('home'))

    player_name = request.args.get('player', '')
    game_data = games[game_key]
    return render_template('game.html',
                           available_cards=len(game_data['cards']),
                           game_key=game_key,
                           player_name=player_name,
                           players=game_data['players'],
                           drawn_order=game_data['drawn_order'],
                           is_revealed=game_data['is_revealed'])

@app.route('/draw_card/<game_key>', methods=['POST'])
def draw_card(game_key):
    if game_key not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_data = games[game_key]
    data = request.get_json() or {}
    player_name = data.get('player_name', '')

    if player_name and game_data['players'].get(player_name) is not None:
        return jsonify({'error': 'You have already drawn a card'}), 400

    if not game_data['cards']:
        return jsonify({'error': 'No cards left'}), 400

    card = random.choice(game_data['cards'])
    game_data['cards'].remove(card)

    if player_name:
        game_data['players'][player_name] = card
        game_data['drawn_order'].append(player_name)

    return jsonify({'card': card, 'remaining': len(game_data['cards'])})

@app.route('/status/<game_key>')
def status(game_key):
    if game_key not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_data = games[game_key]
    return jsonify({
        'available_cards': len(game_data['cards']),
        'players': game_data['players'],
        'drawn_order': game_data['drawn_order'],
        'is_revealed': game_data['is_revealed']
    })

@app.route('/reset/<game_key>', methods=['POST'])
def reset_game(game_key):
    if game_key not in games:
        return jsonify({'error': 'Game not found'}), 404

    existing_players = list(games[game_key]['players'].keys())
    games[game_key] = create_new_game()
    for name in existing_players:
        games[game_key]['players'][name] = None
    return jsonify({'message': 'Game reset successfully', 'available_cards': 10})

@app.route('/reveal/<game_key>', methods=['POST'])
def reveal_game(game_key):
    if game_key not in games:
        return jsonify({'error': 'Game not found'}), 404
    games[game_key]['is_revealed'] = True
    return jsonify({'is_revealed': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

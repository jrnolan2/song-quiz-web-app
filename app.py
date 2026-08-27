from flask import Flask, abort, request, render_template, send_from_directory, url_for
import os
import random
import re
import hashlib

from pydub import AudioSegment
from pydub.generators import WhiteNoise

app = Flask(__name__)

ALLOW_REPEATS = False
song_lists_dict = {}
curr_song_list = []
curr_song_list_name = ''
local_audio_enabled = False
audio_settings = {
    'duration': 10.0,
    'playback_rate': 1.0,
    'reverse': False,
    'static_level': 0,
    'combine_count': 1,
}

class Song:
    def __init__(self,name,link,artists,year):
        self.name = name
        self.link = link
        self.artists = artists
        self.year = year

def clean_filename(filename: str) -> str:
    """Return a filename that is safe to use across common operating systems."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", filename)
    return cleaned.strip(" .")

def local_audio_filename(song):
    return clean_filename(f'{song.name} - {song.artists}') + '.mp3'

def create_processed_audio(songs):
    """Create one cached MP3 after applying the current effects to every song."""
    source_names = [local_audio_filename(song) for song in songs]
    cache_key = repr((curr_song_list_name, source_names, audio_settings)).encode()
    output_name = hashlib.sha256(cache_key).hexdigest() + '.mp3'
    output_directory = os.path.join('songs', 'generated')
    output_path = os.path.join(output_directory, output_name)
    if os.path.isfile(output_path):
        return output_name

    processed_segments = []
    for song in songs:
        source_path = os.path.join('songs', curr_song_list_name,
                                   local_audio_filename(song))
        if not os.path.isfile(source_path):
            return None

        segment = AudioSegment.from_file(source_path)
        segment = segment[:int(audio_settings['duration'] * 1000)]
        rate = audio_settings['playback_rate']
        if rate != 1.0:
            segment = segment._spawn(
                segment.raw_data,
                overrides={'frame_rate': int(segment.frame_rate * rate)}
            ).set_frame_rate(segment.frame_rate)
        if audio_settings['reverse']:
            segment = segment.reverse()
        static_level = audio_settings['static_level']
        if static_level:
            noise = WhiteNoise().to_audio_segment(duration=len(segment))
            noise = noise - (60 - (static_level * 0.6))
            segment = segment.overlay(noise)
        processed_segments.append(segment)

    combined = processed_segments[0]
    for segment in processed_segments[1:]:
        combined = combined.overlay(segment)
    os.makedirs(output_directory, exist_ok=True)
    combined.export(output_path, format='mp3')
    return output_name

def read_song_list_file(song_list_file):
    """
    Read in a song list file and return a list of Song objects.
    A song list file should be a tab-separated value file with a header.
    The TSV columns are:
    Title \t Link to Song \t Artist(s) \t Year
    """
    song_list = []
    with open(song_list_file,encoding='utf-8') as f:
        song_lines = f.read().replace('\r','').split('\n')[1:]
        for song_line in song_lines:
            try:
                song_line_parts = song_line.split('\t')
                song_name = song_line_parts[0]
                song_link = song_line_parts[1]
                
                if len(song_line_parts) > 2:
                    song_artist = song_line_parts[2]
                else:
                    song_artist = "" # if no artist is provided

                if len(song_line_parts) > 3:
                    song_year = int(song_line_parts[3])
                else:
                    song_year = 0 # if no year provided, default to 0
                
                song_list.append(Song(song_name,song_link,song_artist,song_year))
            except:
                print(f"Error: could not parse line: {song_line}")
    return song_list

def initialize_song_lists():
    """
    Read in all song list files in the song lists directory and save their lists of songs
    in the song_lists_dict.
    """
    SONG_LISTS_DIRECTORY = 'song_lists'

    song_list_files = os.listdir(SONG_LISTS_DIRECTORY)
    song_list_files = [f for f in song_list_files if f.endswith('.txt') or f.endswith('.tsv')]
    for song_list_file in song_list_files:
        print('Reading in file', song_list_file)
        song_list_file_name = song_list_file.split('.')[0]
        try:
            song_lists_dict[song_list_file_name] = read_song_list_file(os.path.join(SONG_LISTS_DIRECTORY,song_list_file))
        except:
            print(f'Error: could not read file {song_list_file}')

@app.route('/random-song', methods=['GET','POST'])
def random_song_page():
    """Return a page with a random song from the selected list."""
    if len(curr_song_list) == 0:
        # No songs left
        return render_template('no_songs_left.html')

    song_count = audio_settings['combine_count'] if local_audio_enabled else 1
    if len(curr_song_list) < song_count:
        return render_template('no_songs_left.html')
    selected_songs = random.sample(curr_song_list, song_count)
    if not ALLOW_REPEATS:
        for song in selected_songs:
            curr_song_list.remove(song)

    local_audio_url = None
    local_audio_missing = False
    if local_audio_enabled:
        audio_filename = create_processed_audio(selected_songs)
        if audio_filename:
            local_audio_url = url_for(
                'generated_audio',
                filename=audio_filename
            )
        else:
            local_audio_missing = True

    song_name = ' + '.join(song.name for song in selected_songs)
    song_artists = ', '.join(song.artists for song in selected_songs)
    song_links = [song.link for song in selected_songs]
    song_year = ', '.join(str(song.year) for song in selected_songs)

    return render_template('random_song.html',
                           song_name=song_name,
                           song_artists=song_artists,
                           song_year=song_year,
                           song_links=song_links,
                           local_audio_enabled=local_audio_enabled,
                           local_audio_url=local_audio_url,
                           local_audio_missing=local_audio_missing)

@app.route('/local-audio/<song_list>/<path:filename>')
def local_audio(song_list, filename):
    """Serve a downloaded ten-second clip from the selected song list."""
    if song_list not in song_lists_dict:
        abort(404)
    return send_from_directory(
        os.path.join('songs', song_list), filename, mimetype='audio/mpeg'
    )

@app.route('/generated-audio/<path:filename>')
def generated_audio(filename):
    return send_from_directory('songs/generated', filename, mimetype='audio/mpeg')

@app.route('/start-quiz', methods=['POST'])
def start_quiz():
    """
    Create the list of songs for the quiz based off user form values and start the quiz.
    """
    global curr_song_list, curr_song_list_name, ALLOW_REPEATS, local_audio_enabled

    # Get all songs in selected song list
    song_list_name = request.form.get('song_list')
    curr_song_list_name = song_list_name
    curr_song_list = song_lists_dict[song_list_name].copy()

    # Filter songs released from min year to max year
    min_year = int(request.form.get('min_year'))
    max_year = int(request.form.get('max_year'))
    filtered_curr_song_list = []
    for song in curr_song_list:
        if min_year <= song.year <= max_year:
            filtered_curr_song_list.append(song)
    curr_song_list = filtered_curr_song_list

    # Set whether repeat songs are allowed
    repeats = request.form.get('repeats')
    if repeats == None:
        ALLOW_REPEATS = False
    else:
        ALLOW_REPEATS = True

    local_audio_enabled = request.form.get('local_audio') is not None
    if local_audio_enabled:
        try:
            duration = float(request.form.get('audio_duration', 10))
            playback_rate = float(request.form.get('playback_rate', 1))
            static_level = int(request.form.get('static_level', 0))
            combine_count = int(request.form.get('combine_count', 1))
            if not 0 < duration <= 10 or not 0.25 <= playback_rate <= 4:
                raise ValueError
            if not 0 <= static_level <= 100 or not 1 <= combine_count <= 20:
                raise ValueError
            audio_settings.update({
                'duration': duration,
                'playback_rate': playback_rate,
                'reverse': request.form.get('play_reverse') is not None,
                'static_level': static_level,
                'combine_count': combine_count,
            })
        except (TypeError, ValueError):
            return 'Audio settings are invalid.', 400
    else:
        audio_settings.update({
            'duration': 10.0, 'playback_rate': 1.0, 'reverse': False,
            'static_level': 0, 'combine_count': 1,
        })

    return random_song_page()

@app.route('/', methods=['GET'])
def index():
    """Render the start song quiz form."""
    return render_template('index.html',
                           song_lists=sorted(song_lists_dict.keys()),
                           default_song_list='radio')

if __name__ == '__main__':
    initialize_song_lists()
    app.run(debug=True)
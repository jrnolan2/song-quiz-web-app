# Song Quiz Web App
This app is a song quiz that will run on your web browser. This app was built for the Quiz Bowl club at NC State. The app uses any song list file in the `song_lists` folder in the format described below.

## How to run
Before you run:
* Install Python
* Install flask with `pip install flask`

Start web app:
* Run `python app.py` from this directory
* Visit `localhost:5000` to play song quiz

## How to play
Once the web app has started with the instructions above, you'll be greeted with the start page. The start page lets the user select options before starting the quiz. The options are:
* **Song Set**: The list of songs that will be used for the quiz
* **Year Range**: The minimum and maximum years that should be included in the quiz. These bounds are inclusive so for example, min year = 2000 and max year = 2009 will include songs from 2000 and 2009.
* **Allow Repeats**: Whether a song can be played multiple times during the quiz. Defaults to false. When no repeats are allowed, the songs will eventually run out if you play long enough and you will be returned to the start page.

After selecting the options, press "Start Song Quiz!". You will get a random song from the list that satisfies your selected options. The song's title, artist, and year will displayed. A link to the music will also be included. The song quiz master should click on the link (opens in new tab) to start the music. The song quiz players will buzz in and then the song quiz master should pause the song. The player who buzzed in should immediately have the answer, if they are stalling to think then the master should disqualify them and then continue the music for someone else to buzz in.

Note: The web app only allows one game at a time, don't start it in multiple tabs.

## Song list file
All song list files should be put in a directory named `song_lists`. The format of these files is described in this section. The file should be a tab-separated value file. The first line should be a header describing the columns:

<code>Song \t Link \t Artist(s) \t Year</code>

The "Song" column should be the song's title. The "Link" column should be a Youtube link to the song. If the music video has a non-music intro or immediately says the title than a different starting time should be chosen. On Youtube, this can be accomplished by clicking "Share" and then checking the "Start at" box. The "Artist" column should be the artist who released the song including any featured artists. This field can also be used for the movie/TV show/video game a song originates from. Finally, the "Year" column should be the year that the song was released.
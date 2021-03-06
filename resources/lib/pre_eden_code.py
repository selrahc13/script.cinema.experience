# -*- coding: utf-8 -*-
__scriptID__ = "script.cinema.experience"
__modname__ = "pre_eden_code.py"
log_message = "[ " + __scriptID__ + " ] - [ " + __modname__ + " ]"
log_sep = "-"*70

import xbmc, xbmcgui, xbmcaddon
import traceback, os
from urllib import quote_plus
from json_utils import find_movie_details, retrieve_json_dict

_A_ = xbmcaddon.Addon( __scriptID__ )
# language method
_L_ = _A_.getLocalizedString
# settings method
_S_ = _A_.getSetting

def _build_playlist( movie_titles ):
    for movie in movie_titles:
        xbmc.log( "[script.cinema.experience] - Movie Title: %s" % movie, level=xbmc.LOGNOTICE )
        xbmc.executehttpapi( "SetResponseFormat()" )
        xbmc.executehttpapi( "SetResponseFormat(OpenField,)" )
        # select Movie path from movieview Limit 1
        sql = "SELECT movieview.idMovie, movieview.c00, movieview.strPath, movieview.strFileName, movieview.c08, movieview.c14 FROM movieview WHERE c00 LIKE '%s' LIMIT 1" % ( movie.replace( "'", "''", ), )
        xbmc.log( "[script.cinema.experience]  - SQL: %s" % ( sql, ), level=xbmc.LOGDEBUG )
        # query database for info dummy is needed as there are two </field> formatters
        try:
            movie_id, movie_title, movie_path, movie_filename, thumb, genre, dummy = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % quote_plus( sql ), ).split( "</field>" )
            movie_id = int( movie_id )
        except:
            traceback.print_exc()
            xbmc.log( "[script.cinema.experience] - Unable to match movie", level=xbmc.LOGERROR )
            movie_id = 0
            movie_title = movie_path = movie_filename = thumb = genre = dummy = ""
        movie_full_path = os.path.join(movie_path, movie_filename).replace("\\\\" , "\\")
        xbmc.log( "[script.cinema.experience] - Movie Title: %s" % movie_title, level=xbmc.LOGNOTICE )
        xbmc.log( "[script.cinema.experience] - Movie Path: %s" % movie_path, level=xbmc.LOGNOTICE )
        xbmc.log( "[script.cinema.experience] - Movie Filename: %s" % movie_filename, level=xbmc.LOGNOTICE )
        xbmc.log( "[script.cinema.experience] - Full Movie Path: %s" % movie_full_path, level=xbmc.LOGNOTICE )
        if not movie_id == 0:
            json_command = '{"jsonrpc": "2.0", "method": "Playlist.Add", "params": {"playlistid": 1, "item": {"movieid": %d} }, "id": 1}' % movie_id
            json_response = xbmc.executeJSONRPC(json_command)
            xbmc.log( "[script.cinema.experience] - JSONRPC Response: \n%s" % movie_title, level=xbmc.LOGDEBUG )
            xbmc.sleep( 50 )

def _store_playlist():
    p_list = []
    xbmc.log( "[script.cinema.experience] - Storing Playlist", level=xbmc.LOGNOTICE )
    json_query = '{"jsonrpc": "2.0", "method": "Playlist.GetItems", "params": {"playlistid": 1, "properties": ["title", "file", "thumbnail", "streamdetails", "mpaa", "genre"] }, "id": 1}'
    p_list = retrieve_json_dict( json_query, items="items", force_log=False )
    return p_list

def _rebuild_playlist( plist ): # rebuild movie playlist
    xbmc.log( "[script.cinema.experience] - [ce_playlist.py] - Rebuilding Playlist", level=xbmc.LOGNOTICE )
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    playlist.clear()
    print plist
    for movie in plist:
        try:
            xbmc.log( "[script.cinema.experience] - Movie Title: %s" % movie["title"], level=xbmc.LOGDEBUG )
            xbmc.log( "[script.cinema.experience] - Movie Thumbnail: %s" % movie["thumbnail"], level=xbmc.LOGDEBUG )
            xbmc.log( "[script.cinema.experience] - Full Movie Path: %s" % movie["file"], level=xbmc.LOGDEBUG )
            json_command = '{"jsonrpc": "2.0", "method": "Playlist.Add", "params": {"playlistid": 1, "item": {"movieid": %d} }, "id": 1}' % movie["id"]
            json_response = xbmc.executeJSONRPC(json_command)
            xbmc.log( "[script.cinema.experience] - JSONRPC Response: \n%s" % movie["title"], level=xbmc.LOGDEBUG )
        except:
            traceback.print_exc()
        # give XBMC a chance to add to the playlist... May not be needed, but what's 50ms?
        xbmc.sleep( 50 )

def _get_queued_video_info( feature = 0 ):
    xbmc.log( "%s - _get_queued_video_info() Started" % log_message, level=xbmc.LOGDEBUG )
    equivalent_mpaa = "NR"
    try:
        # get movie name
        plist = _store_playlist()
        movie_title = plist[feature]['title']
        path = plist[feature]['file']
        mpaa = plist[feature]['mpaa']
        genre = plist[feature]['genre']
        try:
            audio = plist[feature]['streamdetails']['audio'][0]['codec']
        except:
            audio = "other"
        if mpaa == "":
            mpaa = "NR"
        elif mpaa.startswith("Rated"):
            mpaa = mpaa.split( " " )[ 1 - ( len( mpaa.split( " " ) ) == 1 ) ]
            mpaa = ( mpaa, "NR", )[ mpaa not in ( "G", "PG", "PG-13", "R", "NC-17", "Unrated", ) ]
        elif mpaa.startswith("UK"):
            mpaa = mpaa.split( ":" )[ 1 - ( len( mpaa.split( ":" ) ) == 1 ) ]
            mpaa = ( mpaa, "NR", )[ mpaa not in ( "12", "12A", "PG", "15", "18", "R18", "MA", "U", ) ]
        else:
            mpaa = ( mpaa, "NR", )[ mpaa not in ( "12", "12A", "PG", "15", "18", "R18", "MA", "U", ) ]
        if mpaa not in ( "G", "PG", "PG-13", "R", "NC-17", "Unrated", "NR" ):
            if mpaa in ("12", "12A",):
                equivalent_mpaa = "PG-13"
            elif mpaa == "15":
                equivalent_mpaa = "R"
            elif mpaa == "U":
                equivalent_mpaa = "G"
            elif mpaa in ("18", "R18", "MA",):
                equivalent_mpaa = "NC-17"
        else:
            equivalent_mpaa = mpaa
    except:
        traceback.print_exc()
        movie_title = path = mpaa = audio = genre = movie = equivalent_mpaa = ""
    # spew queued video info to log
    xbmc.log( "%s - Queued Movie Information" % log_message, level=xbmc.LOGDEBUG )
    xbmc.log( "%s %s" % ( log_message,log_sep ), level=xbmc.LOGDEBUG )
    xbmc.log( "%s - Title: %s" % ( log_message, movie_title, ), level=xbmc.LOGDEBUG )
    xbmc.log( "%s - Path: %s" % ( log_message, path, ), level=xbmc.LOGDEBUG )
    xbmc.log( "%s - Genre: %s" % ( log_message, genre, ), level=xbmc.LOGDEBUG )
    xbmc.log( "%s - MPAA: %s" % ( log_message, mpaa, ), level=xbmc.LOGDEBUG )
    xbmc.log( "%s - Audio: %s" % ( log_message, audio, ), level=xbmc.LOGDEBUG )
    if _S_( "audio_videos_folder" ):
        xbmc.log( "%s - Folder: %s" % ( log_message, ( xbmc.translatePath( _S_( "audio_videos_folder" ) ) + { "dca": "DTS", "ac3": "Dolby", "dtsma": "DTSHD-MA", "dtshd_ma": "DTSHD-MA", "a_truehd": "Dolby TrueHD", "truehd": "Dolby TrueHD" }.get( audio, "Other" ) + xbmc.translatePath( _S_( "audio_videos_folder" ) )[ -1 ], ) ), level=xbmc.LOGDEBUG )
    xbmc.log( "%s  %s" % ( log_message, log_sep ), level=xbmc.LOGDEBUG )
    # return results
    return mpaa, audio, genre, path, equivalent_mpaa
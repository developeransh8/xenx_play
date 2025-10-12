import sqlite3
import json
from datetime import datetime
from pathlib import Path
import config

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DB_PATH
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'uploading',
                progress INTEGER DEFAULT 0,
                duration REAL,
                width INTEGER,
                height INTEGER,
                fps REAL,
                video_codec TEXT,
                file_size INTEGER,
                hls_master_path TEXT,
                thumbnail_path TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                watch_count INTEGER DEFAULT 0
            )
        ''')
        
        # Create audio_tracks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audio_tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                track_index INTEGER NOT NULL,
                language TEXT,
                title TEXT,
                codec TEXT,
                channels INTEGER,
                sample_rate INTEGER,
                is_default BOOLEAN DEFAULT 0,
                hls_playlist_path TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audio_tracks_video_id ON audio_tracks(video_id)')
        
        conn.commit()
        conn.close()
    
    def create_video(self, video_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO videos (id, filename, original_filename, status, file_size)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            video_data['id'],
            video_data['filename'],
            video_data['original_filename'],
            video_data.get('status', 'uploading'),
            video_data.get('file_size', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def update_video(self, video_id, updates):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [video_id]
        
        cursor.execute(f'UPDATE videos SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
    
    def get_video(self, video_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_videos(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM videos ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete_video(self, video_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        conn.commit()
        conn.close()
    
    def create_audio_track(self, track_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audio_tracks 
            (video_id, track_index, language, title, codec, channels, sample_rate, is_default, hls_playlist_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            track_data['video_id'],
            track_data['track_index'],
            track_data.get('language', 'und'),
            track_data.get('title', f"Audio Track {track_data['track_index']}"),
            track_data.get('codec', 'aac'),
            track_data.get('channels', 2),
            track_data.get('sample_rate', 48000),
            track_data.get('is_default', False),
            track_data.get('hls_playlist_path', '')
        ))
        
        conn.commit()
        conn.close()
    
    def get_audio_tracks(self, video_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audio_tracks WHERE video_id = ? ORDER BY track_index', (video_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def increment_watch_count(self, video_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE videos SET watch_count = watch_count + 1 WHERE id = ?', (video_id,))
        conn.commit()
        conn.close()

"""SQLite database utilities for storing study data"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import config


class StudyDatabase:
    """SQLite database for storing study materials and progress"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = config.DB_PATH
            if db_path.endswith('.json'):
                db_path = db_path.replace('.json', '.db')
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Files table - store uploaded files info
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                UNIQUE(file_path)
            )
        ''')
        
        # Topics table - store identified topics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                topic_name TEXT NOT NULL,
                subtopics TEXT,
                key_concepts TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        # Flashcards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                topic TEXT,
                chunk_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        # Quizzes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answer INTEGER NOT NULL,
                explanation TEXT,
                difficulty TEXT,
                chunk_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        # Revision plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revision_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                topic_name TEXT NOT NULL,
                difficulty TEXT,
                importance TEXT,
                first_revision DATE,
                subsequent_revisions TEXT,
                estimated_study_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        # Quiz results table - track user performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                selected_answer INTEGER,
                is_correct BOOLEAN,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
            )
        ''')
        
        # Chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence TEXT,
                asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_file(self, file_name: str, file_path: str, file_size: int) -> int:
        """Add uploaded file to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if file already exists
        cursor.execute('SELECT id FROM files WHERE file_path = ?', (file_path,))
        existing = cursor.fetchone()
        
        if existing:
            file_id = existing[0]
            # Update processed_at
            cursor.execute(
                'UPDATE files SET processed_at = ? WHERE id = ?',
                (datetime.now().isoformat(), file_id)
            )
        else:
            cursor.execute(
                'INSERT INTO files (file_name, file_path, file_size, processed_at) VALUES (?, ?, ?, ?)',
                (file_name, file_path, file_size, datetime.now().isoformat())
            )
            file_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return file_id
    
    def add_topics(self, file_id: int, topics: List[Dict]):
        """Add topics for a file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing topics for this file
        cursor.execute('DELETE FROM topics WHERE file_id = ?', (file_id,))
        
        for topic in topics:
            cursor.execute(
                'INSERT INTO topics (file_id, topic_name, subtopics, key_concepts) VALUES (?, ?, ?, ?)',
                (
                    file_id,
                    topic.get('topic', ''),
                    json.dumps(topic.get('subtopics', [])),
                    json.dumps(topic.get('key_concepts', []))
                )
            )
        
        conn.commit()
        conn.close()
    
    def save_flashcards(self, file_id: int, flashcards: List[Dict]):
        """Save flashcards to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing flashcards for this file
        cursor.execute('DELETE FROM flashcards WHERE file_id = ?', (file_id,))
        
        for card in flashcards:
            cursor.execute(
                'INSERT INTO flashcards (file_id, question, answer, topic, chunk_id) VALUES (?, ?, ?, ?, ?)',
                (
                    file_id,
                    card.get('question', ''),
                    card.get('answer', ''),
                    card.get('topic', 'General'),
                    card.get('chunk_id', 0)
                )
            )
        
        conn.commit()
        conn.close()
    
    def get_flashcards(self, file_id: int = None) -> List[Dict]:
        """Get flashcards from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if file_id:
            cursor.execute('SELECT * FROM flashcards WHERE file_id = ? ORDER BY id', (file_id,))
        else:
            cursor.execute('SELECT * FROM flashcards ORDER BY id DESC LIMIT 100')
        
        rows = cursor.fetchall()
        flashcards = []
        for row in rows:
            flashcards.append({
                'id': row['id'],
                'question': row['question'],
                'answer': row['answer'],
                'topic': row['topic'],
                'chunk_id': row['chunk_id']
            })
        
        conn.close()
        return flashcards
    
    def save_quizzes(self, file_id: int, quizzes: List[Dict]):
        """Save quiz questions to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing quizzes for this file
        cursor.execute('DELETE FROM quizzes WHERE file_id = ?', (file_id,))
        
        for quiz in quizzes:
            cursor.execute(
                '''INSERT INTO quizzes (file_id, question, options, correct_answer, explanation, difficulty, chunk_id) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    file_id,
                    quiz.get('question', ''),
                    json.dumps(quiz.get('options', [])),
                    quiz.get('correct_answer', 0),
                    quiz.get('explanation', ''),
                    quiz.get('difficulty', 'Medium'),
                    quiz.get('chunk_id', 0)
                )
            )
        
        conn.commit()
        conn.close()
    
    def get_quizzes(self, file_id: int = None) -> List[Dict]:
        """Get quiz questions from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if file_id:
            cursor.execute('SELECT * FROM quizzes WHERE file_id = ? ORDER BY id', (file_id,))
        else:
            cursor.execute('SELECT * FROM quizzes ORDER BY id DESC LIMIT 100')
        
        rows = cursor.fetchall()
        quizzes = []
        for row in rows:
            quizzes.append({
                'id': row['id'],
                'question': row['question'],
                'options': json.loads(row['options']),
                'correct_answer': row['correct_answer'],
                'explanation': row['explanation'],
                'difficulty': row['difficulty'],
                'chunk_id': row['chunk_id']
            })
        
        conn.close()
        return quizzes
    
    def save_revision_plan(self, file_id: int, plan: Dict):
        """Save revision plan to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing plan for this file
        cursor.execute('DELETE FROM revision_plans WHERE file_id = ?', (file_id,))
        
        for topic_plan in plan.get('topics', []):
            cursor.execute(
                '''INSERT INTO revision_plans (file_id, topic_name, difficulty, importance, first_revision, subsequent_revisions, estimated_study_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    file_id,
                    topic_plan.get('topic_name', ''),
                    topic_plan.get('difficulty', 'Medium'),
                    topic_plan.get('importance', 'Medium'),
                    topic_plan.get('first_revision', ''),
                    json.dumps(topic_plan.get('subsequent_revisions', [])),
                    topic_plan.get('estimated_study_time', '30 minutes')
                )
            )
        
        conn.commit()
        conn.close()
    
    def get_revision_plan(self, file_id: int = None) -> Dict:
        """Get revision plan from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if file_id:
            cursor.execute('SELECT * FROM revision_plans WHERE file_id = ? ORDER BY first_revision', (file_id,))
        else:
            cursor.execute('SELECT * FROM revision_plans ORDER BY first_revision LIMIT 50')
        
        rows = cursor.fetchall()
        topics = []
        for row in rows:
            topics.append({
                'topic_name': row['topic_name'],
                'difficulty': row['difficulty'],
                'importance': row['importance'],
                'first_revision': row['first_revision'],
                'subsequent_revisions': json.loads(row['subsequent_revisions']),
                'estimated_study_time': row['estimated_study_time']
            })
        
        conn.close()
        return {'topics': topics, 'total_topics': len(topics)}
    
    def save_chat_message(self, file_id: int, question: str, answer: str, confidence: str = 'medium'):
        """Save chat message to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO chat_history (file_id, question, answer, confidence) VALUES (?, ?, ?, ?)',
            (file_id, question, answer, confidence)
        )
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, file_id: int = None, limit: int = 20) -> List[Dict]:
        """Get chat history from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if file_id:
            cursor.execute(
                'SELECT * FROM chat_history WHERE file_id = ? ORDER BY asked_at DESC LIMIT ?',
                (file_id, limit)
            )
        else:
            cursor.execute('SELECT * FROM chat_history ORDER BY asked_at DESC LIMIT ?', (limit,))
        
        rows = cursor.fetchall()
        history = []
        for row in rows:
            history.append({
                'question': row['question'],
                'answer': row['answer'],
                'confidence': row['confidence'],
                'timestamp': row['asked_at']
            })
        
        conn.close()
        return history
    
    def get_file_by_path(self, file_path: str) -> Optional[Dict]:
        """Get file info by path"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files WHERE file_path = ?', (file_path,))
        row = cursor.fetchone()
        
        conn.close()
        if row:
            return {
                'id': row['id'],
                'file_name': row['file_name'],
                'file_path': row['file_path'],
                'file_size': row['file_size'],
                'uploaded_at': row['uploaded_at'],
                'processed_at': row['processed_at']
            }
        return None
    
    def get_all_files(self) -> List[Dict]:
        """Get all uploaded files"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files ORDER BY processed_at DESC')
        rows = cursor.fetchall()
        
        files = []
        for row in rows:
            files.append({
                'id': row['id'],
                'file_name': row['file_name'],
                'file_path': row['file_path'],
                'file_size': row['file_size'],
                'uploaded_at': row['uploaded_at'],
                'processed_at': row['processed_at']
            })
        
        conn.close()
        return files


"""
Enhanced Database Schema with Segments Table
Stores raw files, chunks/segments, and generated artifacts
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import config


def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    # Files table - store uploaded files info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            file_type TEXT,
            raw_text TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            UNIQUE(file_path)
        )
    ''')
    
    # Segments table - store chunked and labeled text segments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            label TEXT,
            topic TEXT,
            page_number INTEGER,
            start_char INTEGER,
            end_char INTEGER,
            embedding_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(id),
            UNIQUE(file_id, chunk_index)
        )
    ''')
    
    # Embeddings table - store embedding vectors metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id TEXT PRIMARY KEY,
            segment_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            embedding_type TEXT DEFAULT 'faiss',
            vector_index INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (segment_id) REFERENCES segments(id),
            FOREIGN KEY (file_id) REFERENCES files(id)
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
            segment_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(id),
            FOREIGN KEY (segment_id) REFERENCES segments(id)
        )
    ''')
    
    # Quizzes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            segment_id INTEGER,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answer INTEGER NOT NULL,
            explanation TEXT,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(id),
            FOREIGN KEY (segment_id) REFERENCES segments(id)
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
    
    # Artifacts table - store generated artifacts metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            artifact_type TEXT NOT NULL,
            artifact_data TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {config.DB_PATH}")


class Database:
    """Database operations for the API"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
    
    def add_file(self, file_name: str, file_path: str, file_size: int, 
                 file_type: str = "pdf", raw_text: str = None) -> int:
        """Add uploaded file to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM files WHERE file_path = ?', (file_path,))
        existing = cursor.fetchone()
        
        if existing:
            file_id = existing[0]
            cursor.execute(
                'UPDATE files SET processed_at = ?, raw_text = ? WHERE id = ?',
                (datetime.now().isoformat(), raw_text, file_id)
            )
        else:
            cursor.execute(
                '''INSERT INTO files (file_name, file_path, file_size, file_type, raw_text, processed_at) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (file_name, file_path, file_size, file_type, raw_text, datetime.now().isoformat())
            )
            file_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return file_id
    
    def add_segments(self, file_id: int, segments: List[Dict]):
        """
        Add text segments/chunks to database with commit verification
        
        Args:
            file_id: File ID
            segments: List of segment dictionaries
            
        Returns:
            Number of segments inserted
        """
        import logging
        logger = logging.getLogger(__name__)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Clear existing segments for this file
            cursor.execute('DELETE FROM segments WHERE file_id = ?', (file_id,))
            deleted = cursor.rowcount
            logger.debug(f"db: deleted {deleted} existing segments for file_id={file_id}")
            
            inserted = 0
            for seg in segments:
                cursor.execute(
                    '''INSERT INTO segments (file_id, chunk_index, text_content, label, topic, 
                       page_number, start_char, end_char) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        file_id,
                        seg.get('chunk_index', 0),
                        seg.get('text_content', ''),
                        seg.get('label', ''),
                        seg.get('topic', ''),
                        seg.get('page_number', 0),
                        seg.get('start_char', 0),
                        seg.get('end_char', 0)
                    )
                )
                inserted += 1
            
            # CRITICAL: Commit transaction
            conn.commit()
            logger.debug(f"db: committed transaction for {inserted} segments, file_id={file_id}")
            
            # Read-back assertion to verify writes
            cursor.execute('SELECT COUNT(*) FROM segments WHERE file_id = ?', (file_id,))
            count = cursor.fetchone()[0]
            
            logger.debug(f"db: inserted {inserted} segments, db count={count} for file_id={file_id}")
            
            if count < inserted:
                raise Exception(f"DB write inconsistency: inserted {inserted} but count={count} for file_id={file_id}")
            
            logger.info(f"db: successfully inserted and verified {count} segments for file_id={file_id}")
            return inserted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"db: error inserting segments for file_id={file_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_segments(self, file_id: int) -> List[Dict]:
        """Get all segments for a file"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM segments WHERE file_id = ? ORDER BY chunk_index', (file_id,))
        rows = cursor.fetchall()
        
        segments = []
        for row in rows:
            segments.append({
                'id': row['id'],
                'file_id': row['file_id'],
                'chunk_index': row['chunk_index'],
                'text_content': row['text_content'],
                'label': row['label'],
                'topic': row['topic'],
                'page_number': row['page_number'],
                'start_char': row['start_char'],
                'end_char': row['end_char']
            })
        
        conn.close()
        return segments
    
    def get_segment_by_id(self, segment_id: int) -> Optional[Dict]:
        """Get a specific segment by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM segments WHERE id = ?', (segment_id,))
        row = cursor.fetchone()
        
        conn.close()
        if row:
            return {
                'id': row['id'],
                'file_id': row['file_id'],
                'chunk_index': row['chunk_index'],
                'text_content': row['text_content'],
                'label': row['label'],
                'topic': row['topic'],
                'page_number': row['page_number']
            }
        return None
    
    def get_file(self, file_id: int) -> Optional[Dict]:
        """Get file information"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = cursor.fetchone()
        
        conn.close()
        if row:
            return {
                'id': row['id'],
                'file_name': row['file_name'],
                'file_path': row['file_path'],
                'file_size': row['file_size'],
                'file_type': row['file_type'],
                'uploaded_at': row['uploaded_at'],
                'processed_at': row['processed_at']
            }
        return None
    
    def save_artifact(self, file_id: int, artifact_type: str, artifact_data: Dict, 
                     metadata: Dict = None):
        """Save generated artifact with commit verification"""
        import logging
        logger = logging.getLogger(__name__)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            artifact_data_json = json.dumps(artifact_data)
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute(
                '''INSERT INTO artifacts (file_id, artifact_type, artifact_data, metadata) 
                   VALUES (?, ?, ?, ?)''',
                (file_id, artifact_type, artifact_data_json, metadata_json)
            )
            artifact_id = cursor.lastrowid
            
            # CRITICAL: Commit transaction
            conn.commit()
            logger.debug(f"db: committed artifact id={artifact_id}, type={artifact_type}, file_id={file_id}")
            
            # Read-back verification
            cursor.execute('SELECT id FROM artifacts WHERE id = ?', (artifact_id,))
            verify = cursor.fetchone()
            
            if not verify:
                raise Exception(f"DB write inconsistency: artifact {artifact_id} not found after commit")
            
            logger.info(f"db: successfully saved artifact id={artifact_id}, type={artifact_type}, file_id={file_id}")
            return artifact_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"db: error saving artifact for file_id={file_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_artifacts(self, file_id: int, artifact_type: str = None) -> List[Dict]:
        """Get artifacts for a file"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if artifact_type:
            cursor.execute(
                'SELECT * FROM artifacts WHERE file_id = ? AND artifact_type = ? ORDER BY created_at DESC',
                (file_id, artifact_type)
            )
        else:
            cursor.execute(
                'SELECT * FROM artifacts WHERE file_id = ? ORDER BY created_at DESC',
                (file_id,)
            )
        
        rows = cursor.fetchall()
        artifacts = []
        for row in rows:
            artifacts.append({
                'id': row['id'],
                'artifact_type': row['artifact_type'],
                'artifact_data': json.loads(row['artifact_data']),
                'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                'created_at': row['created_at']
            })
        
        conn.close()
        return artifacts


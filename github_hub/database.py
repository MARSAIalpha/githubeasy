# GitHub Hub - 数据库层
import sqlite3
import json
import threading
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

class Database:
    def __init__(self, db_path="data/projects.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        # Thread lock for application-level serialization of writes (optional but good for safety)
        self.lock = threading.RLock()
        
        # Initialize WAL mode
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
        
        self._init_tables()
    
    @contextmanager
    def _get_connection(self):
        """获取独立的数据库连接，使用后自动关闭"""
        # Timeout 60s to wait for lock to be released
        conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_tables(self):
        with self.lock:
            with self._get_connection() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        stars INTEGER DEFAULT 0,
                        forks INTEGER DEFAULT 0,
                        description TEXT,
                        url TEXT,
                        homepage TEXT,
                        language TEXT,
                        topics TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        readme_content TEXT,
                        ai_summary TEXT,
                        ai_tech_stack TEXT,
                        ai_use_cases TEXT,
                        ai_difficulty INTEGER,
                        ai_quick_start TEXT,
                        ai_tutorial TEXT,
                        last_scanned TEXT,
                        last_analyzed TEXT,
                        recent_stars_growth INTEGER DEFAULT 0,
                        ai_rag_summary TEXT,
                        ai_visual_summary TEXT,
                        screenshot TEXT
                    );
                    
                    CREATE TABLE IF NOT EXISTS scan_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT,
                        scan_time TEXT,
                        projects_found INTEGER,
                        projects_new INTEGER,
                        status TEXT
                    );
                    
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_category ON projects(category);
                    CREATE TABLE IF NOT EXISTS news_sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL UNIQUE,
                        last_scanned TEXT,
                        created_at TEXT
                    );
                """)
                conn.commit()

                # Migrations (idempotent checks)
                try:
                    conn.execute("ALTER TABLE projects ADD COLUMN screenshot TEXT")
                    conn.commit()
                except:
                    pass
                    
                try:
                    conn.execute("ALTER TABLE projects ADD COLUMN ai_visual_summary TEXT")
                    conn.commit()
                except:
                    pass

                try:
                    conn.execute("ALTER TABLE projects ADD COLUMN ai_rag_summary TEXT")
                    conn.commit()
                except:
                    pass
    
    def upsert_project(self, project: dict):
        """插入或更新项目"""
        now = datetime.now().isoformat()
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO projects (
                        id, name, full_name, category, stars, forks, 
                        description, url, homepage, language, topics,
                        created_at, updated_at, last_scanned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        stars = excluded.stars,
                        forks = excluded.forks,
                        description = excluded.description,
                        updated_at = excluded.updated_at,
                        last_scanned = excluded.last_scanned
                """, (
                    project['id'], project['name'], project['full_name'],
                    project['category'], project['stars'], project['forks'],
                    project.get('description'), project['url'],
                    project.get('homepage'), project.get('language'),
                    json.dumps(project.get('topics', [])),
                    project.get('created_at'), project.get('updated_at'), now
                ))
                conn.commit()
        
    def project_exists(self, project_id: str) -> bool:
        """检查项目是否存在"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,))
            return cursor.fetchone() is not None

    def add_news_source(self, name: str, url: str):
        """添加新闻源"""
        now = datetime.now().isoformat()
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("INSERT OR IGNORE INTO news_sources (name, url, created_at) VALUES (?, ?, ?)", (name, url, now))
                conn.commit()

    def get_news_sources(self):
        """获取所有新闻源"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM news_sources ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_news_source(self, source_id: int):
        """删除新闻源"""
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM news_sources WHERE id = ?", (source_id,))
                conn.commit()

    def update_news_source_scan_time(self, source_id: int):
        """更新新闻源扫描时间"""
        now = datetime.now().isoformat()
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("UPDATE news_sources SET last_scanned = ? WHERE id = ?", (now, source_id))
                conn.commit()

    def update_screenshot(self, project_id: str, path: str):
        """更新截图路径"""
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("UPDATE projects SET screenshot = ? WHERE id = ?", (path, project_id))
                conn.commit()
    
    def update_ai_analysis(self, project_id: str, analysis: dict):
        """更新 AI 分析结果"""
        now = datetime.now().isoformat()
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE projects SET
                        ai_summary = ?,
                        ai_tech_stack = ?,
                        ai_use_cases = ?,
                        ai_difficulty = ?,
                        ai_quick_start = ?,
                        ai_tutorial = ?,
                        ai_visual_summary = ?,
                        ai_rag_summary = ?,
                        last_analyzed = ?
                    WHERE id = ?
                """, (
                    analysis.get('summary'),
                    json.dumps(analysis.get('tech_stack', [])),
                    json.dumps(analysis.get('use_cases', [])),
                    analysis.get('difficulty'),
                    analysis.get('quick_start'),
                    analysis.get('tutorial'),
                    analysis.get('visual_summary'),
                    analysis.get('rag_summary'),
                    now, project_id
                ))
                conn.commit()
    
    def get_projects_by_category(self, category: str, limit: int = 30):
        """按分类获取项目，按星标排序"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM projects 
                WHERE category = ? 
                ORDER BY stars DESC 
                LIMIT ?
            """, (category, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_categories_summary(self):
        """获取所有分类的摘要"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count, MAX(stars) as top_stars
                FROM projects GROUP BY category
            """)
            return {row['category']: dict(row) for row in cursor.fetchall()}
    
    def get_projects_needing_analysis(self, limit: int = 10):
        """获取需要 AI 分析的项目"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM projects 
                WHERE ai_summary IS NULL
                ORDER BY stars DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def log_scan(self, category: str, found: int, new: int, status: str):
        """记录扫描历史"""
        now = datetime.now().isoformat()
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO scan_history (category, scan_time, projects_found, projects_new, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (category, now, found, new, status))
                conn.commit()
    
    def get_pending_count(self) -> int:
        """获取待分析项目数量"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM projects 
                WHERE ai_summary IS NULL OR ai_tutorial IS NULL
            """)
            return cursor.fetchone()[0]
    
    def search_projects(self, query: str, limit: int = 10):
        """简单的全文搜索"""
        keywords = query.split()
        if not keywords:
            return []
        
        conditions = []
        params = []
        for kw in keywords:
            like_term = f"%{kw}%"
            conditions.append("""(
                name LIKE ? OR 
                description LIKE ? OR 
                ai_summary LIKE ? OR 
                ai_use_cases LIKE ? OR
                ai_tutorial LIKE ?
            )""")
            params.extend([like_term] * 5)
            
        sql = f"SELECT * FROM projects WHERE {' AND '.join(conditions)} ORDER BY stars DESC LIMIT ?"
        params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
            
    def get_project(self, project_id: str):
        """获取单个项目详情"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_project(self, project_id: str):
        """删除项目"""
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                conn.commit()

    def get_tutorial(self, project_id: str):
        """获取项目教程"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT ai_tutorial FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return row['ai_tutorial'] if row else None
            
    def get_stats(self):
        """获取统计信息"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_projects,
                    COUNT(ai_summary) as analyzed_projects,
                    SUM(stars) as total_stars
                FROM projects
            """)
            row = cursor.fetchone()
            return {
                "total_projects": row[0],
                "analyzed_projects": row[1],
                "total_stars": row[2] or 0
            }

    def get_all_projects(self):
        """获取所有项目"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects ORDER BY stars DESC")
            return [dict(row) for row in cursor.fetchall()]

        
    def clear_database(self):
        """清空数据库"""
        with self.lock:
            with self._get_connection() as conn:
                conn.executescript("""
                    DELETE FROM projects;
                    DELETE FROM scan_history;
                    DELETE FROM news_sources;
                    DELETE FROM sqlite_sequence;
                """)
                conn.commit()

    def close(self):
        """兼容性方法，不做任何事，因为连接按需创建"""
        pass

    def get_setting(self, key: str, default: str = None) -> str:
        """获取设置"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row['value'] if row else default
        except:
            return default
        
    def set_setting(self, key: str, value: str):
        """保存设置"""
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
                conn.commit()

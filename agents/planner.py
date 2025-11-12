"""Planner Agent - Creates adaptive revision schedules"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from utils.llm_utils import call_llm, parse_json_response
from utils.prompts import PLANNER_PROMPT
from utils.database import StudyDatabase
import config
import json
import os


class PlannerAgent:
    """Agent responsible for creating revision plans"""
    
    def __init__(self):
        self.revision_intervals = config.DEFAULT_REVISION_INTERVALS
        self.db = StudyDatabase()
    
    def create_revision_plan(self, topics: List[Dict], current_date: datetime = None) -> Dict:
        """
        Create a revision plan based on topics.
        
        Args:
            topics: List of topic dictionaries
            current_date: Starting date for the plan
            
        Returns:
            Revision plan dictionary
        """
        if current_date is None:
            current_date = datetime.now()
        
        # Format topics for prompt
        topics_text = "\n".join([
            f"- {t.get('topic', 'Unknown Topic')}: {', '.join(t.get('key_concepts', [])[:3])}"
            for t in topics[:20]  # Limit to 20 topics
        ])
        
        prompt = PLANNER_PROMPT.format(
            topics=topics_text,
            current_date=current_date.strftime("%Y-%m-%d")
        )
        
        try:
            # Planner agent uses Groq LLaMA 3.1 70B
            response = call_llm(prompt, provider="groq")
            plan = parse_json_response(response)
            
            # Validate and enhance plan
            if isinstance(plan, dict) and 'topics' in plan:
                # Ensure dates are valid
                for topic_plan in plan['topics']:
                    topic_plan = self._validate_topic_plan(topic_plan, current_date)
                
                return plan
            else:
                # Fallback: create simple plan
                return self._create_simple_plan(topics, current_date)
        
        except Exception as e:
            print(f"Error creating revision plan: {str(e)}")
            return self._create_simple_plan(topics, current_date)
    
    def _validate_topic_plan(self, topic_plan: Dict, current_date: datetime) -> Dict:
        """Validate and fix topic plan dates"""
        try:
            # Parse first revision date
            first_rev = datetime.strptime(topic_plan.get('first_revision', ''), "%Y-%m-%d")
            if first_rev < current_date:
                first_rev = current_date + timedelta(days=1)
                topic_plan['first_revision'] = first_rev.strftime("%Y-%m-%d")
            
            # Generate subsequent revisions
            subsequent = []
            last_date = first_rev
            for interval in self.revision_intervals[1:]:
                next_date = last_date + timedelta(days=interval)
                subsequent.append(next_date.strftime("%Y-%m-%d"))
                last_date = next_date
            
            topic_plan['subsequent_revisions'] = subsequent
        except:
            # If parsing fails, use default schedule
            first_rev = current_date + timedelta(days=1)
            topic_plan['first_revision'] = first_rev.strftime("%Y-%m-%d")
            subsequent = []
            last_date = first_rev
            for interval in self.revision_intervals[1:]:
                next_date = last_date + timedelta(days=interval)
                subsequent.append(next_date.strftime("%Y-%m-%d"))
                last_date = next_date
            topic_plan['subsequent_revisions'] = subsequent
        
        return topic_plan
    
    def _create_simple_plan(self, topics: List[Dict], current_date: datetime) -> Dict:
        """Create a simple revision plan without LLM"""
        plan_topics = []
        
        for i, topic in enumerate(topics[:15]):  # Limit to 15 topics
            topic_name = topic.get('topic', f'Topic {i+1}')
            first_rev = current_date + timedelta(days=1 + i)
            
            subsequent = []
            last_date = first_rev
            for interval in self.revision_intervals[1:]:
                next_date = last_date + timedelta(days=interval)
                subsequent.append(next_date.strftime("%Y-%m-%d"))
                last_date = next_date
            
            plan_topics.append({
                "topic_name": topic_name,
                "difficulty": "Medium",
                "importance": "Medium",
                "first_revision": first_rev.strftime("%Y-%m-%d"),
                "subsequent_revisions": subsequent,
                "estimated_study_time": "30 minutes"
            })
        
        return {
            "topics": plan_topics,
            "total_topics": len(plan_topics),
            "study_plan_duration": "14 days"
        }
    
    def get_upcoming_revisions(self, plan: Dict, days_ahead: int = 7) -> List[Dict]:
        """
        Get revisions scheduled for the next N days.
        
        Args:
            plan: Revision plan dictionary
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming revision tasks
        """
        upcoming = []
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)
        
        for topic_plan in plan.get('topics', []):
            # Check first revision
            first_rev_str = topic_plan.get('first_revision', '')
            if first_rev_str:
                try:
                    first_rev = datetime.strptime(first_rev_str, "%Y-%m-%d")
                    if today <= first_rev <= end_date:
                        upcoming.append({
                            "topic": topic_plan.get('topic_name', 'Unknown'),
                            "date": first_rev_str,
                            "type": "First Revision",
                            "estimated_time": topic_plan.get('estimated_study_time', '30 minutes')
                        })
                except:
                    pass
            
            # Check subsequent revisions
            for rev_date_str in topic_plan.get('subsequent_revisions', []):
                try:
                    rev_date = datetime.strptime(rev_date_str, "%Y-%m-%d")
                    if today <= rev_date <= end_date:
                        upcoming.append({
                            "topic": topic_plan.get('topic_name', 'Unknown'),
                            "date": rev_date_str,
                            "type": "Revision",
                            "estimated_time": topic_plan.get('estimated_study_time', '30 minutes')
                        })
                except:
                    pass
        
        # Sort by date
        upcoming.sort(key=lambda x: x['date'])
        return upcoming
    
    def save_plan(self, plan: Dict, file_id: Optional[int] = None, filename: str = "planner.json"):
        """
        Save revision plan to database and JSON file (for backup).
        
        Args:
            plan: Revision plan dictionary
            file_id: Database file ID (optional)
            filename: Output filename for JSON backup
        """
        # Save to SQLite database if file_id provided
        if file_id:
            self.db.save_revision_plan(file_id, plan)
        
        # Also save to JSON for backup/compatibility
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        
        filepath = os.path.join("outputs", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
    
    def load_plan(self, file_id: Optional[int] = None, filename: str = "planner.json") -> Dict:
        """
        Load revision plan from database or JSON file.
        
        Args:
            file_id: Database file ID (optional, if provided loads from DB)
            filename: Input filename for JSON fallback
            
        Returns:
            Revision plan dictionary
        """
        # Try database first if file_id provided
        if file_id:
            db_plan = self.db.get_revision_plan(file_id)
            if db_plan:
                return db_plan
        
        # Fallback to JSON
        filepath = os.path.join("outputs", filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


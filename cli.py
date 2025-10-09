#!/usr/bin/env python3
"""
AI Story Agent CLI - Enhanced command-line interface
Supports both standalone mode and API backend mode
"""

import os
import sys
import json
import random
import argparse
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Symbols:
    """Unicode symbols for cross-platform compatibility"""
    SUCCESS = '[OK]'
    WARNING = '[!]'
    ERROR = '[X]'
    INFO = '[i]'
    GAME = '[GAME]'

class AIStoryCLI:
    """Enhanced CLI for AI Story Agent"""
    
    def __init__(self, api_mode: bool = False, api_url: str = "http://localhost:8000", api_token: str = None):
        self.api_mode = api_mode
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token or os.getenv("API_TOKEN")
        self.session_id = None
        self.session_data = None
        
        # Session storage paths
        self.sessions_dir = "./sessions"
        self.story_memory_dir = "./story_memory"
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.story_memory_dir, exist_ok=True)
    
    def print_colored(self, text: str, color: str = Colors.ENDC):
        """Print colored text"""
        print(f"{color}{text}{Colors.ENDC}")
    
    def print_header(self, text: str):
        """Print header text"""
        self.print_colored(f"\n{'='*60}", Colors.HEADER)
        self.print_colored(f"{Symbols.GAME} {text}", Colors.BOLD + Colors.HEADER)
        self.print_colored(f"{'='*60}", Colors.HEADER)
    
    def print_success(self, text: str):
        """Print success message"""
        self.print_colored(f"{Symbols.SUCCESS} {text}", Colors.OKGREEN)
    
    def print_warning(self, text: str):
        """Print warning message"""
        self.print_colored(f"{Symbols.WARNING} {text}", Colors.WARNING)
    
    def print_error(self, text: str):
        """Print error message"""
        self.print_colored(f"{Symbols.ERROR} {text}", Colors.FAIL)
    
    def print_info(self, text: str):
        """Print info message"""
        self.print_colored(f"{Symbols.INFO} {text}", Colors.OKCYAN)
    
    def check_api_connection(self) -> bool:
        """Check if API backend is available"""
        try:
            headers = {}
            if self.api_token:
                headers["X-API-Token"] = self.api_token
            
            response = requests.get(f"{self.api_url}/health", headers=headers, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def api_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request with error handling"""
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["X-API-Token"] = self.api_token
            
            url = f"{self.api_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to API at {self.api_url}. Is the server running?")
        except requests.exceptions.Timeout:
            raise Exception("API request timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid API token")
            elif e.response.status_code == 404:
                raise Exception("Session not found")
            else:
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def list_sessions(self) -> List[Dict]:
        """List available sessions"""
        if self.api_mode:
            try:
                result = self.api_request("GET", "/list_sessions")
                sessions = result.get("sessions", [])
                # Add source indicator for API sessions
                for session in sessions:
                    session['source'] = 'API'
                return sessions
            except Exception as e:
                self.print_warning(f"API session listing failed: {e}")
                self.print_info("Falling back to local files")
        
        sessions = []
        
        # Check API session directory first (data/sessions/)
        api_sessions_dir = os.path.join("data", "sessions")
        if os.path.exists(api_sessions_dir):
            for filename in os.listdir(api_sessions_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(api_sessions_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        session_id = data.get('session_id', filename[:-5])
                        sessions.append({
                            'session_id': session_id,
                            'session_name': data.get('session_name', 'Unnamed Session'),
                            'created_at': data.get('created_at', 'Unknown'),
                            'history_count': len(data.get('history', [])),
                            'source': 'API Storage',
                            'filepath': filepath
                        })
                    except Exception:
                        continue
        
        # Check CLI session directories
        for session_dir in [self.sessions_dir, self.story_memory_dir]:
            if os.path.exists(session_dir):
                for filename in os.listdir(session_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(session_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            # Extract session info
                            session_id = data.get('id') or data.get('session_id', filename.replace('.json', ''))
                            session_name = data.get('session_name', 'Unnamed Session')
                            created_at = data.get('created_at', 'Unknown')
                            history_count = len(data.get('history', []))
                            
                            sessions.append({
                                'session_id': session_id,
                                'session_name': session_name,
                                'created_at': created_at,
                                'history_count': history_count,
                                'source': 'Local',
                                'filepath': filepath
                            })
                        except Exception as e:
                            self.print_warning(f"Could not read session file {filename}: {e}")
        
        return sorted(sessions, key=lambda x: x['created_at'], reverse=True)
    
    def create_session(self, session_name: str = None, seed_text: str = None) -> str:
        """Create a new session"""
        if not session_name:
            session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if not seed_text:
            seed_text = "You wake up in a misty forest. The air is heavy with fog. In the distance, a flickering lantern glows faintly."
        
        if self.api_mode:
            try:
                data = {
                    "session_name": session_name,
                    "seed_text": seed_text
                }
                result = self.api_request("POST", "/create_session", data)
                self.session_id = result["session_id"]
                self.session_data = result
                self.print_success(f"Created session: {self.session_id}")
                return self.session_id
            except Exception as e:
                self.print_error(f"Failed to create session via API: {e}")
                self.print_info("Falling back to standalone mode")
                self.api_mode = False
        
        # Standalone mode
        self.session_id = str(random.randint(10000, 99999))
        self.session_data = {
            "id": self.session_id,
            "session_name": session_name,
            "created_at": datetime.now().isoformat(),
            "history": [seed_text],
            "world": {
                "location": "",
                "inventory": [],
                "npcs": {},
                "notes": ""
            }
        }
        
        # Save to file
        filepath = os.path.join(self.sessions_dir, f"story_memory_{self.session_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        self.print_success(f"Created session: {self.session_id}")
        return self.session_id
    
    def load_session(self, session_id: str) -> bool:
        """Load an existing session"""
        if self.api_mode:
            try:
                result = self.api_request("GET", f"/get_session?session_id={session_id}")
                self.session_id = session_id
                self.session_data = result
                self.print_success(f"Loaded session: {session_id}")
                return True
            except Exception as e:
                self.print_error(f"Failed to load session via API: {e}")
                # Try to load from local files as fallback
                self.print_info("Trying to load from local files...")
        
        # Try API storage directory first
        api_sessions_dir = os.path.join("data", "sessions")
        api_filepath = os.path.join(api_sessions_dir, f"{session_id}.json")
        if os.path.exists(api_filepath):
            try:
                with open(api_filepath, 'r', encoding='utf-8') as f:
                    self.session_data = json.load(f)
                self.session_id = session_id
                self.print_success(f"Loaded session from API storage: {session_id}")
                return True
            except Exception as e:
                self.print_error(f"Failed to read API session file: {e}")
        
        # Try CLI session directories
        for session_dir in [self.sessions_dir, self.story_memory_dir]:
            filepath = os.path.join(session_dir, f"story_memory_{session_id}.json")
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.session_data = json.load(f)
                    self.session_id = session_id
                    self.print_success(f"Loaded session from local storage: {session_id}")
                    return True
                except Exception as e:
                    self.print_error(f"Failed to read local session file: {e}")
                    return False
        
        self.print_error(f"Session {session_id} not found in any storage location")
        return False
    
    def take_action(self, action: str, use_rag: bool = True) -> str:
        """Take an action in the current session"""
        if not self.session_id or not self.session_data:
            raise Exception("No active session")
        
        if self.api_mode:
            try:
                data = {
                    "session_id": self.session_id,
                    "player_action": action,
                    "options": {"use_rag": use_rag}
                }
                result = self.api_request("POST", "/take_action", data)
                
                # Update local session data
                self.session_data["history"].append(result["ai_response"])
                if "world" in result:
                    self.session_data["world"] = result["world"]
                
                return result["ai_response"]
            except Exception as e:
                self.print_error(f"Failed to take action via API: {e}")
                self.print_info("Falling back to standalone mode")
                self.api_mode = False
        
        # Standalone mode - use the original play.py logic
        return self._standalone_take_action(action)
    
    def _standalone_take_action(self, action: str) -> str:
        """Standalone story generation (simplified version)"""
        # This is a simplified version - in a real implementation, you'd want to
        # integrate with the full AI model from your backend
        story_responses = [
            "The wind rustles through the trees as you continue your journey. A mysterious path opens before you.",
            "You feel a strange energy in the air. Something important is about to happen.",
            "The fog begins to clear, revealing ancient ruins in the distance. What secrets do they hold?",
            "A friendly voice calls out from the shadows. Someone is watching over you.",
            "The ground beneath your feet feels different now. You sense you're entering a new realm."
        ]
        
        response = random.choice(story_responses)
        response += "\n\nA) Explore further\nB) Call out for help"
        
        # Update session
        self.session_data["history"].append(f"{action}: {response}")
        
        # Save session
        self.save_session()
        
        return response
    
    def save_session(self):
        """Save current session"""
        if not self.session_data:
            return
        
        if self.api_mode:
            # API mode - session is automatically saved
            return
        
        # Standalone mode - save to file
        filepath = os.path.join(self.sessions_dir, f"story_memory_{self.session_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
    
    def delete_session(self, session_id: str = None) -> bool:
        """Delete a session"""
        target_id = session_id or self.session_id
        
        if not target_id:
            self.print_error("No session ID provided")
            return False
        
        if self.api_mode:
            try:
                self.api_request("POST", f"/delete_session?session_id={target_id}")
                self.print_success(f"Deleted session: {target_id}")
                return True
            except Exception as e:
                self.print_error(f"Failed to delete session via API: {e}")
                return False
        
        # Standalone mode - delete file
        for session_dir in [self.sessions_dir, self.story_memory_dir]:
            filepath = os.path.join(session_dir, f"story_memory_{target_id}.json")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    self.print_success(f"Deleted session: {target_id}")
                    return True
                except Exception as e:
                    self.print_error(f"Failed to delete session file: {e}")
                    return False
        
        self.print_error(f"Session {target_id} not found")
        return False
    
    def show_session_info(self):
        """Display current session information"""
        if not self.session_data:
            self.print_error("No active session")
            return
        
        self.print_header("Session Information")
        self.print_colored(f"Session ID: {self.session_id}", Colors.OKBLUE)
        self.print_colored(f"Session Name: {self.session_data.get('session_name', 'Unnamed')}", Colors.OKBLUE)
        self.print_colored(f"Created: {self.session_data.get('created_at', 'Unknown')}", Colors.OKBLUE)
        self.print_colored(f"History Entries: {len(self.session_data.get('history', []))}", Colors.OKBLUE)
        
        # Show world state
        world = self.session_data.get('world', {})
        if world:
            self.print_colored("\nWorld State:", Colors.BOLD)
            if world.get('location'):
                self.print_colored(f"  Location: {world['location']}", Colors.OKCYAN)
            if world.get('inventory'):
                self.print_colored(f"  Inventory: {', '.join(world['inventory'])}", Colors.OKCYAN)
            if world.get('npcs'):
                npcs = ', '.join(f"{k} ({v})" for k, v in world['npcs'].items())
                self.print_colored(f"  NPCs: {npcs}", Colors.OKCYAN)
            if world.get('notes'):
                self.print_colored(f"  Notes: {world['notes']}", Colors.OKCYAN)
    
    def show_history(self, limit: int = 5):
        """Show recent history"""
        if not self.session_data or not self.session_data.get('history'):
            self.print_error("No history available")
            return
        
        history = self.session_data['history']
        recent = history[-limit:] if limit > 0 else history
        
        self.print_header(f"Recent History (Last {len(recent)} entries)")
        for i, entry in enumerate(recent, 1):
            self.print_colored(f"{i}. {entry}", Colors.OKCYAN)
    
    def interactive_mode(self):
        """Run interactive CLI mode"""
        self.print_header("AI Story Agent CLI")
        
        # Check API connection if in API mode
        if self.api_mode:
            if self.check_api_connection():
                self.print_success("Connected to API backend")
            else:
                self.print_warning("Cannot connect to API backend, switching to standalone mode")
                self.api_mode = False
        
        # Session management
        while True:
            self.print_colored("\n" + "="*50, Colors.HEADER)
            self.print_colored("Session Management", Colors.BOLD)
            print("1. Create new session")
            print("2. Load existing session")
            print("3. List all sessions")
            print("4. Delete session")
            print("5. Start playing (if session loaded)")
            print("6. Exit")
            
            choice = input("\nChoose an option (1-6): ").strip()
            
            if choice == "1":
                session_name = input("Enter session name (or press Enter for default): ").strip()
                seed_text = input("Enter seed text (or press Enter for default): ").strip()
                self.create_session(session_name or None, seed_text or None)
            
            elif choice == "2":
                sessions = self.list_sessions()
                if not sessions:
                    self.print_warning("No sessions found")
                    continue
                
                self.print_colored("\nAvailable sessions:", Colors.BOLD)
                for i, session in enumerate(sessions, 1):
                    source = session.get('source', 'Unknown')
                    source_indicator = " [API]" if source == 'API' else " [Local]"
                    self.print_colored(f"{i}. {session['session_name']} (ID: {session['session_id']}){source_indicator}", Colors.OKBLUE)
                
                try:
                    session_choice = int(input("\nSelect session number: ")) - 1
                    if 0 <= session_choice < len(sessions):
                        self.load_session(sessions[session_choice]['session_id'])
                    else:
                        self.print_error("Invalid selection")
                except ValueError:
                    self.print_error("Please enter a valid number")
            
            elif choice == "3":
                sessions = self.list_sessions()
                if not sessions:
                    self.print_warning("No sessions found")
                else:
                    self.print_colored(f"\nFound {len(sessions)} sessions:", Colors.BOLD)
                    for session in sessions:
                        source = session.get('source', 'Unknown')
                        source_color = Colors.OKGREEN if source == 'API' else Colors.OKCYAN
                        self.print_colored(f"  • {session['session_name']} (ID: {session['session_id']})", Colors.OKBLUE)
                        self.print_colored(f"    Created: {session['created_at']}, Entries: {session['history_count']}", Colors.OKCYAN)
                        self.print_colored(f"    Source: {source}", source_color)
            
            elif choice == "4":
                sessions = self.list_sessions()
                if not sessions:
                    self.print_warning("No sessions found")
                    continue
                
                self.print_colored("\nAvailable sessions:", Colors.BOLD)
                for i, session in enumerate(sessions, 1):
                    source = session.get('source', 'Unknown')
                    source_indicator = " [API]" if source == 'API' else " [Local]"
                    self.print_colored(f"{i}. {session['session_name']} (ID: {session['session_id']}){source_indicator}", Colors.OKBLUE)
                
                try:
                    session_choice = int(input("\nSelect session to delete: ")) - 1
                    if 0 <= session_choice < len(sessions):
                        self.delete_session(sessions[session_choice]['session_id'])
                    else:
                        self.print_error("Invalid selection")
                except ValueError:
                    self.print_error("Please enter a valid number")
            
            elif choice == "5":
                if not self.session_id:
                    self.print_error("No session loaded. Please create or load a session first.")
                    continue
                
                self.play_session()
            
            elif choice == "6":
                self.print_colored("Goodbye!", Colors.OKGREEN)
                break
            
            else:
                self.print_error("Invalid choice. Please select 1-6.")
    
    def play_session(self):
        """Play the current session"""
        if not self.session_id or not self.session_data:
            self.print_error("No active session")
            return
        
        self.print_header("Playing Session")
        self.show_session_info()
        
        # Show initial story
        history = self.session_data.get('history', [])
        if history:
            self.print_colored(f"\n{history[-1]}", Colors.OKCYAN)
        
        self.print_colored("\nCommands:", Colors.BOLD)
        self.print_colored("  • Type your action to continue the story", Colors.OKBLUE)
        self.print_colored("  • 'info' - Show session information", Colors.OKBLUE)
        self.print_colored("  • 'history [n]' - Show last n history entries", Colors.OKBLUE)
        self.print_colored("  • 'save' - Save current session", Colors.OKBLUE)
        self.print_colored("  • 'exit' - Exit to session management", Colors.OKBLUE)
        
        while True:
            try:
                user_input = input(f"\n👉 Your action: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    self.save_session()
                    self.print_success("Session saved. Returning to main menu.")
                    break
                
                elif user_input.lower() == 'info':
                    self.show_session_info()
                    continue
                
                elif user_input.lower().startswith('history'):
                    parts = user_input.split()
                    limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
                    self.show_history(limit)
                    continue
                
                elif user_input.lower() == 'save':
                    self.save_session()
                    self.print_success("Session saved!")
                    continue
                
                elif not user_input:
                    self.print_warning("Please enter an action")
                    continue
                
                # Take action
                self.print_colored("\n🤖 AI Response:", Colors.BOLD)
                try:
                    response = self.take_action(user_input)
                    self.print_colored(response, Colors.OKCYAN)
                except Exception as e:
                    self.print_error(f"Failed to take action: {e}")
                
            except KeyboardInterrupt:
                self.print_colored("\n\nInterrupted by user", Colors.WARNING)
                self.save_session()
                self.print_success("Session saved. Returning to main menu.")
                break
            except EOFError:
                self.print_colored("\n\nGoodbye!", Colors.OKGREEN)
                self.save_session()
                break

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="AI Story Agent CLI")
    parser.add_argument("--api", action="store_true", help="Use API backend mode")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API backend URL")
    parser.add_argument("--api-token", help="API authentication token")
    parser.add_argument("--session-id", help="Load specific session ID")
    parser.add_argument("--create", help="Create new session with given name")
    parser.add_argument("--action", help="Take a single action and exit")
    parser.add_argument("--list-sessions", action="store_true", help="List all sessions and exit")
    parser.add_argument("--delete-session", help="Delete session with given ID and exit")
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = AIStoryCLI(
        api_mode=args.api,
        api_url=args.api_url,
        api_token=args.api_token
    )
    
    try:
        # Handle command-line operations
        if args.list_sessions:
            sessions = cli.list_sessions()
            if sessions:
                print(f"Found {len(sessions)} sessions:")
                for session in sessions:
                    print(f"  • {session['session_name']} (ID: {session['session_id']})")
            else:
                print("No sessions found")
            return
        
        if args.delete_session:
            if cli.delete_session(args.delete_session):
                print(f"Session {args.delete_session} deleted successfully")
            else:
                print(f"Failed to delete session {args.delete_session}")
            return
        
        if args.create:
            session_id = cli.create_session(args.create)
            print(f"Created session: {session_id}")
            return
        
        if args.session_id:
            if cli.load_session(args.session_id):
                if args.action:
                    response = cli.take_action(args.action)
                    print(f"AI Response: {response}")
                else:
                    cli.play_session()
            else:
                print(f"Failed to load session {args.session_id}")
            return
        
        if args.action:
            print("Error: --action requires --session-id")
            return
        
        # Interactive mode
        cli.interactive_mode()
        
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

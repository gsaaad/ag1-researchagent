"""
Sequential Agents with Google ADK - Google Trends Analysis Pipeline
====================================================================
Production-level sequential agent pipeline with FULL LOGGING & MONITORING:
1. Fetches LIVE trending topics from Google Trends RSS feeds
2. Uses AI to analyze and categorize the trending data
3. Generates actionable insights with complete audit trail

Features:
- Comprehensive logging to file and console
- Agent action tracking with timestamps
- Data perception logging (what each agent sees)
- Decision audit trail
- Performance metrics

Google Trends Categories:
- Entertainment (category 4)
- Games (category 6)
- Shopping (category 16)
"""

import asyncio
import json
import logging
import os
from typing import AsyncGenerator
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import SequentialAgent, LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# ============================================================================
# LOGGING & MONITORING SYSTEM
# ============================================================================

class AgentLogger:
    """
    Comprehensive logging system for agent pipeline.
    Tracks all actions, perceptions, and decisions.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create unique log file for this run
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"pipeline_run_{self.run_id}.log"
        self.json_log_file = self.log_dir / f"pipeline_data_{self.run_id}.json"
        
        # In-memory log storage for JSON export
        self.run_data = {
            "run_id": self.run_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "agents": [],
            "events": [],
            "metrics": {
                "total_agents": 0,
                "successful_agents": 0,
                "failed_agents": 0,
                "total_data_bytes": 0,
            }
        }
        
        # Setup file logger
        self._setup_file_logger()
        
        print(f"\n📁 Log files:")
        print(f"   📝 Text log: {self.log_file}")
        print(f"   📊 JSON log: {self.json_log_file}")
    
    def _setup_file_logger(self):
        """Configure file-based logging."""
        self.file_logger = logging.getLogger(f"AgentPipeline_{self.run_id}")
        self.file_logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        
        # Formatter with timestamp
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        self.file_logger.addHandler(fh)
        
        # Log header
        self.file_logger.info("="*80)
        self.file_logger.info("GOOGLE TRENDS PIPELINE - RUN LOG")
        self.file_logger.info(f"Run ID: {self.run_id}")
        self.file_logger.info("="*80)
    
    def log_agent_start(self, agent_name: str, description: str = ""):
        """Log when an agent starts executing."""
        timestamp = datetime.now().isoformat()
        
        agent_entry = {
            "name": agent_name,
            "start_time": timestamp,
            "end_time": None,
            "status": "running",
            "input_data": None,
            "output_data": None,
            "perceptions": [],
            "actions": [],
            "errors": [],
        }
        self.run_data["agents"].append(agent_entry)
        self.run_data["metrics"]["total_agents"] += 1
        
        self.file_logger.info(f"[AGENT START] {agent_name}")
        self.file_logger.info(f"  Description: {description}")
        
        print(f"\n🚀 [{timestamp[11:19]}] Agent Starting: {agent_name}")
    
    def log_agent_perception(self, agent_name: str, perception_type: str, data: any):
        """Log what data an agent perceives/receives."""
        timestamp = datetime.now().isoformat()
        
        # Find current agent
        for agent in reversed(self.run_data["agents"]):
            if agent["name"] == agent_name:
                perception = {
                    "timestamp": timestamp,
                    "type": perception_type,
                    "data_summary": self._summarize_data(data),
                    "data_size": len(str(data)) if data else 0,
                }
                agent["perceptions"].append(perception)
                agent["input_data"] = self._summarize_data(data)
                self.run_data["metrics"]["total_data_bytes"] += perception["data_size"]
                break
        
        self.file_logger.info(f"[PERCEPTION] {agent_name} received {perception_type}")
        self.file_logger.debug(f"  Data size: {len(str(data)) if data else 0} bytes")
        
        print(f"   👁️ Perceived: {perception_type} ({len(str(data)) if data else 0} bytes)")
    
    def log_agent_action(self, agent_name: str, action: str, details: str = ""):
        """Log an action taken by an agent."""
        timestamp = datetime.now().isoformat()
        
        for agent in reversed(self.run_data["agents"]):
            if agent["name"] == agent_name:
                action_entry = {
                    "timestamp": timestamp,
                    "action": action,
                    "details": details,
                }
                agent["actions"].append(action_entry)
                break
        
        self.file_logger.info(f"[ACTION] {agent_name}: {action}")
        if details:
            self.file_logger.debug(f"  Details: {details[:200]}...")
        
        print(f"   ⚡ Action: {action}")
    
    def log_agent_output(self, agent_name: str, output: any):
        """Log the output produced by an agent."""
        timestamp = datetime.now().isoformat()
        
        for agent in reversed(self.run_data["agents"]):
            if agent["name"] == agent_name:
                agent["output_data"] = self._summarize_data(output)
                break
        
        output_size = len(str(output)) if output else 0
        self.file_logger.info(f"[OUTPUT] {agent_name} produced {output_size} bytes")
        
        print(f"   📤 Output: {output_size} bytes")
    
    def log_agent_complete(self, agent_name: str, success: bool = True, error: str = None):
        """Log when an agent completes."""
        timestamp = datetime.now().isoformat()
        
        for agent in reversed(self.run_data["agents"]):
            if agent["name"] == agent_name:
                agent["end_time"] = timestamp
                agent["status"] = "success" if success else "failed"
                if error:
                    agent["errors"].append(error)
                break
        
        if success:
            self.run_data["metrics"]["successful_agents"] += 1
            self.file_logger.info(f"[AGENT COMPLETE] {agent_name} ✅")
            print(f"   ✅ Completed successfully")
        else:
            self.run_data["metrics"]["failed_agents"] += 1
            self.file_logger.error(f"[AGENT FAILED] {agent_name} ❌ - {error}")
            print(f"   ❌ Failed: {error}")
    
    def log_event(self, event_type: str, data: dict):
        """Log a general pipeline event."""
        timestamp = datetime.now().isoformat()
        
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "data": data,
        }
        self.run_data["events"].append(event)
        
        self.file_logger.info(f"[EVENT] {event_type}: {json.dumps(data, default=str)[:200]}")
    
    def _summarize_data(self, data) -> str:
        """Create a summary of data for logging."""
        if data is None:
            return "None"
        
        data_str = str(data)
        if len(data_str) > 500:
            return data_str[:500] + f"... ({len(data_str)} total chars)"
        return data_str
    
    def finalize(self):
        """Finalize logging and save JSON report."""
        self.run_data["end_time"] = datetime.now().isoformat()
        
        # Calculate duration
        start = datetime.fromisoformat(self.run_data["start_time"])
        end = datetime.fromisoformat(self.run_data["end_time"])
        duration = (end - start).total_seconds()
        self.run_data["metrics"]["duration_seconds"] = duration
        
        # Save JSON log
        with open(self.json_log_file, "w", encoding="utf-8") as f:
            json.dump(self.run_data, f, indent=2, default=str)
        
        self.file_logger.info("="*80)
        self.file_logger.info("PIPELINE RUN COMPLETE")
        self.file_logger.info(f"Duration: {duration:.2f} seconds")
        self.file_logger.info(f"Agents: {self.run_data['metrics']['successful_agents']}/{self.run_data['metrics']['total_agents']} successful")
        self.file_logger.info("="*80)
        
        print(f"\n📊 Run Metrics:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Agents: {self.run_data['metrics']['successful_agents']}/{self.run_data['metrics']['total_agents']} successful")
        print(f"   Data processed: {self.run_data['metrics']['total_data_bytes']:,} bytes")
        print(f"\n💾 Logs saved to: {self.log_dir}/")


# Global logger instance
agent_logger: AgentLogger = None


# ============================================================================
# CONFIGURATION
# ============================================================================

GEMINI_MODEL = "gemini-2.0-flash-exp"
APP_NAME = "google_trends_pipeline"
USER_ID = "trends_analyst"
SESSION_ID = "session_trends"

# Google Trends RSS feeds - These contain LIVE data (no JS rendering needed)
# Using Google Trends Daily Trends API endpoint that returns actual data
TRENDS_SOURCES = {
    "entertainment": {
        "rss_url": "https://trends.google.com/trending/rss?geo=US",
        "search_url": "https://trends.google.com/trending?geo=US&hours=48&category=4",
        "name": "Entertainment",
        "emoji": "🎬",
        "category_id": 4,
    },
    "games": {
        "rss_url": "https://trends.google.com/trending/rss?geo=US",
        "search_url": "https://trends.google.com/trending?geo=US&hours=48&category=6",
        "name": "Games", 
        "emoji": "🎮",
        "category_id": 6,
    },
    "shopping": {
        "rss_url": "https://trends.google.com/trending/rss?geo=US",
        "search_url": "https://trends.google.com/trending?geo=US&hours=48&category=16",
        "name": "Shopping",
        "emoji": "🛒",
        "category_id": 16,
    },
}


# ============================================================================
# AGENT 1: Live Data Fetcher (with logging) - SELENIUM VERSION FOR EXACT DATA
# ============================================================================

class LiveTrendsFetcher(BaseAgent):
    """
    Fetches LIVE trending data directly from Google Trends pages.
    Uses Selenium to render JavaScript and get EXACT data shown on the page.
    Fetches multiple URL variations for comprehensive coverage:
    - 48 hours active (Entertainment, Games, Shopping)
    - 48 hours active (all categories)
    - 168 hours (7 days) active
    - 168 hours active sorted by recency
    """
    
    name: str = "LiveTrendsFetcher"
    description: str = "Fetches live trending data from Google Trends with Selenium for accurate data."

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Fetch live trends with comprehensive logging."""
        global agent_logger
        
        agent_logger.log_agent_start(
            self.name, 
            "Fetching live Google Trends data using Selenium (renders JavaScript)"
        )
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            import time
            import re
            
            agent_logger.log_agent_action(self.name, "Initializing Chrome WebDriver (headless)")
            
            # Setup headless Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            print("\n" + "="*70)
            print("📡 FETCHING LIVE GOOGLE TRENDS - COMPREHENSIVE COVERAGE")
            print("="*70)
            print("\n🌐 Starting headless Chrome browser...")
            
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            fetched_data = {
                "fetch_time": datetime.now().isoformat(),
                "data_source": "selenium_direct",
                "geo": "US",
                "categories": {},
                "timeframes": {},
                "all_trends_flat": [],  # Flat list for easy LLM access
            }
            
            # ============================================================
            # URL CONFIGURATIONS - Comprehensive coverage
            # ============================================================
            url_configs = [
                # Category-specific 48-hour active trends
                {
                    "key": "entertainment_48h",
                    "name": "Entertainment (48h Active)",
                    "emoji": "🎬",
                    "url": "https://trends.google.com/trending?geo=US&hours=48&status=active&category=4",
                    "timeframe": "48h",
                    "category": "Entertainment",
                },
                {
                    "key": "games_48h",
                    "name": "Games (48h Active)",
                    "emoji": "🎮",
                    "url": "https://trends.google.com/trending?geo=US&hours=48&status=active&category=6",
                    "timeframe": "48h",
                    "category": "Games",
                },
                {
                    "key": "shopping_48h",
                    "name": "Shopping (48h Active)",
                    "emoji": "🛒",
                    "url": "https://trends.google.com/trending?geo=US&hours=48&status=active&category=16",
                    "timeframe": "48h",
                    "category": "Shopping",
                },
                # All categories - different timeframes
                {
                    "key": "all_48h_active",
                    "name": "All Categories (48h Active)",
                    "emoji": "🔥",
                    "url": "https://trends.google.com/trending?geo=US&hours=48&status=active",
                    "timeframe": "48h",
                    "category": "All",
                },
                {
                    "key": "all_168h_active",
                    "name": "All Categories (7-Day Active)",
                    "emoji": "📅",
                    "url": "https://trends.google.com/trending?geo=US&hours=168&status=active",
                    "timeframe": "168h",
                    "category": "All",
                },
                {
                    "key": "all_168h_recent",
                    "name": "All Categories (7-Day Recent)",
                    "emoji": "🆕",
                    "url": "https://trends.google.com/trending?geo=US&hours=168&status=active&sort=recency",
                    "timeframe": "168h_recent",
                    "category": "All",
                },
            ]
            
            def extract_trends_from_page(driver, page_text):
                """Extract trends using multiple methods."""
                trends = []
                
                # Method 1: Find trend links
                try:
                    trend_elements = driver.find_elements(
                        By.CSS_SELECTOR, 
                        "a[href*='trends.google.com/trends/explore']"
                    )
                    for elem in trend_elements[:30]:
                        title = elem.text.strip()
                        if title and len(title) > 1 and len(title) < 100:
                            parent = elem.find_element(By.XPATH, "./../..")
                            parent_text = parent.text
                            traffic_match = re.search(r'(\d+[KMB]\+?|\d+,\d+)', parent_text)
                            traffic = traffic_match.group(1) if traffic_match else "N/A"
                            if title not in [t['title'] for t in trends]:
                                trends.append({"title": title, "traffic": traffic})
                except:
                    pass
                
                # Method 2: Parse text patterns
                if len(trends) < 5:
                    lines = page_text.split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line and len(line) > 2 and len(line) < 100:
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                if re.match(r'^\d+[KMB]?\+?$', next_line):
                                    if line not in [t['title'] for t in trends]:
                                        trends.append({"title": line, "traffic": next_line})
                
                # Method 3: JSON in scripts
                if len(trends) < 5:
                    try:
                        scripts = driver.find_elements(By.TAG_NAME, "script")
                        for script in scripts:
                            content = script.get_attribute("innerHTML")
                            if content and "trendingSearchesSummary" in content:
                                titles = re.findall(r'"title"\s*:\s*"([^"]+)"', content)
                                traffics = re.findall(r'"formattedTraffic"\s*:\s*"([^"]+)"', content)
                                for j, title in enumerate(titles[:20]):
                                    if title not in [t['title'] for t in trends]:
                                        traffic = traffics[j] if j < len(traffics) else "N/A"
                                        trends.append({"title": title, "traffic": traffic})
                    except:
                        pass
                
                return trends
            
            # Fetch each URL
            for config in url_configs:
                key = config["key"]
                name = config["name"]
                emoji = config["emoji"]
                url = config["url"]
                timeframe = config["timeframe"]
                category = config["category"]
                
                agent_logger.log_agent_action(self.name, f"Fetching {name}", url)
                print(f"\n{emoji} Fetching {name}...")
                print(f"   URL: {url}")
                
                try:
                    driver.get(url)
                    agent_logger.log_agent_action(self.name, f"Waiting for {name} to render")
                    time.sleep(4)
                    
                    try:
                        WebDriverWait(driver, 8).until(
                            EC.presence_of_element_located((By.TAG_NAME, "table"))
                        )
                    except:
                        pass
                    
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    trends = extract_trends_from_page(driver, page_text)
                    
                    # Filter out UI elements
                    trends = [t for t in trends if t['title'].lower() not in 
                              ['rows per page', 'next', 'previous', 'trending', 'explore']]
                    
                    # Store in categories
                    fetched_data["categories"][key] = {
                        "name": name,
                        "emoji": emoji,
                        "url": url,
                        "timeframe": timeframe,
                        "category": category,
                        "trends_count": len(trends),
                        "trends": trends[:20],
                    }
                    
                    # Add to flat list with source info
                    for t in trends[:20]:
                        flat_entry = {
                            "title": t["title"],
                            "traffic": t["traffic"],
                            "source": key,
                            "category": category,
                            "timeframe": timeframe,
                        }
                        if flat_entry["title"] not in [x["title"] for x in fetched_data["all_trends_flat"]]:
                            fetched_data["all_trends_flat"].append(flat_entry)
                    
                    agent_logger.log_agent_action(
                        self.name,
                        f"Extracted {len(trends)} trends from {name}"
                    )
                    
                    print(f"   ✅ Found {len(trends)} trends")
                    for t in trends[:6]:
                        print(f"      • {t['title']} ({t['traffic']})")
                    
                except Exception as e:
                    agent_logger.log_agent_action(self.name, f"Error fetching {name}: {e}")
                    print(f"   ❌ Error: {e}")
            
            # Cleanup
            driver.quit()
            agent_logger.log_agent_action(self.name, "Closed WebDriver")
            
            # Create summary for LLM agents
            fetched_data["summary"] = {
                "total_unique_trends": len(fetched_data["all_trends_flat"]),
                "sources_fetched": len(url_configs),
                "fetch_time": fetched_data["fetch_time"],
            }
            
            # Store data for next agent
            context.session.state["live_trends_data"] = fetched_data
            
            # Also create a simple text list for the LLM to use
            trends_text_list = "\n".join([
                f"- {t['title']} ({t['traffic']}) [{t['category']}]" 
                for t in fetched_data["all_trends_flat"][:50]
            ])
            context.session.state["trends_text_list"] = trends_text_list
            
            agent_logger.log_agent_output(self.name, fetched_data)
            agent_logger.log_agent_complete(self.name, success=True)
            
            total_trends = len(fetched_data["all_trends_flat"])
            
            print(f"\n{'='*70}")
            print(f"📊 FETCH SUMMARY")
            print(f"   Total unique trends: {total_trends}")
            print(f"   Sources: {len(url_configs)}")
            print(f"{'='*70}")
            
            content = types.Content(
                role="model",
                parts=[types.Part(text=f"✅ Fetched {total_trends} unique live trends from {len(url_configs)} Google Trends sources")]
            )
            yield Event(author=self.name, content=content)
            
        except ImportError as e:
            error_msg = f"Missing package. Install: pip install selenium webdriver-manager\nError: {e}"
            agent_logger.log_agent_complete(self.name, success=False, error=error_msg)
            print(f"\n❌ {error_msg}")
            content = types.Content(role="model", parts=[types.Part(text=f"❌ {error_msg}")])
            yield Event(author=self.name, content=content)
            
        except Exception as e:
            agent_logger.log_agent_complete(self.name, success=False, error=str(e))
            print(f"\n❌ Error: {e}")
            content = types.Content(role="model", parts=[types.Part(text=f"❌ Error: {e}")])
            yield Event(author=self.name, content=content)


# ============================================================================
# AGENT 2: Trend Categorizer (LLM Agent with logging wrapper)
# ============================================================================

class LoggingLlmAgent(LlmAgent):
    """LLM Agent wrapper that adds logging capabilities."""
    
    def __init__(self, *args, log_name: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_name = log_name or self.name


# Create the categorizer agent
trend_categorizer = LlmAgent(
    name="TrendCategorizer",
    model=GEMINI_MODEL,
    description="Categorizes and organizes the live trends data.",
    instruction="""You are a data organization assistant. Your job is to organize the fetched Google Trends data.

TODAY'S DATE: December 17, 2025

The session state contains:
- 'live_trends_data': Full structured data with categories
- 'trends_text_list': Simple text list of all trends

HERE IS THE ACTUAL DATA YOU MUST USE (from trends_text_list):
{trends_text_list}

YOUR TASK:
1. Read the trends from the list above
2. Organize them by category (Entertainment, Games, Shopping, All)
3. Sort by traffic volume (500K > 200K > 100K > 50K > 20K > 10K > 5K > 2K > 1K)

OUTPUT FORMAT - Return ONLY this JSON using the ACTUAL trends above:
```json
{
  "date": "2025-12-17",
  "data_freshness": "48h-168h active trends",
  "top_15_by_traffic": [
    {"title": "EXACT NAME FROM LIST", "traffic": "EXACT TRAFFIC", "category": "category"}
  ],
  "entertainment_trends": [
    {"title": "EXACT NAME", "traffic": "EXACT TRAFFIC"}
  ],
  "games_trends": [
    {"title": "EXACT NAME", "traffic": "EXACT TRAFFIC"}
  ],
  "shopping_trends": [
    {"title": "EXACT NAME", "traffic": "EXACT TRAFFIC"}
  ],
  "recent_breakouts": [
    {"title": "EXACT NAME", "traffic": "EXACT TRAFFIC", "note": "why notable"}
  ]
}
```

⚠️ CRITICAL: You MUST only use trend names that appear in the data above.
Copy names and traffic values EXACTLY as shown. Do NOT invent trends.""",
    output_key="categorized_trends",
)


# ============================================================================
# AGENT 3: Trends Analyzer (with logging)
# ============================================================================

trends_analyzer = LlmAgent(
    name="TrendsAnalyzer",
    model=GEMINI_MODEL,
    description="Deep-dive trend analyst with monetization intelligence.",
    instruction="""You are a SENIOR TREND INTELLIGENCE ANALYST with expertise in:
- Consumer behavior analysis
- Viral content mechanics
- E-commerce opportunities
- Content monetization strategies

TODAY'S DATE: December 17, 2025

HERE IS THE ACTUAL TREND DATA (use ONLY these):
{trends_text_list}

═══════════════════════════════════════════════════════════════════════════════
DELIVER A COMPREHENSIVE TREND INTELLIGENCE REPORT
═══════════════════════════════════════════════════════════════════════════════

## 📊 EXECUTIVE INTELLIGENCE BRIEFING
3-4 sentences: What's dominating search? Why NOW? What does this reveal about current cultural moment?

## 🔥 TOP 10 TRENDS - DEEP ANALYSIS

For EACH of the top 10 trends (by traffic), provide:

### 1. [TREND NAME] - [TRAFFIC]
**Why It's Trending:**
- Root cause (news event, release, controversy, seasonal)
- Timeline: When did this start? Peak window estimate?
- Sentiment: Positive/Negative/Neutral/Controversial

**Search Intent Analysis:**
- Informational: People want to learn about X
- Transactional: People want to buy/watch/download X
- Navigational: People looking for specific site/platform
- Commercial: People comparing options/researching purchases

**Audience Profile:**
- Demographics: Age range, interests, platforms they use
- Psychographics: What motivates this search?
- Purchase intent level: 1-10

**Monetization Potential:** ⭐⭐⭐⭐⭐ (1-5 stars)
- Content opportunity score
- E-commerce opportunity score
- Affiliate opportunity score

(Repeat for all 10 trends)

## 🎯 TREND CLUSTERING & PATTERNS

### Theme Clusters Identified:
1. **[CLUSTER NAME]** (e.g., "Sports Events")
   - Trends in cluster: [list from data]
   - Combined search volume estimate
   - Cross-promotion opportunities

2. **[CLUSTER NAME]** (e.g., "Celebrity News")
   - Trends in cluster: [list from data]
   - Combined search volume estimate
   - Cross-promotion opportunities

(Identify 3-5 clusters)

### Timing Analysis:
- **Peaking NOW (0-24h window):** [trends]
- **Rising (24-48h runway):** [trends]
- **Sustained interest (7-day):** [trends]

## 💡 OPPORTUNITY MATRIX

| Trend | Content Play | Product Play | Affiliate Play | Urgency |
|-------|-------------|--------------|----------------|----------|
| [name] | Blog/Video/Thread | Merch/Digital | Amazon/Course | 🔴/🟡/🟢 |
(Top 15 trends)

## 🧠 DEEPER UNDERSTANDING NEEDED

For each major trend, what questions should we research further?

1. **[TREND]**: 
   - What exactly happened? (research query)
   - Who are the key players involved?
   - What's the controversy/interest angle?
   - Historical context needed?

2. **[TREND]**:
   - (same structure)

(Top 5 trends that need deeper research)

⚠️ CRITICAL: Use ONLY trend names from the data above. No hallucinations.""",
    output_key="analysis_report",
)


# ============================================================================
# AGENT 4: Strategic Insights Generator (with logging)
# ============================================================================

insights_generator = LlmAgent(
    name="InsightsGenerator",
    model=GEMINI_MODEL,
    description="Strategic monetization architect with detailed execution plans.",
    instruction="""You are a STRATEGIC MONETIZATION ARCHITECT - an expert in:
- Content marketing & SEO
- E-commerce & print-on-demand
- Affiliate marketing
- Digital product creation
- Viral content engineering

TODAY'S DATE: December 17, 2025

HERE IS THE ACTUAL TREND DATA (use ONLY these):
{trends_text_list}

═══════════════════════════════════════════════════════════════════════════════
STRATEGIC MONETIZATION PLAYBOOK - DETAILED EXECUTION PLANS
═══════════════════════════════════════════════════════════════════════════════

## 🚀 SECTION 1: CONTENT EMPIRE BUILDING

For the TOP 5 highest-traffic trends, provide DETAILED content plans:

### 📝 CONTENT PLAY #1: [TREND NAME]

**A. BLOG/WEBSITE STRATEGY**
```
Article Title: "[SEO-optimized title with trend name]"
Target Keywords: [primary], [secondary], [long-tail]
Word Count: [recommended length]
Article Structure:
  1. Hook/Introduction (what happened, why it matters)
  2. Background/Context section
  3. Main analysis (3-4 subheadings)
  4. Expert opinions/quotes to source
  5. What this means for [audience]
  6. FAQ section (5 questions people are asking)
  7. Call-to-action

Internal Linking Opportunities: [related topics]
External Sources to Cite: [authoritative sources]
Publish Timeline: Within [X] hours for maximum SEO benefit
```

**B. VIDEO CONTENT PLAN**
```
Platform: YouTube / TikTok / Both
Video Type: Explainer / Reaction / News / Tutorial
Title: "[Clickable title with trend]"
Thumbnail Concept: [specific visual description]
Script Outline:
  - Hook (0-15 sec): [exact hook]
  - Context (15-60 sec): [what to cover]
  - Main Content (1-5 min): [key points]
  - CTA (final 30 sec): [subscribe, comment prompt]

Hashtags: #[tag1] #[tag2] #[tag3] #[tag4] #[tag5]
Best Upload Time: [specific time based on trend lifecycle]
Expected Performance: [view estimate based on search volume]
```

**C. SOCIAL MEDIA THREAD**
```
Platform: X/Twitter
Thread Structure (10 tweets):
  1. 🧵 Hook: "[Attention-grabbing opener about trend]"
  2. Context: "Here's what happened..."
  3-7. Key points with data/insights
  8. Hot take / unique angle
  9. What to watch next
  10. CTA + follow prompt

Post Timing: [optimal time]
Engagement Tactics: Poll, question, quote-tweet strategy
```

(Repeat for 5 trends)

---

## 🛍️ SECTION 2: E-COMMERCE & MERCH EXPLOITATION

For trends with PRODUCT POTENTIAL:

### 👕 MERCHANDISE PLAY #1: [TREND NAME]

**Print-on-Demand Execution Plan:**
```
Product Type: T-Shirt / Hoodie / Mug / Poster / Phone Case

Design Concepts (3 options):
  1. "[Specific text/slogan idea]" - Style: [minimalist/bold/vintage]
  2. "[Another slogan]" - Style: [description]
  3. "[Visual concept]" - Style: [description]

Target Audience: [specific demographic]
Price Point: $[XX] (cost $[X], margin $[X])

Platform Strategy:
  - Merch by Amazon: [yes/no, why]
  - Redbubble: [yes/no, why]
  - Printful + Shopify: [yes/no, why]
  - Etsy: [yes/no, why]

Marketing Plan:
  - Reddit communities to target: r/[subreddit1], r/[subreddit2]
  - Facebook groups: [group types]
  - Instagram hashtags: #[tag1] #[tag2]
  - TikTok angle: "[specific video concept]"

Launch Timeline:
  - Hour 0-2: Design creation
  - Hour 2-4: Upload to platforms
  - Hour 4-6: First social posts
  - Hour 6-24: Paid ads if traction

Profit Projection: [X] sales × $[X] margin = $[XXX] potential
```

**Digital Product Opportunities:**
```
Product Type: [Ebook / Course / Template / Printable]
Title: "[Specific product name]"
Price: $[X]
Platform: Gumroad / Teachable / Etsy Digital
Creation Time: [X] hours
Content Outline:
  - Chapter/Module 1: [topic]
  - Chapter/Module 2: [topic]
  - Chapter/Module 3: [topic]
  - Bonus: [additional value]
```

(Create for 3-4 trends with merch potential)

---

## 💰 SECTION 3: AFFILIATE & PARTNERSHIP PLAYS

### 🔗 AFFILIATE PLAY #1: [TREND NAME]

```
Affiliate Programs to Join:
  1. Amazon Associates - Products: [specific items related to trend]
     - Search: "[exact Amazon search query]"
     - Top products to feature: [product types]
     - Commission: [X]%
  
  2. [Relevant brand affiliate] - [product type]
     - Commission: [X]%
     - Cookie duration: [X] days

Content Strategy for Affiliate:
  - "Best [Products] for [Trend-Related Activity]" article
  - "[Trend] Starter Kit - Everything You Need" roundup
  - Comparison: "[Product A] vs [Product B] for [trend]"

Traffic Strategy:
  - SEO play: Target "[long-tail keyword]"
  - Pinterest pins: [X] pins with [description]
  - YouTube: "[Trend] Unboxing/Review" video

Revenue Projection:
  - Traffic estimate: [X] visitors from trend
  - Conversion rate: [X]%
  - Average order: $[X]
  - Commission: $[X] per sale
  - Projected revenue: $[XXX]
```

(Create for 3 trends with affiliate potential)

---

## 📰 SECTION 4: NEWS/AUTHORITY SITE PLAYS

For NEWSWORTHY trends:

### 📰 NEWS PLAY: [TREND NAME]

```
Angle: [Breaking news / Analysis / Opinion / Investigation]

Research Required:
  - Primary sources to contact: [list]
  - Data to gather: [statistics, quotes]
  - Fact-check: [claims to verify]

Article Formats:
  1. Breaking: "[Trend]: What We Know So Far"
  2. Explainer: "[Trend] Explained: Everything You Need to Know"
  3. Opinion: "Why [Trend] Matters for [Audience]"
  4. Roundup: "[X] Reactions to [Trend]"

Syndication Strategy:
  - Medium republish: [yes/no]
  - LinkedIn article: [yes/no]
  - Guest post pitches: [target sites]
  - HARO queries to answer: [topic areas]
```

---

## ⚡ SECTION 5: RAPID EXECUTION TIMELINE

### 🔴 NEXT 2 HOURS - CRITICAL ACTIONS
```
□ [Specific action for Trend 1] - Est. time: [X] min
□ [Specific action for Trend 2] - Est. time: [X] min
□ [Specific action for Trend 3] - Est. time: [X] min
□ [Social post about Trend 4] - Est. time: [X] min
```

### 🟡 HOURS 2-6 - HIGH PRIORITY
```
□ Complete blog post for [Trend] - Target: [X] words
□ Design merch for [Trend] - [X] designs
□ Set up affiliate links for [Trend products]
□ Film/edit video for [Trend]
```

### 🟢 HOURS 6-24 - BUILD OUT
```
□ SEO optimization for published content
□ Launch paid promotion if organic traction
□ Email list: Send trend roundup
□ Repurpose content across platforms
```

### 📅 24-48 HOURS - SCALE
```
□ Analyze performance metrics
□ Double down on winners
□ Create follow-up content
□ Build evergreen content from trending topics
```

---

## ⚠️ SECTION 6: RISK ASSESSMENT & COMPLIANCE

### Trends Requiring Caution:
```
[TREND NAME]: 
  - Risk Type: [Legal / Reputation / Sensitivity]
  - Specific Concern: [what to avoid]
  - Safe Approach: [how to handle]
  - DO NOT: [explicit warnings]
```

### Copyright/Trademark Considerations:
```
- [Trend]: Owned by [entity] - License needed: [yes/no]
- [Trend]: Fair use applies for [context]
- [Trend]: Avoid using [specific terms/images]
```

---

## 💎 SECTION 7: HIDDEN GEM OPPORTUNITIES

Lower-traffic trends with HIGH monetization potential:

### 💎 GEM #1: [TREND NAME] ([TRAFFIC])
```
Why It's Undervalued: [explanation]
Niche Audience: [specific demographic]
Monetization Path: [specific strategy]
Competition Level: Low/Medium/High
First-Mover Advantage Window: [X] hours/days
Execution Priority: [1-10]
```

(Identify 3 hidden gems)

---

*Strategic Playbook generated from live Google Trends - December 17, 2025*
*Execute within trend lifecycle windows for maximum ROI*

⚠️ CRITICAL: All trend names MUST come from the provided data. No hallucinations.""",
    output_key="strategic_insights",
)


# ============================================================================
# AGENT 5: Google Search Sources Collector
# ============================================================================

class TrendSourcesCollector(BaseAgent):
    """
    Searches Google for each trending topic and collects source URLs.
    
    For each trend keyword, performs multiple search variations:
    - "KEYWORD breaking news"
    - "KEYWORD trending news"
    - "KEYWORD news"
    - "KEYWORD latest news"
    
    Collects up to 10 pages of results per query and saves all URLs to a .txt file.
    """
    
    name: str = "TrendSourcesCollector"
    description: str = "Searches Google for trend sources and saves URLs to text file."
    
    # Configuration
    RESULTS_PER_PAGE: int = 10
    MAX_PAGES: int = 4  # 4 pages = up to 40 results per query (rate limit friendly)
    SEARCH_VARIATIONS: list = [
        "{keyword} breaking news",
        "{keyword} trending news", 
        "{keyword} news",
        "{keyword} latest news",
    ]

    def _search_google(self, query: str, num_results: int = 100, driver=None) -> list:
        """
        Perform a Google search using Selenium and return URLs.
        Uses multiple selector strategies to find results.
        
        Args:
            query: Search query string
            num_results: Maximum number of results to collect
            driver: Selenium WebDriver instance (required)
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import urllib.parse
        import time
        import random
        
        urls = []
        results_per_page = 10
        
        if driver is None:
            print("      ⚠️ No driver provided!")
            return urls
        
        # Calculate pages to fetch
        pages_needed = min((num_results + results_per_page - 1) // results_per_page, 10)
        
        for page in range(pages_needed):
            start = page * results_per_page
            
            # Build Google search URL
            params = {
                'q': query,
                'start': start,
                'num': results_per_page,
                'hl': 'en',
            }
            search_url = f"https://www.google.com/search?{urllib.parse.urlencode(params)}"
            
            try:
                driver.get(search_url)
                time.sleep(random.uniform(3.0, 5.0))  # Let page load - increased for stability
                
                # Wait for any content to load
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except:
                    pass
                
                # Check for CAPTCHA or unusual traffic page
                page_source = driver.page_source.lower()
                if "unusual traffic" in page_source or "captcha" in page_source or "recaptcha" in page_source:
                    print(f"      ⚠️ Rate limited at page {page+1}")
                    time.sleep(random.uniform(15, 25))
                    continue
                
                # STRATEGY 1: Find all anchor tags and filter
                all_links = driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        if not href:
                            continue
                        
                        # Skip Google internal URLs
                        skip_patterns = [
                            'google.com', 'google.co', 'gstatic.com', 'googleapis.com',
                            'accounts.google', 'support.google', 'webcache.googleusercontent',
                            'translate.google', 'maps.google', 'news.google',
                            '/search?', '/url?', '/imgres?', 'youtube.com/results',
                            '#', 'javascript:', 'about:'
                        ]
                        
                        if any(pattern in href.lower() for pattern in skip_patterns):
                            continue
                        
                        # Must be a valid HTTP URL
                        if href.startswith("http://") or href.startswith("https://"):
                            # Additional validation - must have a proper domain
                            if '.' in href.split('/')[2]:  # Check domain has dot
                                if href not in urls:
                                    urls.append(href)
                    except:
                        continue
                
                # STRATEGY 2: Look for cite elements (Google shows URLs in cite tags)
                cite_elements = driver.find_elements(By.TAG_NAME, "cite")
                for cite in cite_elements:
                    try:
                        # Get parent anchor
                        parent = cite.find_element(By.XPATH, "./ancestor::a")
                        href = parent.get_attribute("href")
                        if href and href.startswith("http") and 'google' not in href.lower():
                            if href not in urls:
                                urls.append(href)
                    except:
                        continue
                
                # STRATEGY 3: Look for h3 elements (result titles) and get parent links
                h3_elements = driver.find_elements(By.TAG_NAME, "h3")
                for h3 in h3_elements:
                    try:
                        parent = h3.find_element(By.XPATH, "./ancestor::a")
                        href = parent.get_attribute("href")
                        if href and href.startswith("http") and 'google' not in href.lower():
                            if href not in urls:
                                urls.append(href)
                    except:
                        continue
                
                # Check if we have enough results
                if len(urls) >= num_results:
                    break
                
                # Longer delay between pages to avoid rate limiting
                time.sleep(random.uniform(6.0, 10.0))
                
            except Exception as page_error:
                error_str = str(page_error)[:60]
                if "timeout" not in error_str.lower():
                    print(f"      ⚠️ Page {page+1} error: {error_str}")
                time.sleep(8)
                continue
        
        return urls[:num_results]

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Search Google for each trend and collect source URLs."""
        global agent_logger
        
        agent_logger.log_agent_start(
            self.name,
            "Collecting news sources for each trending topic via Google Search"
        )
        
        try:
            import time
            import re
            import random  # Import at top for all delay operations
            
            # Get trends from session state
            live_trends_data = context.session.state.get("live_trends_data", {})
            all_trends = live_trends_data.get("all_trends_flat", [])
            
            if not all_trends:
                error_msg = "No trends data found in session state"
                agent_logger.log_agent_complete(self.name, success=False, error=error_msg)
                content = types.Content(role="model", parts=[types.Part(text=f"❌ {error_msg}")])
                yield Event(author=self.name, content=content)
                return
            
            # Select top trends to search (limit to avoid rate limiting)
            # Sort by traffic and take top 15
            def traffic_sort_key(t):
                traffic = t.get("traffic", "0")
                # Convert traffic string to numeric for sorting
                multipliers = {"M": 1000000, "K": 1000, "B": 1000000000}
                match = re.match(r'(\d+)([KMB])?', traffic.replace("+", "").replace(",", ""))
                if match:
                    num = int(match.group(1))
                    suffix = match.group(2)
                    if suffix:
                        num *= multipliers.get(suffix, 1)
                    return num
                return 0
            
            sorted_trends = sorted(all_trends, key=traffic_sort_key, reverse=True)
            top_trends = sorted_trends[:15]  # Top 15 trends
            
            print("\n" + "="*70)
            print("🔍 GOOGLE SEARCH - COLLECTING NEWS SOURCES")
            print("="*70)
            print(f"\n📊 Processing top {len(top_trends)} trends")
            print(f"📄 Search variations: {len(self.SEARCH_VARIATIONS)} per trend")
            print(f"📑 Max pages per search: {self.MAX_PAGES} ({self.MAX_PAGES * self.RESULTS_PER_PAGE} results)")
            
            # Prepare output file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("logs/sources")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"trend_sources_{timestamp}.txt"
            
            # Collect all sources
            all_sources = {}
            total_urls_collected = 0
            
            agent_logger.log_agent_action(self.name, f"Will search {len(top_trends)} trends")
            
            # Initialize shared Selenium driver for all searches
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            print("\n🚀 Initializing Selenium browser for Google Search...")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            shared_driver = webdriver.Chrome(service=service, options=chrome_options)
            shared_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("   ✅ Browser ready!")
            
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    # Write header
                    f.write("="*80 + "\n")
                    f.write("GOOGLE TRENDS - NEWS SOURCES COLLECTION\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write(f"Total Trends Searched: {len(top_trends)}\n")
                    f.write("="*80 + "\n\n")
                    
                    for idx, trend in enumerate(top_trends, 1):
                        keyword = trend.get("title", "")
                        traffic = trend.get("traffic", "N/A")
                        category = trend.get("category", "Unknown")
                        
                        if not keyword:
                            continue
                        
                        print(f"\n{'─'*60}")
                        print(f"🔎 [{idx}/{len(top_trends)}] Searching: {keyword} ({traffic})")
                        print(f"{'─'*60}")
                        
                        agent_logger.log_agent_action(
                            self.name, 
                            f"Searching trend {idx}/{len(top_trends)}: {keyword}"
                        )
                        
                        # Write trend header to file
                        f.write("\n" + "="*80 + "\n")
                        f.write(f"TREND: {keyword}\n")
                        f.write(f"Traffic: {traffic} | Category: {category}\n")
                        f.write("="*80 + "\n")
                        
                        trend_urls = []
                        
                        # Search each variation
                        for variation in self.SEARCH_VARIATIONS:
                            query = variation.format(keyword=keyword)
                            
                            print(f"   🔍 Query: \"{query}\"")
                            f.write(f"\n--- Query: \"{query}\" ---\n")
                            
                            try:
                                # Perform Google search using shared driver
                                results = self._search_google(
                                    query,
                                    num_results=self.MAX_PAGES * self.RESULTS_PER_PAGE,
                                    driver=shared_driver
                                )
                                
                                urls_found = len(results)
                                print(f"      ✅ Found {urls_found} URLs")
                                
                                # Write URLs to file
                                for i, url in enumerate(results, 1):
                                    f.write(f"{i}. {url}\n")
                                    if url not in trend_urls:
                                        trend_urls.append(url)
                                
                                total_urls_collected += urls_found
                                import random
                                # Longer delay between queries to avoid rate limiting
                                time.sleep(random.uniform(8.0, 12.0))
                            
                            except Exception as e:
                                error_msg = str(e)
                                print(f"      ⚠️ Error: {error_msg[:50]}...")
                                f.write(f"ERROR: {error_msg}\n")
                                agent_logger.log_agent_action(
                                    self.name,
                                    f"Search error for '{query}': {error_msg[:100]}"
                                )
                                # If rate limited, wait longer
                                if "429" in error_msg or "rate" in error_msg.lower():
                                    print("      ⏳ Rate limited, waiting 30 seconds...")
                                    time.sleep(30)
                        
                        # Store unique URLs for this trend (after all variations searched)
                        all_sources[keyword] = {
                            "traffic": traffic,
                            "category": category,
                            "urls": trend_urls,
                            "url_count": len(trend_urls),
                        }
                        
                        # Write summary for this trend
                        f.write(f"\n📊 Total unique URLs for '{keyword}': {len(trend_urls)}\n")
                        
                        print(f"   📊 Total unique URLs: {len(trend_urls)}")
                        
                        # Long delay between trends to let browser recover
                        print(f"   ⏳ Waiting 15-20 seconds before next trend...")
                        time.sleep(random.uniform(15.0, 20.0))
                    
                    # Write final summary to file
                    f.write("\n\n" + "="*80 + "\n")
                    f.write("COLLECTION SUMMARY\n")
                    f.write("="*80 + "\n")
                    f.write(f"Total Trends Searched: {len(top_trends)}\n")
                    f.write(f"Total URLs Collected: {total_urls_collected}\n")
                    f.write(f"Unique URLs per Trend:\n")
                    for keyword, data in all_sources.items():
                        f.write(f"  - {keyword}: {data['url_count']} URLs\n")
                    f.write("\n" + "="*80 + "\n")
                
                # Also save as JSON for programmatic access
                json_file = output_dir / f"trend_sources_{timestamp}.json"
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "generated": datetime.now().isoformat(),
                        "total_trends": len(top_trends),
                        "total_urls": total_urls_collected,
                        "search_variations": self.SEARCH_VARIATIONS,
                        "sources_by_trend": all_sources,
                    }, f, indent=2)
                
                # Store in session state for next agents
                context.session.state["trend_sources"] = all_sources
                context.session.state["sources_file"] = str(output_file)
                context.session.state["sources_json_file"] = str(json_file)
                
                agent_logger.log_agent_output(self.name, {
                    "trends_searched": len(top_trends),
                    "total_urls": total_urls_collected,
                    "output_file": str(output_file),
                })
                agent_logger.log_agent_complete(self.name, success=True)
                
                print(f"\n{'='*70}")
                print(f"📊 SEARCH COMPLETE")
                print(f"   Trends searched: {len(top_trends)}")
                print(f"   Total URLs collected: {total_urls_collected}")
                print(f"   📄 Text file: {output_file}")
                print(f"   📄 JSON file: {json_file}")
                print(f"{'='*70}")
                
                content = types.Content(
                    role="model",
                    parts=[types.Part(text=f"✅ Collected {total_urls_collected} source URLs for {len(top_trends)} trends. Saved to {output_file}")]
                )
                yield Event(author=self.name, content=content)
                
            finally:
                # Always close the shared Selenium driver
                try:
                    shared_driver.quit()
                    print("\n🔒 Browser closed.")
                except:
                    pass
            
        except Exception as e:
            error_msg = f"Error in TrendSourcesCollector: {str(e)}"
            agent_logger.log_agent_complete(self.name, success=False, error=error_msg)
            print(f"\n❌ {error_msg}")
            import traceback
            traceback.print_exc()
            content = types.Content(role="model", parts=[types.Part(text=f"❌ {error_msg}")])
            yield Event(author=self.name, content=content)


# ============================================================================
# SEQUENTIAL PIPELINE
# ============================================================================

trends_pipeline = SequentialAgent(
    name="GoogleTrendsPipeline",
    description="Live Fetch → Categorize → Analyze → Insights → Collect Sources (with full logging)",
    sub_agents=[
        LiveTrendsFetcher(),      # Step 1: Fetch LIVE data from Google Trends
        trend_categorizer,        # Step 2: Organize and categorize trends
        trends_analyzer,          # Step 3: Analyze patterns
        insights_generator,       # Step 4: Business insights
        TrendSourcesCollector(),  # Step 5: Google search for news sources
    ],
)

root_agent = trends_pipeline


# ============================================================================
# RUNNER SETUP
# ============================================================================

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def run_pipeline():
    """Execute the pipeline with full logging."""
    global agent_logger
    
    # Initialize logger
    agent_logger = AgentLogger(log_dir="logs")
    
    print("\n" + "🎯"*35)
    print("  GOOGLE TRENDS LIVE PIPELINE")
    print("  With Full Logging & Monitoring")
    print("🎯"*35)
    
    agent_logger.log_event("pipeline_start", {
        "categories": ["Entertainment", "Games", "Shopping"],
        "data_source": "selenium_direct",
        "urls": [
            "48h active (Entertainment, Games, Shopping)",
            "48h active (All)",
            "168h active (All)",
            "168h recent (All)",
        ],
    })
    
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={},
    )
    
    agent_logger.log_event("session_created", {
        "app_name": APP_NAME,
        "user_id": USER_ID,
        "session_id": SESSION_ID,
    })
    
    print("\n✅ Session created")
    print("📊 Logging to: logs/")
    
    content = types.Content(
        role="user",
        parts=[types.Part(text="Fetch and analyze LIVE Google Trends data for Entertainment, Games, and Shopping.")]
    )
    
    import warnings
    warnings.filterwarnings("ignore")
    
    current_agent = ""
    agent_outputs = {}  # Track outputs for data processing metrics
    
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if hasattr(event, "author") and event.author and event.author != current_agent:
            if event.author not in ["GoogleTrendsPipeline", "user"]:
                # Log agent transition
                if current_agent:
                    agent_logger.log_event("agent_transition", {
                        "from": current_agent,
                        "to": event.author,
                    })
                
                current_agent = event.author
                
                # Log agent start for LLM agents
                if current_agent in ["TrendCategorizer", "TrendsAnalyzer", "InsightsGenerator"]:
                    agent_logger.log_agent_start(current_agent, f"LLM processing step")
                    
                    # Log the input data the LLM agent is receiving
                    # Get the trends_text_list from session state
                    session = await session_service.get_session(
                        app_name=APP_NAME,
                        user_id=USER_ID,
                        session_id=SESSION_ID,
                    )
                    if session and session.state:
                        input_data = session.state.get("trends_text_list", "")
                        if input_data:
                            agent_logger.log_agent_perception(
                                current_agent,
                                "Session State: trends_text_list",
                                input_data
                            )
                
                print(f"\n{'─'*70}")
                print(f"📍 Agent: {current_agent}")
                print(f"{'─'*70}")
        
        if hasattr(event, "content") and event.content:
            if hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        output_text = part.text
                        output_size = len(output_text)
                        
                        # Log output for LLM agents with actual data size
                        if current_agent in ["TrendCategorizer", "TrendsAnalyzer", "InsightsGenerator"]:
                            agent_outputs[current_agent] = output_text
                            agent_logger.log_agent_output(current_agent, output_text)
                            agent_logger.log_agent_complete(current_agent, success=True)
                            
                            # Add to data processed metric
                            agent_logger.run_data["metrics"]["total_data_bytes"] += output_size
                        
                        print(output_text)
    
    # Log final data summary
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    
    if session and session.state:
        # Calculate total data in session state
        live_data = session.state.get("live_trends_data", {})
        trends_list = session.state.get("trends_text_list", "")
        categorized = session.state.get("categorized_trends", "")
        analysis = session.state.get("analysis_report", "")
        insights = session.state.get("strategic_insights", "")
        trend_sources = session.state.get("trend_sources", {})
        sources_file = session.state.get("sources_file", "")
        
        total_session_data = (
            len(json.dumps(live_data, default=str)) +
            len(str(trends_list)) +
            len(str(categorized)) +
            len(str(analysis)) +
            len(str(insights)) +
            len(json.dumps(trend_sources, default=str))
        )
        
        agent_logger.run_data["metrics"]["total_data_bytes"] += total_session_data
        
        # Count total URLs collected
        total_urls = sum(data.get("url_count", 0) for data in trend_sources.values())
        
        agent_logger.log_event("session_data_summary", {
            "live_trends_data_size": len(json.dumps(live_data, default=str)),
            "trends_text_list_size": len(str(trends_list)),
            "total_unique_trends": live_data.get("summary", {}).get("total_unique_trends", 0),
            "sources_fetched": live_data.get("summary", {}).get("sources_fetched", 0),
            "trends_searched_for_sources": len(trend_sources),
            "total_source_urls_collected": total_urls,
            "sources_file": sources_file,
        })
    
    # Finalize logging
    agent_logger.log_event("pipeline_complete", {"status": "success"})
    agent_logger.finalize()
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE - Check logs/ folder for detailed audit trail")
    print("="*70)


async def main():
    """Entry point."""
    try:
        import pytrends
    except ImportError:
        print("❌ Missing 'pytrends' package.")
        print("   Install with: pip install pytrends")
        print("\nInstalling now...")
        import subprocess
        subprocess.run(["pip", "install", "pytrends"], check=True)
        print("✅ Installed pytrends")
    
    await run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
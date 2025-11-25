"""
Web search tools for AI agents using LangChain + DuckDuckGo.
100% gratuit, pas d'API key nécessaire !
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Tool for AI to search the web using DuckDuckGo (gratuit, pas d'API key).
    
    Usage:
        tool = WebSearchTool()
        results = tool.search("best necro build gw2 wvw 2024")
    """
    
    def __init__(self):
        """Initialize web search tool."""
        self._search_function = None
        self._initialize_search()
    
    def _initialize_search(self):
        """Initialize DuckDuckGo search (lazy loading)."""
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            self._search_function = DuckDuckGoSearchRun()
            logger.info("✅ DuckDuckGo search tool initialized (gratuit)")
        except ImportError:
            logger.warning(
                "⚠️ langchain-community not installed. "
                "Run: poetry add langchain langchain-community duckduckgo-search"
            )
            self._search_function = None
    
    def search(self, query: str, max_results: int = 5) -> str:
        """
        Search the web for a query.
        
        Args:
            query: Search query
            max_results: Maximum number of results (default 5)
        
        Returns:
            Search results as formatted string
        """
        if self._search_function is None:
            return "Error: Web search not available. Install langchain-community."
        
        try:
            # DuckDuckGoSearchRun returns a formatted string
            results = self._search_function.run(query)
            return results
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Search failed: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if web search is available."""
        return self._search_function is not None


class GW2MetaSearchTool:
    """
    Specialized tool for searching GW2 meta builds and strategies.
    Wraps WebSearchTool with GW2-specific queries.
    """
    
    def __init__(self):
        """Initialize GW2 meta search tool."""
        self.web_search = WebSearchTool()
    
    def search_wvw_meta(self, profession: str, role: Optional[str] = None) -> str:
        """
        Search for WvW meta builds for a profession.
        
        Args:
            profession: GW2 profession (e.g., "Guardian", "Necromancer")
            role: Optional role (e.g., "DPS", "Support", "Tank")
        
        Returns:
            Search results
        """
        role_part = f"{role} " if role else ""
        query = f"gw2 {profession} {role_part}wvw meta build 2024"
        
        logger.info(f"🔍 Searching WvW meta: {query}")
        return self.web_search.search(query)
    
    def search_skill_info(self, skill_name: str) -> str:
        """
        Search for GW2 skill information.
        
        Args:
            skill_name: Skill name
        
        Returns:
            Search results
        """
        query = f"gw2 wiki {skill_name} skill"
        return self.web_search.search(query)
    
    def search_trait_info(self, trait_name: str, specialization: str) -> str:
        """
        Search for GW2 trait information.
        
        Args:
            trait_name: Trait name
            specialization: Specialization name
        
        Returns:
            Search results
        """
        query = f"gw2 wiki {specialization} {trait_name} trait"
        return self.web_search.search(query)
    
    def search_current_meta(self, game_mode: str = "WvW") -> str:
        """
        Search for current GW2 meta.
        
        Args:
            game_mode: Game mode (default "WvW")
        
        Returns:
            Search results about current meta
        """
        query = f"gw2 {game_mode} meta 2024 tier list"
        return self.web_search.search(query)


# Global instances (singletons)
_web_search_tool: Optional[WebSearchTool] = None
_gw2_meta_search_tool: Optional[GW2MetaSearchTool] = None


def create_web_search_tool() -> WebSearchTool:
    """
    Get or create the web search tool singleton.
    
    Returns:
        WebSearchTool instance
    """
    global _web_search_tool
    if _web_search_tool is None:
        _web_search_tool = WebSearchTool()
    return _web_search_tool


def create_gw2_meta_search_tool() -> GW2MetaSearchTool:
    """
    Get or create the GW2 meta search tool singleton.
    
    Returns:
        GW2MetaSearchTool instance
    """
    global _gw2_meta_search_tool
    if _gw2_meta_search_tool is None:
        _gw2_meta_search_tool = GW2MetaSearchTool()
    return _gw2_meta_search_tool


# Convenience function for quick searches
def search_gw2_meta(profession: str, role: Optional[str] = None, game_mode: str = "WvW") -> str:
    """
    Quick function to search GW2 meta builds.
    
    Args:
        profession: Profession name
        role: Optional role
        game_mode: Game mode (default "WvW")
    
    Returns:
        Search results
    
    Example:
        >>> results = search_gw2_meta("Guardian", "Support", "WvW")
        >>> print(results)
    """
    tool = create_gw2_meta_search_tool()
    if game_mode == "WvW":
        return tool.search_wvw_meta(profession, role)
    else:
        query = f"gw2 {profession} {role or ''} {game_mode} meta build 2024"
        return tool.web_search.search(query)


# Function calling schema for Mistral (LangChain Tools format)
def get_langchain_tools() -> list:
    """
    Get LangChain-compatible tools for Mistral function calling.
    
    Returns:
        List of LangChain Tool objects
    
    Usage with Mistral:
        from langchain_ollama import ChatOllama
        from app.agents.tools import get_langchain_tools
        
        llm = ChatOllama(model="mistral")
        tools = get_langchain_tools()
        
        # Mistral can now call these tools automatically
        llm_with_tools = llm.bind_tools(tools)
    """
    try:
        from langchain.tools import Tool
        
        web_search = create_web_search_tool()
        gw2_search = create_gw2_meta_search_tool()
        
        tools = [
            Tool(
                name="web_search",
                description="Search the web using DuckDuckGo. Use this when you need current information about GW2 builds, meta, or general questions.",
                func=web_search.search,
            ),
            Tool(
                name="search_wvw_meta",
                description="Search for WvW meta builds for a specific profession. Args: profession (str), role (str, optional).",
                func=lambda query: gw2_search.search_wvw_meta(*query.split(",")),
            ),
            Tool(
                name="search_current_meta",
                description="Search for the current GW2 WvW meta tier list and popular builds.",
                func=lambda _: gw2_search.search_current_meta("WvW"),
            ),
        ]
        
        return tools
    
    except ImportError:
        logger.warning("LangChain not installed. Tools not available.")
        return []

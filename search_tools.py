import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class WebSearchTool:
    """Web search tool using Serper API or Tavily API"""

    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

    def search_serper(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        if not self.serper_api_key:
            return [{"error": "Serper API key not ืืconfigured"}]

        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": self.serper_api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": num_results}

        try:
            resp = requests.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            results = []
            if "organic" in data:
                for result in data["organic"]:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "source": "serper"
                    })
            return results
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    def search_tavily(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        if not self.tavily_api_key:
            return [{"error": "Tavily API key not configured"}]

        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {"api_key": self.tavily_api_key, "query": query, "max_results": num_results, "search_depth": "basic"}

        try:
            resp = requests.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            results = []
            if "results" in data:
                for result in data["results"]:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("url", ""),
                        "snippet": result.get("content", ""),
                        "source": "tavily"
                    })
            return results
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    def search(self, query: str, num_results: int = 5, preferred_api: str = "serper") -> List[Dict[str, Any]]:
        if preferred_api == "serper" and self.serper_api_key:
            results = self.search_serper(query, num_results)
            if not any("error" in r for r in results):
                return results

        if preferred_api == "tavily" and self.tavily_api_key:
            results = self.search_tavily(query, num_results)
            if not any("error" in r for r in results):
                return results

        # fallback
        if preferred_api == "serper" and self.tavily_api_key:
            return self.search_tavily(query, num_results)
        elif preferred_api == "tavily" and self.serper_api_key:
            return self.search_serper(query, num_results)

        return [{"error": "No search API configured"}]

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for display"""
        if not results:
            return "No search results found."
        formatted = "Search Results:\n\n"
        for i, result in enumerate(results, 1):
            if "error" in result:
                formatted += f"Error: {result['error']}\n"
            else:
                formatted += f"{i}. **{result['title']}**\n"
                formatted += f"   {result['snippet']}\n"
                formatted += f"   Source: {result['link']}\n\n"
        return formatted

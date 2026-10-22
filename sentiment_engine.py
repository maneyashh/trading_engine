import os
import google.generativeai as genai
from newsapi import NewsApiClient

class MarketPsychologist:
    def __init__(self):
        # We will inject these securely via GitHub Secrets later
        self.news_api = NewsApiClient(api_key=os.environ.get('NEWS_API_KEY'))
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def fetch_market_news(self):
        """Scrapes the latest financial headlines for the Indian market."""
        print("Fetching NIFTY 50 and RBI headlines...")
        top_headlines = self.news_api.get_top_headlines(
            q='market OR nifty OR rbi OR sensex',
            category='business',
            language='en',
            country='in'
        )
        
        headlines = [article['title'] for article in top_headlines.get('articles', [])]
        return headlines

    def analyze_sentiment(self, headlines):
        """Forces the LLM to score the market sentiment as a float."""
        if not headlines:
            return 0.0 # Neutral if no news

        prompt = f"""
        Analyze the following financial news headlines for the Indian stock market.
        Provide a single overall sentiment score between -1.0 (extreme panic/bearish) and 1.0 (extreme greed/bullish).
        Only return the number, nothing else.
        
        Headlines:
        {headlines}
        """
        
        try:
            response = self.model.generate_content(prompt)
            score = float(response.text.strip())
            return score
        except Exception as e:
            print(f"Psychology Engine Error: {e}")
            return 0.0 # Default to neutral if the API fails

    def get_current_psychology(self):
        headlines = self.fetch_market_news()
        score = self.analyze_sentiment(headlines)
        print(f"Current Market Psychology Score: {score}")
        return score

# Quick test execution
if __name__ == "__main__":
    psychologist = MarketPsychologist()
    # psychologist.get_current_psychology() # Uncomment to test locally once keys are set
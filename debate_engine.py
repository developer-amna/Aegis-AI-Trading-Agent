import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

load_dotenv()

# ==========================================
# 1. STRICT WINNER-GRADE OUTPUT SCHEMA
# ==========================================
class AgentDecisionSchema(BaseModel):
    symbol: str = Field(description="Stock ticker symbol (e.g., AAPL, NVDA)")
    action: str = Field(description="Final Trading Decision: MUST be 'BUY', 'SELL', or 'HOLD'")
    confidence: float = Field(description="Consensus confidence score between 0.0 and 1.0")
    bull_case: str = Field(description="Key argument presented by Bullish Growth Agent")
    bear_case: str = Field(description="Key argument presented by Bearish Risk Agent")
    reasoning: str = Field(description="Synthesis & final rationale by Portfolio Risk Manager")
    hedge_required: bool = Field(description="True if high volatility requires buying a protective Put Option")


# ==========================================
# 2. MULTI-AGENT DEBATE ENGINE CLASS
# ==========================================
class DebateEngine:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        print("🧠 [Task 4: Aegis-AI Debate Engine] Autonomous Multi-Agent Consensus Ready.")

    def evaluate_signals(self, payload: Dict[str, Any]) -> AgentDecisionSchema:
        symbol = payload.get("symbol", "UNKNOWN")
        market_data = payload.get("market_data", {})
        sentiment_data = payload.get("sentiment_data", {})

        candidate_models = [
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "mixtral-8x7b-32768"
        ]

        if self.groq_key:
            for model_name in candidate_models:
                try:
                    llm = ChatGroq(
                        temperature=0.2, # Low temp for deterministic debate logic
                        model_name=model_name,
                        groq_api_key=self.groq_key
                    )
                    parser = JsonOutputParser(pydantic_object=AgentDecisionSchema)

                    # Multi-Agent Debate System Prompt
                    prompt_template = PromptTemplate(
                        template="""
                        You are running the Autonomous Multi-Agent Consensus Engine for 'Aegis-AI' Hedge Fund.
                        Simulate an internal investment committee debate for Asset: {symbol}

                        --- DATA INPUTS ---
                        Price: ${current_price} | RSI (14): {rsi_14} | MACD: {macd_signal} | Volatility Index: {volatility_index}
                        News Sentiment Score: {news_score} (-1.0 to +1.0) | Sentiment: {overall_sentiment}

                        --- AGENT ROLES FOR DEBATE ---
                        1. BULL AGENT (Growth Specialist): Argues the positive catalysts, momentum, and technical upside.
                        2. BEAR AGENT (Downside Risk Analyst): Challenge bullish claims, highlighting valuation risks, overbought conditions, or negative news.
                        3. RISK MANAGER AGENT (Arbitrator): Synthesizes both arguments, enforces 2% max portfolio risk threshold, checks if Volatility > 0.28 requires Put Option hedging, and makes final BUY/SELL/HOLD decision.

                        {format_instructions}
                        """,
                        input_variables=["symbol", "current_price", "rsi_14", "macd_signal", "volatility_index", "news_score", "overall_sentiment"],
                        partial_variables={"format_instructions": parser.get_format_instructions()}
                    )

                    formatted_prompt = prompt_template.format(
                        symbol=symbol,
                        current_price=market_data.get('current_price', 'N/A'),
                        rsi_14=market_data.get('rsi_14', 'N/A'),
                        macd_signal=market_data.get('macd_signal', 'NEUTRAL'),
                        volatility_index=market_data.get('volatility_index', 'N/A'),
                        news_score=sentiment_data.get('news_headline_score', 0.0),
                        overall_sentiment=sentiment_data.get('overall_sentiment', 'NEUTRAL')
                    )

                    response = llm.invoke(formatted_prompt)
                    parsed_res = parser.parse(response.content)
                    print(f"🔥 [Multi-Agent Debate Success] Executed via Groq ({model_name})")
                    return AgentDecisionSchema(**parsed_res)
                except Exception:
                    continue

        # Deterministic Fallback Mechanism for High Reliability
        print("💡 [Fallback Logic Engine] Executing Quantitative Consensus Rule Engine.")
        news_score = sentiment_data.get("news_headline_score", 0.0)
        rsi = market_data.get("rsi_14", 50.0)
        macd = market_data.get("macd_signal", "NEUTRAL")
        volatility = market_data.get("volatility_index", 0.20)

        normalized_sentiment = (news_score + 1.0) / 2.0
        tech_score = 0.5
        if macd == "BULLISH": tech_score += 0.25
        elif macd == "BEARISH": tech_score -= 0.25

        if rsi < 30: tech_score += 0.25
        elif rsi > 70: tech_score -= 0.25

        tech_score = max(0.0, min(1.0, tech_score))
        combined_score = (tech_score * 0.40) + (normalized_sentiment * 0.30) + 0.30

        if combined_score >= 0.70:
            action, hedge = "BUY", volatility > 0.28
            reason = f"Bull consensus confirmed. Technicals: {round(tech_score, 2)}, Sentiment: {round(normalized_sentiment, 2)}"
        elif combined_score <= 0.40:
            action, hedge = "SELL", True
            reason = f"Bearish risk flags triggered across indicators."
        else:
            action, hedge = "HOLD", False
            reason = f"Consensus score ({round(combined_score, 2)}) insufficient for position entry."

        return AgentDecisionSchema(
            symbol=symbol,
            action=action,
            confidence=round(combined_score, 2),
            bull_case="RSI and sentiment score show upside trajectory.",
            bear_case="High volatility index introduces downside risk.",
            reasoning=reason,
            hedge_required=hedge
        )


if __name__ == "__main__":
    sample_input = {
        "symbol": "AAPL",
        "market_data": {
            "current_price": 185.50,
            "rsi_14": 28.0,
            "macd_signal": "BULLISH",
            "volatility_index": 0.30
        },
        "sentiment_data": {
            "news_headline_score": 0.82,
            "overall_sentiment": "BULLISH"
        }
    }

    engine = DebateEngine()
    output = engine.evaluate_signals(sample_input)
    
    print("\n--- 🏆 TASK 4 WINNER-GRADE OUTPUT JSON CONTRACT ---")
    print(output.model_dump_json(indent=2))
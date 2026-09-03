import json
from typing import Dict, Any, List, Tuple

from aegis_schemas import TradeDecision


class DebateEngine:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        print("🧠 [Task 4: Aegis-AI Debate Engine] Autonomous Multi-Agent Consensus Ready.")

    def evaluate_signals(self, payload: Dict[str, Any]) -> AgentDecisionSchema:
        symbol = payload.get("symbol", "UNKNOWN")
        
        # Handle flat payload or nested dictionary structures automatically
        if "market_data" in payload:
            market_data = payload.get("market_data", {})
            sentiment_data = payload.get("sentiment_data", {})
        else:
            market_data = {
                "current_price": payload.get("price", "N/A"),
                "rsi_14": payload.get("rsi", "N/A"),
                "macd_signal": payload.get("macd_signal", "NEUTRAL"),
                "volatility_index": payload.get("volatility_index", 0.25)
            }
            sentiment_data = {
                "news_headline_score": payload.get("sentiment_score", 0.0),
                "overall_sentiment": "BULLISH" if payload.get("sentiment_score", 0) > 0 else "BEARISH"
            }

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
        if isinstance(rsi, str):
            rsi = 50.0
        macd = market_data.get("macd_signal", "NEUTRAL")
        volatility = market_data.get("volatility_index", 0.20)
        if isinstance(volatility, str):
            volatility = 0.20

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

        return TradeDecision(
            symbol=symbol,
            action=action,
            confidence=confidence,
            hedge_required=hedge_required,
            reasoning=reasoning,
            bull_case=bull_case,
            bear_case=bear_case,
            position_size_pct=position_size_pct,
        )

    def run_debate(self, payload: Dict[str, Any]) -> AgentDecisionSchema:
        """Alias for backward compatibility with main execution calls."""
        return self.evaluate_signals(payload)


if __name__ == "__main__":
    sample_payload = {
        "symbol": "AAPL",
        "market_data": {
            "current_price": 185.50,
            "rsi_14": 28.0,
            "macd_signal": "BULLISH",
            "volatility_index": 0.25,
        },
        "sentiment_data": {
            "news_headline_score": 0.6,
            "overall_sentiment": "BULLISH",
        },
        "risk_tolerance": 7,
    }
    engine = DebateEngine()
    output = engine.run_debate(sample_input)
    
    print("\n--- 🏆 TASK 4 WINNER-GRADE OUTPUT JSON CONTRACT ---")
    print(output.model_dump_json(indent=2))

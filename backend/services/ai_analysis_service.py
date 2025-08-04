import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class AIAnalysisService:
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # TODO: OLLAMA INTEGRATION - Add these environment variables to .env when ready:
        # OLLAMA_ENABLED=true
        # OLLAMA_MODEL=llama3.2:3b (or llama3.1:8b, qwen2.5:7b, codellama:7b)
        # OLLAMA_BASE_URL=http://localhost:11434
        self.ollama_enabled = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Try to import AI libraries
        try:
            # TODO: OLLAMA SETUP STEPS:
            # 1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh
            # 2. Download model: ollama pull llama3.2:3b
            # 3. Install requests: pip install requests
            # 4. Set OLLAMA_ENABLED=true in .env
            # 5. Restart backend
            
            if self.ollama_enabled:
                # TODO: Add requests import when Ollama is ready
                # import requests
                # self.ollama_client = requests  # Use requests for HTTP calls to Ollama
                self.ai_provider = "ollama"
                logger.info(f"Ollama client initialized - Model: {self.ollama_model}")
            elif self.anthropic_api_key:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                self.ai_provider = "anthropic"
                logger.info("Initialized Anthropic Claude client")
            elif self.openai_api_key:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                self.ai_provider = "openai"
                logger.info("Initialized OpenAI client")
            else:
                logger.warning("No AI API keys found - using fallback analysis")
                self.ai_provider = "fallback"
        except ImportError as e:
            logger.warning(f"AI libraries not available: {e} - using fallback analysis")
            self.ai_provider = "fallback"

    def analyze_market_data(self, symbol: str, price_data: List[Dict], 
                          technical_indicators: Dict, market_context: Dict = None) -> Dict:
        """
        Analyze market data using AI to generate trading signals
        """
        try:
            if self.ai_provider == "anthropic":
                return self._analyze_with_claude(symbol, price_data, technical_indicators, market_context)
            elif self.ai_provider == "openai":
                return self._analyze_with_openai(symbol, price_data, technical_indicators, market_context)
            elif self.ai_provider == "ollama":
                return self._analyze_with_ollama(symbol, price_data, technical_indicators, market_context)
            else:
                return self._fallback_analysis(symbol, price_data, technical_indicators)
                
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(symbol, price_data, technical_indicators)

    def _analyze_with_claude(self, symbol: str, price_data: List[Dict], 
                           technical_indicators: Dict, market_context: Dict) -> Dict:
        """Use Claude for market analysis"""
        try:
            # Prepare market data summary
            latest_price = price_data[-1]['close'] if price_data else 0
            price_change = ((price_data[-1]['close'] - price_data[-2]['close']) / price_data[-2]['close'] * 100) if len(price_data) > 1 else 0
            
            prompt = f"""
            You are an expert cryptocurrency trader analyzing {symbol} for a scalping strategy.
            
            CURRENT MARKET DATA:
            - Current Price: ${latest_price:.2f}
            - Price Change: {price_change:.2f}%
            - Volume: {price_data[-1]['volume'] if price_data else 0}
            
            TECHNICAL INDICATORS:
            - Short MA (3-period): {technical_indicators.get('short_ma', 'N/A')}
            - Long MA (5-period): {technical_indicators.get('long_ma', 'N/A')}
            - RSI: {technical_indicators.get('rsi', 'N/A')}
            - Bollinger Bands: {technical_indicators.get('bb_upper', 'N/A')} / {technical_indicators.get('bb_lower', 'N/A')}
            
            RECENT PRICE ACTION:
            {self._format_recent_prices(price_data[-10:] if len(price_data) >= 10 else price_data)}
            
            ANALYSIS REQUEST:
            Provide a trading recommendation for a scalping strategy with these criteria:
            - Time horizon: 1-5 minutes
            - Risk tolerance: Conservative (0.1% stop loss, 0.2% take profit)
            - Position size: 0.001 BTC (~$43)
            
            Respond with a JSON object containing:
            {{
                "signal": "BUY", "SELL", or "HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "Brief explanation of the decision",
                "risk_assessment": "LOW", "MEDIUM", or "HIGH",
                "suggested_entry": price_level,
                "suggested_stop_loss": price_level,
                "suggested_take_profit": price_level,
                "time_horizon_minutes": 1-10
            }}
            
            Focus on momentum, volume, and short-term price action for scalping opportunities.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse AI response
            response_text = message.content[0].text
            
            # Extract JSON from response
            try:
                # Find JSON in the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = response_text[json_start:json_end]
                    ai_analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError):
                # Fallback if JSON parsing fails
                ai_analysis = {
                    "signal": "HOLD",
                    "confidence": 0.5,
                    "reasoning": "AI response parsing failed, using conservative approach",
                    "risk_assessment": "MEDIUM"
                }
            
            # Add metadata
            ai_analysis["ai_provider"] = "claude"
            ai_analysis["analysis_time"] = datetime.now().isoformat()
            ai_analysis["symbol"] = symbol
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return self._fallback_analysis(symbol, price_data, technical_indicators)

    def _analyze_with_openai(self, symbol: str, price_data: List[Dict], 
                           technical_indicators: Dict, market_context: Dict) -> Dict:
        """Use OpenAI for market analysis"""
        try:
            latest_price = price_data[-1]['close'] if price_data else 0
            price_change = ((price_data[-1]['close'] - price_data[-2]['close']) / price_data[-2]['close'] * 100) if len(price_data) > 1 else 0
            
            prompt = f"""
            Analyze {symbol} for scalping trading opportunity.
            
            Current: ${latest_price:.2f} ({price_change:.2f}%)
            Technical: Short MA={technical_indicators.get('short_ma', 'N/A')}, Long MA={technical_indicators.get('long_ma', 'N/A')}
            
            Provide JSON response:
            {{"signal": "BUY/SELL/HOLD", "confidence": 0.0-1.0, "reasoning": "explanation", "risk_assessment": "LOW/MEDIUM/HIGH"}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = response_text[json_start:json_end]
                    ai_analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found")
            except:
                ai_analysis = {
                    "signal": "HOLD",
                    "confidence": 0.5,
                    "reasoning": "Parsing failed",
                    "risk_assessment": "MEDIUM"
                }
            
            ai_analysis["ai_provider"] = "openai"
            ai_analysis["analysis_time"] = datetime.now().isoformat()
            ai_analysis["symbol"] = symbol
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return self._fallback_analysis(symbol, price_data, technical_indicators)

    def _analyze_with_ollama(self, symbol: str, price_data: List[Dict], 
                           technical_indicators: Dict, market_context: Dict) -> Dict:
        """Use Ollama for market analysis"""
        try:
            # TODO: OLLAMA IMPLEMENTATION - Add requests import at top of file when ready
            # import requests
            
            # Prepare market data summary
            latest_price = price_data[-1]['close'] if price_data else 0
            price_change = ((price_data[-1]['close'] - price_data[-2]['close']) / price_data[-2]['close'] * 100) if len(price_data) > 1 else 0
            
            prompt = f"""
            You are an expert cryptocurrency trader analyzing {symbol} for a scalping strategy.
            
            CURRENT MARKET DATA:
            - Current Price: ${latest_price:.2f}
            - Price Change: {price_change:.2f}%
            - Volume: {price_data[-1]['volume'] if price_data else 0}
            
            TECHNICAL INDICATORS:
            - Short MA (3-period): {technical_indicators.get('short_ma', 'N/A')}
            - Long MA (5-period): {technical_indicators.get('long_ma', 'N/A')}
            - RSI: {technical_indicators.get('rsi', 'N/A')}
            - Bollinger Bands: {technical_indicators.get('bb_upper', 'N/A')} / {technical_indicators.get('bb_lower', 'N/A')}
            
            RECENT PRICE ACTION:
            {self._format_recent_prices(price_data[-10:] if len(price_data) >= 10 else price_data)}
            
            ANALYSIS REQUEST:
            Provide a trading recommendation for a scalping strategy with these criteria:
            - Time horizon: 1-5 minutes
            - Risk tolerance: Conservative (0.1% stop loss, 0.2% take profit)
            - Position size: 0.001 BTC (~$43)
            
            Respond with ONLY a JSON object containing:
            {{
                "signal": "BUY", "SELL", or "HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "Brief explanation of the decision",
                "risk_assessment": "LOW", "MEDIUM", or "HIGH",
                "suggested_entry": price_level,
                "suggested_stop_loss": price_level,
                "suggested_take_profit": price_level,
                "time_horizon_minutes": 1-10
            }}
            
            Focus on momentum, volume, and short-term price action for scalping opportunities.
            """
            
            # TODO: OLLAMA HTTP REQUEST - Uncomment when requests is imported
            # payload = {
            #     "model": self.ollama_model,
            #     "prompt": prompt,
            #     "stream": False,
            #     "options": {
            #         "temperature": 0.3,
            #         "top_p": 0.9,
            #         "max_tokens": 1000
            #     }
            # }
            # 
            # response = requests.post(
            #     f"{self.ollama_base_url}/api/generate",
            #     json=payload,
            #     timeout=30
            # )
            # response.raise_for_status()
            # 
            # response_data = response.json()
            # response_text = response_data.get("response", "")
            
            # TODO: TEMPORARY FALLBACK - Remove when Ollama is implemented
            logger.warning("Ollama is enabled but not fully implemented - using fallback analysis")
            return self._fallback_analysis(symbol, price_data, technical_indicators)
            
            # TODO: OLLAMA JSON PARSING - Uncomment when HTTP request is implemented
            # # Parse AI response
            # try:
            #     # Find JSON in the response
            #     json_start = response_text.find('{')
            #     json_end = response_text.rfind('}') + 1
            #     if json_start != -1 and json_end != -1:
            #         json_str = response_text[json_start:json_end]
            #         ai_analysis = json.loads(json_str)
            #     else:
            #         raise ValueError("No JSON found in response")
            # except (json.JSONDecodeError, ValueError):
            #     # Fallback if JSON parsing fails
            #     ai_analysis = {
            #         "signal": "HOLD",
            #         "confidence": 0.5,
            #         "reasoning": "AI response parsing failed, using conservative approach",
            #         "risk_assessment": "MEDIUM"
            #     }
            # 
            # # Add metadata
            # ai_analysis["ai_provider"] = "ollama"
            # ai_analysis["analysis_time"] = datetime.now().isoformat()
            # ai_analysis["symbol"] = symbol
            # ai_analysis["model"] = self.ollama_model
            # 
            # return ai_analysis
            
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return self._fallback_analysis(symbol, price_data, technical_indicators)

    def _fallback_analysis(self, symbol: str, price_data: List[Dict], 
                         technical_indicators: Dict) -> Dict:
        """Fallback analysis when AI is not available"""
        try:
            if not price_data or len(price_data) < 2:
                return {
                    "signal": "HOLD",
                    "confidence": 0.3,
                    "reasoning": "Insufficient data for analysis",
                    "risk_assessment": "HIGH",
                    "ai_provider": "fallback",
                    "analysis_time": datetime.now().isoformat(),
                    "symbol": symbol
                }
            
            latest_price = price_data[-1]['close']
            prev_price = price_data[-2]['close']
            price_change_pct = (latest_price - prev_price) / prev_price * 100
            
            short_ma = technical_indicators.get('short_ma', latest_price)
            long_ma = technical_indicators.get('long_ma', latest_price)
            volume = price_data[-1]['volume']
            avg_volume = sum(bar['volume'] for bar in price_data[-5:]) / min(5, len(price_data))
            
            # Simple rule-based analysis
            signal = "HOLD"
            confidence = 0.5
            reasoning = "Neutral market conditions"
            risk_assessment = "MEDIUM"
            
            # Bullish conditions
            if (short_ma > long_ma and 
                latest_price > short_ma and 
                price_change_pct > 0.1 and 
                volume > avg_volume * 1.2):
                signal = "BUY"
                confidence = 0.7
                reasoning = "Short MA above long MA, price momentum up, volume increasing"
                risk_assessment = "LOW"
            
            # Bearish conditions
            elif (short_ma < long_ma and 
                  latest_price < short_ma and 
                  price_change_pct < -0.1):
                signal = "SELL"
                confidence = 0.6
                reasoning = "Short MA below long MA, price momentum down"
                risk_assessment = "MEDIUM"
            
            # High volatility warning
            if abs(price_change_pct) > 2.0:
                risk_assessment = "HIGH"
                confidence *= 0.8
                reasoning += " (High volatility detected)"
            
            return {
                "signal": signal,
                "confidence": confidence,
                "reasoning": reasoning,
                "risk_assessment": risk_assessment,
                "ai_provider": "fallback",
                "analysis_time": datetime.now().isoformat(),
                "symbol": symbol,
                "suggested_entry": latest_price,
                "suggested_stop_loss": latest_price * 0.999 if signal == "BUY" else latest_price * 1.001,
                "suggested_take_profit": latest_price * 1.002 if signal == "BUY" else latest_price * 0.998
            }
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {
                "signal": "HOLD",
                "confidence": 0.3,
                "reasoning": f"Analysis error: {str(e)}",
                "risk_assessment": "HIGH",
                "ai_provider": "fallback",
                "analysis_time": datetime.now().isoformat(),
                "symbol": symbol
            }

    def _format_recent_prices(self, price_data: List[Dict]) -> str:
        """Format recent price data for AI prompt"""
        if not price_data:
            return "No recent price data available"
        
        formatted = []
        for i, bar in enumerate(price_data):
            timestamp = bar.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            formatted.append(
                f"  {timestamp.strftime('%H:%M')}: ${bar['close']:.2f} (Vol: {bar['volume']:.0f})"
            )
        
        return "\n".join(formatted)

    def calculate_technical_indicators(self, price_data: List[Dict]) -> Dict:
        """Calculate technical indicators for AI analysis"""
        if not price_data or len(price_data) < 5:
            return {}
        
        df = pd.DataFrame(price_data)
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        indicators = {}
        
        try:
            # Moving averages
            indicators['short_ma'] = df['close'].rolling(window=3).mean().iloc[-1]
            indicators['long_ma'] = df['close'].rolling(window=5).mean().iloc[-1]
            
            # RSI calculation (simplified)
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Bollinger Bands
            if len(df) >= 20:
                ma20 = df['close'].rolling(window=20).mean()
                std20 = df['close'].rolling(window=20).std()
                indicators['bb_upper'] = (ma20 + (std20 * 2)).iloc[-1]
                indicators['bb_lower'] = (ma20 - (std20 * 2)).iloc[-1]
                indicators['bb_middle'] = ma20.iloc[-1]
            
            # Volume indicators
            indicators['avg_volume'] = df['volume'].rolling(window=10).mean().iloc[-1]
            indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['avg_volume']
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
        
        return indicators
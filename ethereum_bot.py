#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT BINANCE - ETHEREUM TRADING AUTOMATIZADO
Bot para trading automatizado de Ethereum na Binance
Usa estratégia de médias móveis para decisões de compra/venda
"""

import os
import time
from datetime import datetime
import logging
import pandas as pd
from binance.client import Client
from binance.enums import *

# --- Substitua pelas suas chaves ou configure variáveis de ambiente ---
api_key = "SUA API"
secret_key = "SUA CHAVE"

# CONFIGURAÇÕES ETHEREUM
STOCK_CODE = "ETH"
OPERATION_CODE = "ETHBRL"
CANDLE_PERIOD = Client.KLINE_INTERVAL_15MINUTE
TRADED_QUANTITY = 0.0001  # Quantidade mínima de ETH (stepSize)
MAX_TRADE_VALUE = 20.00   # Valor máximo em reais por operação
MIN_NOTIONAL = 10.00     # Valor mínimo exigido pela Binance
RESERVE_BALANCE = 5.00   # Saldo reserva que nunca será usado (R$ 5,00)
PROFIT_ONLY_MODE = True  # Usar apenas lucros para compras

# CONFIGURAÇÕES AVANÇADAS
STOP_LOSS_PERCENT = 0.05    # 5% de perda máxima
TRAILING_STOP_PERCENT = 0.03 # 3% trailing stop
RSI_OVERSOLD = 30           # RSI sobrevendido
RSI_OVERBOUGHT = 70         # RSI sobrecomprado

# Define o logger
logging.basicConfig(
    filename='/home/klaus/repo/binance_bot/logs/ethereum_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def createLogOrder(order):
    from datetime import datetime
    
    # Extrai informações da ordem
    side = order.get('side', 'N/A')
    symbol = order.get('symbol', 'N/A')
    quantity = float(order.get('executedQty', order.get('quantity', 0)))
    avg_price = float(order.get('price', order.get('fills', [{}])[0].get('price', 0)) if order.get('fills') else 0)
    order_type = order.get('type', 'N/A')
    
    # Define moeda principal baseada no símbolo
    main_currency = 'BRL' if 'BRL' in symbol else 'USDT'
    main_value = quantity * avg_price if avg_price > 0 else 0
    
    # Formata data e hora
    now = datetime.now()
    formatted_time = now.strftime("%H:%M:%S")
    formatted_date = now.strftime("%d/%m/%Y")
    
    log_message = f"""
-----------------------------------
ORDEM EXECUTADA:
Side: {side}
Ativo: {symbol}
Quantidade: {quantity:.8f}
Valor no momento: {avg_price:.8f}
Moeda: {main_currency}
Valor em {main_currency}: {main_value:.6f}
Type: {order_type}
Data/Hora: ({formatted_time}) {formatted_date}

Complete_order:
{str(order)}
-----------------------------------"""
    
    print(log_message)
    logging.info(log_message)

class EthereumTraderBot():
    last_trade_decision : bool
    last_buy_price : float
    profit_margin : float
    highest_price_since_buy : float

    def __init__(self, stock_code, operation_code, traded_quantity, traded_percentage, candle_period):
        self.stock_code = stock_code
        self.operation_code = operation_code
        self.traded_quantity = traded_quantity
        self.traded_percentage = traded_percentage
        self.candle_period = candle_period
        self.client_binance = Client(api_key, secret_key)
        self.last_buy_price = 0.0
        self.profit_margin = 0.04  # 4% de lucro mínimo
        self.highest_price_since_buy = 0.0
        self.last_trade_decision = False  # Inicializa decisão anterior
        self.previous_price = 0.0  # Para calcular variação percentual
        self.updateAllData()
        
        # Se já tem posição ETH ao iniciar, define preço atual como referência
        if self.actual_trade_position and self.last_buy_price == 0.0:
            ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
            self.last_buy_price = float(ticker['price'])
            self.highest_price_since_buy = self.last_buy_price
            print(f"📊 Posição ETH detectada! Preço de referência: R$ {self.last_buy_price:,.2f}")
            logging.info(f"Posição ETH existente - Preço de referência definido: R$ {self.last_buy_price:,.2f}")
        
        print('_________________________________________')
        print(' Robo Trader ETHEREUM Iniciado... ')
        logging.info("Bot Ethereum iniciado")

    def updateAllData(self):
        self.account_data = self.getUpdatedAccountData()
        self.last_stock_account_balance = self.getLastStockAccountBalance()
        self.actual_trade_position = self.getActualTradePosition()
        self.stock_data = self.getStockData_ClosePrice_OpenTime()

    def getUpdatedAccountData(self):
        return self.client_binance.get_account()

    def getLastStockAccountBalance(self):
        for stock in self.account_data['balances']:
            if stock['asset'] == self.stock_code:
                in_wallet_amount = stock['free']
        return float(in_wallet_amount)

    def getBrlBalance(self):
        for stock in self.account_data['balances']:
            if stock['asset'] == 'BRL':
                return float(stock['free'])
        return 0.0

    def getActualTradePosition(self):
        if self.last_stock_account_balance > 0.0001:  # Reduzido para detectar posições menores
            return True
        else:
            return False

    def getStockData_ClosePrice_OpenTime(self):
        candles = self.client_binance.get_klines(symbol = self.operation_code, interval = self.candle_period, limit=1000)
        prices = pd.DataFrame(candles)
        prices.columns = [ 'open_time', 'open_price', 'high_price', 'low_price', 'close_price',
                            'volume', 'close_time', 'quote_asset_volume', 'number_of_trades',
                            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', "-" ]
        prices = prices[["close_price", "open_time"]]
        prices["close_price"] = pd.to_numeric(prices["close_price"])
        prices["open_time"] = pd.to_datetime(prices["open_time"], unit = "ms").dt.tz_localize("UTC")
        prices["open_time"] = prices["open_time"].dt.tz_convert("America/Sao_Paulo")
        return prices

    def getMovingAverageTradeStrategy(self, fast_window = 7, slow_window = 40):
        self.stock_data["ma_fast"] = self.stock_data["close_price"].rolling(window=fast_window).mean()
        self.stock_data["ma_slow"] = self.stock_data["close_price"].rolling(window=slow_window).mean()
        last_ma_fast = self.stock_data["ma_fast"].iloc[-1]
        last_ma_slow = self.stock_data["ma_slow"].iloc[-1]

        # Calcula RSI
        rsi = self.calculateRSI()
        
        # ESTRATÉGIA AGRESSIVA - Compra na queda, vende na alta
        
        # COMPRA: RSI muito baixo (sobrevenda extrema) - oportunidade!
        aggressive_buy = rsi < 25  # Compra quando RSI < 25 (muito oversold)
        
        # VENDA: RSI alto (sobrecompra) OU prejuízo muito grande
        aggressive_sell = rsi > 70  # Vende quando RSI > 70 (overbought)
        
        # Decisão final
        if aggressive_buy:
            ma_trade_decision = True  # COMPRAR na queda
            decision_reason = f"COMPRA AGRESSIVA - RSI {rsi:.1f} (sobrevenda extrema)"
        elif aggressive_sell:
            ma_trade_decision = False  # VENDER na alta
            decision_reason = f"VENDA AGRESSIVA - RSI {rsi:.1f} (sobrecompra)"
        else:
            # Mantém posição atual se RSI neutro (25-70)
            ma_trade_decision = self.actual_trade_position
            decision_reason = f"MANTER - RSI {rsi:.1f} (zona neutra)"
        
        # Log da estratégia agressiva
        print(f'📊 {decision_reason}')
        logging.info(f"Estratégia AGRESSIVA - {decision_reason}")
        
        return ma_trade_decision

    def printWallet(self):
        for stock in self.account_data["balances"]:
            if float(stock["free"]) > 0:
                print(stock)

    def printStock(self):
        for stock in self.account_data["balances"]:
            if stock['asset'] == self.stock_code:
                print(stock)
    
    def printBrl(self):
        for stock in self.account_data["balances"]:
            if stock['asset'] == 'BRL':
                print(stock)

    def formatQuantity(self, quantity):
        """Formata a quantidade para atender ao stepSize da Binance (0.0001)"""
        return round(quantity - (quantity % 0.0001), 4)

    def calculateQuantityForMaxValue(self, max_value_brl):
        try:
            ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
            current_price = float(ticker['price'])
            quantity = self.formatQuantity(max_value_brl / current_price)
            print(f"Preço atual do ETH: R$ {current_price:,.2f}")
            print(f"Quantidade calculada: {quantity} ETH (R$ {max_value_brl:.2f})")
            return quantity
        except Exception as e:
            print(f"Erro ao calcular quantidade ETH: {e}")
            logging.error(f"Erro ao calcular quantidade ETH: {e}")
            return self.traded_quantity

    def buyStock(self):
        if not self.actual_trade_position:
            try:
                brl_balance = self.getBrlBalance()
                available_balance = self.getAvailableBalanceForTrading()
                
                print(f"Saldo total BRL: R$ {brl_balance:.2f}")
                print(f"Saldo reserva: R$ {RESERVE_BALANCE:.2f}")
                print(f"Saldo disponível para trading: R$ {available_balance:.2f}")
                
                # Usa o menor valor entre MAX_TRADE_VALUE e 80% do saldo disponível
                trade_value = min(MAX_TRADE_VALUE, available_balance * 0.8)
                
                if available_balance < trade_value or trade_value < 1.0:
                    print(f"❌ Saldo insuficiente para compra!")
                    print(f"   Necessário: R$ {trade_value:.2f}")
                    print(f"   Disponível: R$ {available_balance:.2f}")
                    if PROFIT_ONLY_MODE:
                        print(f"   💡 Modo LUCRO APENAS ativo - Reserva: R$ {RESERVE_BALANCE:.2f}")
                    logging.warning(f"Saldo insuficiente para compra ETH: R$ {available_balance:.2f}")
                    return False
                
                # Salva o preço atual para controle de lucro e trailing stop
                ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
                self.last_buy_price = float(ticker['price'])
                self.highest_price_since_buy = self.last_buy_price  # Inicializa trailing stop
                
                quantity = self.calculateQuantityForMaxValue(trade_value)
                
                order_buy = self.client_binance.create_order(
                    symbol = self.operation_code,
                    side = SIDE_BUY,
                    type = ORDER_TYPE_MARKET,
                    quantity = quantity,
                )
                self.actual_trade_position = True
                print(f"💰 Compra executada! Preço: R$ {self.last_buy_price:,.2f}")
                print(f"💡 Valor usado: R$ {trade_value:.2f} (do saldo disponível)")
                createLogOrder(order_buy)
                return order_buy
            except Exception as e:
                print(f"Erro ao comprar ETH: {e}")
                logging.error(f"Erro ao comprar ETH: {e}")
                return False
        else: 
            print('Já está em posição de compra ETH, nenhuma ação tomada.')
            return False

    def calculateRSI(self, period=14):
        """Calcula o RSI (Relative Strength Index)"""
        closes = self.stock_data["close_price"]
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def checkStopLoss(self):
        """Verifica se deve executar stop loss"""
        if not self.actual_trade_position or self.last_buy_price <= 0:
            return False
        
        try:
            ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
            current_price = float(ticker['price'])
            loss_percent = (self.last_buy_price - current_price) / self.last_buy_price
            
            if loss_percent >= STOP_LOSS_PERCENT:
                print(f"🚨 STOP LOSS ATIVADO!")
                print(f"   Preço de compra: R$ {self.last_buy_price:,.2f}")
                print(f"   Preço atual: R$ {current_price:,.2f}")
                print(f"   Perda: {loss_percent*100:.2f}%")
                return True
        except:
            pass
        return False

    def checkTrailingStop(self):
        """Verifica trailing stop"""
        if not self.actual_trade_position or self.last_buy_price <= 0:
            return False
        
        try:
            ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
            current_price = float(ticker['price'])
            
            # Atualiza maior preço desde a compra
            if current_price > self.highest_price_since_buy:
                self.highest_price_since_buy = current_price
            
            # Verifica se caiu X% do pico
            if self.highest_price_since_buy > 0:
                drop_from_peak = (self.highest_price_since_buy - current_price) / self.highest_price_since_buy
                
                if drop_from_peak >= TRAILING_STOP_PERCENT:
                    print(f"📉 TRAILING STOP ATIVADO!")
                    print(f"   Pico: R$ {self.highest_price_since_buy:,.2f}")
                    print(f"   Atual: R$ {current_price:,.2f}")
                    print(f"   Queda do pico: {drop_from_peak*100:.2f}%")
                    return True
        except:
            pass
        return False

    def shouldSellForProfit(self):
        """Verifica se deve vender para obter lucro quando saldo BRL está baixo"""
        try:
            ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
            current_price = float(ticker['price'])
            
            # Se tem posição e preço atual é maior que preço de compra + margem
            if self.actual_trade_position and self.last_buy_price > 0:
                target_price = self.last_buy_price * (1 + self.profit_margin)
                if current_price >= target_price:
                    print(f"🎯 OPORTUNIDADE DE LUCRO!")
                    print(f"   Preço de compra: R$ {self.last_buy_price:,.2f}")
                    print(f"   Preço atual: R$ {current_price:,.2f}")
                    print(f"   Lucro: {((current_price/self.last_buy_price)-1)*100:.2f}%")
                    return True
            return False
        except:
            return False
        """Verifica se deve vender para obter lucro quando saldo BRL está baixo"""
        try:
            ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
            current_price = float(ticker['price'])
            
            # Se tem posição e preço atual é maior que preço de compra + margem
            if self.actual_trade_position and self.last_buy_price > 0:
                target_price = self.last_buy_price * (1 + self.profit_margin)
                if current_price >= target_price:
                    print(f"🎯 OPORTUNIDADE DE LUCRO!")
                    print(f"   Preço de compra: R$ {self.last_buy_price:,.2f}")
                    print(f"   Preço atual: R$ {current_price:,.2f}")
                    print(f"   Lucro: {((current_price/self.last_buy_price)-1)*100:.2f}%")
                    return True
            return False
        except:
            return False

    def getAvailableBalanceForTrading(self):
        """Retorna saldo disponível para trading (descontando reserva)"""
        brl_balance = self.getBrlBalance()
        if PROFIT_ONLY_MODE:
            available = brl_balance - RESERVE_BALANCE
            return max(0, available)  # Nunca retorna negativo
        return brl_balance

    def checkLowBalance(self):
        """Verifica se o saldo disponível está muito baixo para continuar comprando"""
        available_balance = self.getAvailableBalanceForTrading()
        return available_balance < MAX_TRADE_VALUE

    def checkMinNotional(self, quantity):
        """Verifica se a quantidade atende ao valor mínimo de R$ 10,00"""
        try:
            ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
            current_price = float(ticker['price'])
            total_value = quantity * current_price
            return total_value >= MIN_NOTIONAL
        except:
            return False

    def sellStock(self):
        if self.actual_trade_position:
            try:
                quantity = self.formatQuantity(self.last_stock_account_balance)
                
                # Verifica se atende ao valor mínimo
                if not self.checkMinNotional(quantity):
                    ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
                    current_price = float(ticker['price'])
                    current_value = quantity * current_price
                    print(f"Valor atual da posição ETH: R$ {current_value:.2f}")
                    print(f"Valor mínimo exigido: R$ {MIN_NOTIONAL:.2f}")
                    print("Posição muito pequena para vender. Aguardando...")
                    logging.warning(f"Posição ETH muito pequena para vender: R$ {current_value:.2f}")
                    return False
                
                order_sell = self.client_binance.create_order(
                    symbol = self.operation_code,
                    side = SIDE_SELL,
                    type = ORDER_TYPE_MARKET,
                    quantity = quantity,
                )
                self.actual_trade_position = False
                createLogOrder(order_sell)
                return order_sell
            except Exception as e:
                print(f"Erro ao vender ETH: {e}")
                logging.error(f"Erro ao vender ETH: {e}")
                return False
        else: 
            print('Não há ETH para vender, nenhuma ação tomada.')
            return False
            
    def execute(self):
        self.updateAllData()
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Log detalhado de heartbeat com percentuais e métricas
        ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
        current_price = float(ticker['price'])
        
        # Calcula variação percentual
        price_change = ""
        if self.previous_price > 0:
            change_percent = ((current_price - self.previous_price) / self.previous_price) * 100
            change_value = current_price - self.previous_price
            if change_percent > 0:
                price_change = f" (+{change_percent:.2f}% +R${change_value:.0f})"
            elif change_percent < 0:
                price_change = f" ({change_percent:.2f}% R${change_value:.0f})"
            else:
                price_change = " (0.00%)"
        
        # Calcula valor da posição atual
        position_value = self.last_stock_account_balance * current_price
        
        # Calcula lucro/prejuízo se tiver posição
        profit_info = ""
        if self.actual_trade_position and self.last_buy_price > 0:
            profit_percent = ((current_price - self.last_buy_price) / self.last_buy_price) * 100
            profit_value = (current_price - self.last_buy_price) * self.last_stock_account_balance
            if profit_percent > 0:
                profit_info = f" | Lucro: +{profit_percent:.1f}% (+R${profit_value:.2f})"
            else:
                profit_info = f" | Prejuízo: {profit_percent:.1f}% (R${profit_value:.2f})"
        
        print(f"🤖 [{current_time}] Bot ativo - ETH: R$ {current_price:,.0f}{price_change} | Posição: {self.last_stock_account_balance:.6f} ETH (R$ {position_value:.2f}) | BRL: R$ {self.getBrlBalance():.2f}{profit_info}")
        logging.info(f"Heartbeat - Preço: R$ {current_price:,.0f}{price_change}, ETH: {self.last_stock_account_balance:.6f} (R$ {position_value:.2f}), BRL: R$ {self.getBrlBalance():.2f}{profit_info}")
        
        # Atualiza preço anterior para próxima comparação
        self.previous_price = current_price

        # Verifica stop loss e trailing stop primeiro
        stop_loss_triggered = self.checkStopLoss()
        trailing_stop_triggered = self.checkTrailingStop()
        
        if stop_loss_triggered or trailing_stop_triggered:
            reason = "STOP LOSS" if stop_loss_triggered else "TRAILING STOP"
            print(f"\n🚨 [{current_time}] VENDA FORÇADA - {reason}!")
            logging.warning(f"VENDA FORÇADA - {reason}")
            self.sellStock()
            time.sleep(2)
            self.updateAllData()
            return

        # Verifica se deve vender com lucro quando saldo está baixo
        low_balance = self.checkLowBalance()
        should_sell_profit = self.shouldSellForProfit()
        
        if low_balance and should_sell_profit:
            print(f"\n💰 [{current_time}] VENDA COM LUCRO - Saldo baixo + Oportunidade!")
            logging.info("VENDA COM LUCRO - Saldo baixo + Oportunidade")
            self.sellStock()
            time.sleep(2)
            self.updateAllData()
            return

        ma_trade_decision = self.getMovingAverageTradeStrategy()
        self.last_trade_decision = ma_trade_decision

        # Lógica normal de trading baseada em médias móveis
        if not self.actual_trade_position and self.last_trade_decision and not low_balance:
            print(f"\n📈 [{current_time}] COMPRANDO ETH - Estratégia favorável!")
            logging.info("COMPRA EXECUTADA - Estratégia favorável")
            self.buyStock()
            time.sleep(2)
            self.updateAllData()
        elif self.actual_trade_position and not self.last_trade_decision:
            print(f"\n📉 [{current_time}] VENDENDO ETH - Estratégia indica venda!")
            logging.info("VENDA EXECUTADA - Estratégia indica venda")
            self.sellStock()
            time.sleep(2)
            self.updateAllData()
        else:
            # Log detalhado do que está bloqueando a ação
            if self.actual_trade_position:
                if self.last_trade_decision:
                    print(f"⏸️  [{current_time}] MANTENDO - Tenho ETH mas estratégia indica COMPRAR")
                    logging.info("BLOQUEIO: Posição ETH + Estratégia indica compra = Manter")
                else:
                    print(f"❓ [{current_time}] ERRO LÓGICO - Deveria vender mas não vendeu!")
                    logging.warning("ERRO: Condição de venda não capturada")
            else:
                if not self.last_trade_decision:
                    print(f"⏸️  [{current_time}] MANTENDO - Sem ETH e estratégia indica VENDER")
                    logging.info("BLOQUEIO: Sem posição + Estratégia indica venda = Manter")
                elif low_balance:
                    print(f"💸 [{current_time}] BLOQUEADO - Saldo baixo (R$ {self.getBrlBalance():.2f}) impede compra")
                    logging.info(f"BLOQUEIO: Saldo insuficiente R$ {self.getBrlBalance():.2f}")
                else:
                    print(f"❓ [{current_time}] ERRO LÓGICO - Deveria comprar mas não comprou!")
                    logging.warning("ERRO: Condição de compra não capturada")

if __name__ == '__main__':
    EthTrader = EthereumTraderBot(STOCK_CODE, OPERATION_CODE, TRADED_QUANTITY, 100, CANDLE_PERIOD)

    while(True):
        try:
            EthTrader.execute()
            print(f"\nAguardando 60 segundos para a próxima execução ETH...\n")
            time.sleep(60)
        except Exception as e:
            print(f"Ocorreu um erro no loop principal ETH: {e}")
            logging.critical(f"Erro no loop principal ETH: {e}")
            time.sleep(60)

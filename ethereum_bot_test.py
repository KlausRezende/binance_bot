#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT ETHEREUM - VERSÃO DE TESTE
Versão de teste que não executa ordens reais na Binance
Apenas simula as operações de Ethereum e salva logs
"""

import os
import time
from datetime import datetime
import logging
import random

# Logger para testes
logging.basicConfig(
    filename='/home/klaus/repo/binance_bot/logs/ethereum_bot_test.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def createLogOrder(order):
    from datetime import datetime
    
    # Extrai informações da ordem simulada
    side = order.get('side', 'N/A')
    symbol = order.get('symbol', 'N/A')
    quantity = float(order.get('quantity', 0))
    avg_price = float(order.get('price', 0))
    order_type = order.get('type', 'N/A')
    
    # Define moeda principal
    main_currency = 'BRL'
    main_value = float(order.get('value', 0))
    
    # Formata data e hora
    now = datetime.now()
    formatted_time = now.strftime("%H:%M:%S")
    formatted_date = now.strftime("%d/%m/%Y")
    
    log_message = f"""
-----------------------------------
ORDEM EXECUTADA (SIMULADA):
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

class EthereumTraderBotTest():
    def __init__(self):
        self.simulated_eth_balance = 0.0
        self.simulated_brl_balance = 12.02
        self.actual_trade_position = False
        self.last_trade_decision = False
        self.max_trade_value = 5.00
        
        print('_________________________________________')
        print(' Robo Trader ETHEREUM TESTE Iniciado... ')
        print(f' Saldo inicial BRL: R$ {self.simulated_brl_balance:.2f}')
        print(f' Saldo inicial ETH: {self.simulated_eth_balance:.5f} ETH')
        logging.info("Bot Ethereum de teste iniciado")

    def getMovingAverageTradeStrategy(self):
        # Simula estratégia com valores aleatórios para teste
        ma_trade_decision = random.choice([True, False])
        
        # Simula valores de médias móveis
        fast_ma = random.uniform(23000, 24000)
        slow_ma = random.uniform(23000, 24000)
        
        print('_________________________________________')
        print('Estratégia executada: Moving Average ETH (SIMULADA)')
        print(f'ETHBRL\n | last_ma_fast: {fast_ma:.3f} = Última Média Rápida \n | last_ma_slow: {slow_ma:.3f} = Última Média Lenta')
        print(f'Decisão de posição: {"Comprar" if ma_trade_decision else "Vender"}')
        print('_________________________________________')
        
        logging.info(f"Estratégia MA ETH simulada - Fast: {fast_ma:.3f}, Slow: {slow_ma:.3f}, Decisão: {'Comprar' if ma_trade_decision else 'Vender'}")
        return ma_trade_decision

    def buyStock(self):
        if not self.actual_trade_position:
            if self.simulated_brl_balance >= self.max_trade_value:
                # Simula compra
                eth_price = random.uniform(23000, 24000)  # Preço simulado
                quantity = self.max_trade_value / eth_price
                
                self.simulated_brl_balance -= self.max_trade_value
                self.simulated_eth_balance += quantity
                self.actual_trade_position = True
                
                order_simulation = {
                    'symbol': 'ETHBRL',
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quantity': round(quantity, 5),
                    'price': eth_price,
                    'value': self.max_trade_value,
                    'status': 'FILLED (SIMULADO)'
                }
                
                createLogOrder(order_simulation)
                print(f"COMPRA SIMULADA: {quantity:.5f} ETH por R$ {self.max_trade_value:.2f}")
                logging.info(f"Compra ETH simulada: {quantity:.5f} ETH por R$ {self.max_trade_value:.2f}")
                return order_simulation
            else:
                print(f"Saldo insuficiente! Necessário: R$ {self.max_trade_value:.2f}, Disponível: R$ {self.simulated_brl_balance:.2f}")
                logging.warning(f"Saldo insuficiente para compra ETH simulada: R$ {self.simulated_brl_balance:.2f}")
                return False
        else:
            print('Já está em posição de compra ETH, nenhuma ação tomada.')
            return False

    def sellStock(self):
        if self.actual_trade_position:
            # Simula venda
            eth_price = random.uniform(23000, 24000)  # Preço simulado
            sell_value = self.simulated_eth_balance * eth_price
            
            self.simulated_brl_balance += sell_value
            sold_quantity = self.simulated_eth_balance
            self.simulated_eth_balance = 0.0
            self.actual_trade_position = False
            
            order_simulation = {
                'symbol': 'ETHBRL',
                'side': 'SELL',
                'type': 'MARKET',
                'quantity': round(sold_quantity, 5),
                'price': eth_price,
                'value': sell_value,
                'status': 'FILLED (SIMULADO)'
            }
            
            createLogOrder(order_simulation)
            print(f"VENDA SIMULADA: {sold_quantity:.5f} ETH por R$ {sell_value:.2f}")
            logging.info(f"Venda ETH simulada: {sold_quantity:.5f} ETH por R$ {sell_value:.2f}")
            return order_simulation
        else:
            print('Não há ETH para vender, nenhuma ação tomada.')
            return False

    def execute(self):
        print('_________________________________________')
        print(f'Executado ETH TESTE ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})') 
        print(f'Posição atual: {"Comprado" if self.actual_trade_position else "Vendido"}')
        print(f'Balanço ETH: {self.simulated_eth_balance:.5f}')
        print(f'Saldo BRL: R$ {self.simulated_brl_balance:.2f}')
        print(f'Valor máximo por operação: R$ {self.max_trade_value:.2f}')
        
        logging.info(f"Execução ETH teste - Posição: {'Comprado' if self.actual_trade_position else 'Vendido'}, ETH: {self.simulated_eth_balance:.5f}, BRL: {self.simulated_brl_balance:.2f}")

        ma_trade_decision = self.getMovingAverageTradeStrategy()
        self.last_trade_decision = ma_trade_decision

        if not self.actual_trade_position and self.last_trade_decision:
            print("\nDecisão: COMPRAR ETH (SIMULADO)")
            self.buyStock()
        elif self.actual_trade_position and not self.last_trade_decision:
            print("\nDecisão: VENDER ETH (SIMULADO)")
            self.sellStock()
        else:
            print("\nDecisão: MANTER POSIÇÃO ETH")
        
        print('_________________________________________')

if __name__ == '__main__':
    print("MODO TESTE ETH - Nenhuma ordem real será executada!")
    TestEthTrader = EthereumTraderBotTest()

    # Executa apenas 10 ciclos para teste
    for i in range(10):
        try:
            TestEthTrader.execute()
            print(f"\nAguardando 5 segundos para próxima execução ETH... ({i+1}/10)\n")
            time.sleep(5)
        except Exception as e:
            print(f"Erro no teste ETH: {e}")
            logging.error(f"Erro no teste ETH: {e}")
            break
    
    print("Teste ETH finalizado!")
    logging.info("Teste ETH finalizado")
